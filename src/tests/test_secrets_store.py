"""Tests for the encrypted secrets store."""

from __future__ import annotations

import json
from pathlib import Path

from cryptography.fernet import Fernet

from btc_bot.secrets.store import SecretsStore


def _make_store(tmp_path: Path) -> SecretsStore:
    return SecretsStore(path=tmp_path / "vault.json", master_key=Fernet.generate_key())


def test_save_and_status_roundtrip(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    store.save("binance", "AKIA1234567890", "supersecret-very-long-string")

    rec = store.status("binance")
    assert rec.has_key is True
    assert rec.has_secret is True
    assert rec.last_updated is not None
    assert rec.test_result is None


def test_disk_payload_is_encrypted(tmp_path: Path) -> None:
    vault = tmp_path / "vault.json"
    store = SecretsStore(path=vault, master_key=Fernet.generate_key())
    plaintext = "AKIA-PLAIN-TEXT-DETECTOR-9999"
    store.save("binance", plaintext, "secret-also-encrypted-9999")

    raw = vault.read_text("utf-8")
    assert plaintext not in raw
    assert "secret-also-encrypted-9999" not in raw

    parsed = json.loads(raw)
    assert "binance" in parsed
    assert "key" in parsed["binance"]


def test_with_secret_decrypts(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    store.save("binance", "AKIA-key", "AKIA-secret")

    with store.with_secret("binance") as (key, secret):
        assert key == "AKIA-key"
        assert secret == "AKIA-secret"


def test_delete(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    store.save("binance", "k", "s")
    assert store.delete("binance") is True
    assert store.delete("binance") is False
    assert store.status("binance").has_key is False


def test_record_test_persists(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    store.save("binance", "k", "s")
    store.record_test("binance", "ok", "All good", withdraw_enabled=False, trade_enabled=True)
    rec = store.status("binance")
    assert rec.test_result == "ok"
    assert rec.test_message == "All good"
    assert rec.withdraw_enabled is False
    assert rec.trade_enabled is True


def test_anthropic_no_secret_required(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    store.save("anthropic", "sk-ant-12345678901234567890")
    rec = store.status("anthropic")
    assert rec.has_key is True
    assert rec.has_secret is False
