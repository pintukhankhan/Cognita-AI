from __future__ import annotations
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from src.config.settings import settings

_HEADER = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)

VALID_API_KEYS: dict[str, dict] = {
    "test_key": {"name": "Test", "roles": ["read", "write", "admin"]},
}


def is_valid_api_key(key: str | None) -> bool:
    return bool(key) and key in VALID_API_KEYS


async def verify_api_key(key: str | None = Security(_HEADER)) -> dict:
    if not is_valid_api_key(key):
        raise HTTPException(status_code=401, detail="invalid api key")
    return VALID_API_KEYS[key]  # type: ignore


def require_role(role: str):
    async def _dep(client: dict = Security(verify_api_key)) -> dict:
        if role not in client.get("roles", []):
            raise HTTPException(status_code=403, detail=f"role '{role}' required")
        return client
    return _dep
