"""FastAPI application factory."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from btc_bot.api.routes import control, credentials, status, trades

log = logging.getLogger(__name__)


def _bootstrap_vault() -> None:
    """Seed the encrypted vault from env vars on first boot.

    If BINANCE_API_KEY / MB_API_KEY / ANTHROPIC_API_KEY are set in the
    environment (via .env) but the vault has no entry yet, save them now.
    This lets users configure credentials by editing .env instead of using
    the panel UI.
    """
    from btc_bot.secrets import get_store

    store = get_store()

    pairs: list[tuple[str, str, str | None]] = [
        ("binance",   os.getenv("BINANCE_API_KEY", ""),  os.getenv("BINANCE_API_SECRET", "")),
        ("mb",        os.getenv("MB_API_KEY", ""),        os.getenv("MB_API_SECRET", "")),
        ("anthropic", os.getenv("ANTHROPIC_API_KEY", ""), None),
    ]

    for provider, key, secret in pairs:
        if not key:
            continue
        rec = store.status(provider)
        if rec.has_key:
            log.debug("bootstrap: %s already in vault, skipping", provider)
            continue
        store.save(provider, key, secret)
        log.info("bootstrap: seeded %s credentials from environment", provider)


def create_app() -> FastAPI:
    app = FastAPI(
        title="btc-bot API",
        description="Internal control plane for the BTC trading bot.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://pap-bot-panel.vercel.app",
            # local development
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["X-API-Key", "Content-Type", "Accept"],
    )

    app.include_router(status.router)
    app.include_router(trades.router)
    app.include_router(control.router)
    app.include_router(credentials.router)

    @app.on_event("startup")
    async def on_startup() -> None:
        _bootstrap_vault()

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
