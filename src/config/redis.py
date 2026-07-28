import redis.asyncio as redis
from src.config.settings import settings


def create_redis() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL, decode_responses=True)
