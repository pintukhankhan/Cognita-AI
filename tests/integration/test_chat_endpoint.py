import pytest
from httpx import ASGITransport, AsyncClient
from src.main import app

class _FakeOrch:
    async def process_message(self, **kw):
        return {"session_id": kw["session_id"], "response": "ok", "metadata": {}}

@pytest.mark.asyncio
async def test_unauthorized():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        assert (await c.post("/api/v1/chat/", json={"message": "hi"})).status_code == 401

@pytest.mark.asyncio
async def test_authorized_with_stub():
    app.state.services = {"orchestrator": _FakeOrch()}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/api/v1/chat/", json={"message": "hi"}, headers={"X-API-Key": "test_key"})
        assert r.status_code == 200 and r.json()["response"] == "ok"
