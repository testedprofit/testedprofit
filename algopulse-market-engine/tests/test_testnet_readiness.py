from __future__ import annotations

import json
from dataclasses import replace

from fastapi.testclient import TestClient

import algopulse.api as api_module
from algopulse.api import app
from algopulse.config import get_settings
from algopulse.testnet_readiness import build_testnet_readiness


TESTNET_PNET_ASSET_ID = 9_999_999
TESTNET_USDC_ASSET_ID = 10_458_941


def _testnet_settings(**overrides):
    base = get_settings()
    values = {
        "env": "testnet",
        "network": "testnet",
        "connector_mode": "tinyman,pact",
        "public_delay_seconds": 900,
        "algod_url": "https://testnet-api.algonode.cloud",
        "indexer_url": "https://testnet-idx.algonode.cloud",
        "target_asset_id": TESTNET_PNET_ASSET_ID,
        "asset_pairs": (
            (0, TESTNET_PNET_ASSET_ID),
            (TESTNET_USDC_ASSET_ID, TESTNET_PNET_ASSET_ID),
        ),
        "enable_live_execution": False,
        "execute_approved": False,
        "allow_api_execution": False,
        "unsigned_executor_only": True,
        "signer_enabled": False,
        "signer_kill_switch": True,
        "trader_mnemonic": "",
    }
    values.update(overrides)
    return replace(base, **values)


def _check(report: dict, key: str) -> dict:
    return next(item for item in report["checks"] if item["key"] == key)


def test_safe_testnet_profile_is_ready_for_read_only_wallet_review():
    report = build_testnet_readiness(_testnet_settings())

    # Without live health probes, config-only path remains ready for read-only review;
    # walletConnectionReady requires live algod/Indexer evidence (access phase).
    assert report["readOnlyStatus"] == "ready"
    assert report["testnetReadOnlyReady"] is True
    assert report["productionReady"] is False
    assert _check(report, "execution_boundary")["reason"] == "execution_and_signer_disarmed"
    assert _check(report, "wallet_boundary")["reason"] == "connect_only_pera_defly_adapters_available"
    assert _check(report, "wallet_boundary")["status"] == "pass"
    assert report["walletAccessMode"] == "connect_only"
    assert report["supportedWallets"] == ["pera", "defly"]


def test_mainnet_network_and_asset_ids_block_testnet_readiness():
    report = build_testnet_readiness(
        _testnet_settings(
            network="mainnet",
            target_asset_id=3_169_177_585,
            asset_pairs=((0, 31_566_704), (0, 3_169_177_585)),
            algod_url="https://mainnet-api.algonode.cloud",
            indexer_url="https://mainnet-idx.algonode.cloud",
        )
    )

    assert report["status"] == "blocked"
    assert _check(report, "network")["status"] == "blocked"
    assert _check(report, "algod_endpoint")["reason"] == "algod_endpoint_points_to_mainnet"
    assert _check(report, "indexer_endpoint")["reason"] == "indexer_endpoint_points_to_mainnet"
    assert _check(report, "asset_configuration")["reason"] == "target_asset_3169177585_is_mainnet_only"


def test_missing_testnet_pnet_asset_and_mock_connectors_are_explicit():
    report = build_testnet_readiness(
        _testnet_settings(
            target_asset_id=0,
            asset_pairs=((0, TESTNET_USDC_ASSET_ID),),
            connector_mode="mock",
        )
    )

    assert report["readOnlyStatus"] == "blocked"
    assert _check(report, "asset_configuration")["reason"] == "testnet_pnet_asset_id_not_configured"
    assert _check(report, "connectors")["status"] == "wait"
    assert _check(report, "connectors")["reason"] == "mock_connectors_not_testnet_evidence"


def test_execution_or_signer_enablement_blocks_testnet_readiness():
    report = build_testnet_readiness(
        _testnet_settings(enable_live_execution=True, signer_enabled=True, signer_kill_switch=False)
    )

    assert report["readOnlyStatus"] == "blocked"
    assert _check(report, "execution_boundary")["reason"] == "execution_or_signer_boundary_open"
    # boundaries must reflect runtime flags, not hardcode a false disarmed posture
    assert report["boundaries"]["readOnly"] is False
    assert report["boundaries"]["signingEnabled"] is True
    assert report["boundaries"]["submissionEnabled"] is True
    assert report["boundaries"]["liveTradingEnabled"] is True
    assert report["boundaries"]["killSwitchActive"] is False


def test_safe_testnet_profile_boundaries_report_disarmed_truthfully():
    report = build_testnet_readiness(_testnet_settings())

    assert report["boundaries"] == {
        "readOnly": True,
        "walletConnectOnly": True,
        "signingEnabled": False,
        "submissionEnabled": False,
        "liveTradingEnabled": False,
        "killSwitchActive": True,
    }


def test_custom_node_endpoints_require_review_without_exposing_urls():
    report = build_testnet_readiness(
        _testnet_settings(
            algod_url="https://node.internal.example?token=sensitive",
            indexer_url="https://index.internal.example?token=sensitive",
        )
    )
    serialized = json.dumps(report, sort_keys=True)

    assert report["readOnlyStatus"] == "in_progress"
    assert _check(report, "algod_endpoint")["reason"] == "algod_endpoint_custom_network_requires_review"
    assert _check(report, "indexer_endpoint")["reason"] == "indexer_endpoint_custom_network_requires_review"
    assert "sensitive" not in serialized
    assert "node.internal.example" not in serialized


def test_testnet_readiness_api_returns_public_safe_redacted_contract(monkeypatch):
    monkeypatch.setattr(api_module, "settings", _testnet_settings())

    response = TestClient(app).get("/api/testnet/readiness")
    payload = response.json()

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["data"]["testnetReadOnlyReady"] is True
    assert payload["data"]["walletAccessMode"] == "connect_only"
    # Live health is probed by the API; connection readiness depends on probe result.
    assert "walletConnectionReady" in payload["data"]
    serialized = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "private_key",
        "mnemonic",
        "signed_txn",
        "submission_payload",
        "hot_wallet",
        "algod_token",
        "indexer_token",
    ):
        assert forbidden not in serialized
