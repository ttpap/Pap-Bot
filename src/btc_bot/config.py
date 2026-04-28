"""Application configuration loaded from environment variables."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Mode(str, Enum):
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"


class Settings(BaseSettings):
    """Top-level configuration. Loaded from env vars and `.env` files."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    # Mode
    mode: Mode = Field(Mode.BACKTEST, alias="BTC_BOT_MODE")
    exchanges: str = Field("binance,mb", alias="BTC_BOT_EXCHANGES")

    # Binance
    binance_api_key: SecretStr | None = Field(None, alias="BINANCE_API_KEY")
    binance_api_secret: SecretStr | None = Field(None, alias="BINANCE_API_SECRET")

    # Mercado Bitcoin
    mb_api_key: SecretStr | None = Field(None, alias="MB_API_KEY")
    mb_api_secret: SecretStr | None = Field(None, alias="MB_API_SECRET")

    # Anthropic
    anthropic_api_key: SecretStr | None = Field(None, alias="ANTHROPIC_API_KEY")
    ai_model: str = Field("claude-sonnet-4-6", alias="AI_MODEL")
    ai_news_interval_min: int = Field(15, alias="AI_NEWS_INTERVAL_MIN")

    # News providers
    newsapi_key: SecretStr | None = Field(None, alias="NEWSAPI_KEY")
    cryptopanic_key: SecretStr | None = Field(None, alias="CRYPTOPANIC_KEY")

    # Persistence
    database_url: str = Field(
        "postgresql+asyncpg://btc_bot:btc_bot@localhost:5432/btc_bot",
        alias="DATABASE_URL",
    )
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # Strategy
    timeframe: str = Field("15m", alias="TIMEFRAME")
    max_position_pct: Decimal = Field(Decimal("0.50"), alias="MAX_POSITION_PCT")
    atr_stop_multiplier: Decimal = Field(Decimal("1.5"), alias="ATR_STOP_MULTIPLIER")
    atr_tp_multiplier: Decimal = Field(Decimal("3.0"), alias="ATR_TP_MULTIPLIER")
    daily_loss_limit_pct: Decimal = Field(Decimal("0.03"), alias="DAILY_LOSS_LIMIT_PCT")
    max_ops_per_day: int = Field(5, alias="MAX_OPS_PER_DAY")
    min_confluence_score: int = Field(4, alias="MIN_CONFLUENCE_SCORE")

    # Live gate
    gate_min_sharpe: Decimal = Field(Decimal("1.0"), alias="GATE_MIN_SHARPE")
    gate_max_drawdown_pct: Decimal = Field(Decimal("0.20"), alias="GATE_MAX_DRAWDOWN_PCT")
    gate_min_win_rate: Decimal = Field(Decimal("0.45"), alias="GATE_MIN_WIN_RATE")

    # API server
    api_host: str = Field("0.0.0.0", alias="API_HOST")
    api_port: int = Field(8000, alias="API_PORT")
    api_key: SecretStr = Field(SecretStr("change-me"), alias="API_KEY")

    log_level: str = Field("INFO", alias="LOG_LEVEL")

    @property
    def enabled_exchanges(self) -> list[str]:
        return [e.strip().lower() for e in self.exchanges.split(",") if e.strip()]


settings = Settings()
