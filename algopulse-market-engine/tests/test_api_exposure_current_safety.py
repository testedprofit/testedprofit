from __future__ import annotations

import json
import re
from collections.abc import Iterator

from fastapi.testclient import TestClient

import algopulse.api as api_module
from algopulse.api import LOCAL_REVIEW_ADMIN_WALLET
from algopulse.api import app


SECRET_KEY_FRAGMENTS = (
    "mnemonic",
    "private_key",
    "privatekey",
    "seed_phrase",
    "seedphrase",
    "wallet_mnemonic",
    "signing_key",
    "signer_secret",
    "secret_key",
    "api_secret",
    "api_token",
    "algod_token",
    "indexer_token",
)

SECRET_VALUE_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\b[a-fA-F0-9]{64,}\b"),
)

EXECUTION_PAYLOAD_FRAGMENTS = (
    "signed_transaction",
    "signedtransaction",
    "signed_txn",
    "signedtxn",
    "signed_group",
    "transaction_id",
    "submitted_txid",
    "submission_payload",
    "private_key",
    "mnemonic",
    "hot_wallet",
)


def _client() -> TestClient:
    return TestClient(app)


def _walk_json(value: object, path: str = "$") -> Iterator[tuple[str, object]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_json(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_json(child, f"{path}[{index}]")


def _assert_no_secret_like_keys_or_values(payload: object) -> None:
    for path, value in _walk_json(payload):
        path_lower = path.lower()
        assert not any(fragment in path_lower for fragment in SECRET_KEY_FRAGMENTS), path
        if isinstance(value, str):
            assert not any(pattern.search(value) for pattern in SECRET_VALUE_PATTERNS), path
            assert not _looks_like_exact_mnemonic(value), path


def _looks_like_exact_mnemonic(value: str) -> bool:
    words = value.strip().split()
    if len(words) not in {12, 15, 18, 21, 24}:
        return False
    return bool(re.fullmatch(r"[a-z]+(?: [a-z]+)*", value.strip()))


def _assert_no_execution_payload(payload: object) -> None:
    serialized = json.dumps(payload, sort_keys=True).lower()
    for fragment in EXECUTION_PAYLOAD_FRAGMENTS:
        assert fragment not in serialized


def test_public_config_exposes_no_secret_like_keys_or_values():
    response = _client().get("/api/config/public")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    _assert_no_secret_like_keys_or_values(payload)
    assert payload["data"]["liveExecutionEnabled"] is False
    assert payload["data"]["signerEnabled"] is False


def test_wallet_session_clearly_labels_local_review_mock_behavior():
    response = _client().get(f"/api/session/wallet/{LOCAL_REVIEW_ADMIN_WALLET}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    session = payload["data"]
    assert session["authMode"] == "local-review-mock"
    assert "Mock wallet session only" in session["warning"]
    assert "signed wallet proof" in session["warning"]


def test_demo_run_is_synthetic_mock_and_contains_no_execution_payload():
    response = _client().get("/api/demo-run")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "synthetic-demo"
    assert payload["live"] is False
    assert payload["submitted"] is False
    assert payload["checks"]["dry_run_only"] is True
    assert "Synthetic proof run only" in payload["warning"]
    assert "uses no funds" in payload["warning"]
    _assert_no_execution_payload(payload)


def test_execute_best_is_blocked_by_default_and_does_not_call_execution(monkeypatch):
    def fail_if_called() -> dict:
        raise AssertionError("execute_best_once should not be called while API execution is disabled")

    monkeypatch.setattr(api_module.scanner, "execute_best_once", fail_if_called)

    response = _client().post("/api/execute-best")

    assert response.status_code == 403
    payload = response.json()
    assert "API execution is disabled" in payload["detail"]
    _assert_no_execution_payload(payload)
