"""Binance BTC/USDT adapter — implementation skeleton.

Uses ccxt async for unified API.

TODO:
  - implement real calls
  - add retry/backoff on rate limits
  - validate min_notional dynamically from /exchangeInfo
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import ccxt.async_support as ccxt

from btc_bot.exchanges.base import Balance, Candle, Exchange, Order


class BinanceExchange(Exchange):
    name = "binance"
    symbol = "BTC/USDT"
    base = "BTC"
    quote = "USDT"
    min_notional = Decimal("10")  # ~ Binance default for spot pairs; refresh from API

    def __init__(self, api_key: str, api_secret: str) -> None:
        self._client = ccxt.binance(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "options": {"defaultType": "spot"},
            }
        )

    async def get_balances(self) -> dict[str, Balance]:
        raise NotImplementedError

    async def get_ohlcv(
        self,
        timeframe: str,
        limit: int = 200,
        since: datetime | None = None,
    ) -> list[Candle]:
        raise NotImplementedError

    async def get_ticker(self) -> Decimal:
        raise NotImplementedError

    async def place_market_order(self, side: str, quantity: Decimal) -> Order:
        raise NotImplementedError

    async def place_oco_order(
        self,
        side: str,
        quantity: Decimal,
        take_profit: Decimal,
        stop_loss: Decimal,
    ) -> Order:
        raise NotImplementedError

    async def cancel_order(self, order_id: str) -> bool:
        raise NotImplementedError

    async def get_open_orders(self) -> list[Order]:
        raise NotImplementedError

    async def close(self) -> None:
        await self._client.close()
