"""Paper trading mode — uses real market data but simulated order fills.

Bridges live data feeds (Binance/MB ticker + OHLCV) with the same engine as
live mode, but instead of submitting orders to the exchange it records
synthetic fills assuming maker fees and zero slippage.

Useful between backtest validation and live promotion to verify the live
data path without risking capital.
"""

from __future__ import annotations
