import uuid
from datetime import datetime, timezone


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex}" if prefix else uuid.uuid4().hex


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)
