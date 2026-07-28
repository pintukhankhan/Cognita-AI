from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
import structlog
from src.utils.data_privacy import redact

logger = structlog.get_logger(__name__)
_BLOCK = ["ignore previous instructions", "jailbreak", "dan mode", "reveal system prompt"]
_MAX = 8000


class Verdict(BaseModel):
    safe: bool
    reason: Optional[str] = None
    sanitized: Optional[str] = None


class Guardrails:
    def __init__(self, blocklist: Optional[List[str]] = None):
        self.blocklist = [b.lower() for b in (blocklist or _BLOCK)]

    def check_input(self, text: str) -> Verdict:
        if not text or not text.strip():
            return Verdict(safe=False, reason="empty_input")
        if len(text) > _MAX:
            return Verdict(safe=False, reason="input_too_long")
        low = text.lower()
        for ph in self.blocklist:
            if ph in low:
                logger.warning("cognita.guardrails.injection", phrase=ph)
                return Verdict(safe=False, reason=f"injection:{ph}")
        return Verdict(safe=True, sanitized=redact(text))

    def check_output(self, text: str) -> Verdict:
        cleaned = redact(text)
        if not cleaned.strip():
            return Verdict(safe=False, reason="empty_output", sanitized=cleaned)
        return Verdict(safe=True, sanitized=cleaned)
