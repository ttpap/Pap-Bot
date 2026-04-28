"""Bollinger Bands."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class BollingerBands:
    middle: pd.Series
    upper: pd.Series
    lower: pd.Series
    bandwidth: pd.Series  # (upper - lower) / middle, squeeze indicator


def bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2.0) -> BollingerBands:
    """Standard Bollinger Bands.

    Default settings: 20-period SMA, 2 standard deviations.
    """
    middle = close.rolling(window=period, min_periods=period).mean()
    std = close.rolling(window=period, min_periods=period).std(ddof=0)
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    bandwidth = (upper - lower) / middle
    return BollingerBands(middle=middle, upper=upper, lower=lower, bandwidth=bandwidth)
