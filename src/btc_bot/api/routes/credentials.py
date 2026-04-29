"""Credentials API.

Endpoints:
  GET    /api/credentials                  -> public status of every provider
  POST   /api/credentials                  -> save a new key (encrypts + tests)
  POST   /api/credentials/{provider}/test  -> retest existing credentials
  DELETE /api/credentials/{provider}       -> delete encrypted record

Plaintext keys never travel back to the client. Only status flags do.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from btc_bot.api.auth import require_api_key
from btc_bot.exchanges.binance import test_credentials as test_binance
from btc_bot.exchanges.mercadobitcoin import test_credentials as test_mb
from btc_bot.secrets import SecretsStore, get_store

router = APIRouter(prefix="/api/credentials", tags=["credentials"], dependencies=[Depends(require_api_key)])

ProviderId = Literal["binance", "mb", "anthropic"]
PROVIDERS: tuple[ProviderId, ...] = ("binance", "mb", "anthropic")


class CredentialStatus(BaseModel):
    provider: ProviderId
    configured: bool
    last_updated: str | None = None
    last_tested: str | None = None
    test_result: str | None = None
    test_message: str | None = None
    withdraw_enabled: bool | None = None
    trade_enabled: bool | None = None


class CredentialsState(BaseModel):
    binance: CredentialStatus
    mb: CredentialStatus
    anthropic: CredentialStatus


class SavePayload(BaseModel):
    provider: ProviderId
    api_key: str = Field(min_length=8, max_length=512)
    api_secret: str | None = Field(default=None, max_length=512)


class SaveResponse(BaseModel):
    ok: bool
    message: str
    status: CredentialStatus | None = None


def _to_status(provider: ProviderId, store: SecretsStore) -> CredentialStatus:
    rec = store.status(provider)
    return CredentialStatus(
        provider=provider,
        configured=rec.has_key and (provider == "anthropic" or rec.has_secret),
        last_updated=rec.last_updated,
        last_tested=rec.last_tested,
        test_result=rec.test_result,
        test_message=rec.test_message,
        withdraw_enabled=rec.withdraw_enabled,
        trade_enabled=rec.trade_enabled,
    )


@router.get("", response_model=CredentialsState)
async def list_credentials() -> CredentialsState:
    store = get_store()
    return CredentialsState(
        binance=_to_status("binance", store),
        mb=_to_status("mb", store),
        anthropic=_to_status("anthropic", store),
    )


@router.post("", response_model=SaveResponse)
async def save_credentials(payload: SavePayload) -> SaveResponse:
    if payload.provider in ("binance", "mb") and not payload.api_secret:
        raise HTTPException(status_code=400, detail="Exchange providers require api_secret")

    store = get_store()
    store.save(payload.provider, payload.api_key, payload.api_secret)

    # Run a connectivity / permission test right after saving.
    test_message = "Saved. Test skipped for this provider."
    test_ok = True
    if payload.provider == "binance":
        result = await test_binance(payload.api_key, payload.api_secret or "")
        store.record_test(
            "binance",
            result.code,
            result.message,
            withdraw_enabled=result.withdraw_enabled,
            trade_enabled=result.trade_enabled,
        )
        test_ok = result.code == "ok"
        test_message = result.message
    elif payload.provider == "mb":
        result = await test_mb(payload.api_key, payload.api_secret or "")
        store.record_test(
            "mb",
            result.code,
            result.message,
            withdraw_enabled=result.withdraw_enabled,
            trade_enabled=result.trade_enabled,
        )
        test_ok = result.code == "ok"
        test_message = result.message
    elif payload.provider == "anthropic":
        # Cheap test: try to instantiate the client. Real validation happens on first call.
        try:
            from anthropic import AsyncAnthropic
            _ = AsyncAnthropic(api_key=payload.api_key)
            store.record_test("anthropic", "ok", "Key accepted by client.")
            test_message = "Saved. Anthropic client accepts key format."
        except Exception as exc:  # noqa: BLE001
            store.record_test("anthropic", "other_error", str(exc))
            test_ok = False
            test_message = f"Failed to initialize Anthropic client: {exc}"

    return SaveResponse(ok=test_ok, message=test_message, status=_to_status(payload.provider, store))


@router.post("/{provider}/test", response_model=SaveResponse)
async def retest(provider: ProviderId) -> SaveResponse:
    store = get_store()
    try:
        with store.with_secret(provider) as (api_key, api_secret):
            if provider == "binance":
                result = await test_binance(api_key, api_secret or "")
            elif provider == "mb":
                result = await test_mb(api_key, api_secret or "")
            else:
                return SaveResponse(ok=True, message="Anthropic test only on save.", status=_to_status(provider, store))
    except KeyError:
        raise HTTPException(status_code=404, detail=f"No credentials saved for {provider}")

    store.record_test(
        provider,
        result.code,
        result.message,
        withdraw_enabled=result.withdraw_enabled,
        trade_enabled=result.trade_enabled,
    )
    return SaveResponse(
        ok=result.code == "ok",
        message=result.message,
        status=_to_status(provider, store),
    )


@router.delete("/{provider}", response_model=SaveResponse)
async def delete(provider: ProviderId) -> SaveResponse:
    store = get_store()
    removed = store.delete(provider)
    if not removed:
        return SaveResponse(ok=True, message="Nothing to remove.")
    return SaveResponse(ok=True, message="Encrypted record removed.", status=_to_status(provider, store))
