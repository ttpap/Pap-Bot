"""Weighted confluence strategy.

Each indicator emits a directional signal: -1 (sell), 0 (neutral), +1 (buy).
Indicators carry weights:
    MA  = 2  (trend)
    RSI = 2  (momentum)
    BB  = 1  (volatility / mean reversion)
    RCI = 1  (rank momentum)

The strategy aggregates a *signed* score per direction and triggers an entry
when |score| >= min_confluence_score (default 4).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd

from btc_bot.indicators import bollinger_bands, ema, rci, rsi, sma


class Signal(int, Enum):
    SELL = -1
    NEUTRAL = 0
    BUY = 1


WEIGHTS = {
    "ma": 2,
    "rsi": 2,
    "bb": 1,
    "rci": 1,
}


@dataclass(slots=True)
class ConfluenceResult:
    signal: Signal
    score: int                  # signed: positive=buy, negative=sell
    components: dict[str, int]  # individual signals per indicator
    score_buy: int
    score_sell: int


def _ma_signal(close: pd.Series) -> int:
    """Trend via fast/slow EMA cross. +1 if fast > slow."""
    fast = ema(close, period=9).iloc[-1]
    slow = ema(close, period=21).iloc[-1]
    if pd.isna(fast) or pd.isna(slow):
        return Signal.NEUTRAL.value
    if fast > slow:
        return Signal.BUY.value
    if fast < slow:
        return Signal.SELL.value
    return Signal.NEUTRAL.value


def _rsi_signal(close: pd.Series) -> int:
    """RSI: <30 oversold (buy), >70 overbought (sell)."""
    value = rsi(close, period=14).iloc[-1]
    if pd.isna(value):
        return Signal.NEUTRAL.value
    if value < 30:
        return Signal.BUY.value
    if value > 70:
        return Signal.SELL.value
    return Signal.NEUTRAL.value


def _bb_signal(close: pd.Series) -> int:
    """BB: close below lower band -> buy; above upper -> sell.

    Returns NEUTRAL when bandwidth is degenerate (flat market: std == 0).
    """
    bb = bollinger_bands(close, period=20, std_dev=2.0)
    last_close = close.iloc[-1]
    last_lower = bb.lower.iloc[-1]
    last_upper = bb.upper.iloc[-1]
    last_bandwidth = bb.bandwidth.iloc[-1]
    if pd.isna(last_lower) or pd.isna(last_upper):
        return Signal.NEUTRAL.value
    if pd.isna(last_bandwidth) or last_bandwidth <= 1e-9:
        return Signal.NEUTRAL.value
    if last_close < last_lower:
        return Signal.BUY.value
    if last_close > last_upper:
        return Signal.SELL.value
    return Signal.NEUTRAL.value


def _rci_signal(close: pd.Series) -> int:
    """RCI: > +60 strong up (sell setup near top), < -60 strong down (buy setup near bottom).

    Note: classic RCI uses inversion-style trades — extreme values are reversal cues.
    """
    value = rci(close, period=9).iloc[-1]
    if pd.isna(value):
        return Signal.NEUTRAL.value
    if value < -60:
        return Signal.BUY.value
    if value > 60:
        return Signal.SELL.value
    return Signal.NEUTRAL.value


def evaluate(close: pd.Series) -> ConfluenceResult:
    """Compute confluence score from the latest closed candle in `close`."""
    components = {
        "ma": _ma_signal(close),
        "rsi": _rsi_signal(close),
        "bb": _bb_signal(close),
        "rci": _rci_signal(close),
    }

    score_buy = sum(WEIGHTS[k] for k, v in components.items() if v == Signal.BUY.value)
    score_sell = sum(WEIGHTS[k] for k, v in components.items() if v == Signal.SELL.value)

    if score_buy > score_sell:
        signed = score_buy
        signal = Signal.BUY
    elif score_sell > score_buy:
        signed = -score_sell
        signal = Signal.SELL
    else:
        signed = 0
        signal = Signal.NEUTRAL

    return ConfluenceResult(
        signal=signal,
        score=signed,
        components=components,
        score_buy=score_buy,
        score_sell=score_sell,
    )


# Re-export for convenience
__all__ = ["Signal", "ConfluenceResult", "WEIGHTS", "evaluate"]
# silence unused warnings for re-exports
_ = (sma,)
