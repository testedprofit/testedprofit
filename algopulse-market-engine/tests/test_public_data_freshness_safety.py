from __future__ import annotations

import json
import time
from collections.abc import Iterator
from dataclasses import replace

from fastapi.testclient import TestClient

import algopulse.api as api_module
from algopulse.api import app
from algopulse.models import Opportunity
from algopulse.store import MarketStore


PUBLIC_DELAY_SECONDS = 900
FRESH_ROUTE_HASH = "fresh-high-profit-route"
DELAYED_ROUTE_HASH = "delayed-lower-profit-route"
EXECUTION_PAYLOAD_FRAGMENTS = (
    "signed_transaction",
    "signedtransaction",
    "signed_txn",
    "signedtxn",
    "signed_group",
    "submission_payload",
    "submitted_txid",
    "submitted_transaction",
    "hot_wallet",
    "hotwallet",
    "private_key",
    "privatekey",
    "mnemonic",
    "wallet_mnemonic",
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


def _assert_no_execution_payload(payload: object) -> None:
    serialized = json.dumps(payload, sort_keys=True).lower()
    for fragment in EXECUTION_PAYLOAD_FRAGMENTS:
        assert fragment not in serialized


def _assert_fresh_route_is_not_exposed(payload: object) -> None:
    for path, value in _walk_json(payload):
        if isinstance(value, str):
            assert FRESH_ROUTE_HASH not in value, path


def _opportunity(route_hash: str, created_at: float, expected_net_profit: float) -> Opportunity:
    return Opportunity(
        route_hash=route_hash,
        route=[
            {
                "venue": "pact",
                "pool_id": "pact:ALGO-USDC",
                "input_asset_id": 0,
                "output_asset_id": 31566704,
                "input_amount": 5.0,
                "expected_output": 1.0,
            },
            {
                "venue": "tinyman",
                "pool_id": "tinyman:USDC-ALGO",
                "input_asset_id": 31566704,
                "output_asset_id": 0,
                "input_amount": 1.0,
                "expected_output": 5.5,
            },
        ],
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=5.5,
        expected_net_profit=expected_net_profit,
        expected_profit_bps=expected_net_profit / 5.0 * 10_000,
        max_price_impact_bps=10.0,
        involved_pool_ids=["pact:ALGO-USDC", "tinyman:USDC-ALGO"],
        involved_asset_ids=[0, 31566704],
        status="approved",
        risk_rules={"net_profit_after_fees_ok": True},
        created_at=created_at,
    )


def _seed_public_delay_store(tmp_path, monkeypatch) -> None:
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    now = time.time()
    store.record_opportunities(
        [
            _opportunity(
                FRESH_ROUTE_HASH,
                created_at=now - 10,
                expected_net_profit=1.25,
            ),
            _opportunity(
                DELAYED_ROUTE_HASH,
                created_at=now - PUBLIC_DELAY_SECONDS - 60,
                expected_net_profit=0.25,
            ),
        ]
    )
    monkeypatch.setattr(api_module, "store", store)
    monkeypatch.setattr(
        api_module,
        "settings",
        replace(
            api_module.settings,
            public_delay_seconds=PUBLIC_DELAY_SECONDS,
            use_vestige_discovery=False,
        ),
    )


def test_public_opportunities_exclude_fresh_routes_before_configured_delay(tmp_path, monkeypatch):
    _seed_public_delay_store(tmp_path, monkeypatch)

    response = _client().get("/api/opportunities")

    assert response.status_code == 200
    payload = response.json()
    route_hashes = {item["route_hash"] for item in payload}
    assert FRESH_ROUTE_HASH not in route_hashes
    assert route_hashes == {DELAYED_ROUTE_HASH}
    _assert_fresh_route_is_not_exposed(payload)
    _assert_no_execution_payload(payload)


def test_public_pulse_best_opportunity_uses_delayed_route_not_fresh_route(tmp_path, monkeypatch):
    _seed_public_delay_store(tmp_path, monkeypatch)

    response = _client().get("/api/pulse")

    assert response.status_code == 200
    payload = response.json()
    assert payload["opportunities_24h"] == 2
    assert payload["approved_24h"] == 2
    assert payload["best_opportunity"]["route_hash"] == DELAYED_ROUTE_HASH
    assert payload["best_opportunity"]["route_hash"] != FRESH_ROUTE_HASH
    _assert_fresh_route_is_not_exposed(payload)
    _assert_no_execution_payload(payload)
