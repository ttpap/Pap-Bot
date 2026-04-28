"""APScheduler-based clock for the engine.

Runs:
  - every 15m: engine tick (per enabled exchange)
  - every 15m (offset): AI news refresh
  - daily 00:05 UTC: rotate daily state, snapshot bankroll
  - monthly day 1 00:30 UTC: emit IR CSV for previous month
"""
