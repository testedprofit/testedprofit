from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FailureScenario:
    key: str
    label: str
    failure_type: str
    severity: str
    trigger: str
    services_affected: tuple[str, ...]
    expected_status: str
    expected_response: str
    actual_status: str
    actual_response: str
    alerts: tuple[str, ...]
    operator_action: str
    blocks_live_execution: bool = True


FAILURE_SCENARIOS: tuple[FailureScenario, ...] = (
    FailureScenario(
        key="tinyman_offline",
        label="Tinyman Offline",
        failure_type="connector",
        severity="critical",
        trigger="Tinyman connector returns timeout or non-200 response.",
        services_affected=("Pool Scanner", "Quote Engine", "Route Engine", "Public Dashboard"),
        expected_status="degraded",
        expected_response="Disable Tinyman-sourced fresh quotes, keep Pact/scanner paths alive, label affected data stale/unavailable, and alert operators.",
        actual_status="degraded",
        actual_response="Tinyman quotes are rejected as unavailable while Pact-only intelligence remains available with source labels.",
        alerts=("tinyman_connector_failing", "quote_age_above_threshold"),
        operator_action="Check Tinyman endpoint health, preserve stale quote evidence, and do not promote affected routes.",
    ),
    FailureScenario(
        key="pact_offline",
        label="Pact Offline",
        failure_type="connector",
        severity="critical",
        trigger="Pact connector returns timeout or malformed pool state.",
        services_affected=("Pool Scanner", "Quote Engine", "Route Engine", "Public Dashboard"),
        expected_status="degraded",
        expected_response="Disable Pact-sourced fresh quotes, keep Tinyman/scanner paths alive, label affected data stale/unavailable, and alert operators.",
        actual_status="degraded",
        actual_response="Pact quotes are rejected as unavailable while Tinyman-only intelligence remains available with source labels.",
        alerts=("pact_connector_failing", "quote_age_above_threshold"),
        operator_action="Check Pact connector health, preserve stale quote evidence, and do not promote affected routes.",
    ),
    FailureScenario(
        key="stale_quotes",
        label="Stale Quotes",
        failure_type="freshness",
        severity="warning",
        trigger="Quote age is greater than the freshness threshold.",
        services_affected=("Quote Engine", "Route Engine", "Risk Engine", "Paper Trader"),
        expected_status="blocked",
        expected_response="Reject candidate routes with quote freshness reason, keep scanning, and show stale quote alerts.",
        actual_status="blocked",
        actual_response="Routes are rejected before dry-run handoff; paper trader can continue recording quote decay when data resumes.",
        alerts=("quote_age_above_threshold",),
        operator_action="Refresh quotes and verify the route engine explains every stale rejection.",
    ),
    FailureScenario(
        key="database_unavailable",
        label="Database Unavailable",
        failure_type="storage",
        severity="critical",
        trigger="Postgres/SQLite write or read fails.",
        services_affected=("All Services", "Dashboard", "Reports", "Receipts/Reconciliation"),
        expected_status="blocked",
        expected_response="Stop report generation and persistence-dependent work, keep live execution locked, and show unavailable source labels.",
        actual_status="blocked",
        actual_response="Control-plane data is marked unavailable; dashboards fall back only to mock-labeled data and no execution path is opened.",
        alerts=("database_unavailable",),
        operator_action="Restore database, verify migrations, and reconcile missing scanner/report intervals before proceeding.",
    ),
    FailureScenario(
        key="route_engine_crash",
        label="Route Engine Crash",
        failure_type="route_engine",
        severity="critical",
        trigger="Route generation raises an exception or exits unexpectedly.",
        services_affected=("Route Engine", "Risk Engine", "Paper Trader", "Dry-Run Builder"),
        expected_status="blocked",
        expected_response="Stop candidate promotion, keep scanner and quote capture running, alert operators, and require route-engine restart evidence.",
        actual_status="blocked",
        actual_response="No routes are promoted to paper/dry-run; scanner and quote evidence remain read-only and live execution stays locked.",
        alerts=("route_engine_crash",),
        operator_action="Restart route engine, inspect stack trace, and rerun route-forensics completeness checks.",
    ),
    FailureScenario(
        key="signer_unavailable",
        label="Signer Unavailable",
        failure_type="signer_boundary",
        severity="critical",
        trigger="Signer health check is offline or signer is intentionally disabled.",
        services_affected=("Signer Gate", "Dry-Run Builder", "Live Micro-Execution"),
        expected_status="locked",
        expected_response="Keep dry-run unsigned, reject signing requests, log signer unavailable, and keep live execution disarmed.",
        actual_status="locked",
        actual_response="Signer stays disabled/unavailable; no key material is exposed and no transaction submission path is opened.",
        alerts=("signer_offline",),
        operator_action="Verify signer isolation, kill switch, and policy logs before any future manual trade review.",
    ),
    FailureScenario(
        key="unknown_asset",
        label="Unknown Asset",
        failure_type="allowlist",
        severity="high",
        trigger="Route contains an asset outside the reviewed allowlist.",
        services_affected=("Route Engine", "Risk Engine", "Paper Trader", "Dry-Run Builder"),
        expected_status="rejected",
        expected_response="Reject route, store asset allowlist reason, alert operators, and exclude from delayed public intelligence.",
        actual_status="rejected",
        actual_response="Route is blocked by asset allowlist before paper/dry-run promotion.",
        alerts=("unknown_asset_detected",),
        operator_action="Review asset metadata, freeze/clawback flags, liquidity, and allowlist policy before considering support.",
    ),
    FailureScenario(
        key="unknown_app_id",
        label="Unknown App ID",
        failure_type="allowlist",
        severity="high",
        trigger="Route or unsigned group references an application outside the reviewed app ID allowlist.",
        services_affected=("Route Engine", "Risk Engine", "Dry-Run Builder", "Signer Gate"),
        expected_status="rejected",
        expected_response="Reject route/group, store app ID allowlist reason, and keep signer unavailable to unknown apps.",
        actual_status="rejected",
        actual_response="Route is blocked by app ID allowlist; signer policy would also reject the group.",
        alerts=("unknown_app_id_detected",),
        operator_action="Review venue/app provenance and update allowlist only through explicit security review.",
    ),
    FailureScenario(
        key="daily_loss_breach",
        label="Daily Loss Breach",
        failure_type="risk_limit",
        severity="critical",
        trigger="Realized or simulated daily loss breaches the configured cap.",
        services_affected=("Risk Engine", "Dry-Run Builder", "Live Micro-Execution", "Receipts/Reconciliation"),
        expected_status="locked",
        expected_response="Block new execution requests, preserve reconciliation evidence, alert operators, and require manual go/no-go review.",
        actual_status="locked",
        actual_response="Risk gate blocks additional execution; live micro-execution remains disarmed with daily-loss alert evidence.",
        alerts=("daily_loss_limit_near_breach", "kill_switch_triggered"),
        operator_action="Stop trading, reconcile expected-vs-actual outputs, and reset limits only after documented review.",
    ),
)


def build_failure_lab_report() -> dict[str, Any]:
    scenarios = [_scenario_payload(scenario) for scenario in FAILURE_SCENARIOS]
    graceful_count = sum(1 for scenario in scenarios if scenario["gracefulDegradation"])
    critical_count = sum(1 for scenario in scenarios if scenario["severity"] == "critical")
    blocked_count = sum(
        1
        for scenario in scenarios
        if scenario["actualResponse"]["status"] in {"blocked", "locked", "rejected"}
    )
    return {
        "scenarios": scenarios,
        "summary": {
            "scenarioCount": len(scenarios),
            "gracefulCount": graceful_count,
            "criticalCount": critical_count,
            "blockedCount": blocked_count,
            "gracefulPercent": 0 if not scenarios else round((graceful_count / len(scenarios)) * 100),
            "headline": f"{graceful_count}/{len(scenarios)} simulated failures degrade safely",
        },
        "source": "mock",
        "mode": "simulation",
        "liveExecutionTouched": False,
        "signerCodeTouched": False,
    }


def _scenario_payload(scenario: FailureScenario) -> dict[str, Any]:
    expected = {
        "status": scenario.expected_status,
        "message": scenario.expected_response,
        "blocksLiveExecution": scenario.blocks_live_execution,
    }
    actual = {
        "status": scenario.actual_status,
        "message": scenario.actual_response,
        "blocksLiveExecution": scenario.blocks_live_execution,
    }
    graceful = _is_graceful(expected, actual, scenario.alerts)
    return {
        "key": scenario.key,
        "label": scenario.label,
        "failureType": scenario.failure_type,
        "severity": scenario.severity,
        "trigger": scenario.trigger,
        "expectedResponse": expected,
        "actualResponse": actual,
        "alertsGenerated": list(scenario.alerts),
        "servicesAffected": list(scenario.services_affected),
        "operatorAction": scenario.operator_action,
        "gracefulDegradation": graceful,
        "source": "mock",
    }


def _is_graceful(expected: dict[str, Any], actual: dict[str, Any], alerts: tuple[str, ...]) -> bool:
    blocking_states = {"blocked", "locked", "rejected", "degraded"}
    expected_blocks = bool(expected.get("blocksLiveExecution"))
    actual_blocks = bool(actual.get("blocksLiveExecution"))
    actual_status = str(actual.get("status") or "")
    return expected_blocks == actual_blocks and actual_status in blocking_states and bool(alerts)
