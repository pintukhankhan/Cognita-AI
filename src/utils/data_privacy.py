import re

_PII = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    (re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"), "[CARD]"),
]


def redact(text: str) -> str:
    for pat, repl in _PII:
        text = pat.sub(repl, text)
    return text


def mask(data: dict, fields: list[str]) -> dict:
    out = dict(data)
    for f in fields:
        if f in out and out[f]:
            out[f] = "***REDACTED***"
    return out
