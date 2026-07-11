from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

import algopulse.api as api_module
from algopulse.api import LOCAL_REVIEW_ADMIN_WALLET
from algopulse.api import app
from algopulse.config import get_settings
from algopulse.store import MarketStore
from algopulse.testnet_soak import SoakProbeDeps
from algopulse.testnet_soak import acquire_soak_lock
from algopulse.testnet_soak import contains_forbidden_evidence
from algopulse.testnet_soak import release_soak_lock
from algopulse.testnet_soak import run_once


REQUIRED_ROLLUP_KEYS = {
    "firstObservationAt",
    "latestObservationAt",
    "elapsedCoverageSeconds",
    "completedObservationCount",
    "expectedObservationCount",
    "coveragePercent",
    "longestGapSeconds",
    "scannerSuccessRate",
    "connectors",
    "poolsObserved",
    "quotesObserved",
    "freshQuoteCount",
    "staleQuoteCount",
    "paper",
    "blockers",
    "warnings",
    "gateStatus",
    "productionReady",
}

DANGEROUS_TOKENS = (
    "mnemonic",
    "private_key",
    "seed_phrase",
    "hot_wallet",
    "signed_txn",
    "submission_payload",
    "execution_queue",
    "raw_route_json",
    "signer_secret",
)


def _settings(tmp_path: Path, **overrides):
    get_settings.cache_clear()
    base = get_settings()
    values = {
        "env": "testnet",
        "network": "testnet",
        "data_dir": tmp_path / "data",
        "database_path": tmp_path / "data" / "soak-api.db",
        "connector_mode": "tinyman,pact",
        "public_delay_seconds": 900,
        "enable_live_execution": False,
        "execute_approved": False,
        "allow_api_execution": False,
        "unsigned_executor_only": True,
        "signer_enabled": False,
        "signer_kill_switch": True,
        "trader_mnemonic": "",
        "max_route_age_seconds": 5.0,
    }
    values.update(overrides)
    return replace(base, **values)


def _admin_headers() -> dict[str, str]:
    return {
        "X-Algopulse-Role": "admin",
        "X-Algopulse-Wallet": LOCAL_REVIEW_ADMIN_WALLET,
    }


def _live_deps(*, pact_status: str = "ok") -> SoakProbeDeps:
    def probe_algod() -> dict:
        return {"status": "ok", "latencyMs": 10.0, "latestRound": 1000, "detail": None}

    def probe_indexer() -> dict:
        return {"status": "ok", "latencyMs": 12.0, "latestRound": 999, "detail": None}

    def run_scan() -> dict:
        return {
            "status": "degraded" if pact_status == "error" else "ok",
            "pools": 1,
            "opportunities": 0,
            "approved": 0,
            "paper_candidates": 0,
            "paper_rechecks_5s": 0,
            "paper_rechecks_30s": 0,
            "connector_error_count": 1 if pact_status == "error" else 0,
            "connector_degraded_count": 0,
            "connector_health": [
                {
                    "connectorName": "tinyman",
                    "status": "ok",
                    "detail": None,
                    "latencyMs": 40.0,
                    "poolCount": 1,
                },
                {
                    "connectorName": "pact",
                    "status": pact_status,
                    "detail": None if pact_status == "ok" else "pact_api_non_json_response",
                    "latencyMs": 90.0,
                    "poolCount": 0 if pact_status == "error" else 1,
                },
            ],
        }

    return SoakProbeDeps(
        probe_algod=probe_algod,
        probe_indexer=probe_indexer,
        run_scan=run_scan,
        quote_freshness=lambda: {
            "quoteCount": 2,
            "freshCount": 1,
            "agingCount": 0,
            "staleCount": 1,
            "unavailableCount": 0,
            "source": "stored",
        },
    )


def _bind_store(monkeypatch, settings, store: MarketStore) -> TestClient:
    monkeypatch.setattr(api_module, "store", store)
    monkeypatch.setattr(api_module, "settings", settings)
    return TestClient(app)


def test_admin_can_access_both_testnet_soak_endpoints(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    observation = run_once(settings=settings, store=store, run_id="api_ok", deps=_live_deps())
    client = _bind_store(monkeypatch, settings, store)

    summary = client.get("/api/ops/testnet-soak", headers=_admin_headers())
    recent = client.get("/api/ops/testnet-soak/observations?limit=50", headers=_admin_headers())

    assert summary.status_code == 200
    assert recent.status_code == 200
    assert summary.json()["ok"] is True
    assert recent.json()["ok"] is True
    assert recent.json()["data"]["count"] == 1
    assert recent.json()["data"]["observations"][0]["observationId"] == observation["observationId"]


def test_summary_reports_the_real_runner_lock_state(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)
    client = _bind_store(monkeypatch, settings, store)
    lock = acquire_soak_lock(settings, run_id="api_running")
    try:
        data = client.get("/api/ops/testnet-soak", headers=_admin_headers()).json()["data"]
        assert data["runnerState"] == "running"
        assert data["productionReady"] is False
        assert data["liveExecutionLocked"] is True
    finally:
        release_soak_lock(lock)


def test_non_admin_is_rejected_by_backend(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)
    client = _bind_store(monkeypatch, settings, store)

    guest = client.get("/api/ops/testnet-soak")
    user = client.get(
        "/api/ops/testnet-soak/observations",
        headers={"X-Algopulse-Role": "user", "X-Algopulse-Wallet": "USERWALLET123"},
    )
    assert guest.status_code == 403
    assert user.status_code == 403


def test_empty_store_returns_valid_empty_state(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)
    client = _bind_store(monkeypatch, settings, store)

    summary = client.get("/api/ops/testnet-soak", headers=_admin_headers()).json()["data"]
    recent = client.get("/api/ops/testnet-soak/observations", headers=_admin_headers()).json()["data"]

    assert summary["completedObservationCount"] == 0
    assert summary["firstObservationAt"] is None
    assert summary["latestObservationAt"] is None
    assert summary["gateStatus"] in {"not_started", "in_progress"}
    assert "no_live_observations" in summary["blockers"]
    assert summary["productionReady"] is False
    assert recent["observations"] == []
    assert recent["count"] == 0
    assert recent["source"] == "unavailable"
    assert recent["productionReady"] is False


def test_summary_response_matches_rollup_contract(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    run_once(settings=settings, store=store, run_id="contract", deps=_live_deps(pact_status="error"))
    client = _bind_store(monkeypatch, settings, store)

    data = client.get("/api/ops/testnet-soak", headers=_admin_headers()).json()["data"]
    missing = REQUIRED_ROLLUP_KEYS - set(data.keys())
    assert not missing, f"missing rollup keys: {missing}"
    assert data["productionReady"] is False
    assert data["gateStatus"] in {"not_started", "in_progress", "blocked", "ready_for_review"}
    assert isinstance(data["blockers"], list)
    assert isinstance(data["warnings"], list)
    assert "tinyman" in data["connectors"]
    assert "pact" in data["connectors"]
    assert data["paper"]["recheckCompleted5s"] == 0
    assert data["paper"]["recheckCompleted30s"] == 0
    # One-shot must not claim 24h completion.
    assert "elapsed_coverage_below_24h" in data["blockers"]
    assert data["gateStatus"] != "ready_for_review"


def test_observation_limit_is_enforced_at_fifty(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    for index in range(55):
        run_once(
            settings=settings,
            store=store,
            run_id="limit_run",
            deps=_live_deps(),
            acquire_lock=False,
        )
    client = _bind_store(monkeypatch, settings, store)

    recent = client.get("/api/ops/testnet-soak/observations?limit=999", headers=_admin_headers()).json()["data"]
    assert recent["limit"] == 50
    assert recent["requestedLimit"] == 999
    assert recent["count"] == 50
    assert len(recent["observations"]) == 50
    # Newest first: sequence numbers should be non-increasing.
    sequences = [item["sequenceNumber"] for item in recent["observations"]]
    assert sequences == sorted(sequences, reverse=True)


def test_api_responses_exclude_dangerous_wallet_and_execution_fields(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    run_once(settings=settings, store=store, run_id="safe_api", deps=_live_deps())
    client = _bind_store(monkeypatch, settings, store)

    summary = client.get("/api/ops/testnet-soak", headers=_admin_headers()).json()
    recent = client.get("/api/ops/testnet-soak/observations?limit=10", headers=_admin_headers()).json()

    for payload in (summary, recent):
        assert contains_forbidden_evidence(payload) == []
        data = payload["data"]
        # Evidence body (excluding local-review adminSession) must not carry wallet/signing material.
        evidence = {key: value for key, value in data.items() if key != "adminSession"}
        serialized = json.dumps(evidence).lower()
        for token in DANGEROUS_TOKENS:
            assert token not in serialized
        assert "mnemonic" not in serialized
        assert "private_key" not in serialized
        assert "signed_txn" not in serialized
        assert "submission_payload" not in serialized
        assert "hot_wallet" not in serialized
        assert "execution_queue" not in serialized
        assert "raw_route" not in serialized
        assert "signer" not in serialized
        # No wallet custody fields on the soak evidence itself.
        assert "wallet" not in serialized


def test_mock_evidence_cannot_report_production_ready(tmp_path, monkeypatch):
    settings = _settings(tmp_path, connector_mode="mock")
    store = MarketStore(settings.database_path)
    run_once(settings=settings, store=store, run_id="mock_api", deps=_live_deps())
    client = _bind_store(monkeypatch, settings, store)

    summary = client.get("/api/ops/testnet-soak", headers=_admin_headers()).json()["data"]
    recent = client.get("/api/ops/testnet-soak/observations", headers=_admin_headers()).json()["data"]

    assert summary["productionReady"] is False
    assert recent["productionReady"] is False
    assert summary["completedObservationCount"] == 0
    assert "mock_observations_do_not_count_toward_live_coverage" in summary["blockers"] or "no_live_observations" in summary["blockers"]
    assert recent["observations"][0]["source"] == "mock"
    assert recent["observations"][0]["productionReady"] is False
