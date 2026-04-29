"""API key auth dependency.

A simple shared-secret header check is sufficient for a single-user bot.
The panel sends `X-API-Key: <settings.api_key>`. CORS is restricted to the
panel's origin.
"""

from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, status

from btc_bot.config import settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = settings.api_key.get_secret_value()
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "X-API-Key"},
        )
