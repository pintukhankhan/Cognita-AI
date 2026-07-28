from __future__ import annotations
from typing import List
import structlog
from src.services.llm_service import LLMService

logger = structlog.get_logger(__name__)
PROMPT = ('Update the running conversation summary. Keep goals, facts, decisions, open questions. '
          'Drop filler.\nPREVIOUS:\n{prev}\nNEW:\n{msgs}\nNEW SUMMARY (<=200 words):')


class ConversationSummarizer:
    def __init__(self, llm: LLMService, trigger_every: int = 10):
        self.llm, self.trigger = llm, trigger_every

    async def maybe_summarize(self, history: List[dict], previous: str = "") -> str | None:
        if len(history) < self.trigger:
            return None
        msgs = "\n".join(f"{m['role']}: {m['content']}" for m in history[-self.trigger:])
        r = await self.llm.complete([{"role": "user", "content": PROMPT.format(prev=previous or "(none)", msgs=msgs)}],
                                    temperature=0.2, max_tokens=400)
        return r.content.strip()
