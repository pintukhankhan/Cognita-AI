from __future__ import annotations
import json, uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from src.api.schemas import ChatRequest, ChatResponse
from src.api.middleware.auth import verify_api_key

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(req: Request, body: ChatRequest, _: dict = Depends(verify_api_key)):
    sid = body.session_id or str(uuid.uuid4())
    try:
        res = await req.app.state.services["orchestrator"].process_message(
            session_id=sid, user_id=body.user_id, message=body.message, metadata=body.metadata)
        return ChatResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(req: Request, body: ChatRequest, _: dict = Depends(verify_api_key)):
    sid = body.session_id or str(uuid.uuid4())
    orch = req.app.state.services["orchestrator"]

    async def gen():
        yield f"event: meta\ndata: {json.dumps({'session_id': sid})}\n\n"
        async for tok in orch.process_message_stream(sid, body.user_id, body.message):
            yield f"event: token\ndata: {json.dumps({'t': tok})}\n\n"
        yield f"event: done\ndata: {json.dumps({'session_id': sid})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.delete("/sessions/{session_id}")
async def clear(req: Request, session_id: str, _: dict = Depends(verify_api_key)):
    await req.app.state.services["memory_manager"].clear_session(session_id)
    return {"status": "cleared"}


@router.get("/sessions/{session_id}/history")
async def history(req: Request, session_id: str, limit: int = 10, _: dict = Depends(verify_api_key)):
    h = await req.app.state.services["memory_manager"].get_conversation_history(session_id, limit)
    return {"session_id": session_id, "history": h}
