from __future__ import annotations

from typing import Any


EVIDENCE_CATEGORIES = (
    "scanner",
    "quotes",
    "routes",
    "paper_trading",
    "risk",
    "dry_run",
    "execution",
    "receipts",
)

EVIDENCE_STATUSES = ("pass", "pending", "warn", "fail")


def build_evidence_records(*, metrics: dict[str, Any], system_state: dict[str, Any], now: float) -> list[dict[str, Any]]:
    scanner = metrics.get("scanner", {})
    quotes = metrics.get("quotes", {})
    opportunities = metrics.get("opportunities", {})
    paper = metrics.get("paper", {})
    risk = metrics.get("risk", {})
    dry_run = metrics.get("dryRun", {})
    reconciliation = metrics.get("reconciliation", {})

    records = [
        _record(
            "scanner.uptime_24h",
            "pool_scanner",
            "scanner",
            "24h uptime achieved",
            f"{_duration(scanner.get('spanSeconds', 0.0))} scanner history captured.",
            _pass_pending(float(scanner.get("spanSeconds") or 0.0) >= 86_400),
            now,
            scanner,
        ),
        _record(
            "scanner.pools_100",
            "pool_scanner",
            "scanner",
            "100 pools scanned",
            f"{int(scanner.get('poolCount') or 0)} distinct pools scanned.",
            _pass_pending(int(scanner.get("poolCount") or 0) >= 100),
            now,
            scanner,
        ),
        _record(
            "scanner.snapshots_recorded",
            "pool_scanner",
            "scanner",
            "Pool snapshots recorded",
            f"{int(scanner.get('snapshotCount') or 0)} pool snapshot rows stored.",
            _pass_pending(int(scanner.get("snapshotCount") or 0) > 0),
            now,
            scanner,
        ),
        _record(
            "quotes.rows_recorded",
            "quote_engine",
            "quotes",
            "Quote rows recorded",
            f"{int(quotes.get('quoteCount') or 0)} quote rows stored.",
            _pass_pending(int(quotes.get("quoteCount") or 0) > 0),
            now,
            quotes,
        ),
        _record(
            "quotes.comparable_venues",
            "quote_engine",
            "quotes",
            "Comparable venues observed",
            f"{int(quotes.get('venueCount') or 0)} venues represented in quotes.",
            _pass_pending(int(quotes.get("venueCount") or 0) >= 2),
            now,
            quotes,
        ),
        _record(
            "quotes.freshness_under_threshold",
            "quote_engine",
            "quotes",
            "Quote freshness under threshold",
            _freshness_summary(quotes.get("latestAgeSeconds"), system_state.get("maxRouteAgeSeconds")),
            _freshness_status(quotes.get("latestAgeSeconds"), system_state.get("maxRouteAgeSeconds")),
            now,
            {**quotes, "maxRouteAgeSeconds": system_state.get("maxRouteAgeSeconds")},
        ),
        _record(
            "routes.opportunities_50",
            "route_engine",
            "routes",
            "50 opportunities generated",
            f"{int(opportunities.get('opportunityCount') or 0)} route opportunities generated.",
            _pass_pending(int(opportunities.get("opportunityCount") or 0) >= 50),
            now,
            opportunities,
        ),
        _record(
            "routes.rejection_reasons_100",
            "route_engine",
            "routes",
            "100% rejection reasons recorded",
            _rejection_summary(opportunities),
            _rejection_status(opportunities),
            now,
            opportunities,
        ),
        _record(
            "routes.forensics_complete",
            "route_engine",
            "routes",
            "Route forensics complete",
            f"{int(system_state.get('routeForensicsCompleteCount') or 0)}/{int(system_state.get('routeForensicsCount') or 0)} route forensic records complete.",
            _forensics_status(system_state),
            now,
            {
                "routeForensicsCount": system_state.get("routeForensicsCount", 0),
                "routeForensicsCompleteCount": system_state.get("routeForensicsCompleteCount", 0),
            },
        ),
        _record(
            "paper.sample_7d",
            "paper_trader",
            "paper_trading",
            "7-day sample complete",
            f"{int(paper.get('daysCollected') or 0)}/7 days collected across {int(paper.get('paperCount') or 0)} paper trades.",
            _pass_pending(int(paper.get("daysCollected") or 0) >= 7 and int(paper.get("paperCount") or 0) > 0),
            now,
            paper,
        ),
        _record(
            "paper.rechecks_recorded",
            "paper_trader",
            "paper_trading",
            "5s/30s rechecks recorded",
            f"5s {int(paper.get('checked5sCount') or 0)} / 30s {int(paper.get('checked30sCount') or 0)} rechecks.",
            _pass_pending(int(paper.get("paperCount") or 0) > 0 and float(paper.get("completionRate30s") or 0.0) >= 0.8),
            now,
            paper,
        ),
        _record(
            "paper.expected_vs_simulated_report",
            "paper_trader",
            "paper_trading",
            "Expected vs simulated report generated",
            f"{int(paper.get('checked30sCount') or 0)} routes have T+30s simulated output.",
            _pass_pending(int(paper.get("checked30sCount") or 0) > 0),
            now,
            paper,
        ),
        _record(
            "risk.decisions_recorded",
            "risk_engine",
            "risk",
            "Risk decisions recorded",
            f"{int(risk.get('riskDecisionCount') or 0)}/{int(opportunities.get('opportunityCount') or 0)} opportunity decisions stored.",
            _risk_decision_status(risk, opportunities),
            now,
            {**risk, **opportunities},
        ),
        _record(
            "risk.rejections_recorded",
            "risk_engine",
            "risk",
            "Risk rejections recorded",
            f"{int(risk.get('rejectedDecisionCount') or 0)} risk rejections recorded.",
            _pass_pending(int(risk.get("rejectedDecisionCount") or 0) > 0),
            now,
            risk,
        ),
        _record(
            "risk.allowlists_configured",
            "risk_engine",
            "risk",
            "Asset and app allowlists configured",
            f"{int(system_state.get('allowedAssetCount') or 0)} assets / {int(system_state.get('allowedAppCount') or 0)} apps configured.",
            "pass" if int(system_state.get("allowedAssetCount") or 0) > 0 and int(system_state.get("allowedAppCount") or 0) > 0 else "warn",
            now,
            {
                "allowedAssetCount": system_state.get("allowedAssetCount", 0),
                "allowedAppCount": system_state.get("allowedAppCount", 0),
                "requireAppIdAllowlist": system_state.get("requireAppIdAllowlist", True),
            },
        ),
        _record(
            "dry_run.receipts_recorded",
            "dry_run_builder",
            "dry_run",
            "Unsigned dry-run receipts recorded",
            f"{int(dry_run.get('dryRunCount') or 0)} dry-run receipts stored.",
            _pass_pending(int(dry_run.get("dryRunCount") or 0) > 0),
            now,
            dry_run,
        ),
        _record(
            "dry_run.group_size_guard",
            "dry_run_builder",
            "dry_run",
            "Transaction group size guard verified",
            f"{int(dry_run.get('dryRunGroupSizeOkCount') or 0)}/{int(dry_run.get('dryRunCount') or 0)} dry-run groups within 16 transactions.",
            _dry_run_group_status(dry_run),
            now,
            dry_run,
        ),
        _record(
            "execution.live_disarmed",
            "execution_controls",
            "execution",
            "Live execution disarmed",
            "Live execution and execute-approved flags are off.",
            "pass"
            if not system_state.get("enableLiveExecution") and not system_state.get("executeApproved")
            else "fail",
            now,
            {
                "enableLiveExecution": system_state.get("enableLiveExecution"),
                "executeApproved": system_state.get("executeApproved"),
                "signerEnabled": system_state.get("signerEnabled"),
            },
        ),
        _record(
            "execution.kill_switch_active",
            "execution_controls",
            "execution",
            "Kill switch active",
            "Kill switch is active." if system_state.get("signerKillSwitch") else "Kill switch is open.",
            "pass" if system_state.get("signerKillSwitch") else "fail",
            now,
            {"signerKillSwitch": system_state.get("signerKillSwitch")},
        ),
        _record(
            "execution.no_live_submissions",
            "execution_controls",
            "execution",
            "No live submissions from control plane",
            f"{int(dry_run.get('submittedCount') or 0)} submitted live trades recorded.",
            "pass" if int(dry_run.get("submittedCount") or 0) == 0 else "warn",
            now,
            dry_run,
        ),
        _record(
            "receipts.payment_verifications",
            "receipt_verifier",
            "receipts",
            "Payment verification receipts recorded",
            f"{int(system_state.get('paymentVerificationCount') or 0)} PNET payment verification receipts stored.",
            _pass_pending(int(system_state.get("paymentVerificationCount") or 0) > 0),
            now,
            {"paymentVerificationCount": system_state.get("paymentVerificationCount", 0)},
        ),
        _record(
            "receipts.reconciliation_records",
            "receipt_verifier",
            "receipts",
            "Reconciliation records stored",
            f"{int(reconciliation.get('reconciliationCount') or 0)} reconciliation records / {int(reconciliation.get('mismatchCount') or 0)} mismatches.",
            _reconciliation_status(reconciliation),
            now,
            reconciliation,
        ),
        _record(
            "receipts.daily_report_generated",
            "research_reporter",
            "receipts",
            "Daily intelligence report generated",
            f"{int(system_state.get('marketReportCount') or 0)} daily market reports stored.",
            _pass_pending(int(system_state.get("marketReportCount") or 0) > 0),
            now,
            {
                "marketReportCount": system_state.get("marketReportCount", 0),
                "latestMarketReportDate": system_state.get("latestMarketReportDate"),
            },
        ),
    ]
    return records


def summarize_evidence_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_category = _counter(records, "category")
    by_service = _counter(records, "service")
    by_status = _counter(records, "status")
    total = len(records)
    passing = by_status.get("pass", 0)
    return {
        "total": total,
        "passing": passing,
        "pending": by_status.get("pending", 0),
        "warn": by_status.get("warn", 0),
        "fail": by_status.get("fail", 0),
        "proofPercent": round((passing / total) * 100) if total else 0,
        "byCategory": by_category,
        "byService": by_service,
        "byStatus": by_status,
        "categories": list(EVIDENCE_CATEGORIES),
        "statuses": list(EVIDENCE_STATUSES),
    }


def _record(
    evidence_id: str,
    service: str,
    category: str,
    title: str,
    summary: str,
    status: str,
    now: float,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "evidenceId": evidence_id,
        "service": service,
        "category": category,
        "title": title,
        "summary": summary,
        "status": status,
        "createdAt": float(now),
        "metadata": {
            "source": "stored",
            "evidenceUrl": _evidence_url(category),
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
            **metadata,
        },
    }


def _evidence_url(category: str) -> str:
    return {
        "scanner": "/api/pools",
        "quotes": "/api/opportunities",
        "routes": "/api/ops/route-forensics",
        "paper_trading": "/api/ops/replay-lab",
        "risk": "/api/ops/rejections",
        "dry_run": "/api/live-trades",
        "execution": "/api/ops/risk-gates",
        "receipts": "/api/reports/market/archive",
    }.get(category, "/api/ops/evidence")


def _pass_pending(passed: bool) -> str:
    return "pass" if passed else "pending"


def _freshness_summary(age: Any, threshold: Any) -> str:
    if age is None:
        return "No stored quote age is available yet."
    return f"Latest quote age is {float(age):.1f}s against {float(threshold or 0.0):.1f}s threshold."


def _freshness_status(age: Any, threshold: Any) -> str:
    if age is None:
        return "pending"
    return "pass" if float(age) <= float(threshold or 0.0) else "fail"


def _rejection_summary(opportunities: dict[str, Any]) -> str:
    rejected = int(opportunities.get("rejectedCount") or 0)
    with_reason = int(opportunities.get("rejectedWithReasonCount") or 0)
    return f"{with_reason}/{rejected} rejected routes have skip reasons."


def _rejection_status(opportunities: dict[str, Any]) -> str:
    rejected = int(opportunities.get("rejectedCount") or 0)
    with_reason = int(opportunities.get("rejectedWithReasonCount") or 0)
    if rejected == 0:
        return "pending"
    return "pass" if with_reason == rejected else "fail"


def _forensics_status(system_state: dict[str, Any]) -> str:
    total = int(system_state.get("routeForensicsCount") or 0)
    complete = int(system_state.get("routeForensicsCompleteCount") or 0)
    if total == 0:
        return "pending"
    return "pass" if complete == total else "fail"


def _risk_decision_status(risk: dict[str, Any], opportunities: dict[str, Any]) -> str:
    opportunity_count = int(opportunities.get("opportunityCount") or 0)
    decision_count = int(risk.get("riskDecisionCount") or 0)
    if opportunity_count == 0:
        return "pending"
    return "pass" if decision_count >= opportunity_count else "fail"


def _dry_run_group_status(dry_run: dict[str, Any]) -> str:
    total = int(dry_run.get("dryRunCount") or 0)
    ok = int(dry_run.get("dryRunGroupSizeOkCount") or 0)
    if total == 0:
        return "pending"
    return "pass" if ok == total else "fail"


def _reconciliation_status(reconciliation: dict[str, Any]) -> str:
    count = int(reconciliation.get("reconciliationCount") or 0)
    mismatch = int(reconciliation.get("mismatchCount") or 0)
    if count == 0:
        return "pending"
    return "pass" if mismatch == 0 else "fail"


def _counter(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in records:
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _duration(seconds: float) -> str:
    seconds = max(0.0, float(seconds or 0.0))
    if seconds >= 86_400:
        return f"{seconds / 86_400:.1f}d"
    if seconds >= 3_600:
        return f"{seconds / 3_600:.1f}h"
    return f"{seconds / 60:.1f}m"
