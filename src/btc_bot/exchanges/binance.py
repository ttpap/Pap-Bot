"""Binance BTC/USDT adapter."""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

import ccxt.async_support as ccxt
import httpx

from btc_bot.exchanges.base import Balance, Candle, Exchange, Order


# ---------------------------------------------------------------------------
# Timeframe mapping ccxt → milliseconds (for `since` conversion)
# ---------------------------------------------------------------------------
_TF_MS: dict[str, int] = {
    "1m": 60_000,
    "3m": 3 * 60_000,
    "5m": 5 * 60_000,
    "15m": 15 * 60_000,
    "30m": 30 * 60_000,
    "1h": 3_600_000,
    "4h": 4 * 3_600_000,
    "1d": 86_400_000,
}


def _to_candle(raw: list) -> Candle:
    """Convert ccxt OHLCV row [ts_ms, o, h, l, c, v] to Candle."""
    return Candle(
        open_time=datetime.fromtimestamp(raw[0] / 1000, tz=timezone.utc),
        open=Decimal(str(raw[1])),
        high=Decimal(str(raw[2])),
        low=Decimal(str(raw[3])),
        close=Decimal(str(raw[4])),
        volume=Decimal(str(raw[5])),
    )


def _to_order(raw: dict) -> Order:
    """Convert ccxt order dict to Order dataclass."""
    return Order(
        id=str(raw["id"]),
        symbol=raw["symbol"],
        side=raw["side"],
        type=raw["type"],
        price=Decimal(str(raw["price"])) if raw.get("price") else None,
        quantity=Decimal(str(raw["amount"])),
        status=raw["status"],
        created_at=datetime.fromtimestamp(
            raw["timestamp"] / 1000, tz=timezone.utc
        ) if raw.get("timestamp") else datetime.now(tz=timezone.utc),
        filled_quantity=Decimal(str(raw.get("filled") or 0)),
        average_price=Decimal(str(raw["average"])) if raw.get("average") else None,
    )


class BinanceExchange(Exchange):
    name = "binance"
    symbol = "BTC/USDT"
    base = "BTC"
    quote = "USDT"
    min_notional = Decimal("10")  # Binance spot default; refreshed from /exchangeInfo

    def __init__(self, api_key: str, api_secret: str) -> None:
        self._client = ccxt.binance(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "options": {"defaultType": "spot"},
            }
        )

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------

    async def get_ohlcv(
        self,
        timeframe: str = "15m",
        limit: int = 200,
        since: datetime | None = None,
    ) -> list[Candle]:
        since_ms: int | None = None
        if since is not None:
            since_ms = int(since.timestamp() * 1000)

        rows = await self._client.fetch_ohlcv(
            self.symbol,
            timeframe=timeframe,
            since=since_ms,
            limit=limit,
        )
        return [_to_candle(r) for r in rows]

    async def get_ticker(self) -> Decimal:
        ticker = await self._client.fetch_ticker(self.symbol)
        return Decimal(str(ticker["last"]))

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------

    async def get_balances(self) -> dict[str, Balance]:
        data = await self._client.fetch_balance()
        result: dict[str, Balance] = {}
        for asset in (self.base, self.quote):
            info = data.get(asset, {})
            result[asset] = Balance(
                asset=asset,
                free=Decimal(str(info.get("free", 0))),
                locked=Decimal(str(info.get("used", 0))),
            )
        return result

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    async def place_market_order(self, side: str, quantity: Decimal) -> Order:
        """
        Place a market order.

        side: "buy" | "sell"
        quantity: BTC amount (base asset)
        """
        raw = await self._client.create_order(
            symbol=self.symbol,
            type="market",
            side=side,
            amount=float(quantity),
        )
        return _to_order(raw)

    async def place_oco_order(
        self,
        side: str,
        quantity: Decimal,
        take_profit: Decimal,
        stop_loss: Decimal,
    ) -> Order:
        """
        Place a Binance OCO order (take-profit limit + stop-loss).

        Binance OCO for sell:
          - listClientOrderId: arbitrary
          - price:      take-profit limit price
          - stopPrice:  stop trigger price
          - stopLimitPrice: limit price at the stop (set slightly below stop)

        Returns the take-profit leg as the representative Order.
        """
        sl_limit = stop_loss * Decimal("0.998")  # 0.2% slippage buffer below stop

        params: dict = {
            "listClientOrderId": f"oco-{int(time.time()*1000)}",
            "stopPrice": float(stop_loss),
            "stopLimitPrice": float(sl_limit),
            "stopLimitTimeInForce": "GTC",
        }

        raw = await self._client.create_order(
            symbol=self.symbol,
            type="oco",
            side=side,
            amount=float(quantity),
            price=float(take_profit),
            params=params,
        )

        # ccxt returns the OCO response; wrap the first leg as our Order
        orders = raw.get("orders") or raw.get("orderReports", [])
        if orders:
            leg = orders[0]
            return Order(
                id=str(leg.get("orderId", raw.get("id", ""))),
                symbol=self.symbol,
                side=side,
                type="oco",
                price=take_profit,
                quantity=quantity,
                status="open",
                created_at=datetime.now(tz=timezone.utc),
            )

        return Order(
            id=str(raw.get("id", "")),
            symbol=self.symbol,
            side=side,
            type="oco",
            price=take_profit,
            quantity=quantity,
            status="open",
            created_at=datetime.now(tz=timezone.utc),
        )

    async def cancel_order(self, order_id: str) -> bool:
        try:
            await self._client.cancel_order(order_id, self.symbol)
            return True
        except ccxt.OrderNotFound:
            return False

    async def get_open_orders(self) -> list[Order]:
        raws = await self._client.fetch_open_orders(self.symbol)
        return [_to_order(r) for r in raws]

    async def close(self) -> None:
        await self._client.close()


# ---------------------------------------------------------------------------
# Lightweight credential test (no ccxt — plain HTTPS)
# ---------------------------------------------------------------------------

TestCode = Literal["ok", "auth_failed", "ip_not_whitelisted", "other_error"]


@dataclass(slots=True)
class CredentialTestResult:
    code: TestCode
    message: str
    withdraw_enabled: bool | None = None
    trade_enabled: bool | None = None


def _binance_sign(secret: str, query: str) -> str:
    return hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()


async def test_credentials(api_key: str, api_secret: str) -> CredentialTestResult:
    """Validate Binance credentials via GET /api/v3/account."""
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
