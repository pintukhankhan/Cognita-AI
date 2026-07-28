from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class Experiment:
    name: str
    variants: List[str]
    traffic_split: Dict[str, float]
    start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ABTestingService:
    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self.events: List[dict] = []

    def create(self, name: str, variants: List[str], split: Dict[str, float]) -> Experiment:
        if abs(sum(split.values()) - 100.0) > 0.01:
            raise ValueError("split must sum to 100")
        exp = Experiment(name, variants, split)
        self.experiments[name] = exp
        return exp

    def assign(self, name: str, user_id: str) -> str:
        exp = self.experiments[name]
        h = int(hashlib.md5(f"{name}:{user_id}".encode()).hexdigest(), 16) % 100
        cum = 0.0
        for v, pct in exp.traffic_split.items():
            cum += pct
            if h < cum:
                return v
        return exp.variants[-1]

    def record(self, name: str, user_id: str, variant: str, metric: str, value: float) -> None:
        self.events.append({"exp": name, "user": user_id, "variant": variant,
                            "metric": metric, "value": value,
                            "ts": datetime.now(timezone.utc).isoformat()})
