"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from btc_bot.api.routes import control, credentials, status, trades


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

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
