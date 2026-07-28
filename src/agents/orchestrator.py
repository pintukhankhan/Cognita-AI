from __future__ import annotations
import time
from typing import Any, AsyncIterator, Dict, Optional
import structlog
from src.agents.memory_manager import MemoryManager
from src.agents.reasoning_engine import ReasoningEngine
from src.agents.intent_router import IntentRouter
from src.agents.summarizer import ConversationSummarizer
from src.knowledge.retriever import HybridRetriever
from src.knowledge.reranker import LLMReranker
from src.services.guardrails import Guardrails
from src.services.cost_tracker import CostTracker
from src.services.llm_service import LLMService
from src.utils.metrics import MetricsCollector
from src.utils.helpers import estimate_tokens

logger = structlog.get_logger(__name__)
_FALLBACK = "I'm sorry, I couldn't produce a safe answer for that request."


class AgentOrchestrator:
    def __init__(self, *, memory_manager: MemoryManager, reasoning_engine: ReasoningEngine,
                 retriever: HybridRetriever, llm: LLMService, intent_router: IntentRouter,
                 reranker: LLMReranker, guardrails: Guardrails, summarizer: ConversationSummarizer,
                 cost_tracker: CostTracker, metrics: Optional[MetricsCollector] = None):
        self.mem = memory_manager
        self.reason = reasoning_engine
        self.ret = retriever
        self.llm = llm
        self.router = intent_router
        self.rerank = reranker
        self.guard = guardrails
        self.summ = summarizer
        self.cost = cost_tracker
        self.metrics = metrics

    async def _prepare(self, session_id: str, message: str):
        verdict = self.guard.check_input(message)
        if not verdict.safe:
            return None, None, verdict
        safe_msg = verdict.sanitized or message
        await self.mem.add_message(session_id, "user", safe_msg)
        history = await self.mem.get_conversation_history(session_id, 10)
        decision = await self.router.route(safe_msg, history)
        context = ""
        if decision.needs_retrieval:
            r = await self.ret.retrieve(safe_msg, top_k=8)
            if r["vector_results"]:
                r["vector_results"] = await self.rerank.rerank(safe_msg, r["vector_results"], top_k=5)
            context = r["combined_context"]
        summary = await self.mem.get_summary(session_id)
        return safe_msg, self.reason.build_messages(safe_msg, context, history, summary), verdict

    async def _finalize(self, session_id: str, answer: str, prompt_msgs: list, model: str):
        out = self.guard.check_output(answer)
        final = out.sanitized if out.safe else _FALLBACK
        await self.mem.add_message(session_id, "assistant", final)
        await self.cost.record(model, estimate_tokens("".join(m["content"] for m in prompt_msgs)),
                               estimate_tokens(final))
        hist = await self.mem.get_conversation_history(session_id, 20)
        new_sum = await self.summ.maybe_summarize(hist, await self.mem.get_summary(session_id))
        if new_sum:
            await self.mem.set_summary(session_id, new_sum)
        return final

    async def process_message(self, session_id: str, user_id: Optional[str],
                              message: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        t0 = time.perf_counter()
        safe_msg, msgs, verdict = await self._prepare(session_id, message)
        if msgs is None:
            return {"session_id": session_id, "response": _FALLBACK,
                    "metadata": {"blocked": True, "reason": verdict.reason}}
        resp = await self.reason.reason(msgs)
        final = await self._finalize(session_id, resp.content, msgs, resp.model)
        if self.metrics:
            self.metrics.record_message("ok", "chat")
        return {"session_id": session_id, "response": final,
                "metadata": {"latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                             "model": resp.model, "tokens": resp.prompt_tokens + resp.completion_tokens}}

    async def process_message_stream(self, session_id: str, user_id: Optional[str],
                                     message: str) -> AsyncIterator[str]:
        safe_msg, msgs, verdict = await self._prepare(session_id, message)
        if msgs is None:
            yield _FALLBACK
            return
        buf: list[str] = []
        async for delta in self.llm.stream(msgs):
            buf.append(delta)
            yield delta
        await self._finalize(session_id, "".join(buf), msgs, self.llm.fallback[0])
