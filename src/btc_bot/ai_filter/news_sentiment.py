"""AI news / sentiment filter.

Periodically pulls Bitcoin-related news from configured sources, sends a
batched summary to Claude, and returns a structured verdict that the engine
applies as either a hard veto or a size multiplier.

Modes:
  - VETO: block all new entries (e.g. major regulation / hack / exchange outage)
  - REDUCE: half size (only neutral-leaning negatives)
  - NEUTRAL: pass through
  - BOOST: multiply size by 1.2 (capped by RiskManager max_position_pct)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class SentimentVerdict(str, Enum):
    VETO = "veto"
    REDUCE = "reduce"
    NEUTRAL = "neutral"
    BOOST = "boost"


@dataclass(slots=True)
class NewsItem:
    title: str
    source: str
    url: str
    published_at: datetime
    summary: str | None = None


@dataclass(slots=True)
class FilterDecision:
    verdict: SentimentVerdict
    size_multiplier: Decimal      # 0 if VETO, 0.5 if REDUCE, 1 if NEUTRAL, 1.2 if BOOST
    reasoning: str
    flagged_items: list[str]      # NewsItem ids/urls that drove the decision
    refreshed_at: datetime


class NewsSentimentFilter:
    """Asks Claude to assess macro/regulatory/exchange news for BTC trading.

    TODO:
      - implement news fetching (NewsAPI, CryptoPanic, RSS for BCB / CVM)
      - call Anthropic Messages API with prompt caching for the news bundle
      - cache the verdict in Redis with the configured interval TTL
    """

    SIZE_MAP: dict[SentimentVerdict, Decimal] = {
        SentimentVerdict.VETO: Decimal(0),
        SentimentVerdict.REDUCE: Decimal("0.5"),
        SentimentVerdict.NEUTRAL: Decimal(1),
        SentimentVerdict.BOOST: Decimal("1.2"),
    }

    def __init__(self, anthropic_api_key: str, model: str = "claude-sonnet-4-6") -> None:
        self._api_key = anthropic_api_key
        self._model = model

    async def fetch_news(self) -> list[NewsItem]:
        raise NotImplementedError

    async def assess(self, items: list[NewsItem]) -> FilterDecision:
        raise NotImplementedError

    async def current_decision(self) -> FilterDecision:
        """Return the cached or newly computed verdict."""
        raise NotImplementedError
