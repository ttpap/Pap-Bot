"""Mode + per-exchange enable/disable control endpoints."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from btc_bot.api.auth import require_api_key

router = APIRouter(prefix="/api", tags=["control"], dependencies=[Depends(require_api_key)])


class ModePayload(BaseModel):
    mode: Literal["backtest", "paper", "live"]


@router.post("/mode")
async def set_mode(payload: ModePayload) -> dict:
    if payload.mode == "live":
        # The CLI's `gate` command is the single source of truth. Hard-block from API.
        raise HTTPException(
            status_code=409,
            detail="Live mode must be enabled via CLI after the backtest gate passes.",
        )
    # TODO: mutate the running scheduler config.
    return {"ok": True, "mode": payload.mode}


class TogglePayload(BaseModel):
    enabled: bool


@router.post("/exchanges/{exchange_id}/toggle")
async def toggle_exchange(
    exchange_id: Literal["binance", "mb"],
    payload: TogglePayload,
) -> dict:
    # TODO: mutate the running scheduler config.
    return {"ok": True, "exchange": exchange_id, "enabled": payload.enabled}
