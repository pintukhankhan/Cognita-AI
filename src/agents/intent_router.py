from __future__ import annotations
import json
from enum import Enum
from typing import List
from pydantic import BaseModel
import structlog
from src.services.llm_service import LLMService

logger = structlog.get_logger(__name__)


class Intent(str, Enum):
    FACTUAL = "factual"; CHITCHAT = "chitchat"; TOOL_USE = "tool_use"
    CLARIFY = "clarify"; OUT_OF_SCOPE = "out_of_scope"


class RouteDecision(BaseModel):
    intent: Intent
    confidence: float
    needs_retrieval: bool
    needs_tools: bool
    suggested_tools: List[str]
    reasoning: str


PROMPT = ('Classify intent and routing. Tools: {tools}. '
          'Return STRICT JSON {{"intent":"factual|chitchat|tool_use|clarify|out_of_scope",'
          '"confidence":0-1,"needs_retrieval":bool,"needs_tools":bool,'
          '"suggested_tools":[...],"reasoning":"..."}}\n'
          'History:\n{hist}\nUser: {msg}\n')


class IntentRouter:
    def __init__(self, llm: LLMService, available_tools: List[str]):
        self.llm, self.tools = llm, available_tools

    async def route(self, message: str, history: list | None = None) -> RouteDecision:
        h = "\n".join(f"{m['role']}: {m['content']}" for m in (history or [])[-6:]) or "(empty)"
        try:
            r = await self.llm.complete([{"role": "user", "content":
                PROMPT.format(tools=", ".join(self.tools) or "none", hist=h, msg=message)}],
                temperature=0.0, max_tokens=256, response_format={"type": "json_object"})
            return RouteDecision(**json.loads(r.content))
        except Exception as e:
            logger.warning("cognita.intent.parse_fail", error=str(e))
            return RouteDecision(intent=Intent.FACTUAL, confidence=0.5, needs_retrieval=True,
                                 needs_tools=False, suggested_tools=[], reasoning="fallback")
