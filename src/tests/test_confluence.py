"""Tests for the confluence engine.

Note on indicator philosophy:
  - MA cross is trend-following  (uptrend → BUY)
  - RSI / RCI / BB are mean-reverting (overbought → SELL even in uptrend)

Therefore a sustained uptrend produces a *mixed* aggregate signal: MA says BUY
while RSI + RCI say SELL. The numerical winner depends on weights. Current
weights (MA=2, RSI=2, BB=1, RCI=1) give SELL = 3 vs BUY = 2 in pure trends —
intentional bias toward mean-reversion entries.

These tests verify component contracts and the score arithmetic, not a
specific aggregate direction in idealized series.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from btc_bot.strategy import Signal, evaluate


@pytest.fixture
def strong_uptrend() -> pd.Series:
    return pd.Series(np.linspace(100.0, 250.0, 100))


@pytest.fixture
def strong_downtrend() -> pd.Series:
    return pd.Series(np.linspace(250.0, 100.0, 100))


@pytest.fixture
def flat() -> pd.Series:
    return pd.Series([100.0] * 100)


def test_uptrend_components_consistent(strong_uptrend: pd.Series):
    result = evaluate(strong_uptrend)
    # MA should be bullish on a clean uptrend
    assert result.components["ma"] == Signal.BUY.value
    # RSI should be overbought (->SELL) on prolonged uptrend
    assert result.components["rsi"] in (Signal.SELL.value, Signal.NEUTRAL.value)
    # RCI should peg high (->SELL) under monotonic increase
    assert result.components["rci"] == Signal.SELL.value
    # Weighted score reflects mean-reversion bias
    assert result.score_sell >= 3


def test_downtrend_components_consistent(strong_downtrend: pd.Series):
    result = evaluate(strong_downtrend)
    assert result.components["ma"] == Signal.SELL.value
    assert result.components["rsi"] in (Signal.BUY.value, Signal.NEUTRAL.value)
    assert result.components["rci"] == Signal.BUY.value
    assert result.score_buy >= 3


def test_flat_series_neutral(flat: pd.Series):
    result = evaluate(flat)
    # No price movement → all indicators neutral or undefined
    assert result.score == 0


def test_components_have_expected_keys(strong_uptrend: pd.Series):
    result = evaluate(strong_uptrend)
    assert set(result.components.keys()) == {"ma", "rsi", "bb", "rci"}
    for v in result.components.values():
        assert v in {-1, 0, 1}


def test_score_signs_match_signal(strong_downtrend: pd.Series):
    result = evaluate(strong_downtrend)
    if result.signal == Signal.BUY:
        assert result.score > 0
    elif result.signal == Signal.SELL:
        assert result.score < 0
    else:
        assert result.score == 0
