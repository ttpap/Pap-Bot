"""Mercado Bitcoin BTC/BRL adapter.

MB v4 API: https://api.mercadobitcoin.net/api/v4/
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

import httpx

from btc_bot.exchanges.base import Balance, Candle, Exchange, Order


# ---------------------------------------------------------------------------
# Timeframe mapping bot label → MB candlestick resolution string
# ---------------------------------------------------------------------------
_TF_MB: dict[str, str] = {
    "1m":  "1m",
    "5m":  "5m",
    "15m": "15m",
    "30m": "30m",
    "1h":  "1h",
    "4h":  "4h",
    "1d":  "1d",
}


def _to_candle(raw: dict) -> Candle:
    return Candle(
        open_time=datetime.fromtimestamp(raw["timestamp"], tz=timezone.utc),
        open=Decimal(str(raw["open"])),
        high=Decimal(str(raw["high"])),
        low=Decimal(str(raw["low"])),
        close=Decimal(str(raw["close"])),
        volume=Decimal(str(raw["volume"])),
    )


def _to_order(raw: dict, symbol: str) -> Order:
    side = "buy" if raw.get("side", "").lower() in ("buy", "bid") else "sell"
    status_map = {
        "open":      "open",
        "filled":    "closed",
        "cancelled": "canceled",
        "canceled":  "canceled",
    }
    return Order(
        id=str(raw.get("id", "")),
        symbol=symbol,
        side=side,
        type=raw.get("type", "market").lower(),
        price=Decimal(str(raw["price"])) if raw.get("price") else None,
        quantity=Decimal(str(raw.get("qty", raw.get("quantity", 0)))),
        status=status_map.get(raw.get("status", "").lower(), raw.get("status", "")),
        created_at=datetime.fromtimestamp(
            raw["created_at"], tz=timezone.utc
        ) if raw.get("created_at") else datetime.now(tz=timezone.utc),
        filled_quantity=Decimal(str(raw.get("exec_qty", 0))),
        average_price=Decimal(str(raw["avg_price"])) if raw.get("avg_price") else None,
    )


class MercadoBitcoinExchange(Exchange):
    name = "mb"
    symbol = "BTC/BRL"
    base = "BTC"
    quote = "BRL"
    min_notional = Decimal("25")  # BRL minimum; verify from /symbols

    BASE_URL = "https://api.mercadobitcoin.net/api/v4"
    _PAIR = "BTC-BRL"  # MB v4 pair format

    def __init__(self, api_key: str, api_secret: str) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._client = httpx.AsyncClient(base_url=self.BASE_URL, timeout=15.0)
        self._access_token: str | None = None
        self._token_expiry: float = 0.0

    # ------------------------------------------------------------------
    # Auth: MB v4 uses a JWT obtained from /authorize
    # ------------------------------------------------------------------

    async def _get_token(self) -> str:
        """Return a valid access token, refreshing if expired."""
        if self._access_token and time.time() < self._token_expiry - 30:
            return self._access_token

        resp = await self._client.post(
            "/authorize",
            json={"login": self._api_key, "password": self._api_secret},
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        # MB tokens expire in 1 hour; assume 55m to be safe
        self._token_expiry = time.time() + 55 * 60
        return self._access_token

    def _auth_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    # ------------------------------------------------------------------
    # Market data (public — no auth needed)
    # ------------------------------------------------------------------

    async def get_ohlcv(
        self,
        timeframe: str = "15m",
        limit: int = 200,
        since: datetime | None = None,
    ) -> list[Candle]:
        resolution = _TF_MB.get(timeframe, "15m")
        params: dict = {"resolution": resolution, "limit": limit}
        if since is not None:
            params["from"] = int(since.timestamp())

        resp = await self._client.get(
            f"/{self._PAIR}/candle",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        # MB returns {"candles": [...]} or a list directly
        candles = data.get("candles", data) if isinstance(data, dict) else data
        return [_to_candle(c) for c in candles]

    async def get_ticker(self) -> Decimal:
        resp = await self._client.get(f"/{self._PAIR}/ticker")
        resp.raise_for_status()
        data = resp.json()
        # MB v4: {"pair": "BTC-BRL", "last": "123456.00", ...}
        return Decimal(str(data.get("last", data.get("price", 0))))

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------

    async def get_balances(self) -> dict[str, Balance]:
        token = await self._get_token()
        resp = await self._client.get(
            "/accounts/BTC-BRL/balances",
            headers=self._auth_headers(token),
        )
        resp.raise_for_status()
        data = resp.json()

        result: dict[str, Balance] = {}
        # MB v4 returns a list: [{"symbol": "BRL", "available": "100.00", "on_hold": "0.00"}, ...]
        for item in (data if isinstance(data, list) else [data]):
            asset = item.get("symbol", "")
            if asset in (self.base, self.quote):
                result[asset] = Balance(
                    asset=asset,
                    free=Decimal(str(item.get("available", 0))),
                    locked=Decimal(str(item.get("on_hold", 0))),
                )
        return result

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    async def place_market_order(self, side: str, quantity: Decimal) -> Order:
        token = await self._get_token()
        payload = {
            "async": False,
            "type": "market",
            "side": side,
            "qty": str(quantity),
        }
        resp = await self._client.post(
            f"/{self._PAIR}/orders",
            json=payload,
            headers=self._auth_headers(token),
        )
        resp.raise_for_status()
        return _to_order(resp.json(), self.symbol)

    async def place_oco_order(
        self,
        side: str,
        quantity: Decimal,
        take_profit: Decimal,
        stop_loss: Decimal,
    ) -> Order:
        """
        MB v4 does not have native OCO. Emulate with two limit orders:
        one take-profit limit and one stop-limit.

        Returns the take-profit leg as the primary Order. The caller
        (engine) must track both IDs and cancel the other when one fills.
        """
        token = await self._get_token()
        headers = self._auth_headers(token)

        # Take-profit: sell limit at TP price
        tp_payload = {
            "async": False,
            "type": "limit",
            "side": side,
            "qty": str(quantity),
            "price": str(take_profit),
        }
        tp_resp = await self._client.post(
            f"/{self._PAIR}/orders",
            json=tp_payload,
            headers=headers,
        )
        tp_resp.raise_for_status()
        tp_order = _to_order(tp_resp.json(), self.symbol)

        # Stop-loss: stop-limit order at SL price
        sl_limit = stop_loss * Decimal("0.998")
        sl_payload = {
            "async": False,
            "type": "stop_limit",
            "side": side,
            "qty": str(quantity),
            "stop_price": str(stop_loss),
            "price": str(sl_limit),
        }
        try:
            sl_resp = await self._client.post(
                f"/{self._PAIR}/orders",
                json=sl_payload,
                headers=headers,
            )
            sl_resp.raise_for_status()
        except httpx.HTTPStatusError:
            # If SL order fails, cancel TP to avoid orphan
            await self.cancel_order(tp_order.id)
            raise

        return tp_order  # engine tracks both via tp_order.id + sl_order.id

    async def cancel_order(self, order_id: str) -> bool:
        token = await self._get_token()
        try:
            resp = await self._client.delete(
                f"/{self._PAIR}/orders/{order_id}",
                headers=self._auth_headers(token),
            )
            return resp.status_code in (200, 204)
        except httpx.HTTPStatusError:
            return False

    async def get_open_orders(self) -> list[Order]:
        token = await self._get_token()
        resp = await self._client.get(
            f"/{self._PAIR}/orders",
            params={"status": "open"},
            headers=self._auth_headers(token),
        )
        resp.raise_for_status()
        data = resp.json()
        orders = data.get("orders", data) if isinstance(data, dict) else data
        return [_to_order(o, self.symbol) for o in orders]

    async def close(self) -> None:
        await self._client.aclose()


# ---------------------------------------------------------------------------
# Credential test
# ---------------------------------------------------------------------------

TestCode = Literal["ok", "auth_failed", "ip_not_whitelisted", "other_error"]


@dataclass(slots=True)
class CredentialTestResult:
    code: TestCode
    message: str
    withdraw_enabled: bool | None = None
    trade_enabled: bool | None = None


async def test_credentials(api_key: str, api_secret: str) -> CredentialTestResult:
    """Validate MB credentials via POST /authorize."""
    url = "https://api.mercadobitcoin.net/api/v4/authorize"
    payload = {"login": api_key, "password": api_secret}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload)
        except httpx.HTTPError as exc:
            return CredentialTestResult(code="other_error", message=f"Network error: {exc}")

    if response.status_code == 200:
        return CredentialTestResult(
            code="ok",
            message="Credentials validated; access token issued.",
            withdraw_enabled=None,  # MB /authorize doesn't expose permissions
            trade_enabled=True,
        )

    if response.status_code in (401, 403):
        return CredentialTestResult(code="auth_failed", message="Invalid login/password pair.")

    body = response.text[:200]
    return CredentialTestResult(
        code="other_error",
        message=f"HTTP {response.status_code}: {body}",
    )
