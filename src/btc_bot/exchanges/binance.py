"""Binance BTC/USDT adapter."""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

import ccxt.async_support as ccxt
import httpx

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


# ---------------------------------------------------------------------------
# Lightweight credential test helpers (no ccxt dependency, plain HTTPS calls).
#
# Used by the API layer to validate keys right after they're saved without
# instantiating the full async ccxt client.
# ---------------------------------------------------------------------------

TestCode = Literal["ok", "auth_failed", "ip_not_whitelisted", "other_error"]


@dataclass(slots=True)
class CredentialTestResult:
    code: TestCode
    message: str
    withdraw_enabled: bool | None = None
    trade_enabled: bool | None = None


def _binance_sign(secret: str, query: str) -> str:
    return hmac.new(secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()


async def test_credentials(api_key: str, api_secret: str) -> CredentialTestResult:
    """Validate Binance credentials by reading the account summary.

    Returns permission flags so the caller can refuse to enable trading if
    `withdraw_enabled` is true.
    """
    timestamp = int(time.time() * 1000)
    query = f"timestamp={timestamp}&recvWindow=5000"
    signature = _binance_sign(api_secret, query)
    url = f"https://api.binance.com/api/v3/account?{query}&signature={signature}"
    headers = {"X-MBX-APIKEY": api_key}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers)
        except httpx.HTTPError as exc:
            return CredentialTestResult(code="other_error", message=f"Network error: {exc}")

    if response.status_code == 200:
        data = response.json()
        return CredentialTestResult(
            code="ok",
            message="Account access verified.",
            withdraw_enabled=bool(data.get("canWithdraw", False)),
            trade_enabled=bool(data.get("canTrade", False)),
        )

    if response.status_code == 401:
        return CredentialTestResult(code="auth_failed", message="Invalid API key or signature.")
    body = response.text[:200]
    if "ip" in body.lower() and ("whitelist" in body.lower() or "allowed" in body.lower()):
        return CredentialTestResult(code="ip_not_whitelisted", message=body)
    return CredentialTestResult(
        code="other_error",
        message=f"HTTP {response.status_code}: {body}",
    )
