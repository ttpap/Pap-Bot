"""Backtest engine — replays historical OHLCV through the strategy + risk manager.

This is the gate before live mode is unlocked. The engine outputs:
  - equity curve
  - per-trade log
  - aggregate stats (Sharpe, max drawdown, win rate, profit factor)

TODO:
  - load OHLCV from data/historical/<exchange>/<symbol>/<tf>.parquet
  - simulate fills with realistic slippage + maker/taker fees
  - persist results to backtest_results/<run_id>/
  - validate gate (Sharpe>1, DD<20%, WR>45%) and write GATE_OK if passed
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(slots=True)
class BacktestStats:
    n_trades: int
    win_rate: Decimal
    sharpe: Decimal
    max_drawdown: Decimal
    profit_factor: Decimal
    total_return: Decimal
    final_equity: Decimal


@dataclass(slots=True)
class BacktestResult:
    exchange: str
    start: datetime
    end: datetime
    initial_bankroll: Decimal
    stats: BacktestStats
    gate_passed: bool
