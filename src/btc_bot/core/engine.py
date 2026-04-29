"""Trading engine — one tick per exchange per timeframe interval.

Flow per tick:
  candles → indicators → confluence → [AI filter] → risk check → order
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd

from btc_bot.config import Mode, settings
from btc_bot.exchanges.base import Exchange, Order
from btc_bot.risk.manager import RiskManager, RiskParameters, atr as calc_atr
from btc_bot.strategy.confluence import ConfluenceResult, evaluate

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lightweight in-process position tracker (replaces DB until ledger is wired)
# ---------------------------------------------------------------------------

@dataclass
class OpenPosition:
    exchange: str
    side: str
    quantity: Decimal
    entry_price: Decimal
    take_profit: Decimal
    stop_loss: Decimal
    entry_order_id: str
    tp_order_id: str | None = None
    sl_order_id: str | None = None
    opened_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


@dataclass
class DailyState:
    date: str = ""
    realized_pnl: Decimal = Decimal(0)
    ops: int = 0

    def reset_if_new_day(self) -> None:
        today = datetime.now(tz=timezone.utc).date().isoformat()
        if self.date != today:
            self.date = today
            self.realized_pnl = Decimal(0)
            self.ops = 0


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class Engine:
    """Stateful engine for one exchange. The scheduler creates one per exchange."""

    def __init__(self, exchange: Exchange, bankroll: Decimal) -> None:
        self.exchange = exchange
        self.bankroll = bankroll  # updated after each closed trade
        self.risk = RiskManager(
            RiskParameters(
                max_position_pct=settings.max_position_pct,
                atr_stop_multiplier=settings.atr_stop_multiplier,
                atr_tp_multiplier=settings.atr_tp_multiplier,
                daily_loss_limit_pct=settings.daily_loss_limit_pct,
                max_ops_per_day=settings.max_ops_per_day,
                min_notional=exchange.min_notional,
            )
        )
        self._position: OpenPosition | None = None
        self._daily = DailyState()
        self._paused = False
        self._pause_reason = ""

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    @property
    def has_position(self) -> bool:
        return self._position is not None

    @property
    def paused(self) -> bool:
        return self._paused

    def pause(self, reason: str = "") -> None:
        self._paused = True
        self._pause_reason = reason
        log.warning("[%s] engine paused: %s", self.exchange.name, reason)

    def resume(self) -> None:
        self._paused = False
        self._pause_reason = ""

    async def tick(self, mode: Mode = Mode.paper) -> None:
        """Run one tick. Called every timeframe interval by the scheduler."""
        self._daily.reset_if_new_day()

        if self._paused:
            log.info("[%s] paused (%s) — skipping tick", self.exchange.name, self._pause_reason)
            return

        # --- 1. Fetch candles ---
        try:
            candles = await self.exchange.get_ohlcv(
                timeframe=settings.timeframe,
                limit=250,
            )
        except Exception as exc:
            log.error("[%s] get_ohlcv failed: %s", self.exchange.name, exc)
            return

        if len(candles) < 30:
            log.warning("[%s] not enough candles (%d)", self.exchange.name, len(candles))
            return

        closes = pd.Series(
            [float(c.close) for c in candles],
            name="close",
        )

        # --- 2. Check open position exit ---
        if self._position is not None:
            await self._check_position_exit(closes)
            return  # only one position at a time

        # --- 3. Confluence signal ---
        try:
            result: ConfluenceResult = evaluate(closes)
        except Exception as exc:
            log.error("[%s] confluence error: %s", self.exchange.name, exc)
            return

        log.info(
            "[%s] score=%+d (buy=%d sell=%d) → %s",
            self.exchange.name,
            result.score,
            result.score_buy,
            result.score_sell,
            result.signal.name,
        )

        from btc_bot.strategy.confluence import Signal
        if abs(result.score) < settings.min_confluence_score:
            return
        if result.signal == Signal.NEUTRAL:
            return

        # --- 4. Risk gate ---
        from datetime import date
        allowed, reason = self.risk.can_open(
            today=date.today(),
            bankroll=self.bankroll,
        )
        if not allowed:
            log.info("[%s] risk gate blocked: %s", self.exchange.name, reason)
            if "daily loss" in reason.lower():
                self.pause("daily loss limit hit")
            return

        # --- 5. ATR-based sizing ---
        df_atr = pd.DataFrame({
            "high":  [float(c.high)  for c in candles],
            "low":   [float(c.low)   for c in candles],
            "close": [float(c.close) for c in candles],
        })
        atr_series = calc_atr(df_atr)
        atr_val = Decimal(str(atr_series.iloc[-1]))

        entry_price = Decimal(str(closes.iloc[-1]))
        side = "buy" if result.signal == Signal.BUY else "sell"

        plan = self.risk.plan_trade(
            side=side,
            bankroll=self.bankroll,
            entry_price=entry_price,
            atr_value=atr_val,
        )
        if plan is None:
            log.info("[%s] plan_trade returned None (min_notional or sizing)", self.exchange.name)
            return

        log.info(
            "[%s] signal=%s qty=%s entry=%s tp=%s sl=%s",
            self.exchange.name, side,
            plan.quantity, entry_price, plan.take_profit, plan.stop_loss,
        )

        # --- 6. Execute (skip in backtest / paper if engine is called in dry-run) ---
        if mode == Mode.backtest:
            log.info("[%s] backtest mode — no order sent", self.exchange.name)
            self._daily.ops += 1
            return

        try:
            entry_order = await self.exchange.place_market_order(side, plan.quantity)
        except Exception as exc:
            log.error("[%s] place_market_order failed: %s", self.exchange.name, exc)
            return

        if mode == Mode.paper:
            log.info("[%s] paper mode — entry logged, no OCO placed", self.exchange.name)
            self._position = OpenPosition(
                exchange=self.exchange.name,
                side=side,
                quantity=plan.quantity,
                entry_price=entry_price,
                take_profit=plan.take_profit,
                stop_loss=plan.stop_loss,
                entry_order_id=entry_order.id,
            )
            self._daily.ops += 1
            return

        # Live: place OCO
        try:
            exit_side = "sell" if side == "buy" else "buy"
            oco_order = await self.exchange.place_oco_order(
                exit_side, plan.quantity, plan.take_profit, plan.stop_loss
            )
            self._position = OpenPosition(
                exchange=self.exchange.name,
                side=side,
                quantity=plan.quantity,
                entry_price=entry_price,
                take_profit=plan.take_profit,
                stop_loss=plan.stop_loss,
                entry_order_id=entry_order.id,
                tp_order_id=oco_order.id,
            )
            self._daily.ops += 1
            log.info("[%s] live position opened, OCO=%s", self.exchange.name, oco_order.id)
        except Exception as exc:
            log.error("[%s] place_oco_order failed: %s", self.exchange.name, exc)

    # ------------------------------------------------------------------
    # Position exit check (paper: price-based; live: order status)
    # ------------------------------------------------------------------

    async def _check_position_exit(self, closes: pd.Series) -> None:
        pos = self._position
        if pos is None:
            return

        current_price = Decimal(str(closes.iloc[-1]))

        if pos.side == "buy":
            hit_tp = current_price >= pos.take_profit
            hit_sl = current_price <= pos.stop_loss
        else:
            hit_tp = current_price <= pos.take_profit
            hit_sl = current_price >= pos.stop_loss

        exit_price: Decimal | None = None
        if hit_tp:
            exit_price = pos.take_profit
            log.info("[%s] take-profit hit @ %s", self.exchange.name, exit_price)
        elif hit_sl:
            exit_price = pos.stop_loss
            log.info("[%s] stop-loss hit @ %s", self.exchange.name, exit_price)

        if exit_price is not None:
            pnl = self._calc_pnl(pos, exit_price)
            self.bankroll += pnl
            self._daily.realized_pnl += pnl
            log.info(
                "[%s] position closed pnl=%+.4f bankroll=%s",
                self.exchange.name, float(pnl), self.bankroll,
            )
            self._position = None

    def _calc_pnl(self, pos: OpenPosition, exit_price: Decimal) -> Decimal:
        if pos.side == "buy":
            return (exit_price - pos.entry_price) * pos.quantity
        else:
            return (pos.entry_price - exit_price) * pos.quantity
