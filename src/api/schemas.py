from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    metadata: Dict[str, Any] = {}


class ErrorResponse(BaseModel):
    detail: str
