from __future__ import annotations
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional
import time
import structlog
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from src.config.settings import settings

logger = structlog.get_logger(__name__)

PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"prompt": 0.005, "completion": 0.015},
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
}


@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    finish_reason: str


class LLMService:
    def __init__(self, fallback: Optional[List[str]] = None):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.fallback = fallback or [settings.OPENAI_MODEL, "gpt-4o-mini"]

    @staticmethod
    def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        p = PRICING.get(model, PRICING["gpt-4o-mini"])
        return prompt_tokens / 1000 * p["prompt"] + completion_tokens / 1000 * p["completion"]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8),
           retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError)), reraise=True)
    async def _call(self, model: str, messages: List[Dict[str, str]], **kw) -> Any:
        return await self.client.chat.completions.create(model=model, messages=messages, **kw)

    async def complete(self, messages: List[Dict[str, str]], temperature: float = 0.1,
                       max_tokens: int = 2048, response_format: Optional[Dict[str, str]] = None,
                       tools: Optional[List[Dict]] = None) -> LLMResponse:
        last: Optional[Exception] = None
        for model in self.fallback:
            t0 = time.perf_counter()
            try:
                r = await self._call(model, messages, temperature=temperature, max_tokens=max_tokens,
                                     response_format=response_format, tools=tools)
                u = r.usage
                lat = (time.perf_counter() - t0) * 1000
                logger.info("cognita.llm.complete", model=model, pt=u.prompt_tokens, ct=u.completion_tokens,
                            latency_ms=round(lat, 2),
                            cost_usd=round(self.estimate_cost(model, u.prompt_tokens, u.completion_tokens), 6))
                return LLMResponse(r.choices[0].message.content or "", model, u.prompt_tokens,
                                   u.completion_tokens, lat, r.choices[0].finish_reason or "stop")
            except Exception as e:
                last = e
                logger.warning("cognita.llm.model_failed", model=model, error=str(e))
        raise RuntimeError(f"All LLM fallbacks failed: {last}")

    async def stream(self, messages: List[Dict[str, str]], temperature: float = 0.1,
                     max_tokens: int = 2048) -> AsyncIterator[str]:
        for model in self.fallback:
            try:
                s = await self.client.chat.completions.create(
                    model=model, messages=messages, temperature=temperature, max_tokens=max_tokens,
                    stream=True, stream_options={"include_usage": True})
                async for chunk in s:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception as e:
                logger.warning("cognita.llm.stream_failed", model=model, error=str(e))
        raise RuntimeError("All streaming fallbacks failed")
