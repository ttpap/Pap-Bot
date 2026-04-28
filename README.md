# btc-bot

Automated BTC trading bot integrating **Binance** (BTC/USDT) and **Mercado Bitcoin** (BTC/BRL).

Confluence-based entries (MA + Bollinger + RSI + RCI), ATR-driven stop/take-profit, AI news/sentiment veto, separate bankroll per exchange.

## Status

> **Pre-alpha.** No live trading until backtest gate passes (Sharpe > 1, max drawdown < 20%, win rate > 45%).

## Features (planned)

- [x] Repo scaffold
- [ ] Exchange adapters (Binance, Mercado Bitcoin) with unified interface
- [ ] Indicators: MA, Bollinger Bands, RSI, RCI
- [ ] Weighted confluence engine (`MA=2 + RSI=2 + BB=1 + RCI=1`, threshold ≥ 4)
- [ ] Risk manager: 50% bankroll/order, ATR stop/TP, 3% daily loss limit, 5 ops/day cap
- [ ] Modes: backtest, paper, live (gated by validation)
- [ ] AI filter: Claude Sonnet 4.6 reads news/sentiment, vetoes or boosts (within 50% cap)
- [ ] Ledger: per-exchange isolation, full trade history, monthly IR-ready CSV (BR Receita Federal)
- [ ] Next.js panel on Vercel (live status, P&L, manual override)
- [ ] Per-exchange enable/disable from panel

## Architecture

```
┌────────────┐    ┌────────────┐
│  Binance   │    │ Mercado    │   <- separate bankrolls
│ BTC/USDT   │    │ Bitcoin    │      no fund mixing
└─────┬──────┘    │ BTC/BRL    │
      │           └──────┬─────┘
      │                  │
      └────────┬─────────┘
               │
        ┌──────▼──────┐
        │  Indicators │  MA, BB, RSI, RCI
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │ Confluence  │  weighted score >= 4
        └──────┬──────┘
               │
        ┌──────▼──────┐    ┌──────────────┐
        │ Risk Mgr    │◄───│ AI News      │
        │ ATR / 50% / │    │ Filter       │
        │ 3% / 5 ops  │    │ (veto/boost) │
        └──────┬──────┘    └──────────────┘
               │
        ┌──────▼──────┐
        │ Exchange    │
        │ Order Exec  │
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │   Ledger    │  Postgres
        └─────────────┘
```

## Quick start

### Local development

```bash
# Install deps with uv (or pip)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Configure
cp .env.example .env
# edit .env with your API keys

# Run backtest
btc-bot backtest --start 2024-01-01 --end 2024-06-30 --exchange binance

# Run paper trading
btc-bot run --mode paper

# Run live (only after gate validation)
btc-bot run --mode live
```

### Docker

```bash
cp .env.example .env
docker compose up -d
docker compose logs -f bot
```

## Trading parameters (defaults)

| Parameter | Value | Source |
|---|---|---|
| Timeframe | 15m | sweet spot scalp/swing |
| Position size | 50% of bankroll per order | user requirement |
| Stop loss | 1.5 × ATR | volatility-adaptive |
| Take profit | 3 × ATR | R:R 1:2 |
| Daily loss limit | 3% bankroll → 24h pause | prop-firm style |
| Max ops/day | 5 | avoid churn |
| Confluence threshold | weighted ≥ 4 (`MA=2 + RSI=2 + BB=1 + RCI=1`) | trend + momentum priority |
| AI veto | hard block on critical news (regulation, hack) | AI filter |
| AI boost | +20% size on strongly positive sentiment, capped at 50% | AI filter |

## Live gate

Bot will refuse to enter live mode until a recent backtest run satisfies:

- Sharpe ratio > 1.0
- Max drawdown < 20%
- Win rate > 45%

## Security

- Withdraw permission **must** be disabled on every exchange API key
- IP whitelist **must** be set to the bot's host IP
- No `.env` files are committed; `secrets/` and `.env.*` ignored
- Postgres + Redis bound to `127.0.0.1` only

## Tax compliance (BR)

Monthly CSV export of all operations is generated to `reports/ir/YYYY-MM.csv`, formatted per Receita Federal IN 1888 (mandatory above R$35k/month, useful below as audit trail).

## Hosting

- **Bot core + Postgres + Redis:** Oracle Cloud Free Tier (E2.1.Micro, sa-saopaulo-1) via Docker Compose
- **Panel + AI news worker:** Vercel (Next.js + Functions)

## License

Private. Not for distribution.
