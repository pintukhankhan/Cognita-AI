from __future__ import annotations
from fastapi import Request
from fastapi.responses import JSONResponse
from src.config.settings import settings


class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def allow(self, ip: str) -> bool:
        key = f"rl:{ip}"
        n = await self.redis.incr(key)
        if n == 1:
            await self.redis.expire(key, settings.RATE_LIMIT_WINDOW)
        return n <= settings.RATE_LIMIT_REQUESTS


async def rate_limit_middleware(request: Request, call_next):
    svc = getattr(request.app.state, "services", None)
    if svc and "rate_limiter" in svc:
        ip = request.client.host if request.client else "unknown"
        if not await svc["rate_limiter"].allow(ip):
            return JSONResponse(status_code=429, content={"detail": "rate limit exceeded"})
    return await call_next(request)
