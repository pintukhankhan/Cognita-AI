import pytest
from unittest.mock import AsyncMock
from src.agents.intent_router import IntentRouter

@pytest.mark.asyncio
async def test_fallback_on_error():
    llm = AsyncMock()
    llm.complete = AsyncMock(side_effect=RuntimeError("boom"))
    d = await IntentRouter(llm, ["calculator"]).route("hi")
    assert d.needs_retrieval is True
