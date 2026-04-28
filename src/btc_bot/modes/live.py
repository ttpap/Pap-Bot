"""Live trading mode.

Refuses to start unless `gate.GATE_OK` exists for the configured exchange,
indicating that the most recent backtest passed all gating thresholds.
"""

from __future__ import annotations
