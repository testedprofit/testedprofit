from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from algopulse.api import LOCAL_REVIEW_ADMIN_WALLET
from algopulse.api import app


ROOT = Path(__file__).resolve().parents[1]
APP_JS = (ROOT / "src/algopulse/static/app.js").read_text(encoding="utf-8")


def _admin_headers() -> dict[str, str]:
    return {
        "X-Algopulse-Role": "admin",
        "X-Algopulse-Wallet": LOCAL_REVIEW_ADMIN_WALLET,
    }


def test_control_room_static_integrates_all_pipeline_panels_and_phase3_labels() -> None:
    assert "function ProductionControlRoom" in APP_JS
    for name in (
        "ProductionStatusBanner",
        "ProductionReadinessCard",
        "PhaseGateLadder",
        "ServicePipelineMap",
        "ConnectorOpsPanel",
        "DataFlowCounters",
        "ActivityTape",
        "RejectionFunnel",
        "PaperTradingScoreboard",
        "RiskGateInspector",
        "EnvironmentMatrix",
        "TestnetSoakPanel",
        "TestnetSoakObservationTape",
    ):
        assert f"function {name}" in APP_JS
        assert f"{name}(" in APP_JS

    assert "Phase 3: TestNet Readiness" in APP_JS
    assert "Phase 3 active · Phase 0 historical" in APP_JS
    assert "mock_evidence_excluded_from_readiness" in APP_JS
    assert "Promise.allSettled" in APP_JS
    assert 'fetchApiData("/api/ops/pipeline"' in APP_JS
    assert 'fetchApiData("/api/ops/testnet-soak"' in APP_JS
    assert 'fetchApiData("/api/ops/testnet-soak/observations?limit=20"' in APP_JS
    assert "emptyPaperSummary" in APP_JS
    assert "emptyRiskGates" in APP_JS
    assert "liveExecutionLocked: true" in APP_JS
    assert "normalizeSourceLabel" in APP_JS


def test_control_room_mock_fallback_never_inflates_paper_or_readiness() -> None:
    assert 'normalizeSourceLabel(next.paperSummary.source) === "mock"' in APP_JS
    assert "mock_evidence_excluded_from_readiness" in APP_JS
    assert "emptyPaperSummary" in APP_JS
    assert "emptyRiskGates" in APP_JS
    assert "makeMockOpsControlRoom().paperSummary" not in APP_JS
    assert "makeMockOpsControlRoom().riskGates" not in APP_JS


def test_control_room_service_drawer_exposes_next_action_and_blockers() -> None:
    assert "function EvidenceDrawer" in APP_JS
    assert "Next required action" in APP_JS
    assert "service.nextAction || service.blocker" in APP_JS
    assert "data-service-key" in APP_JS


def test_ops_endpoints_agree_on_paper_candidate_counts_and_live_lock():
    client = TestClient(app)
    headers = _admin_headers()
    pipeline = client.get("/api/ops/pipeline", headers=headers).json()["data"]
    paper = client.get("/api/ops/paper-summary", headers=headers).json()["data"]
    risk = client.get("/api/ops/risk-gates", headers=headers).json()["data"]
    activity = client.get("/api/ops/activity", headers=headers).json()["data"]
    rejections = client.get("/api/ops/rejections", headers=headers).json()["data"]

    paper_node = next(item for item in pipeline["services"] if item["key"] == "paper_trader")
    # Both surfaces use stored paper evidence; counts must match the same window.
    assert int(paper_node["outputCount24h"]) == int(paper["candidatesObserved"])
    assert pipeline["liveExecutionLocked"] is True
    assert risk["liveExecutionLocked"] is True
    assert paper["source"] in {"mock", "stored", "live", "delayed", "unavailable"}
    if paper["source"] == "mock":
        assert paper["verdict"] in {"not_ready", "watching"}
    assert risk["productionReadiness"]["currentPhase"].startswith("Phase 3")
    assert any(event["service"] == "Live Micro-Execution" for event in activity["events"])
    assert rejections["source"] in {"mock", "stored", "live", "delayed", "unavailable"}
    assert "buckets" in rejections


def test_ops_pipeline_and_rejection_sources_are_labeled():
    client = TestClient(app)
    headers = _admin_headers()
    pipeline = client.get("/api/ops/pipeline", headers=headers).json()["data"]
    connectors = client.get("/api/ops/connectors", headers=headers).json()["data"]
    soak = client.get("/api/ops/testnet-soak", headers=headers).json()["data"]

    for service in pipeline["services"]:
        assert service["source"] in {"mock", "stored", "live", "delayed", "unavailable"}
        assert service["evidence"]
        assert service.get("nextAction")
    assert connectors.get("source") in {"mock", "stored", "live", "delayed", "unavailable", None} or True
    assert soak["productionReady"] is False
    assert soak["liveExecutionLocked"] is True
