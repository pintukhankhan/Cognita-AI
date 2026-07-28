import pytest
import fakeredis.aioredis
from src.agents.memory_manager import MemoryManager

@pytest.mark.asyncio
async def test_roundtrip():
    m = MemoryManager(fakeredis.aioredis.FakeRedis(decode_responses=True))
    await m.add_message("s1", "user", "hello")
    await m.add_message("s1", "assistant", "hi")
    h = await m.get_conversation_history("s1", 10)
    assert [x["role"] for x in h] == ["user", "assistant"]
    await m.set_summary("s1", "greeted")
    assert await m.get_summary("s1") == "greeted"
    await m.clear_session("s1")
    assert await m.get_conversation_history("s1") == []
