"""Mercado Bitcoin BTC/BRL adapter — implementation skeleton.

MB v4 API: https://api.mercadobitcoin.net/api/v4/

NOTE: ccxt has limited MB support. We use raw httpx against MB v4.

TODO:
  - implement HMAC SHA256 signing for private endpoints
  - WebSocket book stream for tighter slippage on small books
  - validate min_notional dynamically (current MB minimum ~25 BRL on BTC/BRL)
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import httpx

from btc_bot.exchanges.base import Balance, Candle, Exchange, Order


class MercadoBitcoinExchange(Exchange):
    name = "mb"
    symbol = "BTC/BRL"
    base = "BTC"
    quote = "BRL"
    min_notional = Decimal("25")  # check /symbols endpoint at startup

    BASE_URL = "https://api.mercadobitcoin.net/api/v4"

    def __init__(self, api_key: str, api_secret: str) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._client = httpx.AsyncClient(base_url=self.BASE_URL, timeout=15.0)
        self._access_token: str | None = None

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
        await self._client.aclose()
