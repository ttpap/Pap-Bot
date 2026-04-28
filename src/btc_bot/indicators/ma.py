"""Moving averages."""

from __future__ import annotations

import pandas as pd


def sma(close: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return close.rolling(window=period, min_periods=period).mean()


def ema(close: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return close.ewm(span=period, adjust=False, min_periods=period).mean()
