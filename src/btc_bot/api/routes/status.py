"""Status / overview endpoint.

Until the live engine is wired, this returns a static snapshot derived from
the configured exchanges plus a 0-bankroll placeholder. Once the engine is
running, replace `_static_status` with a read from the engine's in-memory
state (pulled from the ledger snapshot table).
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from btc_bot.api.auth import require_api_key
from btc_bot.config import settings

router = APIRouter(prefix="/api", tags=["status"], dependencies=[Depends(require_api_key)])

_BOOT_TS = time.time()


class IndicatorReading(BaseModel):
    name: str
    value: float | None
    signal: int
    weight: int


class ConfluenceSnapshot(BaseModel):
    ts: str
    score: int
    score_buy: int
    score_sell: int
    signal: Literal["BUY", "SELL", "NEUTRAL"]
    components: list[IndicatorReading]


class ExchangeStatus(BaseModel):
    id: Literal["binance", "mb"]
    enabled: bool
    symbol: str
    quote: str
    bankroll: float
    bankroll_pct_change_24h: float
    open_position: dict | None
    last_signal: ConfluenceSnapshot | None
    ops_today: int
    realized_pnl_today: float
    paused: bool
    paused_reason: str | None = None


class AIStatus(BaseModel):
    verdict: Literal["veto", "reduce", "neutral", "boost"]
    size_multiplier: float
    reasoning: str
    flagged_items: list[str]
    refreshed_at: str


class GateThresholds(BaseModel):
    min_sharpe: float
    max_drawdown: float
    min_win_rate: float


class GateStatus(BaseModel):
    passed: bool
    exchange: Literal["binance", "mb"]
    ran_at: str | None
    start: str | None
    end: str | None
    initial_bankroll: float | None
    stats: dict | None
    thresholds: GateThresholds


class BotStatus(BaseModel):
    mode: Literal["backtest", "paper", "live"]
    uptime_seconds: float
    exchanges: list[ExchangeStatus]
    ai: AIStatus
    gate: GateStatus
    ts: str


def _empty_exchange(eid: Literal["binance", "mb"]) -> ExchangeStatus:
    return ExchangeStatus(
        id=eid,
        enabled=eid in settings.enabled_exchanges,
        symbol="BTC/USDT" if eid == "binance" else "BTC/BRL",
        quote="USDT" if eid == "binance" else "BRL",
        bankroll=0.0,
        bankroll_pct_change_24h=0.0,
        open_position=None,
        last_signal=None,
        ops_today=0,
        realized_pnl_today=0.0,
        paused=False,
    )


@router.get("/status", response_model=BotStatus)
async def get_status() -> BotStatus:
    return BotStatus(
        mode=settings.mode.value,
        uptime_seconds=time.time() - _BOOT_TS,
        ts=datetime.now(UTC).isoformat(),
        exchanges=[_empty_exchange("binance"), _empty_exchange("mb")],
        ai=AIStatus(
            verdict="neutral",
            size_multiplier=1.0,
            reasoning="AI filter not yet running.",
            flagged_items=[],
            refreshed_at=datetime.now(UTC).isoformat(),
        ),
        gate=GateStatus(
            passed=False,
            exchange="binance",
            ran_at=None,
            start=None,
            end=None,
            initial_bankroll=None,
            stats=None,
            thresholds=GateThresholds(
                min_sharpe=float(settings.gate_min_sharpe),
                max_drawdown=float(settings.gate_max_drawdown_pct),
                min_win_rate=float(settings.gate_min_win_rate),
            ),
        ),
    )
