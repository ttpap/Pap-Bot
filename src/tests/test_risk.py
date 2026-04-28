"""Tests for risk manager (sizing, ATR, daily caps)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from btc_bot.risk import RiskManager, RiskParameters, atr


@pytest.fixture
def params() -> RiskParameters:
    return RiskParameters(
        max_position_pct=Decimal("0.50"),
        atr_stop_multiplier=Decimal("1.5"),
        atr_tp_multiplier=Decimal("3.0"),
        daily_loss_limit_pct=Decimal("0.03"),
        max_ops_per_day=5,
        min_notional=Decimal("10"),
    )


def test_atr_constant_high_low_zero():
    df = pd.DataFrame({"high": [100.0] * 30, "low": [100.0] * 30, "close": [100.0] * 30})
    out = atr(df, period=14).dropna()
    assert (out == 0).all()


def test_atr_increasing_volatility_grows():
    rng = np.random.default_rng(0)
    high = 100 + rng.uniform(0, 5, 50)
    low = 100 - rng.uniform(0, 5, 50)
    close = 100 + rng.uniform(-2, 2, 50)
    df = pd.DataFrame({"high": high, "low": low, "close": close})
    out = atr(df, period=14).dropna()
    assert out.iloc[-1] > 0


def test_position_size_respects_max_pct(params: RiskParameters):
    rm = RiskManager(params)
    plan = rm.plan_trade(
        side="buy",
        bankroll=Decimal(100),
        entry_price=Decimal(50000),
        atr_value=Decimal(500),
    )
    assert plan is not None
    assert plan.notional <= Decimal(100) * Decimal("0.50") + Decimal("1e-8")


def test_min_notional_blocks_tiny_size(params: RiskParameters):
    rm = RiskManager(params)
    # bankroll too small: 50% of 5 USDT = 2.5, below 10 USDT min
    plan = rm.plan_trade(
        side="buy",
        bankroll=Decimal(5),
        entry_price=Decimal(50000),
        atr_value=Decimal(500),
    )
    assert plan is None


def test_daily_loss_pauses(params: RiskParameters):
    rm = RiskManager(params)
    today = date(2026, 4, 28)
    bankroll = Decimal(1000)
    # 3% of 1000 = 30 BRL/USDT loss triggers pause
    rm.record_fill(today, Decimal(-30))
    allowed, reason = rm.can_open(today, bankroll)
    assert not allowed
    assert "Daily loss" in reason


def test_ops_cap(params: RiskParameters):
    rm = RiskManager(params)
    today = date(2026, 4, 28)
    for _ in range(5):
        rm.record_fill(today, Decimal(0))
    allowed, _ = rm.can_open(today, Decimal(1000))
    assert not allowed


def test_atr_stop_tp_directions(params: RiskParameters):
    rm = RiskManager(params)
    buy = rm.plan_trade("buy", Decimal(1000), Decimal(50000), Decimal(500))
    sell = rm.plan_trade("sell", Decimal(1000), Decimal(50000), Decimal(500))
    assert buy is not None and sell is not None
    assert buy.stop_loss < buy.entry_price < buy.take_profit
    assert sell.take_profit < sell.entry_price < sell.stop_loss
