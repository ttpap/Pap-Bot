"""Trade history endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from btc_bot.api.auth import require_api_key

router = APIRouter(prefix="/api", tags=["trades"], dependencies=[Depends(require_api_key)])


@router.get("/trades")
async def list_trades(limit: int = Query(default=50, ge=1, le=500)) -> list[dict]:
    # TODO: read from `trades` table via SQLAlchemy session.
    return []
