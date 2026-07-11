import json

from fastapi.testclient import TestClient

import algopulse.api as api_module
from algopulse.api import LOCAL_REVIEW_ADMIN_WALLET
from algopulse.api import app
from algopulse.payment_verification import PaymentVerificationResult
from algopulse.store import MarketStore


def _client() -> TestClient:
    return TestClient(app)


def _admin_headers() -> dict[str, str]:
    return {
        "X-Algopulse-Role": "admin",
        "X-Algopulse-Wallet": LOCAL_REVIEW_ADMIN_WALLET,
    }


def _seed_connector_ops_store(tmp_path, monkeypatch, *, stale_algod: bool = False) -> MarketStore:
    store = MarketStore(tmp_path / ("stale-algod.db" if stale_algod else "connectors.db"))
    store.initialize()
    store.record_service_health(
        "connector:tinyman",
        "ok",
        metrics={
            "connector": "tinyman",
            "connectorType": "dex",
            "latencyMs": 90,
            "freshCount24h": 12,
            "staleCount24h": 0,
        },
    )
    store.record_service_health(
        "connector:pact",
        "error",
        detail="timeout",
        metrics={"connector": "pact", "connectorType": "dex", "latencyMs": 850},
    )
    store.record_service_health(
        "connector:algod",
        "ok",
        metrics={
            "connector": "algod",
            "connectorType": "algod",
            "latestRound": 19_900 if stale_algod else 20_100,
            "expectedMinRound": 20_000,
        },
    )
    store.record_service_health(
        "connector:indexer",
        "ok",
        metrics={
            "connector": "indexer",
            "connectorType": "indexer",
            "latestRound": 19_850,
            "expectedMinRound": 20_000,
        },
    )
    store.record_service_health(
        "connector:mock",
        "ok",
        metrics={"connector": "mock", "connectorType": "dex", "freshCount24h": 2},
    )
    monkeypatch.setattr(api_module, "store", store)
    return store


def test_wallet_session_marks_allowlisted_admin_wallet():
    response = _client().get(f"/api/session/wallet/{LOCAL_REVIEW_ADMIN_WALLET}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["role"] == "admin"
    assert payload["data"]["isAdmin"] is True
    assert payload["data"]["authMode"] == "local-review-mock"


def test_public_config_exposes_review_safe_values_only():
    response = _client().get("/api/config/public")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["appName"] == "AlgoPulse Market Engine"
    assert payload["data"]["pnetAsaId"] == 3169177585
    assert "public_scan" in payload["data"]["supportedPaidActions"]
    assert payload["data"]["liveExecutionEnabled"] is False
    capability_codes = {item["code"] for item in payload["data"]["productCapabilities"]}
    assert {
        "market_intelligence",
        "scanner",
        "route_engine",
        "paper_trading",
        "risk_engine",
        "execution_controls",
        "public_dashboard",
        "pnet_access_layer",
    } == capability_codes
    execution_controls = next(
        item for item in payload["data"]["productCapabilities"] if item["code"] == "execution_controls"
    )
    assert execution_controls["status"] == "gated_future"
    assert "never user deposits" in execution_controls["executionBoundary"]
    pnet_access = next(
        item for item in payload["data"]["productCapabilities"] if item["code"] == "pnet_access_layer"
    )
    assert "not a deposit" in pnet_access["executionBoundary"]
    assert len(payload["data"]["phaseGates"]) == 10
    assert payload["data"]["phaseGates"][0]["gate"] == 1
    assert "24 hours" in payload["data"]["phaseGates"][0]["exitCriteria"]
    assert payload["data"]["phaseGates"][7]["title"] == "Manual First Live Trade"
    assert [mode["mode"] for mode in payload["data"]["deploymentModes"]] == [
        "local",
        "staging",
        "production_phase0",
    ]
    local_mode = payload["data"]["deploymentModes"][0]
    staging_mode = payload["data"]["deploymentModes"][1]
    production_mode = payload["data"]["deploymentModes"][2]
    assert {"mock data", "scanner optional", "no signer", "no real submission"}.issubset(local_mode["capabilities"])
    assert {"live scanner", "live quotes", "paper trading", "no live signing"}.issubset(staging_mode["capabilities"])
    assert "isolated signer only after gates" in production_mode["capabilities"]
    assert "tiny own-funds hot wallet only" in production_mode["capabilities"]


def test_admin_endpoint_rejects_guest_and_user_headers():
    client = _client()

    guest = client.post("/api/admin/scan-now")
    user = client.post(
        "/api/admin/scan-now",
        headers={"X-Algopulse-Role": "user", "X-Algopulse-Wallet": "USER7R3VIEWWALLET"},
    )

    assert guest.status_code == 403
    assert guest.json()["error"]["code"] == "NOT_AUTHORIZED"
    assert user.status_code == 403
    assert user.json()["error"]["code"] == "NOT_AUTHORIZED"


def test_admin_preflight_requires_role_and_returns_checklist():
    rejected = _client().get("/api/admin/preflight")
    response = _client().get("/api/admin/preflight", headers=_admin_headers())

    assert rejected.status_code == 403
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["liveArmed"] is False
    assert payload["data"]["checklist"]
    labels = {item["label"] for item in payload["data"]["checklist"]}
    assert {"Admin wallet connected", "Signer locked", "Live execution disabled"}.issubset(labels)


def test_admin_alert_catalog_requires_role_and_lists_phase0_failures():
    rejected = _client().get("/api/admin/alerts/catalog")
    response = _client().get("/api/admin/alerts/catalog", headers=_admin_headers())

    assert rejected.status_code == 403
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["liveExecutionTouched"] is False
    codes = {item["code"] for item in payload["data"]["alerts"]}
    assert {
        "scanner_down",
        "tinyman_connector_failing",
        "pact_connector_failing",
        "quote_age_above_threshold",
        "route_engine_crash",
        "database_unavailable",
        "redis_unavailable",
        "unknown_asset_detected",
        "unknown_app_id_detected",
        "kill_switch_triggered",
        "signer_offline",
        "signer_rejection_spike",
        "hot_wallet_balance_changed",
        "daily_loss_limit_near_breach",
        "live_trade_failed",
        "reconciliation_mismatch",
    } == codes


def test_admin_policy_catalog_requires_role_and_lists_hard_stops():
    rejected = _client().get("/api/admin/policy/catalog")
    response = _client().get("/api/admin/policy/catalog", headers=_admin_headers())

    assert rejected.status_code == 403
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["liveExecutionTouched"] is False
    assert payload["data"]["signerCodeTouched"] is False
    codes = {item["code"] for item in payload["data"]["controls"]}
    assert {
        "max_input_amount",
        "max_transaction_fee",
        "asset_allowlist",
        "app_id_allowlist",
        "transaction_type_allowlist",
        "route_hash_approval",
        "daily_spend_limit",
        "wallet_reserve_minimum",
        "kill_switch",
    } == codes
    kill_switch = next(item for item in payload["data"]["controls"] if item["code"] == "kill_switch")
    assert kill_switch["configuredValue"] == "active"


def test_ops_control_room_endpoints_require_admin_and_report_locked_state():
    client = _client()
    endpoints = [
        "/api/ops/pipeline",
        "/api/ops/phase-gates",
        "/api/ops/activity",
        "/api/ops/rejections",
        "/api/ops/paper-summary",
        "/api/ops/pipeline-evidence",
        "/api/ops/quote-freshness",
        "/api/ops/connectors",
        "/api/ops/risk-gates",
        "/api/ops/environment",
        "/api/ops/production-readiness",
        "/api/ops/readiness-report",
        "/api/ops/replay-lab",
        "/api/ops/route-forensics",
        "/api/ops/market-heatmap",
        "/api/ops/failure-lab",
        "/api/ops/provenance",
        "/api/ops/evidence",
        "/api/ops/confidence-calibration",
        "/api/ops/opportunity-decay",
        "/api/ops/product-validation",
    ]

    for endpoint in endpoints:
        rejected = client.get(endpoint)
        assert rejected.status_code == 403
        assert rejected.json()["error"]["code"] == "NOT_AUTHORIZED"

    pipeline = client.get("/api/ops/pipeline", headers=_admin_headers()).json()
    assert pipeline["ok"] is True
    assert [item["key"] for item in pipeline["data"]["services"]] == [
        "pool_scanner",
        "quote_engine",
        "route_engine",
        "paper_trader",
        "risk_engine",
        "dry_run_builder",
        "signer_gate",
        "live_micro_execution",
        "receipts_reconciliation",
    ]
    assert pipeline["data"]["liveExecutionLocked"] is True
    production_status = pipeline["data"]["productionStatus"]
    assert production_status["headline"] == "NOT LIVE READY"
    assert production_status["safeMode"] == "Phase 3 TestNet: Scanner / Paper / Dry Run only."
    assert "No user deposits." in production_status["restrictions"]
    assert "No guaranteed returns." in production_status["restrictions"]
    readiness = pipeline["data"]["productionReadiness"]
    assert readiness["currentPhase"].startswith("Phase 3")
    assert readiness.get("historicalPhase", "").startswith("Phase 0") or readiness.get("historicalPhaseKey")
    assert readiness["overallPercent"] == round(
        (readiness["passedEvidenceCount"] / readiness["totalEvidenceCount"]) * 100
    )
    assert readiness["nextGate"]
    assert readiness["blockingItems"]
    assert readiness["source"] == "stored"
    assert {item["source"] for item in pipeline["data"]["services"]}.issubset(
        {"mock", "stored", "live", "delayed", "unavailable"}
    )
    service_by_key = {item["key"]: item for item in pipeline["data"]["services"]}
    for service in service_by_key.values():
        assert service["evidence"], service["key"]
        assert {"label", "value", "detail", "source"}.issubset(service["evidence"][0])
    assert service_by_key["pool_scanner"]["evidence"][0]["label"] == "Pools scanned"
    assert service_by_key["quote_engine"]["evidence"][0]["label"] == "Quote count"
    assert service_by_key["route_engine"]["evidence"][0]["label"] == "Candidate count"
    assert service_by_key["paper_trader"]["evidence"][0]["label"] == "Simulated trades"
    assert service_by_key["risk_engine"]["evidence"][0]["label"] == "Rejection reasons"
    assert service_by_key["signer_gate"]["evidence"][0]["value"] == "disabled"
    assert service_by_key["signer_gate"]["evidence"][1]["label"] == "Key exposure"
    assert service_by_key["signer_gate"]["evidence"][1]["value"] == "none"
    risk_service = next(item for item in pipeline["data"]["services"] if item["key"] == "risk_engine")
    assert "motionLabel" in risk_service
    assert risk_service["approvedCount24h"] is not None
    assert risk_service["rejectedCount24h"] is not None

    phase_gates = client.get("/api/ops/phase-gates", headers=_admin_headers()).json()
    assert phase_gates["ok"] is True
    assert phase_gates["data"]["activePhase"]["label"].startswith("Phase 3")
    assert phase_gates["data"]["productionReadiness"]["currentPhase"].startswith("Phase 3")
    phases = phase_gates["data"]["phases"]
    assert [phase["label"] for phase in phases] == [
        "Phase 0A Inventory",
        "Phase 0B Scanner",
        "Phase 0C Route Engine",
        "Phase 0D Paper Trading",
        "Phase 0E Risk Engine",
        "Phase 0F Live Micro",
        "Phase 0G Public Dash",
    ]
    assert all(phase.get("lane") == "historical" for phase in phases)
    for phase in phases:
        total = len(phase["requiredEvidence"])
        passed = len(phase["completedEvidence"])
        assert phase["percent"] == (round((passed / total) * 100) if total else 0)
    assert phase_gates["data"]["productionReadiness"]["overallPercent"] == readiness["overallPercent"]
    assert phase_gates["data"]["gates"]
    for gate in phase_gates["data"]["gates"]:
        total = len(gate["evidence"])
        passed = sum(1 for item in gate["evidence"] if item["status"] == "pass")
        assert gate["percent"] == (round((passed / total) * 100) if total else 0)
        assert gate["evidenceLinks"]

    activity = client.get("/api/ops/activity", headers=_admin_headers()).json()
    assert activity["ok"] is True
    assert {"Quote Engine", "Risk Engine", "Phase Ladder", "TestNet Soak", "Live Micro-Execution"}.issubset(
        {item["service"] for item in activity["data"]["events"]}
    )
    assert all(item.get("source") in {"mock", "stored", "live", "delayed", "unavailable"} for item in activity["data"]["events"])

    risk = client.get("/api/ops/risk-gates", headers=_admin_headers()).json()
    assert risk["ok"] is True
    assert risk["data"]["liveExecutionLocked"] is True
    assert "signer disabled" in risk["data"]["lockReasons"]
    assert risk["data"]["productionStatus"]["status"] == "not_live_ready"
    assert risk["data"]["productionReadiness"]["currentPhase"].startswith("Phase 3")

    production_readiness = client.get("/api/ops/production-readiness", headers=_admin_headers()).json()
    assert production_readiness["ok"] is True
    assert production_readiness["data"]["liveExecutionTouched"] is False
    assert production_readiness["data"]["signerCodeTouched"] is False
    assert production_readiness["data"]["evidence"]
    assert production_readiness["data"]["overallPercent"] == round(
        (production_readiness["data"]["passedEvidenceCount"] / production_readiness["data"]["totalEvidenceCount"]) * 100
    )
    assert {item.get("source") for item in production_readiness["data"]["evidence"]}.issubset(
        {"mock", "stored", "live", "delayed", "unavailable"}
    )

    readiness_report = client.get("/api/ops/readiness-report", headers=_admin_headers()).json()
    assert readiness_report["ok"] is True
    assert readiness_report["data"]["mode"] == "read_only_staging"
    assert readiness_report["data"]["liveExecutionRequired"] is False
    assert readiness_report["data"]["dryRunRequired"] is False
    assert readiness_report["data"]["status"] in {"blocked", "ready_for_staging_review"}
    assert {
        "scanner",
        "quotes",
        "connectors",
        "routes",
        "risk",
        "paper",
        "evidenceSamples",
        "blockers",
        "nextRequiredGate",
    }.issubset(readiness_report["data"])
    assert {
        "uptimeSeconds",
        "poolsMonitored",
        "snapshotCount",
    }.issubset(readiness_report["data"]["scanner"])
    assert {
        "recorded",
        "fresh",
        "stale",
    }.issubset(readiness_report["data"]["quotes"])
    assert {
        "scannerUptime",
        "quoteFreshness",
        "connectorState",
        "routeDecisions",
        "riskDecisions",
        "paperTradeSurvival",
        "liveExecutionTouched",
        "signerCodeTouched",
    }.issubset(readiness_report["data"]["evidenceSamples"])
    assert readiness_report["data"]["evidenceSamples"]["liveExecutionTouched"] is False
    assert readiness_report["data"]["evidenceSamples"]["signerCodeTouched"] is False

    paper = client.get("/api/ops/paper-summary", headers=_admin_headers()).json()
    assert paper["ok"] is True
    assert paper["data"]["source"] in {"stored", "unavailable"}
    assert paper["data"]["evidence"]["source"] in {"stored", "unavailable"}
    assert {
        "candidateCount",
        "checked5sCount",
        "checked30sCount",
        "survivalRate30s",
        "averageQuoteDecay30s",
        "recentEvidence",
    }.issubset(paper["data"]["evidence"])
    if paper["data"]["evidence"]["recentEvidence"]:
        sample = paper["data"]["evidence"]["recentEvidence"][0]
        assert {
            "detectedAt",
            "routeHash",
            "inputAmount",
            "expectedOutput",
            "expectedProfit",
            "t5SimulatedOutput",
            "t30SimulatedOutput",
            "quoteDecay30s",
            "wouldExecute",
            "skipOrFailureReason",
        }.issubset(sample)

    pipeline_evidence = client.get("/api/ops/pipeline-evidence", headers=_admin_headers()).json()
    assert pipeline_evidence["ok"] is True
    assert pipeline_evidence["data"]["source"] in {"stored", "unavailable"}
    assert pipeline_evidence["data"]["liveExecutionTouched"] is False
    assert pipeline_evidence["data"]["signerCodeTouched"] is False
    assert {
        "scanner",
        "quotes",
        "quoteFreshness",
        "connectorReliability",
        "routes",
        "risk",
        "paper",
        "proof",
    }.issubset(pipeline_evidence["data"])
    assert {
        "scannerToQuotes",
            "quoteFreshness",
            "connectorReliability",
            "routeReadiness",
            "quotesToRoutes",
            "routesToRisk",
            "riskToPaper",
        "paperRechecks",
        "endToEnd",
    } == set(pipeline_evidence["data"]["proof"])
    assert {
        "quoteCount",
        "freshCount",
        "freshQuoteCount",
        "agingQuoteCount",
        "staleCount",
        "staleQuoteCount",
        "readinessEligibleQuoteCount",
        "readinessExcludedQuoteCount",
        "rejectedQuoteCount",
        "rejectedReasons",
        "venuesRepresented",
        "pairsRepresented",
        "freshnessStatus",
    }.issubset(pipeline_evidence["data"]["quoteFreshness"])
    assert {"connectors", "venueCoverage", "healthyConnectorCount"}.issubset(
        pipeline_evidence["data"]["connectorReliability"]
    )
    assert pipeline_evidence["data"]["adminSession"]["authMode"] == "local-review-mock"

    quote_freshness = client.get("/api/ops/quote-freshness", headers=_admin_headers()).json()
    assert quote_freshness["ok"] is True
    assert quote_freshness["data"]["source"] in {"stored", "unavailable"}
    assert {
        "quoteCount",
        "freshCount",
        "agingCount",
        "staleCount",
        "unavailableCount",
        "readinessEligibleQuoteCount",
        "readinessExcludedQuoteCount",
        "freshnessStatus",
        "quotes",
    }.issubset(quote_freshness["data"])
    if quote_freshness["data"]["quotes"]:
        quote = quote_freshness["data"]["quotes"][0]
        assert {
            "venue",
            "pair",
            "poolId",
            "inputAssetId",
            "outputAssetId",
            "inputAmount",
            "expectedOutput",
            "capturedAt",
            "expiresAt",
            "blockRound",
            "quoteAgeSeconds",
            "freshnessStatus",
            "readinessEligible",
            "rejectionReason",
            "source",
        }.issubset(quote)
        assert quote["freshnessStatus"] in {"fresh", "aging", "stale", "unavailable"}

    connectors = client.get("/api/ops/connectors", headers=_admin_headers()).json()
    assert connectors["ok"] is True
    assert connectors["data"]["source"] in {"stored", "unavailable"}
    assert {"status", "connectors", "venues", "blocksReadiness"}.issubset(connectors["data"])
    assert connectors["data"]["status"] in {"ok", "degraded", "down", "mock", "unavailable"}
    if connectors["data"]["venues"]:
        venue = connectors["data"]["venues"][0]
        assert {
            "venueName",
            "lastSuccessAt",
            "lastFailureAt",
            "latencyMs",
            "staleQuoteCount24h",
            "freshQuoteCount24h",
            "errorCount24h",
            "status",
        }.issubset(venue)
        assert venue["status"] in {"ok", "degraded", "down", "mock"}

    replay = client.get("/api/ops/replay-lab", headers=_admin_headers()).json()
    assert replay["ok"] is True
    assert replay["data"]["liveExecutionTouched"] is False
    assert replay["data"]["signerCodeTouched"] is False
    assert replay["data"]["source"] in {"stored", "unavailable"}
    if replay["data"]["replays"]:
        sample = replay["data"]["replays"][0]
        assert [item["label"] for item in sample["timeline"]] == [
            "T0 detected",
            "T+5s recheck",
            "T+30s recheck",
        ]
        assert sample["verdict"] in {"would_execute", "would_skip", "unsafe", "stale"}
        assert {"expectedProfit", "simulatedProfit30s", "quoteDecay30s", "routeConfidence"}.issubset(sample)

    forensics = client.get("/api/ops/route-forensics", headers=_admin_headers()).json()
    assert forensics["ok"] is True
    assert forensics["data"]["liveExecutionTouched"] is False
    assert forensics["data"]["signerCodeTouched"] is False
    assert forensics["data"]["source"] in {"stored", "unavailable"}
    assert {"routeCount", "completeCount", "approvedCount", "rejectedCount", "rejectionReasons"}.issubset(
        forensics["data"]["summary"]
    )
    if forensics["data"]["routes"]:
        route = forensics["data"]["routes"][0]
        assert {
            "routeHash",
            "routePath",
            "profitability",
            "quoteFreshness",
            "priceImpact",
            "liquidityScore",
            "riskResult",
            "approvalDecision",
            "rejectionReason",
            "confidenceCalculation",
            "decisionTree",
            "completeness",
            "pair",
            "path",
            "venues",
            "inputAmount",
            "expectedOutput",
            "grossProfit",
            "fees",
            "safetyBuffer",
            "netExpectedProfit",
            "connectorReadiness",
            "riskDecision",
            "paperDecision",
            "finalDecision",
            "finalReasons",
        }.issubset(route)
        assert route["completeness"]["complete"] is True
        assert route["finalDecision"] in {"approved", "rejected", "wait", "paper_only"}
        assert route["finalReasons"]
        assert route["connectorReadiness"]["status"] in {"ok", "wait", "blocked", "unavailable"}
        assert route["riskDecision"]["status"] in {"approved", "rejected"}

    heatmap = client.get("/api/ops/market-heatmap?view=24h", headers=_admin_headers()).json()
    assert heatmap["ok"] is True
    assert heatmap["data"]["liveExecutionTouched"] is False
    assert heatmap["data"]["signerCodeTouched"] is False
    assert heatmap["data"]["view"] == "24h"
    assert heatmap["data"]["views"] == ["1h", "6h", "24h", "7d"]
    assert {"opportunityCount", "activeCells", "pairCount", "venueCount", "paperTradeCount"}.issubset(
        heatmap["data"]["totals"]
    )
    assert heatmap["data"]["source"] in {"stored", "unavailable"}
    if heatmap["data"]["cells"]:
        cell = heatmap["data"]["cells"][0]
        assert {
            "pairLabel",
            "venue",
            "bucketStart",
            "spreadFrequency",
            "averageSpreadBps",
            "averageRouteCount",
            "opportunityHalfLifeSeconds",
            "paperTradePerformance",
            "intensity",
            "densityLabel",
        }.issubset(cell)

    failure_lab = client.get("/api/ops/failure-lab", headers=_admin_headers()).json()
    assert failure_lab["ok"] is True
    assert failure_lab["data"]["source"] == "mock"
    assert failure_lab["data"]["mode"] == "simulation"
    assert failure_lab["data"]["liveExecutionTouched"] is False
    assert failure_lab["data"]["signerCodeTouched"] is False
    assert failure_lab["data"]["summary"]["scenarioCount"] == 9
    assert failure_lab["data"]["summary"]["gracefulPercent"] == 100
    scenario_keys = {item["key"] for item in failure_lab["data"]["scenarios"]}
    assert {
        "tinyman_offline",
        "pact_offline",
        "stale_quotes",
        "database_unavailable",
        "route_engine_crash",
        "signer_unavailable",
        "unknown_asset",
        "unknown_app_id",
        "daily_loss_breach",
    } == scenario_keys
    signer_failure = next(item for item in failure_lab["data"]["scenarios"] if item["key"] == "signer_unavailable")
    assert signer_failure["actualResponse"]["status"] == "locked"
    assert "signer_offline" in signer_failure["alertsGenerated"]
    assert signer_failure["gracefulDegradation"] is True

    provenance = client.get("/api/ops/provenance?metric=route.expected_net_profit", headers=_admin_headers()).json()
    assert provenance["ok"] is True
    assert provenance["data"]["selectedMetric"]["key"] == "route.expected_net_profit"
    assert provenance["data"]["liveExecutionTouched"] is False
    assert provenance["data"]["signerCodeTouched"] is False
    assert [step["key"] for step in provenance["data"]["lineage"]] == [
        "metric",
        "source_data",
        "quote",
        "pool_snapshot",
        "route_calculation",
        "risk_decision",
    ]
    assert {metric["key"] for metric in provenance["data"]["metrics"]} >= {
        "scanner.pool_count",
        "quote.count",
        "route.count",
        "route.expected_net_profit",
        "risk.decision_count",
    }
    assert provenance["data"]["source"] in {"stored", "unavailable"}

    evidence = client.get("/api/ops/evidence?category=routes", headers=_admin_headers()).json()
    assert evidence["ok"] is True
    assert evidence["data"]["liveExecutionTouched"] is False
    assert evidence["data"]["signerCodeTouched"] is False
    assert evidence["data"]["filters"]["category"] == "routes"
    assert evidence["data"]["records"]
    assert {item["category"] for item in evidence["data"]["records"]} == {"routes"}
    assert {"scanner", "quotes", "routes", "paper_trading", "risk", "dry_run", "execution", "receipts"}.issubset(
        set(evidence["data"]["summary"]["categories"])
    )

    confidence = client.get("/api/ops/confidence-calibration", headers=_admin_headers()).json()
    assert confidence["ok"] is True
    assert confidence["data"]["liveExecutionTouched"] is False
    assert confidence["data"]["signerCodeTouched"] is False
    assert [bucket["label"] for bucket in confidence["data"]["buckets"]] == [
        "0.90-1.00",
        "0.80-0.89",
        "0.70-0.79",
        "0.60-0.69",
        "0.50-0.59",
        "0.00-0.49",
    ]
    assert {"paperTradeCount", "resolvedCount", "overallSuccessRate", "calibrationError", "verdict"}.issubset(
        confidence["data"]["summary"]
    )

    decay = client.get("/api/ops/opportunity-decay?view=24h", headers=_admin_headers()).json()
    assert decay["ok"] is True
    assert decay["data"]["liveExecutionTouched"] is False
    assert decay["data"]["signerCodeTouched"] is False
    assert decay["data"]["view"] == "24h"
    assert decay["data"]["views"] == ["1h", "24h", "7d"]
    assert {
        "opportunityCount",
        "totalOpportunities",
        "survivedT5Count",
        "survivedT30Count",
        "fadedCount",
        "averageDecayT5",
        "averageDecayT30",
        "bestPairBySurvival",
        "worstPairBySurvival",
        "mostCommonFadeReason",
        "averageHalfLifeSeconds",
        "medianHalfLifeSeconds",
        "fastestDecay",
        "slowestDecay",
        "resolved60sCount",
    }.issubset(decay["data"]["summary"])
    assert decay["data"]["source"] in {"stored", "unavailable"}
    if decay["data"]["records"]:
        record = decay["data"]["records"][0]
        assert {
            "detectedAt",
            "pair",
            "venues",
            "expectedProfitAtT0",
            "simulatedProfitAtT5",
            "simulatedProfitAtT30",
            "simulatedProfitAtT60",
            "quoteDecayT5",
            "quoteDecayT30",
            "quoteDecayT60",
            "survivedT5",
            "survivedT30",
            "survivedT60",
            "finalOutcome",
            "reason",
        }.issubset(record)
        assert record["finalOutcome"] in {"survived", "faded", "rejected", "unknown"}
        assert record["reason"]

    validation = client.get("/api/ops/product-validation", headers=_admin_headers()).json()
    assert validation["ok"] is True
    assert validation["data"]["liveExecutionTouched"] is False
    assert validation["data"]["signerCodeTouched"] is False
    assert {"totalActions", "activeUsers", "repeatUsers", "decisionCount", "topPhase1Recommendation"}.issubset(
        validation["data"]["summary"]
    )
    assert [item["label"] for item in validation["data"]["funnel"]] == [
        "Guest",
        "Connected User",
        "PNET User",
        "Report User",
        "Repeat User",
    ]
    assert {item["persona"] for item in validation["data"]["personas"]} == {
        "Trader",
        "Builder",
        "Project Founder",
        "Liquidity Provider",
        "Researcher",
    }
    assert "page_load" in validation["data"]["decisionRules"]["excludedExamples"]
    assert validation["data"]["source"] in {"stored", "unavailable"}


def test_ops_connectors_api_exposes_degradation_contract_and_rollup(tmp_path, monkeypatch):
    _seed_connector_ops_store(tmp_path, monkeypatch)

    response = _client().get("/api/ops/connectors", headers=_admin_headers())
    payload = response.json()
    data = payload["data"]
    by_connector = {item["connectorName"]: item for item in data["connectors"]}
    required_fields = {
        "connectorName",
        "connectorType",
        "status",
        "readinessImpact",
        "degradationReason",
        "productionReady",
        "freshCount24h",
        "staleCount24h",
        "errorCount24h",
        "latestRound",
        "expectedMinRound",
    }

    assert response.status_code == 200
    assert payload["ok"] is True
    assert data["source"] == "stored"
    assert all(required_fields.issubset(item) for item in data["connectors"])
    assert all(item["degradationReason"] for item in data["connectors"] if item["status"] != "ok")

    tinyman = by_connector["tinyman"]
    assert tinyman["connectorType"] == "dex"
    assert tinyman["status"] == "ok"
    assert tinyman["readinessImpact"] == "ok"
    assert tinyman["productionReady"] is True
    assert tinyman["freshCount24h"] == 12

    pact = by_connector["pact"]
    assert pact["status"] == "down"
    assert pact["readinessImpact"] == "blocked"
    assert pact["productionReady"] is False
    assert pact["degradationReason"] == "timeout"
    assert pact["errorCount24h"] == 1

    indexer = by_connector["indexer"]
    assert indexer["connectorType"] == "indexer"
    assert indexer["status"] == "degraded"
    assert indexer["readinessImpact"] == "wait"
    assert indexer["degradationReason"] == "indexer_round_stale"
    assert indexer["latestRound"] == 19_850
    assert indexer["expectedMinRound"] == 20_000

    algod = by_connector["algod"]
    assert algod["connectorType"] == "algod"
    assert algod["status"] == "ok"
    assert algod["readinessImpact"] == "ok"
    assert algod["latestRound"] == 20_100
    assert algod["expectedMinRound"] == 20_000

    mock = by_connector["mock"]
    assert mock["status"] == "mock"
    assert mock["readinessImpact"] == "wait"
    assert mock["productionReady"] is False
    assert mock["degradationReason"] == "mock_connector_not_production_ready"

    assert data["readinessRollup"] == {
        "totalConnectors": 5,
        "okCount": 2,
        "degradedCount": 1,
        "downCount": 1,
        "staleCount": 0,
        "mockCount": 1,
        "productionReadyCount": 2,
        "blockedReasons": [{"connectorName": "pact", "status": "down", "reason": "timeout"}],
        "waitReasons": [
            {"connectorName": "indexer", "status": "degraded", "reason": "indexer_round_stale"},
            {"connectorName": "mock", "status": "mock", "reason": "mock_connector_not_production_ready"},
        ],
        "overallReadiness": "blocked",
    }
    assert data["blocksReadiness"] is True

    evidence_only = {key: value for key, value in data.items() if key != "adminSession"}
    serialized = json.dumps(evidence_only).lower()
    forbidden_artifacts = (
        "mnemonic",
        "private_key",
        "seed_phrase",
        "hot_wallet",
        "signed_txn",
        "submission_payload",
        "execution_queue",
        "submit_transaction",
    )
    assert all(fragment not in serialized for fragment in forbidden_artifacts)


def test_ops_connectors_api_rollup_blocks_stale_algod(tmp_path, monkeypatch):
    _seed_connector_ops_store(tmp_path, monkeypatch, stale_algod=True)

    response = _client().get("/api/ops/connectors", headers=_admin_headers())
    data = response.json()["data"]
    by_connector = {item["connectorName"]: item for item in data["connectors"]}
    rollup = data["readinessRollup"]

    assert response.status_code == 200
    assert by_connector["algod"]["status"] == "stale"
    assert by_connector["algod"]["readinessImpact"] == "blocked"
    assert by_connector["algod"]["degradationReason"] == "algod_round_stale"
    assert by_connector["indexer"]["status"] == "degraded"
    assert by_connector["indexer"]["readinessImpact"] == "wait"
    assert rollup["overallReadiness"] == "blocked"
    assert rollup["staleCount"] == 1
    assert {"connectorName": "algod", "status": "stale", "reason": "algod_round_stale"} in rollup[
        "blockedReasons"
    ]
    assert data["blocksReadiness"] is True


def test_admin_scan_now_returns_safe_queued_job_only():
    response = _client().post("/api/admin/scan-now", headers=_admin_headers())

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["status"] == "queued"
    assert payload["data"]["action"] == "scan_now"
    assert payload["data"]["liveExecutionTouched"] is False


def test_live_arm_stays_blocked_when_execution_disabled():
    response = _client().post("/api/admin/live/arm", headers=_admin_headers())

    assert response.status_code == 403
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "LIVE_EXECUTION_DISABLED"
    assert payload["data"] is None


def test_pnet_fee_quote_is_market_data_only_shape():
    response = _client().post(
        "/api/user/pnet/fee-quote",
        json={"wallet": "USER7R3VIEWWALLET", "action": "pair_scan", "pair": "ALGO/USDC"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["action"] == "pair_scan"
    assert payload["data"]["feeAmount"] == "12.000000"
    assert payload["data"]["paymentIntent"]["transactionType"] == "asset_transfer"
    assert payload["data"]["paymentIntent"]["signer"] == "user_connected_wallet"
    assert payload["data"]["paymentIntent"]["submitter"] == "frontend_user_wallet"
    assert payload["data"]["paymentIntent"]["amountAtomic"] == "12000000"
    assert payload["data"]["accessCheck"]["ok"] is True
    assert payload["data"]["pnetAsaId"] == 3169177585
    assert "does not guarantee profit" in payload["data"]["disclaimer"]
    assert "grant control over platform execution" in payload["data"]["disclaimer"]


def test_product_validation_event_endpoint_records_only_taxonomy_actions():
    client = _client()
    unknown = client.post(
        "/api/events/user-action",
        json={
            "action_type": "page_load",
            "user_role": "guest",
            "wallet_connected": False,
            "source_page": "pulse",
            "metadata": {"session_id": "api-test-guest"},
        },
    )
    assert unknown.status_code == 422
    assert unknown.json()["error"]["code"] == "UNKNOWN_PRODUCT_ACTION"

    passive = client.post(
        "/api/events/user-action",
        json={
            "action_type": "viewed_market_pulse",
            "user_role": "guest",
            "wallet_connected": False,
            "source_page": "pulse",
            "metadata": {"session_id": "api-test-guest"},
        },
    )
    decision = client.post(
        "/api/events/user-action",
        json={
            "action_type": "opened_route",
            "user_role": "user",
            "wallet_connected": True,
            "source_page": "routes",
            "metadata": {"session_id": "api-test-user", "pnet_user": True, "evidence_source": "route_details"},
        },
    )

    assert passive.status_code == 200
    assert passive.json()["data"]["decisionRecorded"] is False
    assert decision.status_code == 200
    assert decision.json()["data"]["decisionRecorded"] is True
    assert decision.json()["data"]["liveExecutionTouched"] is False


def test_pnet_access_check_blocks_wrong_network_before_quote():
    response = _client().post(
        "/api/user/pnet/fee-quote",
        json={
            "wallet": "USER7R3VIEWWALLET",
            "network": "testnet",
            "action": "pair_scan",
            "pair": "ALGO/USDC",
        },
    )

    assert response.status_code == 402
    payload = response.json()
    assert payload["error"]["code"] == "PNET_ACCESS_CHECK_FAILED"
    network_check = next(item for item in payload["error"]["details"]["checks"] if item["label"] == "Correct network")
    assert network_check["ok"] is False


def test_pnet_fee_confirm_is_stubbed_and_does_not_touch_execution():
    response = _client().post(
        "/api/user/pnet/fee-confirm",
        json={
            "wallet": "USER7R3VIEWWALLET",
            "fee_quote_id": "fq_review",
            "txid": "mock-tx-review",
            "action": "pair_scan",
            "pair": "ALGO/USDC",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["status"] == "mock_confirmed"
    assert payload["data"]["paymentVerification"]["status"] == "mock_confirmed"
    assert payload["data"]["creditsGranted"] == 1
    assert payload["data"]["liveExecutionTouched"] is False


def test_pnet_fee_confirm_uses_on_chain_verifier_for_real_txid(monkeypatch):
    class FakeVerifier:
        def verify(self, request):
            return PaymentVerificationResult(
                ok=True,
                status="verified",
                reason=None,
                txid=request.txid,
                asset_id=request.asset_id,
                expected={
                    "receiver": request.expected_receiver,
                    "sender": request.expected_sender,
                    "amount_raw": request.expected_amount_raw,
                    "amount_display": request.expected_amount,
                    "asset_id": request.asset_id,
                    "asset_decimals": request.asset_decimals,
                    "note_prefix": request.note_prefix,
                },
                observed={
                    "sender": request.expected_sender,
                    "receiver": request.expected_receiver,
                    "amount_raw": request.expected_amount_raw,
                    "amount_display": request.expected_amount,
                    "asset_id": request.asset_id,
                    "confirmed_round": 10,
                    "confirmations": 1,
                },
                checks={"confirmed": True},
            )

    monkeypatch.setattr(api_module, "payment_verifier", FakeVerifier())
    response = _client().post(
        "/api/user/pnet/fee-confirm",
        json={
            "wallet": "USER7R3VIEWWALLET",
            "fee_quote_id": "fq_review",
            "txid": "REALTXIDFORREVIEW",
            "action": "pair_scan",
            "pair": "ALGO/USDC",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["status"] == "verified"
    assert payload["data"]["verificationMode"] == "on-chain-indexer"
    assert payload["data"]["paymentVerification"]["expected"]["note_prefix"] == "pnet_fee:fq_review:pair_scan:"
    assert payload["data"]["liveExecutionTouched"] is False


def test_paper_daily_report_endpoint_returns_aggregate_shape():
    response = _client().get("/api/reports/paper/daily")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert {
        "candidates",
        "wouldExecute",
        "checked30s",
        "completionRate30s",
        "skipReasons",
    }.issubset(payload["data"])


def test_market_daily_report_endpoints_return_json_markdown_and_archive():
    client = _client()

    response = client.get("/api/reports/market/daily")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["publicSafe"] is True
    assert payload["data"]["liveExecutionTouched"] is False
    assert payload["data"]["signerCodeTouched"] is False
    assert payload["data"]["reportTier"] == "public-preview"
    assert payload["data"]["preview"] is True
    assert payload["data"]["paymentUpgradeAvailable"] is True
    assert {
        "marketSummary",
        "topPairs",
        "opportunityCounts",
        "scannerHealth",
    }.issubset(payload["data"])
    assert "topSpreads" not in payload["data"]
    assert "routePerformance" not in payload["data"]
    assert {"topSpreads", "routePerformance"}.issubset(payload["data"]["excludedDetailSections"])
    report_date = payload["data"]["reportDate"]

    archive = client.get("/api/reports/market/archive")
    assert archive.status_code == 200
    archive_payload = archive.json()
    assert archive_payload["ok"] is True
    assert archive_payload["data"]["liveExecutionTouched"] is False
    assert archive_payload["data"]["signerCodeTouched"] is False
    assert archive_payload["data"]["reports"]
    assert archive_payload["data"]["reports"][0]["summary"]["headline"]

    json_export = client.get(f"/api/reports/market/daily/export?date={report_date}&format=json")
    assert json_export.status_code == 200
    assert json_export.json()["reportDate"] == report_date
    assert json_export.json()["liveExecutionTouched"] is False

    markdown_export = client.get(f"/api/reports/market/daily/export?date={report_date}&format=markdown")
    assert markdown_export.status_code == 200
    assert markdown_export.headers["content-type"].startswith("text/markdown")
    assert "## Market Summary" in markdown_export.text
    assert "Live execution touched: false" in markdown_export.text
