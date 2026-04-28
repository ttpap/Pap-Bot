"""Sanity tests for indicators. Validates that the math doesn't drift on regression."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from btc_bot.indicators import bollinger_bands, ema, rci, rsi, sma


@pytest.fixture
def trending_close() -> pd.Series:
    return pd.Series(np.linspace(100.0, 200.0, 50))


@pytest.fixture
def noisy_close() -> pd.Series:
    rng = np.random.default_rng(42)
    return pd.Series(100 + np.cumsum(rng.normal(0, 1, 200)))


def test_sma_constant_series_equals_constant():
    s = pd.Series([10.0] * 30)
    out = sma(s, period=5)
    assert out.dropna().eq(10.0).all()


def test_ema_recent_weight():
    s = pd.Series([1.0] * 9 + [10.0])
    fast = ema(s, period=3).iloc[-1]
    slow = ema(s, period=9).iloc[-1]
    # fast EMA should react more to the spike than slow EMA
    assert fast > slow


def test_bollinger_bands_contain_sma(noisy_close: pd.Series):
    bb = bollinger_bands(noisy_close, period=20, std_dev=2.0)
    assert (bb.upper.dropna() >= bb.middle.dropna()).all()
    assert (bb.lower.dropna() <= bb.middle.dropna()).all()


def test_rsi_in_range(noisy_close: pd.Series):
    values = rsi(noisy_close, period=14).dropna()
    assert (values >= 0).all() and (values <= 100).all()


def test_rsi_strong_uptrend_high(trending_close: pd.Series):
    values = rsi(trending_close, period=14).dropna()
    assert values.iloc[-1] > 70


def test_rci_strong_uptrend_positive(trending_close: pd.Series):
    values = rci(trending_close, period=9).dropna()
    # Monotonic increase -> rank correlation should be near +100
    assert values.iloc[-1] > 90


def test_rci_strong_downtrend_negative():
    s = pd.Series(np.linspace(200.0, 100.0, 50))
    values = rci(s, period=9).dropna()
    assert values.iloc[-1] < -90


def test_rci_in_range(noisy_close: pd.Series):
    values = rci(noisy_close, period=9).dropna()
    assert (values >= -100).all() and (values <= 100).all()
