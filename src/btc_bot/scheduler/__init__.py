"""APScheduler-based loop: one tick per exchange per timeframe.

Jobs:
  - every {timeframe}: engine.tick() per enabled exchange
  - daily 00:05 UTC: snapshot bankrolls, rotate daily state
"""

from __future__ import annotations

import asyncio
import logging
from decimal import Decimal

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from btc_bot.config import Mode, settings
from btc_bot.core.engine import Engine
from btc_bot.exchanges.base import Exchange
from btc_bot.exchanges.binance import BinanceExchange
from btc_bot.exchanges.mercadobitcoin import MercadoBitcoinExchange
from btc_bot.secrets import get_store

log = logging.getLogger(__name__)

# Cron expressions per timeframe
_TF_CRON: dict[str, dict] = {
    "1m":  {"minute": "*"},
    "5m":  {"minute": "*/5"},
    "15m": {"minute": "*/15"},
    "30m": {"minute": "*/30"},
    "1h":  {"minute": "0"},
    "4h":  {"minute": "0", "hour": "*/4"},
    "1d":  {"minute": "0", "hour": "0"},
}

_DEFAULT_BANKROLL: dict[str, Decimal] = {
    "binance": Decimal("50"),
    "mb":      Decimal("250"),
}


def _build_exchange(name: str) -> Exchange | None:
    store = get_store()
    if not store.status(name).has_key:
        log.warning("scheduler: no credentials for %s — skipping", name)
        return None
    with store.with_secret(name) as (key, secret):
        if name == "binance":
            return BinanceExchange(api_key=key, api_secret=secret or "")
        if name == "mb":
            return MercadoBitcoinExchange(api_key=key, api_secret=secret or "")
    return None


def build_scheduler(mode: Mode | None = None) -> AsyncIOScheduler:
    """Build and return a configured AsyncIOScheduler. Call .start() to run."""
    effective_mode = mode or settings.mode
    scheduler = AsyncIOScheduler(timezone="UTC")

    cron_kwargs = _TF_CRON.get(settings.timeframe, {"minute": "*/15"})
    trigger = CronTrigger(timezone="UTC", **cron_kwargs)

    engines: list[Engine] = []
    for exch_name in settings.enabled_exchanges:
        exc = _build_exchange(exch_name)
        if exc is None:
            continue
        bankroll = _DEFAULT_BANKROLL.get(exch_name, Decimal("50"))
        engines.append(Engine(exchange=exc, bankroll=bankroll))
        log.info("scheduler: %s registered (mode=%s tf=%s)", exch_name, effective_mode.value, settings.timeframe)

    if not engines:
        log.error("scheduler: no exchanges configured")
        return scheduler

    async def _tick_all() -> None:
        results = await asyncio.gather(
            *[e.tick(mode=effective_mode) for e in engines],
            return_exceptions=True,
        )
        for r, e in zip(results, engines):
            if isinstance(r, Exception):
                log.error("[%s] tick raised: %s", e.exchange.name, r)

    scheduler.add_job(
        _tick_all,
        trigger=trigger,
        id="tick_all",
        name=f"tick[{settings.timeframe}]",
        max_instances=1,
        misfire_grace_time=30,
    )

    return scheduler
