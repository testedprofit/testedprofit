from __future__ import annotations

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

import algopulse.api as api_module
from algopulse.api import app
from algopulse.config import get_settings
from algopulse.testnet_access import (
    assert_testnet_access_profile_safe,
    build_public_wallet_access_config,
    chain_id_for_network,
    is_valid_algo_address,
    validate_wallet_network,
)
from algopulse.testnet_access import TestnetAccessError
from algopulse.testnet_readiness import build_testnet_readiness

ZERO_ADDRESS = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"


def _testnet_settings(**overrides):
    base = get_settings()
    values = {
        "env": "testnet",
        "network": "testnet",
        "connector_mode": "tinyman,pact",
        "public_delay_seconds": 900,
        "algod_url": "https://testnet-api.algonode.cloud",
        "indexer_url": "https://testnet-idx.algonode.cloud",
        "target_asset_id": 0,
        "asset_pairs": ((0, 10_458_941),),
        "enable_live_execution": False,
        "execute_approved": False,
        "allow_api_execution": False,
        "unsigned_executor_only": True,
        "signer_enabled": False,
        "signer_kill_switch": True,
        "trader_mnemonic": "",
        "enable_scanner": False,
    }
    values.update(overrides)
    return replace(base, **values)


def test_fail_closed_testnet_access_profile():
    assert_testnet_access_profile_safe(_testnet_settings())
    with pytest.raises(TestnetAccessError):
        assert_testnet_access_profile_safe(_testnet_settings(network="mainnet"))
    with pytest.raises(TestnetAccessError):
        assert_testnet_access_profile_safe(
            _testnet_settings(algod_url="https://mainnet-api.algonode.cloud")
        )
    with pytest.raises(Exception):
        assert_testnet_access_profile_safe(_testnet_settings(enable_live_execution=True))


def test_api_startup_fails_closed_when_testnet_profile_is_armed(monkeypatch):
    monkeypatch.setattr(
        api_module,
        "settings",
        _testnet_settings(enable_live_execution=True, enable_scanner=False),
    )
    with pytest.raises(Exception, match="refused_live_execution_enabled"):
        with TestClient(app):
            pass


def test_address_validation_checks_algorand_checksum_not_only_shape():
    assert is_valid_algo_address(ZERO_ADDRESS) is True
    assert is_valid_algo_address("B" * 58) is False


def test_validate_wallet_network_rejects_mainnet_mismatch():
    settings = _testnet_settings()
    ok = validate_wallet_network(settings, claimed_network="testnet", claimed_chain_id=416002)
    bad = validate_wallet_network(settings, claimed_network="mainnet", claimed_chain_id=416001)
    assert ok["ok"] is True
    assert bad["ok"] is False
    assert bad["rejected"] is True
    assert "mismatch" in (bad["rejectionCode"] or "")


def test_public_wallet_access_config_identifies_testnet_and_connect_only():
    cfg = build_public_wallet_access_config(_testnet_settings())
    assert cfg["network"] == "testnet"
    assert cfg["developmentPhase"] == "AlgoPulse Phase 3: TestNet Access"
    assert cfg["walletAccessMode"] == "connect_only"
    assert cfg["supportedWallets"] == ["pera", "defly"]
    assert cfg["pnetAsaConfigured"] is False
    assert cfg["pnetMessage"] == "PNET TestNet asset not configured"
    assert cfg["capabilities"]["signTransactions"] is False
    assert cfg["capabilities"]["submitTransactions"] is False
    assert cfg["chainId"] == chain_id_for_network("testnet")


def test_wallet_connection_ready_without_pnet_when_live_health_ok():
    health = {
        "overall": "ok",
        "ok": True,
        "mismatches": [],
        "algod": {"healthy": True, "detail": "algod_status_ok", "connector": "algod"},
        "indexer": {"healthy": True, "detail": "indexer_reachable", "connector": "indexer"},
    }
    report = build_testnet_readiness(_testnet_settings(), network_health=health)
    assert report["walletConnectionReady"] is True
    assert report["pnetAsaConfigured"] is False
    assert report["pnetMessage"] == "PNET TestNet asset not configured"
    wallet = next(item for item in report["checks"] if item["key"] == "wallet_boundary")
    assert wallet["status"] == "pass"
    assert wallet["reason"] == "connect_only_pera_defly_adapters_available"


def test_public_config_and_wallet_account_mismatch_api(monkeypatch):
    monkeypatch.setattr(api_module, "settings", _testnet_settings())
    client = TestClient(app)

    public = client.get("/api/config/public").json()
    assert public["ok"] is True
    data = public["data"]
    assert data["network"] == "testnet"
    assert data["developmentPhase"] == "AlgoPulse Phase 3: TestNet Access"
    assert data["walletAccessMode"] == "connect_only"
    assert data["supportedWallets"] == ["pera", "defly"]
    assert data["backendNetworkAuthority"] is True
    assert data["signingEnabled"] is False
    assert data["submissionEnabled"] is False

    # Valid checksum address shape for validation path (not a live funded account required here)
    address = ZERO_ADDRESS
    mismatch = client.get(
        f"/api/wallet/account/{address}",
        params={"network": "mainnet", "chain_id": 416001, "provider": "pera"},
    )
    assert mismatch.status_code == 409
    body = mismatch.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "WALLET_NETWORK_MISMATCH"


def test_wallet_account_api_refuses_non_testnet_backend(monkeypatch):
    monkeypatch.setattr(api_module, "settings", _testnet_settings(network="mainnet"))
    response = TestClient(app).get(
        f"/api/wallet/account/{ZERO_ADDRESS}",
        params={"network": "mainnet", "chain_id": 416001, "provider": "pera"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "TESTNET_ACCESS_PROFILE_BLOCKED"


def test_public_config_does_not_treat_mainnet_pnet_id_as_testnet_asset(monkeypatch):
    settings = _testnet_settings(target_asset_id=3_169_177_585)
    monkeypatch.setattr(api_module, "settings", settings)
    data = TestClient(app).get("/api/config/public").json()["data"]
    assert data["pnetAsaConfigured"] is False
    assert data["pnetAsaId"] == 0
    assert data["pnetMessage"] == "PNET TestNet asset not configured"


def test_readiness_api_includes_live_health_shape(monkeypatch):
    monkeypatch.setattr(api_module, "settings", _testnet_settings())

    def fake_health(_settings):
        return {
            "network": "testnet",
            "environment": "testnet",
            "overall": "ok",
            "ok": True,
            "mismatches": [],
            "algod": {
                "connector": "algod",
                "status": "ok",
                "healthy": True,
                "lastRound": 12,
                "networkHint": "testnet",
                "latencyMs": 1.2,
                "detail": "algod_status_ok",
            },
            "indexer": {
                "connector": "indexer",
                "status": "ok",
                "healthy": True,
                "lastRound": 11,
                "networkHint": "testnet",
                "latencyMs": 2.2,
                "detail": "indexer_reachable",
            },
            "productionReady": False,
            "signingEnabled": False,
            "submissionEnabled": False,
            "walletAccessMode": "connect_only",
        }

    monkeypatch.setattr(api_module, "build_network_health", fake_health)
    payload = TestClient(app).get("/api/testnet/readiness").json()
    assert payload["ok"] is True
    data = payload["data"]
    assert data["walletConnectionReady"] is True
    assert data["networkHealth"]["algod"]["healthy"] is True
    assert data["networkHealth"]["indexer"]["healthy"] is True
    serialized = str(payload).lower()
    assert "testnet-api.algonode" not in serialized
    assert "token=" not in serialized
