from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import algopulse.api as api_module
from algopulse.api import LOCAL_REVIEW_ADMIN_WALLET
from algopulse.api import app
from algopulse.config import get_settings
from algopulse.store import MarketStore
from algopulse.testnet_soak import (
    FORBIDDEN_EVIDENCE_TOKENS,
    SOAK_TARGET_SECONDS,
    SoakLockError,
    SoakProbeDeps,
    SoakSafetyError,
    acquire_soak_lock,
    assert_safe_to_run,
    build_observation,
    build_soak_rollup,
    build_testnet_soak_summary,
    contains_forbidden_evidence,
    public_safe_observation,
    release_soak_lock,
    run_once,
    summarize_testnet_soak_readiness,
)


def _settings(tmp_path: Path, **overrides):
    get_settings.cache_clear()
    base = get_settings()
    values = {
        "env": "testnet",
        "network": "testnet",
        "data_dir": tmp_path / "data",
        "database_path": tmp_path / "data" / "soak.db",
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


def _live_deps(
    *,
    algod_round: int = 1000,
    indexer_round: int = 990,
    tinyman_status: str = "ok",
    pact_status: str = "ok",
    scanner_status: str = "ok",
    pools: int = 2,
    paper_candidates: int = 1,
    recheck_5s: int = 1,
    recheck_30s: int = 1,
    quotes: dict | None = None,
) -> SoakProbeDeps:
    quote_payload = quotes or {
        "quoteCount": 4,
        "freshCount": 3,
        "agingCount": 1,
        "staleCount": 0,
        "unavailableCount": 0,
        "source": "stored",
    }

    def probe_algod() -> dict:
        return {"status": "ok", "latencyMs": 12.0, "latestRound": algod_round, "detail": None}

    def probe_indexer() -> dict:
        return {
            "status": "ok",
            "latencyMs": 18.0,
            "latestRound": indexer_round,
            "detail": None,
        }

    def run_scan() -> dict:
        return {
            "status": scanner_status,
            "pools": pools,
            "opportunities": 2,
            "approved": 0,
            "paper_candidates": paper_candidates,
            "paper_rechecks_5s": recheck_5s,
            "paper_rechecks_30s": recheck_30s,
            "connector_error_count": 1 if pact_status == "error" else 0,
            "connector_degraded_count": 1 if pact_status == "degraded" else 0,
            "connector_health": [
                {
                    "connectorName": "tinyman",
                    "status": tinyman_status,
                    "detail": None if tinyman_status == "ok" else "tinyman_issue",
                    "latencyMs": 40.0,
                    "poolCount": pools if tinyman_status != "error" else 0,
                },
                {
                    "connectorName": "pact",
                    "status": pact_status,
                    "detail": None if pact_status == "ok" else "pact_api_non_json_response",
                    "latencyMs": 120.0,
                    "poolCount": 0 if pact_status == "error" else 1,
                },
            ],
        }

    return SoakProbeDeps(
        probe_algod=probe_algod,
        probe_indexer=probe_indexer,
        run_scan=run_scan,
        quote_freshness=lambda: quote_payload,
    )


def test_mainnet_configuration_refuses_to_start(tmp_path):
    settings = _settings(tmp_path, network="mainnet")
    with pytest.raises(SoakSafetyError, match="refused_non_testnet_network"):
        assert_safe_to_run(settings)


def test_execution_enabled_configuration_refuses_to_start(tmp_path):
    settings = _settings(tmp_path, enable_live_execution=True)
    with pytest.raises(SoakSafetyError, match="refused_live_execution_enabled"):
        assert_safe_to_run(settings)


def test_signer_enabled_configuration_refuses_to_start(tmp_path):
    settings = _settings(tmp_path, signer_enabled=True)
    with pytest.raises(SoakSafetyError, match="refused_signer_enabled"):
        assert_safe_to_run(settings)


def test_successful_testnet_observation_persists_health_shape(tmp_path):
    """Successful TestNet one-shot stores timestamps, rounds, latency, counts, and status."""
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    observation = run_once(
        settings=settings,
        store=store,
        run_id="run_ok",
        deps=_live_deps(
            algod_round=12_345,
            indexer_round=12_340,
            tinyman_status="ok",
            pact_status="ok",
            scanner_status="ok",
            pools=2,
        ),
        acquire_lock=True,
    )
    rows = store.list_testnet_soak_observations(limit=20)
    assert len(rows) == 1
    stored = rows[0]

    assert stored["observationId"] == observation["observationId"]
    assert stored["network"] == "testnet"
    assert stored["source"] == "live"
    assert stored["status"] == "ok"
    assert stored["startedAt"] <= stored["completedAt"]
    assert stored["algod"]["status"] == "ok"
    assert stored["algod"]["latestRound"] == 12_345
    assert stored["algod"]["latencyMs"] == 12.0
    assert stored["indexer"]["status"] == "ok"
    assert stored["indexer"]["latestRound"] == 12_340
    assert stored["indexer"]["latencyMs"] == 18.0
    assert stored["indexer"]["roundLag"] == 5
    assert stored["tinyman"]["status"] == "ok"
    assert stored["tinyman"]["poolCount"] == 2
    assert stored["tinyman"]["latencyMs"] == 40.0
    assert stored["pact"]["status"] == "ok"
    assert stored["poolsObserved"] == 2
    assert stored["quotesObserved"] == 4
    assert stored["quoteFreshness"]["fresh"] == 3
    assert stored["errors"] == []
    assert stored["degradedReasons"] == []
    assert stored["productionReady"] is False
    assert stored["liveExecutionLocked"] is True


def test_one_shot_mode_stores_exactly_one_completed_observation(tmp_path):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    observation = run_once(
        settings=settings,
        store=store,
        run_id="run_one",
        deps=_live_deps(),
        acquire_lock=True,
    )
    rows = store.list_testnet_soak_observations(limit=20)
    assert len(rows) == 1
    assert rows[0]["observationId"] == observation["observationId"]
    assert rows[0]["source"] == "live"
    assert rows[0]["productionReady"] is False


def test_restarted_run_preserves_earlier_observations(tmp_path):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    first = run_once(settings=settings, store=store, run_id="run_restart", deps=_live_deps(algod_round=10))
    second = run_once(settings=settings, store=store, run_id="run_restart", deps=_live_deps(algod_round=11))
    rows = store.list_testnet_soak_observations(limit=20)
    assert len(rows) == 2
    assert {item["observationId"] for item in rows} == {first["observationId"], second["observationId"]}
    assert [item["sequenceNumber"] for item in rows] == [1, 2]


def test_overlapping_runner_instances_are_rejected(tmp_path, monkeypatch):
    import algopulse.testnet_soak as soak_module

    settings = _settings(tmp_path)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    lock_file = settings.data_dir / "testnet_soak.lock"
    lock_file.write_text(json.dumps({"pid": 424242, "runId": "held"}), encoding="utf-8")
    monkeypatch.setattr(soak_module, "_pid_is_alive", lambda pid: pid == 424242)
    with pytest.raises(SoakLockError, match="another_soak_runner_active"):
        acquire_soak_lock(settings, run_id="challenger")


def test_tinyman_success_plus_pact_failure_records_degraded_evidence(tmp_path):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    observation = run_once(
        settings=settings,
        store=store,
        run_id="run_deg",
        deps=_live_deps(pact_status="error", scanner_status="degraded", pools=1),
    )
    assert observation["status"] == "degraded"
    assert observation["tinyman"]["status"] == "ok"
    assert observation["tinyman"]["poolCount"] == 1
    assert observation["pact"]["status"] == "error"
    assert observation["pact"]["detail"] == "pact_api_non_json_response"
    assert observation["scanner"]["status"] == "degraded"
    assert "pact_error" in observation["degradedReasons"]
    assert observation["poolsObserved"] == 1
    # Tinyman evidence is retained; Pact failure is not fabricated away.
    stored = store.list_testnet_soak_observations(limit=1)[0]
    assert stored["status"] == "degraded"
    assert stored["tinyman"]["status"] == "ok"
    assert stored["pact"]["status"] == "error"


def test_stale_algod_blocks_the_rollup(tmp_path):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)
    base = 1_700_000_000.0
    observations = []
    for index in range(3):
        obs = build_observation(
            settings=settings,
            store=store,
            run_id="run_stale",
            sequence_number=index + 1,
            deps=_live_deps(algod_round=5000, paper_candidates=2, recheck_5s=2, recheck_30s=2),
            now=base + index * 200,
        )
        obs["completedAt"] = base + index * 200
        observations.append(obs)
    rollup = build_soak_rollup(observations, interval_seconds=60, now=base + 700)
    assert "stale_algod_no_round_progress" in rollup["blockers"] or "stale_or_unhealthy_algod" in rollup["blockers"]
    assert rollup["productionReady"] is False
    assert rollup["gateStatus"] in {"blocked", "in_progress"}
    assert rollup["currentGateStatus"] in {"blocked", "in_progress"}


def test_stale_indexer_with_fresh_algod_produces_wait_warning(tmp_path):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)
    observation = build_observation(
        settings=settings,
        store=store,
        run_id="run_idx",
        sequence_number=1,
        deps=_live_deps(algod_round=10_000, indexer_round=9_900, paper_candidates=1, recheck_5s=1, recheck_30s=1),
    )
    assert observation["indexer"]["roundLag"] == 100
    assert "indexer_round_lag" in observation["degradedReasons"]
    rollup = build_soak_rollup([observation], interval_seconds=60)
    assert "indexer_lag_while_algod_progresses" in rollup["warnings"]
    assert rollup["productionReady"] is False


def test_mock_observations_do_not_count_toward_live_24h_coverage(tmp_path):
    settings = _settings(tmp_path, connector_mode="mock")
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)
    observation = build_observation(
        settings=settings,
        store=store,
        run_id="run_mock",
        sequence_number=1,
        deps=_live_deps(),
    )
    assert observation["source"] == "mock"
    rollup = build_soak_rollup([observation], interval_seconds=60)
    assert rollup["completedObservationCount"] == 0
    assert "no_live_observations" in rollup["blockers"]
    assert "mock_observations_do_not_count_toward_live_coverage" in rollup["blockers"]
    assert rollup["coveragePercent"] == 0.0
    assert rollup["productionReady"] is False


def test_coverage_cannot_reach_complete_before_24_elapsed_hours(tmp_path):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)
    base = 1_700_000_000.0
    observations = []
    for index in range(5):
        obs = build_observation(
            settings=settings,
            store=store,
            run_id="run_short",
            sequence_number=index + 1,
            deps=_live_deps(algod_round=1000 + index, paper_candidates=3, recheck_5s=2, recheck_30s=2),
            now=base + index * 60,
        )
        obs["completedAt"] = base + index * 60
        observations.append(obs)
    rollup = build_soak_rollup(observations, interval_seconds=60, now=base + 300)
    assert rollup["elapsedCoverageSeconds"] < 24 * 3600
    assert "elapsed_coverage_below_24h" in rollup["blockers"]
    assert rollup["gateStatus"] != "ready_for_review"
    assert rollup["currentGateStatus"] != "ready_for_review"
    assert rollup["productionReady"] is False
    assert rollup["coveragePercent"] < 100.0


def test_one_shot_evidence_never_claims_24h_completion(tmp_path):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    run_once(settings=settings, store=store, run_id="oneshot", deps=_live_deps())
    rollup = summarize_testnet_soak_readiness(store, interval_seconds=60)
    assert rollup["completedObservationCount"] == 1
    assert rollup["elapsedCoverageSeconds"] == 0.0
    assert "elapsed_coverage_below_24h" in rollup["blockers"]
    assert "one_shot_evidence_not_24h_completion" in rollup["warnings"]
    assert rollup["gateStatus"] != "ready_for_review"
    assert rollup["productionReady"] is False


def test_incomplete_paper_evidence_is_blocker_even_with_long_window():
    base = 1_700_000_000.0
    observations = []
    for index in range(3):
        observations.append(
            {
                "source": "live",
                "runId": "no_paper",
                "completedAt": base + index * (SOAK_TARGET_SECONDS / 2),
                "scanner": {"status": "ok"},
                "algod": {"status": "ok", "latestRound": 100 + index},
                "indexer": {"status": "ok", "latestRound": 100 + index, "roundLag": 0},
                "tinyman": {"status": "ok"},
                "pact": {"status": "ok"},
                "poolsObserved": 1,
                "quotesObserved": 2,
                "quoteFreshness": {"fresh": 2, "aging": 0, "stale": 0, "unavailable": 0},
                "routes": {
                    "routeCandidateCount": 0,
                    "approvedRouteCount": 0,
                    "rejectedRouteCount": 0,
                    "rejectionReasons": [],
                },
                "paper": {"candidateCount": 0, "recheckCompleted5s": 0, "recheckCompleted30s": 0},
            }
        )
    rollup = build_soak_rollup(observations, interval_seconds=60, now=base + SOAK_TARGET_SECONDS)
    assert rollup["elapsedCoverageSeconds"] >= SOAK_TARGET_SECONDS
    assert "missing_paper_trading_evidence" in rollup["blockers"]
    assert rollup["paper"]["recheckCompleted5s"] == 0
    assert rollup["paper"]["recheckCompleted30s"] == 0
    assert rollup["productionReady"] is False
    assert rollup["gateStatus"] != "ready_for_review"


def test_degraded_connectors_remain_visible_in_rollup_counts():
    base = 1_700_000_000.0
    observations = [
        {
            "source": "live",
            "runId": "deg",
            "completedAt": base,
            "scanner": {"status": "degraded"},
            "algod": {"status": "ok", "latestRound": 10},
            "indexer": {"status": "ok", "latestRound": 10, "roundLag": 0},
            "tinyman": {"status": "ok"},
            "pact": {"status": "error"},
            "poolsObserved": 1,
            "quotesObserved": 1,
            "quoteFreshness": {"fresh": 1, "aging": 0, "stale": 0, "unavailable": 0},
            "routes": {
                "routeCandidateCount": 0,
                "approvedRouteCount": 0,
                "rejectedRouteCount": 0,
                "rejectionReasons": [],
            },
            "paper": {"candidateCount": 1, "recheckCompleted5s": 1, "recheckCompleted30s": 0},
        },
        {
            "source": "live",
            "runId": "deg",
            "completedAt": base + 120,
            "scanner": {"status": "degraded"},
            "algod": {"status": "ok", "latestRound": 11},
            "indexer": {"status": "ok", "latestRound": 11, "roundLag": 0},
            "tinyman": {"status": "ok"},
            "pact": {"status": "degraded"},
            "poolsObserved": 1,
            "quotesObserved": 1,
            "quoteFreshness": {"fresh": 0, "aging": 0, "stale": 1, "unavailable": 0},
            "routes": {
                "routeCandidateCount": 0,
                "approvedRouteCount": 0,
                "rejectedRouteCount": 0,
                "rejectionReasons": [],
            },
            "paper": {"candidateCount": 1, "recheckCompleted5s": 1, "recheckCompleted30s": 1},
        },
    ]
    rollup = build_soak_rollup(observations, interval_seconds=60)
    assert rollup["connectors"]["tinyman"]["ok"] == 2
    assert rollup["connectors"]["pact"]["down"] == 1
    assert rollup["connectors"]["pact"]["degraded"] == 1
    assert rollup["staleQuoteCount"] == 1
    assert rollup["freshQuoteCount"] == 1
    assert "pact_degraded_or_down" in rollup["warnings"]
    assert "connector_failures_visible_in_rollup" in rollup["warnings"]
    assert rollup["scannerSuccessRate"] == 0.0
    assert rollup["productionReady"] is False


def test_observation_gaps_are_calculated_correctly(tmp_path):
    base = 1_700_000_000.0
    observations = [
        {
            "source": "live",
            "runId": "g",
            "completedAt": base,
            "scanner": {"status": "ok"},
            "algod": {"status": "ok", "latestRound": 1},
            "indexer": {"status": "ok", "latestRound": 1, "roundLag": 0},
            "tinyman": {"status": "ok"},
            "pact": {"status": "ok"},
            "poolsObserved": 1,
            "quotesObserved": 1,
            "quoteFreshness": {"fresh": 1, "aging": 0, "stale": 0, "unavailable": 0},
            "routes": {"routeCandidateCount": 0, "approvedRouteCount": 0, "rejectedRouteCount": 0, "rejectionReasons": []},
            "paper": {"candidateCount": 1, "recheckCompleted5s": 1, "recheckCompleted30s": 1},
        },
        {
            "source": "live",
            "runId": "g",
            "completedAt": base + 60,
            "scanner": {"status": "ok"},
            "algod": {"status": "ok", "latestRound": 2},
            "indexer": {"status": "ok", "latestRound": 2, "roundLag": 0},
            "tinyman": {"status": "ok"},
            "pact": {"status": "ok"},
            "poolsObserved": 1,
            "quotesObserved": 1,
            "quoteFreshness": {"fresh": 1, "aging": 0, "stale": 0, "unavailable": 0},
            "routes": {"routeCandidateCount": 0, "approvedRouteCount": 0, "rejectedRouteCount": 0, "rejectionReasons": []},
            "paper": {"candidateCount": 1, "recheckCompleted5s": 1, "recheckCompleted30s": 1},
        },
        {
            "source": "live",
            "runId": "g",
            "completedAt": base + 60 + 600,
            "scanner": {"status": "ok"},
            "algod": {"status": "ok", "latestRound": 3},
            "indexer": {"status": "ok", "latestRound": 3, "roundLag": 0},
            "tinyman": {"status": "ok"},
            "pact": {"status": "ok"},
            "poolsObserved": 1,
            "quotesObserved": 1,
            "quoteFreshness": {"fresh": 1, "aging": 0, "stale": 0, "unavailable": 0},
            "routes": {"routeCandidateCount": 0, "approvedRouteCount": 0, "rejectedRouteCount": 0, "rejectionReasons": []},
            "paper": {"candidateCount": 1, "recheckCompleted5s": 1, "recheckCompleted30s": 1},
        },
    ]
    rollup = build_soak_rollup(observations, interval_seconds=60)
    assert rollup["longestGapSeconds"] == 600
    assert "observation_gap_exceeds_3x_interval" in rollup["warnings"]


def test_stored_observation_never_contains_wallet_signing_or_submission_fields(tmp_path):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    observation = run_once(settings=settings, store=store, run_id="run_safe", deps=_live_deps())
    stored = store.list_testnet_soak_observations(limit=1)[0]
    safe = public_safe_observation(observation)

    for payload in (observation, stored, safe):
        hits = contains_forbidden_evidence(payload)
        assert not hits, f"forbidden tokens present: {hits}"
        serialized = json.dumps(payload).lower()
        for token in (
            "mnemonic",
            "private_key",
            "seed_phrase",
            "hot_wallet",
            "signed_txn",
            "submission_payload",
            "execution_queue",
            "raw_route_json",
        ):
            assert token not in serialized
        assert payload.get("productionReady") is False
        assert payload.get("liveExecutionLocked") is True


def test_public_safe_api_output_contains_no_dangerous_fields(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    observation = run_once(settings=settings, store=store, run_id="run_api", deps=_live_deps())
    monkeypatch.setattr(api_module, "store", store)
    monkeypatch.setattr(api_module, "settings", settings)

    admin = {
        "X-Algopulse-Role": "admin",
        "X-Algopulse-Wallet": LOCAL_REVIEW_ADMIN_WALLET,
    }
    client = TestClient(app)
    summary = client.get("/api/ops/testnet-soak", headers=admin)
    recent = client.get("/api/ops/testnet-soak/observations?limit=10", headers=admin)
    assert summary.status_code == 200
    assert recent.status_code == 200
    summary_payload = summary.json()
    recent_payload = recent.json()
    assert summary_payload["ok"] is True
    assert recent_payload["ok"] is True
    assert summary_payload["data"]["productionReady"] is False
    assert recent_payload["data"]["productionReady"] is False
    assert recent_payload["data"]["count"] >= 1
    assert recent_payload["data"]["observations"][0]["observationId"] == observation["observationId"]

    for payload in (summary_payload, recent_payload, public_safe_observation(observation)):
        hits = contains_forbidden_evidence(payload)
        assert not hits, f"forbidden tokens present: {hits}"


def test_non_admin_cannot_access_ops_endpoints(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)
    monkeypatch.setattr(api_module, "store", store)
    monkeypatch.setattr(api_module, "settings", settings)
    client = TestClient(app)
    guest = client.get("/api/ops/testnet-soak")
    user = client.get(
        "/api/ops/testnet-soak/observations",
        headers={"X-Algopulse-Role": "user", "X-Algopulse-Wallet": "USERWALLET123"},
    )
    assert guest.status_code == 403
    assert user.status_code == 403


def test_ui_source_labels_cannot_display_mock_as_production_ready():
    app_js = Path("src/algopulse/static/app.js").read_text(encoding="utf-8")
    assert "function TestnetSoakPanel" in app_js
    assert 'source === "mock" ? "mock" : source' in app_js
    assert "productionReady=false" in app_js
    assert "Live execution" in app_js
    assert "Locked" in app_js
    assert 'fetchApiData("/api/ops/testnet-soak"' in app_js


def test_production_ready_remains_false_even_with_full_looking_rollup(tmp_path):
    base = 1_700_000_000.0
    observations = []
    for index in range(3):
        observations.append(
            {
                "source": "live",
                "runId": "full",
                "completedAt": base + index * 60,
                "scanner": {"status": "ok"},
                "algod": {"status": "ok", "latestRound": 100 + index},
                "indexer": {"status": "ok", "latestRound": 100 + index, "roundLag": 0},
                "tinyman": {"status": "ok"},
                "pact": {"status": "ok"},
                "poolsObserved": 2,
                "quotesObserved": 4,
                "quoteFreshness": {"fresh": 4, "aging": 0, "stale": 0, "unavailable": 0},
                "routes": {
                    "routeCandidateCount": 2,
                    "approvedRouteCount": 0,
                    "rejectedRouteCount": 2,
                    "rejectionReasons": [{"reason": "profit_too_low", "count": 2}],
                },
                "paper": {"candidateCount": 2, "recheckCompleted5s": 2, "recheckCompleted30s": 2},
            }
        )
    # Stretch first/last to 24h with progressing rounds and paper evidence.
    observations[0]["completedAt"] = base
    observations[-1]["completedAt"] = base + 24 * 3600
    observations[-1]["algod"]["latestRound"] = 10_000
    rollup = build_soak_rollup(observations, interval_seconds=60, now=base + 24 * 3600)
    assert rollup["elapsedCoverageSeconds"] >= 24 * 3600
    assert rollup["productionReady"] is False
    assert rollup["liveExecutionLocked"] is True


def test_summary_builder_reports_empty_state(tmp_path):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)
    summary = build_testnet_soak_summary(store, settings)
    assert summary["completedObservationCount"] == 0
    assert summary["productionReady"] is False
    assert summary["liveExecutionLocked"] is True
    assert summary["gateStatus"] in {"not_started", "in_progress"}
    assert summary["currentGateStatus"] in {"not_started", "in_progress"}
    assert "no_live_observations" in summary["blockers"]


def test_summarize_from_store_uses_persisted_live_observations_after_restart(tmp_path):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    run_once(settings=settings, store=store, run_id="persist", deps=_live_deps(algod_round=1, paper_candidates=1, recheck_5s=1, recheck_30s=1))
    run_once(settings=settings, store=store, run_id="persist", deps=_live_deps(algod_round=2, paper_candidates=1, recheck_5s=1, recheck_30s=1))
    # New store handle on same DB path simulates process restart.
    restarted = MarketStore(settings.database_path)
    rollup = summarize_testnet_soak_readiness(restarted, interval_seconds=60)
    assert rollup["completedObservationCount"] == 2
    assert rollup["firstObservationAt"] is not None
    assert rollup["latestObservationAt"] is not None
    assert rollup["latestObservationAt"] >= rollup["firstObservationAt"]
    assert rollup["productionReady"] is False
    assert "elapsed_coverage_below_24h" in rollup["blockers"]


def test_forbidden_token_list_is_complete_for_acceptance():
    required = {
        "mnemonic",
        "private_key",
        "seed",
        "seed_phrase",
        "hot_wallet",
        "signed_txn",
        "submission_payload",
        "execution_queue",
        "raw_route_json",
        "api_key",
        "secret",
    }
    assert required.issubset(set(FORBIDDEN_EVIDENCE_TOKENS))
