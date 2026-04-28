"""Common interface for exchange adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(slots=True, frozen=True)
class Balance:
    asset: str          # e.g. "USDT" or "BRL" (quote) and "BTC" (base)
    free: Decimal       # available
    locked: Decimal     # in open orders


@dataclass(slots=True, frozen=True)
class Candle:
    open_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


@dataclass(slots=True, frozen=True)
class Order:
    id: str
    symbol: str
    side: str           # "buy" | "sell"
    type: str           # "market" | "limit" | "stop_loss_limit" | "take_profit_limit"
    price: Decimal | None
    quantity: Decimal
    status: str
    created_at: datetime
    filled_quantity: Decimal = Decimal(0)
    average_price: Decimal | None = None


class Exchange(ABC):
    """Abstract exchange adapter. Each concrete adapter trades a single pair."""

    name: str
    symbol: str          # e.g. "BTC/USDT" or "BTC/BRL"
    base: str            # "BTC"
    quote: str           # "USDT" or "BRL"
    min_notional: Decimal  # minimum order value in quote currency

    @abstractmethod
    async def get_balances(self) -> dict[str, Balance]: ...

    @abstractmethod
    async def get_ohlcv(
        self,
        timeframe: str,
        limit: int = 200,
        since: datetime | None = None,
    ) -> list[Candle]: ...

    @abstractmethod
    async def get_ticker(self) -> Decimal:
        """Last traded price."""

    @abstractmethod
    async def place_market_order(self, side: str, quantity: Decimal) -> Order: ...

    @abstractmethod
    async def place_oco_order(
        self,
        side: str,
        quantity: Decimal,
        take_profit: Decimal,
        stop_loss: Decimal,
    ) -> Order:
        """Place a one-cancels-other (TP/SL) order pair."""

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool: ...

    @abstractmethod
    async def get_open_orders(self) -> list[Order]: ...

    @abstractmethod
    async def close(self) -> None: ...
