"""Download OHLCV history from Binance for backtesting.

Usage:
    python scripts/download_history.py --symbol BTC/USDT --timeframe 15m --start 2024-01-01

Saves to data/historical/<exchange>/<symbol>/<timeframe>.parquet
"""

from __future__ import annotations

# TODO:
#   - paginate /api/v3/klines (1000 candles/request)
#   - resume from last saved candle
#   - for MB, use /products/{symbol}/candles
