"""Risk manager: position sizing, ATR stop/TP, daily loss cap, ops cap.

All money math uses Decimal to avoid binary float drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_DOWN, Decimal

import pandas as pd


@dataclass(slots=True)
class RiskParameters:
    max_position_pct: Decimal           # e.g. Decimal("0.50")
    atr_stop_multiplier: Decimal        # e.g. Decimal("1.5")
    atr_tp_multiplier: Decimal          # e.g. Decimal("3.0")
    daily_loss_limit_pct: Decimal       # e.g. Decimal("0.03")
    max_ops_per_day: int                # e.g. 5
    min_notional: Decimal               # exchange-specific


@dataclass(slots=True)
class DailyState:
    day: date
    realized_pnl: Decimal = Decimal(0)
    ops_count: int = 0
    paused_until: date | None = None


@dataclass(slots=True)
class TradePlan:
    side: str               # "buy" | "sell"
    entry_price: Decimal
    quantity: Decimal       # in BTC
    stop_loss: Decimal
    take_profit: Decimal
    notional: Decimal       # entry_price * quantity, in quote currency


@dataclass(slots=True)
class RiskDecision:
    allowed: bool
    reason: str
    plan: TradePlan | None = None


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range. df must have columns: high, low, close."""
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


class RiskManager:
    """Stateful per-exchange risk manager."""

    def __init__(self, params: RiskParameters) -> None:
        self.params = params
        self._state: DailyState | None = None

    # --- daily window ----------------------------------------------------

    def _ensure_today(self, today: date) -> DailyState:
        if self._state is None or self._state.day != today:
            self._state = DailyState(day=today)
        return self._state

    def record_fill(self, today: date, pnl: Decimal) -> None:
        state = self._ensure_today(today)
        state.realized_pnl += pnl
        state.ops_count += 1

    def is_paused(self, today: date) -> bool:
        if self._state is None:
            return False
        return self._state.paused_until is not None and self._state.paused_until > today

    # --- gating ----------------------------------------------------------

    def can_open(
        self,
        today: date,
        bankroll: Decimal,
    ) -> tuple[bool, str]:
        if self.is_paused(today):
            return False, "Bot paused after daily loss limit hit."
        state = self._ensure_today(today)
        if state.ops_count >= self.params.max_ops_per_day:
            return False, f"Daily op cap reached ({self.params.max_ops_per_day})."
        loss_limit = -(bankroll * self.params.daily_loss_limit_pct)
        if state.realized_pnl <= loss_limit:
            state.paused_until = date.fromordinal(today.toordinal() + 1)
            return False, "Daily loss limit hit; pausing 24h."
        return True, ""

    # --- sizing ----------------------------------------------------------

    def plan_trade(
        self,
        side: str,
        bankroll: Decimal,
        entry_price: Decimal,
        atr_value: Decimal,
        ai_size_multiplier: Decimal = Decimal(1),
        quantity_step: Decimal = Decimal("0.00001"),
    ) -> TradePlan | None:
        """Compute size + SL/TP for a candidate entry.

        Returns None if the resulting notional is below the exchange's min_notional.
        """
        # ai_size_multiplier comes from the AI filter (e.g. 1.2 for boost). Cap at max_position_pct.
        position_fraction = min(self.params.max_position_pct * ai_size_multiplier, self.params.max_position_pct)

        notional_target = bankroll * position_fraction
        raw_qty = notional_target / entry_price
        # round down to step
        qty = (raw_qty // quantity_step) * quantity_step

        actual_notional = qty * entry_price
        if actual_notional < self.params.min_notional:
            return None

        if side == "buy":
            stop_loss = entry_price - atr_value * self.params.atr_stop_multiplier
            take_profit = entry_price + atr_value * self.params.atr_tp_multiplier
        else:
            stop_loss = entry_price + atr_value * self.params.atr_stop_multiplier
            take_profit = entry_price - atr_value * self.params.atr_tp_multiplier

        return TradePlan(
            side=side,
            entry_price=entry_price,
            quantity=qty.quantize(quantity_step, rounding=ROUND_DOWN),
            stop_loss=stop_loss,
            take_profit=take_profit,
            notional=actual_notional,
        )
