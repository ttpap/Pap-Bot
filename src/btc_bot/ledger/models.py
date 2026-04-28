"""SQLAlchemy models for ledger persistence.

Each row records a single fill (executed trade leg). Bankroll snapshots and
daily state are derived from fills.

Bankrolls are isolated per exchange — there is no cross-exchange transfer.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Trade(Base):
    """A complete round-trip (entry + exit). Updated as fills arrive."""

    __tablename__ = "trades"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    exchange: Mapped[str] = mapped_column(String(16), index=True)         # "binance" | "mb"
    symbol: Mapped[str] = mapped_column(String(16), index=True)            # "BTC/USDT" | "BTC/BRL"
    side: Mapped[str] = mapped_column(String(8))                           # "buy" | "sell"
    mode: Mapped[str] = mapped_column(String(16))                          # backtest | paper | live

    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    entry_price: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    exit_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 10), nullable=True)
    stop_loss: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    take_profit: Mapped[Decimal] = mapped_column(Numeric(24, 10))

    pnl: Mapped[Decimal | None] = mapped_column(Numeric(24, 10), nullable=True)
    fees: Mapped[Decimal] = mapped_column(Numeric(24, 10), default=Decimal(0))

    confluence_score: Mapped[int]
    ai_verdict: Mapped[str | None] = mapped_column(String(16), nullable=True)
    ai_size_multiplier: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)

    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    fills: Mapped[list["Fill"]] = relationship(back_populates="trade", cascade="all, delete-orphan")


class Fill(Base):
    """A single execution from the exchange."""

    __tablename__ = "fills"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    trade_id: Mapped[str] = mapped_column(ForeignKey("trades.id", ondelete="CASCADE"), index=True)
    exchange_order_id: Mapped[str] = mapped_column(String(64), index=True)

    side: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    price: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    fee: Mapped[Decimal] = mapped_column(Numeric(24, 10), default=Decimal(0))
    fee_asset: Mapped[str] = mapped_column(String(8))

    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    trade: Mapped[Trade] = relationship(back_populates="fills")


class BankrollSnapshot(Base):
    """End-of-period (or on-demand) snapshot of bankroll per exchange."""

    __tablename__ = "bankroll_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    exchange: Mapped[str] = mapped_column(String(16), index=True)
    quote_currency: Mapped[str] = mapped_column(String(8))   # "USDT" | "BRL"
    quote_balance: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    base_balance: Mapped[Decimal] = mapped_column(Numeric(24, 10))   # BTC
    base_value_in_quote: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    total_in_quote: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class AIDecision(Base):
    """Audit trail of every AI filter verdict."""

    __tablename__ = "ai_decisions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    verdict: Mapped[str] = mapped_column(String(16))
    size_multiplier: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    reasoning: Mapped[str] = mapped_column(Text)
    flagged_items: Mapped[str] = mapped_column(Text)            # JSON list
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
