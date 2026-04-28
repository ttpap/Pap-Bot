"""Rank Correlation Index (RCI).

RCI measures the rank correlation between price order and time order over a window.
Range: [-100, +100].
  +100  -> price ranks rise monotonically with time (strong uptrend)
  -100  -> price ranks fall monotonically with time (strong downtrend)

Formula (Spearman's rho × 100):
    RCI = (1 - 6 * Σ d_i^2 / (n * (n^2 - 1))) * 100
where d_i = rank_price_i - rank_time_i within the rolling window.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rci(close: pd.Series, period: int = 9) -> pd.Series:
    """Rolling Spearman rank correlation between time and price."""

    def _rci_window(arr: np.ndarray) -> float:
        n = len(arr)
        if n < period or np.isnan(arr).any():
            return np.nan
        time_ranks = np.arange(1, n + 1, dtype=np.float64)
        # Average ranks for ties (default for pd.Series.rank)
        price_ranks = pd.Series(arr).rank(method="average").to_numpy()
        d = time_ranks - price_ranks
        d_squared_sum = float(np.sum(d * d))
        return (1 - (6 * d_squared_sum) / (n * (n * n - 1))) * 100

    return close.rolling(window=period, min_periods=period).apply(_rci_window, raw=True)
