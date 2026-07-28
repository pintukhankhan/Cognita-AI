from __future__ import annotations
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from src.services.llm_service import LLMService


@dataclass
class _Rec:
    ts: datetime; model: str; pt: int; ct: int; cost: float


class CostTracker:
    def __init__(self, window_minutes: int = 60):
        self.window = timedelta(minutes=window_minutes)
        self._recs: List[_Rec] = []
        self._lock = asyncio.Lock()

    async def record(self, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        cost = LLMService.estimate_cost(model, prompt_tokens, completion_tokens)
        async with self._lock:
            self._recs.append(_Rec(datetime.now(timezone.utc), model, prompt_tokens, completion_tokens, cost))
            self._prune()

    def _prune(self) -> None:
        cutoff = datetime.now(timezone.utc) - self.window
        self._recs = [r for r in self._recs if r.ts >= cutoff]

    async def summary(self) -> Dict:
        async with self._lock:
            self._prune()
            by: Dict[str, Dict] = {}
            total = 0.0
            for r in self._recs:
                total += r.cost
                m = by.setdefault(r.model, {"cost_usd": 0.0, "prompt_tokens": 0, "completion_tokens": 0, "calls": 0})
                m["cost_usd"] += r.cost; m["prompt_tokens"] += r.pt; m["completion_tokens"] += r.ct; m["calls"] += 1
            return {"window_minutes": int(self.window.total_seconds() / 60),
                    "total_usd": round(total, 6), "by_model": by}
