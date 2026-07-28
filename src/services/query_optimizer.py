from __future__ import annotations
import re
from typing import List

_STOP = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "is", "of"}


def truncate_context(context: str, max_tokens: int = 3000) -> str:
    cap = max_tokens * 4
    if len(context) <= cap:
        return context
    half = cap // 2
    return context[:half] + "\n...[truncated]...\n" + context[-half:]


def compress_history(messages: List[dict], max_messages: int = 6) -> List[dict]:
    if len(messages) <= max_messages:
        return messages
    return [messages[0], {"role": "system", "content": f"[{len(messages) - 2} messages omitted]"}] + messages[-max_messages:]


def keywords(query: str, top_k: int = 5) -> List[str]:
    words = re.findall(r"\b\w+\b", query.lower())
    return [w for w in words if w not in _STOP and len(w) > 2][:top_k]
