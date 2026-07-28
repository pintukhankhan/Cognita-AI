from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class Feedback(BaseModel):
    session_id: str
    message_id: str
    rating: int
    feedback_text: Optional[str] = None
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FeedbackCollector:
    def __init__(self):
        self._store: List[Feedback] = []

    async def submit(self, fb: Feedback) -> None:
        self._store.append(fb)

    async def nps(self) -> float:
        if not self._store:
            return 0.0
        prom = sum(1 for f in self._store if f.rating >= 4)
        det = sum(1 for f in self._store if f.rating <= 2)
        return round((prom - det) / len(self._store) * 100, 2)

    async def low_rating_topics(self, limit: int = 5) -> List[Dict[str, Any]]:
        from collections import Counter
        c = Counter(f.category or "unknown" for f in self._store if f.rating <= 2)
        return [{"category": k, "count": v} for k, v in c.most_common(limit)]
