"""Encrypted secret store backed by Fernet (AES-128-CBC + HMAC-SHA256).

Keys are encrypted at rest in a single JSON file (default `secrets/vault.json`).
The master key comes from the `BTC_BOT_MASTER_KEY` environment variable; if
unset, we derive a fresh key, write it to `secrets/master.key` (chmod 0600),
and reuse it on subsequent starts.

The vault never returns plaintext keys back to the network layer — callers
either use them server-side via `with_secret(...)` or check status via
`status(...)`.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets as _secrets
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from cryptography.fernet import Fernet, InvalidToken


def derive_master_key(passphrase: str, salt: bytes) -> bytes:
    """PBKDF2-SHA256 derived 32-byte key, base64-encoded for Fernet."""
    raw = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 200_000, dklen=32)
    return base64.urlsafe_b64encode(raw)


@dataclass(slots=True)
class SecretRecord:
    provider: str
    has_key: bool = False
    has_secret: bool = False
    last_updated: str | None = None        # ISO timestamp
    last_tested: str | None = None
    test_result: str | None = None         # "ok" | "auth_failed" | "ip_not_whitelisted" | "other_error"
    test_message: str | None = None
    withdraw_enabled: bool | None = None
    trade_enabled: bool | None = None
    extra: dict = field(default_factory=dict)


class SecretsStore:
    """Single-file encrypted secrets vault.

    Layout on disk (`secrets/vault.json`):
      {
        "binance": {
          "key":    "<fernet-encrypted bytes>",
          "secret": "<fernet-encrypted bytes>",
          "meta":   { ...SecretRecord fields... }
        },
        ...
      }
    """

    def __init__(self, path: str | Path | None = None, master_key: bytes | None = None) -> None:
        self._path = Path(path) if path else Path("secrets/vault.json")
        self._path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._fernet = Fernet(master_key or self._load_or_create_master_key())
        self._lock = threading.RLock()

    # ----- master key bootstrap --------------------------------------

    def _load_or_create_master_key(self) -> bytes:
        env_key = os.environ.get("BTC_BOT_MASTER_KEY")
        if env_key:
            return env_key.encode("utf-8")

        key_path = self._path.parent / "master.key"
        if key_path.exists():
            return key_path.read_bytes().strip()

        new_key = Fernet.generate_key()
        key_path.write_bytes(new_key)
        try:
            key_path.chmod(0o600)
        except (OSError, PermissionError):
            pass
        return new_key

    # ----- raw I/O ---------------------------------------------------

    def _read(self) -> dict:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _write(self, data: dict) -> None:
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        try:
            tmp.chmod(0o600)
        except (OSError, PermissionError):
            pass
        tmp.replace(self._path)

    def _encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")

    def _decrypt(self, ciphertext: str) -> str:
        try:
            return self._fernet.decrypt(ciphertext.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise RuntimeError(
                "Could not decrypt vault entry — master key may be wrong or "
                "vault was tampered with."
            ) from exc

    # ----- public API ------------------------------------------------

    def list(self) -> list[SecretRecord]:
        with self._lock:
            data = self._read()
            return [self._record_from_meta(p, data[p].get("meta", {})) for p in data]

    def status(self, provider: str) -> SecretRecord:
        with self._lock:
            entry = self._read().get(provider, {})
            return self._record_from_meta(provider, entry.get("meta", {}), entry)

    def save(
        self,
        provider: str,
        api_key: str,
        api_secret: str | None = None,
        extra: dict | None = None,
    ) -> SecretRecord:
        with self._lock:
            data = self._read()
            entry = data.get(provider, {"meta": {}})
            entry["key"] = self._encrypt(api_key)
            if api_secret is not None:
                entry["secret"] = self._encrypt(api_secret)
            elif "secret" in entry:
                # Keep previous secret if not replaced.
                pass

            meta = entry.setdefault("meta", {})
            meta["last_updated"] = datetime.now(UTC).isoformat()
            meta["last_tested"] = None
            meta["test_result"] = None
            meta["test_message"] = None
            meta["withdraw_enabled"] = None
            meta["trade_enabled"] = None
            if extra:
                meta.setdefault("extra", {}).update(extra)

            data[provider] = entry
            self._write(data)
            return self._record_from_meta(provider, meta, entry)

    def delete(self, provider: str) -> bool:
        with self._lock:
            data = self._read()
            if provider in data:
                del data[provider]
                self._write(data)
                return True
            return False

    def record_test(
        self,
        provider: str,
        result: str,
        message: str,
        withdraw_enabled: bool | None = None,
        trade_enabled: bool | None = None,
    ) -> SecretRecord:
        with self._lock:
            data = self._read()
            entry = data.setdefault(provider, {"meta": {}})
            meta = entry.setdefault("meta", {})
            meta["last_tested"] = datetime.now(UTC).isoformat()
            meta["test_result"] = result
            meta["test_message"] = message
            if withdraw_enabled is not None:
                meta["withdraw_enabled"] = withdraw_enabled
            if trade_enabled is not None:
                meta["trade_enabled"] = trade_enabled
            self._write(data)
            return self._record_from_meta(provider, meta, entry)

    @contextmanager
    def with_secret(self, provider: str) -> Iterator[tuple[str, str | None]]:
        """Yield decrypted (api_key, api_secret) for server-side use only.

        The plaintext values are wrapped in a context manager so callers don't
        accidentally retain them in long-lived references.
        """
        with self._lock:
            data = self._read()
            if provider not in data or "key" not in data[provider]:
                raise KeyError(f"No credentials saved for {provider!r}")
            api_key = self._decrypt(data[provider]["key"])
            secret_ct = data[provider].get("secret")
            api_secret = self._decrypt(secret_ct) if secret_ct else None
        try:
            yield api_key, api_secret
        finally:
            # Best-effort scrubbing: rebind names so the references drop sooner.
            api_key = ""
            api_secret = ""

    # ----- helpers ---------------------------------------------------

    @staticmethod
    def _record_from_meta(
        provider: str, meta: dict, entry: dict | None = None
    ) -> SecretRecord:
        entry = entry or {}
        return SecretRecord(
            provider=provider,
            has_key="key" in entry,
            has_secret="secret" in entry,
            last_updated=meta.get("last_updated"),
            last_tested=meta.get("last_tested"),
            test_result=meta.get("test_result"),
            test_message=meta.get("test_message"),
            withdraw_enabled=meta.get("withdraw_enabled"),
            trade_enabled=meta.get("trade_enabled"),
            extra=meta.get("extra", {}),
        )


# ----- singleton ----------------------------------------------------

_store: SecretsStore | None = None
_store_lock = threading.Lock()


def get_store(path: str | Path | None = None) -> SecretsStore:
    """Return a process-wide SecretsStore. Tests should pass an explicit path."""
    global _store
    with _store_lock:
        if _store is None:
            _store = SecretsStore(path=path)
        return _store


# Silence unused warnings for re-exports
_ = (_secrets,)
