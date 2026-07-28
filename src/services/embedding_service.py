from __future__ import annotations
import hashlib, json, time
from typing import List
import structlog
from openai import AsyncOpenAI, APITimeoutError, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from src.config.settings import settings

logger = structlog.get_logger(__name__)


class EmbeddingService:
    MAX_BATCH = 100

    def __init__(self, redis_client, model: str = settings.OPENAI_EMBEDDING_MODEL):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model
        self.redis = redis_client

    def _key(self, text: str) -> str:
        return f"emb:{self.model}:{hashlib.sha256(text.encode()).hexdigest()}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8),
           retry=retry_if_exception_type((RateLimitError, APITimeoutError)), reraise=True)
    async def _remote(self, texts: List[str]) -> List[List[float]]:
        r = await self.client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in sorted(r.data, key=lambda x: x.index)]

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        out: list = [None] * len(texts)
        keys = [self._key(t) for t in texts]
        cached = await self.redis.mget(*keys)
        miss_idx, miss_txt = [], []
        for i, v in enumerate(cached):
            if v is not None:
                out[i] = json.loads(v)
            else:
                miss_idx.append(i); miss_txt.append(texts[i])
        if miss_txt:
            remote: List[List[float]] = []
            for i in range(0, len(miss_txt), self.MAX_BATCH):
                batch = miss_txt[i:i + self.MAX_BATCH]
                t0 = time.perf_counter()
                remote.extend(await self._remote(batch))
                logger.info("cognita.embed.batch", size=len(batch),
                            latency_ms=round((time.perf_counter() - t0) * 1000, 2))
            pipe = self.redis.pipeline()
            for t, v in zip(miss_txt, remote):
                pipe.setex(self._key(t), 60 * 60 * 24 * 30, json.dumps(v))
            await pipe.execute()
            for idx, v in zip(miss_idx, remote):
                out[idx] = v
        return out

    async def embed_query(self, text: str) -> List[float]:
        return (await self.embed([text]))[0]
