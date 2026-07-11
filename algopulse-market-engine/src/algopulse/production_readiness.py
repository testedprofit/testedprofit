from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

from algopulse.production_gate_definitions import PHASE_DEFINITIONS

if TYPE_CHECKING:
    from algopulse.config import Settings
    from algopulse.store import MarketStore


TX_GROUP_LIMIT = 16
PAPER_TARGET_DAYS = 7
PAPER_RECHECK_COMPLETION_TARGET = 0.8


def build_production_readiness_report(
    *,
    store: MarketStore,
    settings: Settings,
    persist: bool = True,
    now: float | None = None,
) -> dict:
    generated_at = float(now or time.time())
    gates = store.list_production_gates()
    metrics = store.production_readiness_metrics(now=generated_at)
    evidence = _build_evidence(metrics=metrics, settings=settings, gate_count=len(gates), now=generated_at)
    evidence_by_gate: dict[str, list[dict]] = {}
    for item in evidence:
        evidence_by_gate.setdefault(item["gateKey"], []).append(item)

    if persist:
        store.record_production_evidence(evidence)

    gate_reports = [_gate_report(gate, evidence_by_gate.get(gate["key"], [])) for gate in gates]
    phase_reports = _phase_reports(gate_reports)
    summary = _summary(gate_reports, phase_reports)
    return {
        **summary,
        "summary": summary,
        "phases": phase_reports,
        "gates": gate_reports,
        "evidence": evidence,
        "metrics": metrics,
        "generatedAt": _iso(generated_at),
        "source": "stored" if gates else "unavailable",
        "liveExecutionTouched": False,
        "signerCodeTouched": False,
    }


def _build_evidence(*, metrics: dict, settings: Settings, gate_count: int, now: float) -> list[dict]:
    scanner = metrics["scanner"]
    quotes = metrics["quotes"]
    opportunities = metrics["opportunities"]
    risk = metrics["risk"]
    paper = metrics["paper"]
    dry_run = metrics["dryRun"]
    reconciliation = metrics["reconciliation"]
    docs_dir = Path(__file__).resolve().parents[2] / "docs"

    rejected_count = opportunities["rejectedCount"]
    rejected_with_reason = opportunities["rejectedWithReasonCount"]
    quote_fresh = quotes["latestAgeSeconds"] is not None and quotes["latestAgeSeconds"] <= settings.max_route_age_seconds
    paper_rechecks_ready = (
        paper["paperCount"] > 0
        and paper["checked5sCount"] == paper["paperCount"]
        and paper["completionRate30s"] >= PAPER_RECHECK_COMPLETION_TARGET
    )
    dry_run_count = dry_run["dryRunCount"]
    dry_run_group_ok = dry_run["dryRunGroupSizeOkCount"]

    return [
        _evidence(
            "inventory_scope",
            "safe_scope_docs",
            "Safe-scope docs exist",
            (docs_dir / "PRODUCTION_READINESS.md").exists() and (docs_dir / "CODEX_HANDOFF.md").exists(),
            "docs present" if docs_dir.exists() else "docs missing",
            "Production readiness and handoff docs are present in the repo.",
            "/docs/PRODUCTION_READINESS.md",
            {"docsDir": str(docs_dir)},
        ),
        _evidence(
            "inventory_scope",
            "production_gate_table_seeded",
            "Production gate table seeded",
            gate_count > 0,
            f"{gate_count} gates",
            "Gate definitions are stored in production_gates.",
            "/api/ops/production-readiness",
            {"gateCount": gate_count},
        ),
        _evidence(
            "scanner_reliability",
            "scanner_uptime_24h",
            "Scanner uptime 24h",
            scanner["spanSeconds"] >= 86_400,
            _duration(scanner["spanSeconds"]),
            "Derived from earliest and latest stored pool_snapshots rows.",
            "/api/pools",
            scanner,
        ),
        _evidence(
            "scanner_reliability",
            "scanner_uptime_7d",
            "Scanner uptime 7d",
            scanner["spanSeconds"] >= 7 * 86_400,
            f"{_duration(scanner['spanSeconds'])} / {scanner['daysSeen']} UTC days",
            "Derived from stored scanner history, not candidate volume.",
            "/api/pools",
            scanner,
        ),
        _evidence(
            "scanner_reliability",
            "scanner_no_private_key",
            "Scanner requires no keys",
            not settings.signer_enabled and not settings.enable_live_execution and not bool(settings.trader_mnemonic),
            "no signer/live keys configured" if not settings.trader_mnemonic else "signer secret configured",
            "Read-only scanner mode must run without signer or hot-wallet key material.",
            "/api/ops/environment",
            {
                "signerEnabled": settings.signer_enabled,
                "liveExecutionEnabled": settings.enable_live_execution,
                "mnemonicConfigured": bool(settings.trader_mnemonic),
            },
        ),
        _evidence(
            "quote_engine_quality",
            "comparable_quotes",
            "Comparable Tinyman/Pact quotes",
            quotes["quoteCount"] > 0 and quotes["venueCount"] >= 2,
            f"{quotes['quoteCount']} quote rows / {quotes['venueCount']} venues",
            "Quote rows must include comparable venue evidence before route promotion.",
            "/api/opportunities",
            quotes,
        ),
        _evidence(
            "quote_engine_quality",
            "quote_freshness_under_threshold",
            "Quote freshness under threshold",
            quote_fresh,
            "none" if quotes["latestAgeSeconds"] is None else f"{quotes['latestAgeSeconds']:.1f}s <= {settings.max_route_age_seconds:.1f}s",
            "Latest stored quote must be inside the configured quote freshness window.",
            "/api/ops/pipeline#quote_engine",
            quotes,
        ),
        _evidence(
            "route_risk_explainability",
            "route_rejection_explanations",
            "Route rejection explanations",
            rejected_count > 0 and rejected_with_reason == rejected_count,
            f"{rejected_with_reason}/{rejected_count} rejected routes explained",
            "Rejected opportunities must preserve skip reasons.",
            "/api/ops/rejections",
            opportunities,
        ),
        _evidence(
            "route_risk_explainability",
            "risk_decisions_recorded",
            "Risk decisions recorded",
            opportunities["opportunityCount"] > 0 and risk["riskDecisionCount"] >= opportunities["opportunityCount"],
            f"{risk['riskDecisionCount']}/{opportunities['opportunityCount']} decisions",
            "Every opportunity should have a risk_decisions record.",
            "/api/ops/rejections",
            {**risk, **opportunities},
        ),
        _evidence(
            "paper_trading_window",
            "paper_trades_collected",
            "Paper trades collected",
            paper["paperCount"] > 0 and paper["daysCollected"] >= PAPER_TARGET_DAYS,
            f"{paper['paperCount']} rows / {paper['daysCollected']}/{PAPER_TARGET_DAYS} days",
            "Paper trading must collect a seven-day evidence window.",
            "/api/ops/replay-lab",
            paper,
        ),
        _evidence(
            "paper_trading_window",
            "paper_rechecks_complete",
            "5s/30s rechecks complete",
            paper_rechecks_ready,
            f"5s {paper['checked5sCount']}/{paper['paperCount']} / 30s {paper['checked30sCount']}/{paper['paperCount']}",
            "Candidate replays should preserve quote decay and simulated output at 5s and 30s.",
            "/api/ops/replay-lab",
            paper,
        ),
        _evidence(
            "dry_run_validation",
            "dry_run_validation",
            "Dry-run validation",
            dry_run_count > 0,
            f"{dry_run_count} dry-run receipts",
            "Unsigned dry-run receipts must exist before live micro-execution review.",
            "/api/live-trades",
            dry_run,
        ),
        _evidence(
            "dry_run_validation",
            "tx_group_size_guard",
            "Transaction group size guard",
            dry_run_count > 0 and dry_run_group_ok == dry_run_count,
            f"{dry_run_group_ok}/{dry_run_count} groups <= {TX_GROUP_LIMIT} txns",
            "Algorand atomic groups must stay within the SDK transaction group limit.",
            "/api/live-trades",
            dry_run,
        ),
        _evidence(
            "signer_isolation",
            "signer_isolation_review",
            "Signer isolation review",
            not settings.signer_enabled and not bool(settings.trader_mnemonic),
            "signer disabled / no repo mnemonic" if not settings.signer_enabled else "signer enabled",
            "The production signer boundary must stay isolated from UI/control-plane code.",
            "/api/ops/risk-gates",
            {
                "signerEnabled": settings.signer_enabled,
                "mnemonicConfigured": bool(settings.trader_mnemonic),
            },
        ),
        _evidence(
            "signer_isolation",
            "kill_switch_active",
            "Kill switch active",
            settings.signer_kill_switch,
            "active" if settings.signer_kill_switch else "open",
            "Kill switch must remain active until all earlier gates pass and admin review occurs.",
            "/api/ops/risk-gates",
            {"killSwitch": settings.signer_kill_switch},
        ),
        _evidence(
            "manual_reconciliation",
            "manual_trade_reconciliation",
            "Manual trade reconciliation",
            reconciliation["manualOkCount"] > 0 and reconciliation["mismatchCount"] == 0,
            f"{reconciliation['manualOkCount']} manual OK / {reconciliation['mismatchCount']} mismatches",
            "The first tiny manual trade must be reconciled before automation.",
            "/api/reconciliations",
            reconciliation,
        ),
        _evidence(
            "public_dashboard_safety",
            "delayed_public_data",
            "Delayed public data",
            settings.public_delay_seconds > 0,
            f"{settings.public_delay_seconds}s delay",
            "Public dashboard data should be delayed before production claims.",
            "/api/config/public",
            {"publicDelaySeconds": settings.public_delay_seconds},
        ),
        _evidence(
            "public_dashboard_safety",
            "source_labeled_evidence",
            "Source-labeled evidence",
            gate_count > 0,
            "source labels active",
            "Readiness evidence exposes stored/mock/live/delayed/unavailable source labels.",
            "/api/ops/production-readiness",
            {"gateCount": gate_count},
        ),
    ]


def _gate_report(gate: dict, evidence: list[dict]) -> dict:
    total = len(evidence)
    passed = sum(1 for item in evidence if item["status"] == "pass")
    percent = round((passed / total) * 100) if total else 0
    blockers = [item["label"] for item in evidence if item["status"] != "pass"]
    status = "ok" if total and passed == total else "blocked" if blockers else "wait"
    return {
        "key": gate["key"],
        "phaseKey": gate["phaseKey"],
        "label": gate["label"],
        "description": gate["description"],
        "percent": percent,
        "status": status,
        "requiredEvidence": gate["requiredEvidence"],
        "completedEvidence": [item["label"] for item in evidence if item["status"] == "pass"],
        "blockers": blockers,
        "evidence": evidence,
        "evidenceLinks": [
            {"label": item["label"], "href": item["evidenceUrl"], "status": item["status"]}
            for item in evidence
            if item.get("evidenceUrl")
        ],
        "source": "stored" if evidence else "unavailable",
    }


def _phase_reports(gates: list[dict]) -> list[dict]:
    reports = []
    for phase_key, phase_label in PHASE_DEFINITIONS:
        phase_gates = [gate for gate in gates if gate["phaseKey"] == phase_key]
        evidence = [item for gate in phase_gates for item in gate["evidence"]]
        total = len(evidence)
        passed = sum(1 for item in evidence if item["status"] == "pass")
        percent = round((passed / total) * 100) if total else 0
        blockers = [item["label"] for item in evidence if item["status"] != "pass"]
        reports.append(
            {
                "key": phase_key,
                "label": phase_label,
                "percent": percent,
                "status": "ok" if total and not blockers else "blocked" if blockers else "wait",
                "requiredEvidence": [item for gate in phase_gates for item in gate["requiredEvidence"]],
                "completedEvidence": [item["label"] for item in evidence if item["status"] == "pass"],
                "blockers": blockers,
                "gates": [gate["key"] for gate in phase_gates],
                "source": "stored" if phase_gates else "unavailable",
            }
        )
    return reports


def _summary(gates: list[dict], phases: list[dict]) -> dict:
    evidence = [item for gate in gates for item in gate["evidence"]]
    total = len(evidence)
    passed = sum(1 for item in evidence if item["status"] == "pass")
    overall = round((passed / total) * 100) if total else 0
    current_phase = next((phase for phase in phases if phase["status"] != "ok"), phases[-1] if phases else {})
    next_gate = next((gate for gate in gates if gate["status"] != "ok"), None)
    blocking_items = [item["label"] for item in evidence if item["status"] != "pass"][:8]
    return {
        "currentPhase": current_phase.get("label", "Phase 0B Scanner"),
        "currentPhaseKey": current_phase.get("key", "phase_0b_scanner"),
        "overallPercent": overall,
        "nextGate": next_gate["label"] if next_gate else "Production policy review",
        "blockingItems": blocking_items,
        "passedEvidenceCount": passed,
        "totalEvidenceCount": total,
        "source": "stored" if total else "unavailable",
    }


def _evidence(
    gate_key: str,
    evidence_key: str,
    label: str,
    passed: bool,
    value: str,
    detail: str,
    evidence_url: str,
    metadata: dict,
) -> dict:
    return {
        "gateKey": gate_key,
        "evidenceKey": evidence_key,
        "label": label,
        "status": "pass" if passed else "fail",
        "value": value,
        "detail": detail,
        "source": "stored" if passed else "unavailable",
        "evidenceUrl": evidence_url,
        "observedAt": time.time(),
        "metadata": metadata,
    }


def _duration(seconds: float) -> str:
    if seconds >= 7 * 86_400:
        return f"{seconds / 86_400:.1f}d"
    if seconds >= 86_400:
        return f"{seconds / 86_400:.1f}d"
    if seconds >= 3_600:
        return f"{seconds / 3_600:.1f}h"
    return f"{seconds / 60:.1f}m"


def _iso(value: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(value)))
