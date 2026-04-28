"""Strategy package."""

from btc_bot.strategy.confluence import (
    WEIGHTS,
    ConfluenceResult,
    Signal,
    evaluate,
)

__all__ = ["Signal", "ConfluenceResult", "WEIGHTS", "evaluate"]
