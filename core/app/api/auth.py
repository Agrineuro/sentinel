import hmac
from fastapi import Header, HTTPException
from app.core.config import settings


def require_api_key(x_sentinel_token: str | None = Header(default=None)):
    expected = settings.api_key
    if not expected:
        if settings.environment.casefold() == "production":
            raise HTTPException(status_code=503, detail="API authentication is not configured")
        return
    if not x_sentinel_token or not hmac.compare_digest(x_sentinel_token, expected):
        raise HTTPException(status_code=401, detail="Valid Sentinel API key required")
