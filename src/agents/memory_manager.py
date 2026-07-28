from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from src.utils.helpers import utcnow
import structlog

logger = structlog.get_logger(__name__)


class MemoryManager:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def add_message(self, session_id: str, role: str, content: str,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        msg = json.dumps({"role": role, "content": content,
                          "ts": utcnow().isoformat(), "metadata": metadata or {}})
        key = f"session:{session_id}:messages"
        await self.redis.lpush(key, msg)
        await self.redis.ltrim(key, 0, 49)
        await self.redis.expire(key, 3600 * 24)
        return True

    async def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        raw = await self.redis.lrange(f"session:{session_id}:messages", 0, limit - 1)
        hist = [json.loads(m) for m in raw]
        hist.reverse()
        return hist

    async def get_summary(self, session_id: str) -> str:
        return await self.redis.get(f"session:{session_id}:summary") or ""

    async def set_summary(self, session_id: str, text: str) -> None:
        await self.redis.setex(f"session:{session_id}:summary", 3600 * 24 * 7, text)

    async def clear_session(self, session_id: str) -> bool:
        await self.redis.delete(f"session:{session_id}:messages", f"session:{session_id}:summary")
        return True

    async def close(self) -> None:
        await self.redis.aclose()
