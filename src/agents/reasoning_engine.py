from __future__ import annotations
from typing import Dict, List
import structlog
from src.services.llm_service import LLMService, LLMResponse
from src.services.query_optimizer import compress_history

logger = structlog.get_logger(__name__)
_BASE = ("You are Cognita, a precise knowledge-grounded AI assistant. "
         "Answer using the provided context and cite it as [n]. "
         "If the answer is not in the context, say so honestly. Be concise and accurate.")


class ReasoningEngine:
    def __init__(self, llm: LLMService):
        self.llm = llm

    def build_messages(self, user_input: str, context: str, history: List[dict],
                       summary: str = "") -> List[Dict[str, str]]:
        sys = _BASE
        if context:
            sys += f"\n\nKNOWLEDGE CONTEXT:\n{context}"
        if summary:
            sys += f"\n\nCONVERSATION SUMMARY:\n{summary}"
        msgs: List[Dict[str, str]] = [{"role": "system", "content": sys}]
        for m in compress_history(history, 8):
            if m["role"] in ("user", "assistant"):
                msgs.append({"role": m["role"], "content": m["content"]})
        msgs.append({"role": "user", "content": user_input})
        return msgs

    async def reason(self, messages: List[Dict[str, str]]) -> LLMResponse:
        return await self.llm.complete(messages)
