from __future__ import annotations
import uuid
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from src.api.middleware.auth import is_valid_api_key

router = APIRouter()


@router.websocket("/ws")
async def ws(ws: WebSocket, api_key: str = Query(...), session_id: str | None = None):
    if not is_valid_api_key(api_key):
        await ws.close(code=4001); return
    await ws.accept()
    sid = session_id or str(uuid.uuid4())
    orch = ws.app.state.services["orchestrator"]
    await ws.send_json({"type": "meta", "session_id": sid})
    try:
        while True:
            msg = (await ws.receive_json()).get("message", "").strip()
            if not msg:
                continue
            await ws.send_json({"type": "start"})
            async for tok in orch.process_message_stream(sid, None, msg):
                await ws.send_json({"type": "token", "t": tok})
            await ws.send_json({"type": "end", "session_id": sid})
    except WebSocketDisconnect:
        pass
