from __future__ import annotations
import hashlib
from typing import Optional


class ResponseCache:
    def __init__(self, redis_client, ttl_hours: int = 24):
        self.redis = redis_client
        self.ttl = ttl_hours * 3600

    def _key(self, prompt: str, model: str) -> str:
        return f"resp:{model}:{hashlib.md5(prompt.encode()).hexdigest()}"

    async def get(self, prompt: str, model: str) -> Optional[str]:
        return await self.redis.get(self._key(prompt, model))

    async def set(self, prompt: str, model: str, response: str) -> None:
        await self.redis.setex(self._key(prompt, model), self.ttl, response)

    async def get_stats(self) -> dict:
        info = await self.redis.info("stats")
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        return {"hits": hits, "misses": misses, "hit_rate": round(hits / max(hits + misses, 1), 4)}
