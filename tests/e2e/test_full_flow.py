import uuid, pytest
from httpx import ASGITransport, AsyncClient
from src.main import app

class _FakeOrch:
    async def process_message_stream(self, sid, user, msg):
        for t in ["Hel", "lo"]:
            yield t

class _FakeMem:
    async def get_conversation_history(self, sid, limit=10):
        return [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "Hello"}]

@pytest.mark.asyncio
async def test_stream_and_history():
    app.state.services = {"orchestrator": _FakeOrch(), "memory_manager": _FakeMem()}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        sid = str(uuid.uuid4())
        async with c.stream("POST", "/api/v1/chat/stream",
                            json={"message": "hi", "session_id": sid},
                            headers={"X-API-Key": "test_key"}) as s:
            data = [l async for l in s.aiter_lines() if l.startswith("data:")]
        assert data
        h = await c.get(f"/api/v1/chat/sessions/{sid}/history", headers={"X-API-Key": "test_key"})
        assert h.status_code == 200 and len(h.json()["history"]) == 2
