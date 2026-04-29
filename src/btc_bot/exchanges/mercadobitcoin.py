"""Mercado Bitcoin BTC/BRL adapter.

MB v4 API: https://api.mercadobitcoin.net/api/v4/
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

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


# ---------------------------------------------------------------------------
# Credential test for MB.
# MB v4 uses an "authorize" endpoint: POST /authorize {"login": api_key, "password": api_secret}
# returning an access_token. A successful call validates the credentials.
# ---------------------------------------------------------------------------

TestCode = Literal["ok", "auth_failed", "ip_not_whitelisted", "other_error"]


@dataclass(slots=True)
class CredentialTestResult:
    code: TestCode
    message: str
    withdraw_enabled: bool | None = None
    trade_enabled: bool | None = None


async def test_credentials(api_key: str, api_secret: str) -> CredentialTestResult:
    """Validate MB credentials by exchanging them for an access token."""
    url = "https://api.mercadobitcoin.net/api/v4/authorize"
    payload = {"login": api_key, "password": api_secret}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload)
        except httpx.HTTPError as exc:
            return CredentialTestResult(code="other_error", message=f"Network error: {exc}")

    if response.status_code == 200:
        # MB does not expose granular permissions on /authorize; we mark trade enabled
        # and leave withdraw_enabled unknown — the engine refuses to start trading
        # until the user confirms withdraw is OFF in the panel manually.
        return CredentialTestResult(
            code="ok",
            message="Credentials validated; access token issued.",
            withdraw_enabled=None,
            trade_enabled=True,
        )

    if response.status_code in (401, 403):
        return CredentialTestResult(code="auth_failed", message="Invalid login/password pair.")

    body = response.text[:200]
    return CredentialTestResult(
        code="other_error",
        message=f"HTTP {response.status_code}: {body}",
    )
