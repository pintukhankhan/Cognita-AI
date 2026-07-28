from __future__ import annotations
import asyncio, json
from typing import Any, Dict, List
import structlog
from src.services.llm_service import LLMService

logger = structlog.get_logger(__name__)
PROMPT = ('Score how well DOCUMENT answers QUERY. Return STRICT JSON {{"score":0.0-1.0,"reason":"..."}}\n'
          'QUERY: {q}\nDOCUMENT:\n{d}\n')


class LLMReranker:
    def __init__(self, llm: LLMService, max_concurrent: int = 8, top_k: int = 5):
        self.llm, self.sem, self.top_k = llm, asyncio.Semaphore(max_concurrent), top_k

    async def _one(self, q: str, d: Dict[str, Any]) -> float:
        async with self.sem:
            try:
                r = await self.llm.complete([{"role": "user", "content": PROMPT.format(q=q, d=d["text"][:3000])}],
                                            temperature=0.0, max_tokens=80, response_format={"type": "json_object"})
                return float(json.loads(r.content).get("score", 0.0))
            except Exception as e:
                logger.warning("cognita.rerank.fail", error=str(e))
                return d.get("score", 0.0)

    async def rerank(self, query: str, docs: List[Dict[str, Any]], top_k: int | None = None) -> List[Dict[str, Any]]:
        if not docs:
            return []
        scores = await asyncio.gather(*(self._one(query, d) for d in docs))
        for d, s in zip(docs, scores):
            d["rerank_score"] = s
        return sorted(docs, key=lambda x: x["rerank_score"], reverse=True)[: top_k or self.top_k]
