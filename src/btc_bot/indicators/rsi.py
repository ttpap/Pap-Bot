"""Relative Strength Index (Wilder's smoothing)."""

from __future__ import annotations

import pandas as pd


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's RSI.

    Returns values in [0, 100].
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's smoothing == EMA with alpha = 1/period
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
