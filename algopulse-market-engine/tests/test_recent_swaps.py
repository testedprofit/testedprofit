from __future__ import annotations

import json

from fastapi.testclient import TestClient

import algopulse.api as api_module
from algopulse.api import app
from algopulse.recent_swaps import normalize_vestige_swaps


SENSITIVE_FRAGMENTS = (
    "group",
    "address",
    "signature",
    "signed_transaction",
    "submission_payload",
    "private_key",
    "mnemonic",
    "hot_wallet",
    "raw_route_json",
    "route_json",
)


def _client() -> TestClient:
    return TestClient(app)


def _vestige_payload() -> dict:
    return {
        "results": [
            {
                "type": 0,
                "network_id": 0,
                "protocol_id": 2,
                "asset_1_id": 3169177585,
                "asset_2_id": 0,
                "offset": 3624160196,
                "block": 62718765,
                "timestamp": 1_783_015_919,
                "group": "public-group-id-omitted-by-normalizer",
                "address": "PUBLIC_ADDRESS_OMITTED_BY_NORMALIZER",
                "asset_1_delta": -14982.431022,
                "asset_2_delta": 1.000262,
                "asset_1_delta_value": 1.008272,
                "asset_2_delta_value": 1.000262,
            },
            {
                "type": 0,
                "network_id": 0,
                "protocol_id": 3,
                "asset_1_id": 3169177585,
                "asset_2_id": 1390638935,
                "offset": 3624160199,
                "block": 62718765,
                "timestamp": 1_783_015_919,
                "group": "public-group-id-omitted-by-normalizer",
                "address": "PUBLIC_ADDRESS_OMITTED_BY_NORMALIZER",
                "asset_1_delta": 14982.431022,
                "asset_2_delta": -0.20517296,
                "asset_1_delta_value": 1.008272,
                "asset_2_delta_value": 1.007768,
            },
        ],
        "extra": {
            "0": {"ticker": "ALGO"},
            "3169177585": {"ticker": "PNET"},
            "1390638935": {"ticker": "Max"},
        },
    }


def _assert_public_safe(payload: dict) -> None:
    serialized = json.dumps(payload, sort_keys=True).lower()
    for fragment in SENSITIVE_FRAGMENTS:
        assert fragment not in serialized


def test_vestige_recent_swaps_are_normalized_to_public_safe_rows():
    payload = normalize_vestige_swaps(_vestige_payload(), target_asset_id=3169177585, now=1_783_015_979)

    assert payload["source"] == "live"
    assert payload["sourceLabel"] == "Vestige swaps API"
    assert payload["dataPolicy"] == "public_read_only_historical_swaps"
    assert payload["publicSafe"] is True
    assert payload["freshExecutableRoutes"] is False
    assert payload["liveExecutionTouched"] is False
    assert payload["signerCodeTouched"] is False
    assert payload["count"] == 2

    first = payload["swaps"][0]
    assert first["fromAsset"] == "PNET"
    assert first["toAsset"] == "ALGO"
    assert first["inputAmount"] == 14982.431022
    assert first["expectedOutput"] == 1.000262
    assert first["protocolLabel"] == "Tinyman"
    assert first["ageLabel"] == "1m ago"
    assert first["sample"] is False
    _assert_public_safe(payload)


def test_recent_swaps_api_returns_redacted_vestige_market_data(monkeypatch):
    def fake_fetch_recent_pnet_swaps(**_kwargs):
        return normalize_vestige_swaps(_vestige_payload(), target_asset_id=3169177585, now=1_783_015_979)

    monkeypatch.setattr(api_module, "fetch_recent_pnet_swaps", fake_fetch_recent_pnet_swaps)

    response = _client().get("/api/market/pnet/recent-swaps?limit=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    data = payload["data"]
    assert data["source"] == "live"
    assert data["sourceLabel"] == "Vestige swaps API"
    assert data["count"] == 2
    assert data["swaps"][0]["pair"] == "PNET/ALGO"
    assert data["publicSafe"] is True
    assert data["freshExecutableRoutes"] is False
    assert data["liveExecutionTouched"] is False
    assert data["signerCodeTouched"] is False
    _assert_public_safe(payload)


def test_recent_swaps_api_fails_closed_as_unavailable(monkeypatch):
    def fail_fetch_recent_pnet_swaps(**_kwargs):
        raise OSError("network unavailable")

    monkeypatch.setattr(api_module, "fetch_recent_pnet_swaps", fail_fetch_recent_pnet_swaps)

    response = _client().get("/api/market/pnet/recent-swaps")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["source"] == "unavailable"
    assert data["count"] == 0
    assert data["swaps"] == []
    assert data["error"] == "vestige_recent_swaps_unavailable"
    assert data["liveExecutionTouched"] is False
    assert data["signerCodeTouched"] is False
