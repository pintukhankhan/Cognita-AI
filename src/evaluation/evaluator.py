from __future__ import annotations
import asyncio, json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List
from src.services.llm_service import LLMService

JUDGE = ('Rate 0-1 the ACTUAL answer vs EXPECTED for the QUESTION on accuracy, completeness, clarity.\n'
         'Return STRICT JSON {{"score":0-1,"feedback":"..."}}\n'
         'QUESTION: {q}\nEXPECTED: {e}\nACTUAL: {a}\n')


@dataclass
class EvalResult:
    question: str; expected: str; actual: str; score: float; feedback: str


class AgentEvaluator:
    def __init__(self, llm: LLMService):
        self.llm = llm

    async def evaluate(self, q: str, expected: str, actual: str) -> EvalResult:
        try:
            r = await self.llm.complete([{"role": "user", "content": JUDGE.format(q=q, e=expected, a=actual)}],
                                        temperature=0.0, max_tokens=120, response_format={"type": "json_object"})
            d = json.loads(r.content)
            return EvalResult(q, expected, actual, float(d.get("score", 0.0)), d.get("feedback", ""))
        except Exception:
            return EvalResult(q, expected, actual, 0.0, "judge failed")

    async def batch(self, cases: List[Dict[str, str]], conc: int = 5) -> List[EvalResult]:
        sem = asyncio.Semaphore(conc)
        async def one(c):
            async with sem:
                return await self.evaluate(c["question"], c["expected_answer"], c["actual_answer"])
        return await asyncio.gather(*(one(c) for c in cases))

    def report(self, results: List[EvalResult]) -> Dict[str, Any]:
        scores = [r.score for r in results]
        return {"count": len(results), "avg": round(sum(scores) / max(len(scores), 1), 3),
                "min": round(min(scores), 3) if scores else 0,
                "max": round(max(scores), 3) if scores else 0,
                "ts": datetime.now(timezone.utc).isoformat()}
