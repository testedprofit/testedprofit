from __future__ import annotations

from typing import Any


MetricDefinition = dict[str, Any]


METRIC_CATALOG: dict[str, MetricDefinition] = {
    "scanner.pool_count": {
        "label": "Pools scanned",
        "unit": "pools",
        "entity": "metrics",
        "path": ("scanner", "poolCount"),
        "table": "pool_snapshots",
        "field": "count(distinct pool_id)",
        "description": "Distinct pool ids observed by the read-only scanner.",
    },
    "scanner.snapshot_count": {
        "label": "Pool snapshots",
        "unit": "snapshots",
        "entity": "metrics",
        "path": ("scanner", "snapshotCount"),
        "table": "pool_snapshots",
        "field": "count(*)",
        "description": "Stored pool snapshot rows captured by scanner runs.",
    },
    "quote.count": {
        "label": "Quote legs",
        "unit": "quotes",
        "entity": "metrics",
        "path": ("quotes", "quoteCount"),
        "table": "quotes",
        "field": "count(*)",
        "description": "Comparable quote-leg rows recorded for route calculations.",
    },
    "quote.fresh_count": {
        "label": "Fresh quotes",
        "unit": "quotes",
        "entity": "metrics",
        "path": ("quotes", "freshCount"),
        "table": "quotes",
        "field": "expires_at >= now",
        "description": "Quote rows that remain under the configured freshness threshold.",
    },
    "quote.avg_price_impact_bps": {
        "label": "Average price impact",
        "unit": "bps",
        "entity": "metrics",
        "path": ("quotes", "avgPriceImpactBps"),
        "table": "quotes",
        "field": "avg(price_impact_bps)",
        "description": "Average stored quote price impact in basis points.",
    },
    "route.count": {
        "label": "Route candidates",
        "unit": "routes",
        "entity": "metrics",
        "path": ("opportunities", "opportunityCount"),
        "table": "opportunities",
        "field": "count(*)",
        "description": "Stored route candidates produced from comparable quotes.",
    },
    "route.approved_count": {
        "label": "Approved routes",
        "unit": "routes",
        "entity": "metrics",
        "path": ("opportunities", "approvedCount"),
        "table": "opportunities",
        "field": "sum(status = approved)",
        "description": "Routes approved for review after risk rules, not live execution.",
    },
    "route.rejected_count": {
        "label": "Rejected routes",
        "unit": "routes",
        "entity": "metrics",
        "path": ("opportunities", "rejectedCount"),
        "table": "opportunities",
        "field": "sum(status != approved)",
        "description": "Routes rejected by explainable risk and policy checks.",
    },
    "route.expected_net_profit": {
        "label": "Expected net profit",
        "unit": "input asset",
        "entity": "opportunity",
        "path": ("expected_net_profit",),
        "table": "opportunities",
        "field": "expected_net_profit",
        "description": "Gross profit minus network fees, DEX fees, and slippage buffer for the selected route.",
    },
    "route.expected_profit_bps": {
        "label": "Expected profit bps",
        "unit": "bps",
        "entity": "opportunity",
        "path": ("expected_profit_bps",),
        "table": "opportunities",
        "field": "expected_profit_bps",
        "description": "Expected net profit divided by input size, expressed as basis points.",
    },
    "route.confidence_score": {
        "label": "Route confidence",
        "unit": "score",
        "entity": "opportunity",
        "path": ("confidence_score",),
        "table": "opportunities",
        "field": "confidence_score",
        "description": "Stored route confidence derived from impact, freshness, liquidity, and risk state.",
    },
    "route.price_impact_bps": {
        "label": "Route price impact",
        "unit": "bps",
        "entity": "opportunity",
        "path": ("total_price_impact_bps",),
        "table": "opportunities",
        "field": "total_price_impact_bps",
        "description": "Total price impact accumulated across the route legs.",
    },
    "paper.count": {
        "label": "Paper candidates",
        "unit": "trades",
        "entity": "metrics",
        "path": ("paper", "paperCount"),
        "table": "paper_trades",
        "field": "count(*)",
        "description": "Paper-trade candidates stored before any real-fund execution path.",
    },
    "paper.checked_30s_count": {
        "label": "30s paper checks",
        "unit": "checks",
        "entity": "metrics",
        "path": ("paper", "checked30sCount"),
        "table": "paper_trades",
        "field": "checked_30s_at is not null",
        "description": "Paper-trade candidates with a completed T+30s recheck.",
    },
    "risk.decision_count": {
        "label": "Risk decisions",
        "unit": "decisions",
        "entity": "metrics",
        "path": ("risk", "riskDecisionCount"),
        "table": "risk_decisions",
        "field": "count(*)",
        "description": "Risk decision records tied to route candidates.",
    },
    "risk.rejected_count": {
        "label": "Risk rejections",
        "unit": "decisions",
        "entity": "metrics",
        "path": ("risk", "rejectedDecisionCount"),
        "table": "risk_decisions",
        "field": "sum(approved = 0)",
        "description": "Risk decisions that blocked route promotion.",
    },
    "live.state": {
        "label": "Live execution state",
        "unit": "state",
        "entity": "constant",
        "path": (),
        "table": "settings",
        "field": "live lock",
        "description": "Safety state for live execution. Phase 0 remains locked unless gates pass.",
        "constantValue": "locked",
    },
}


LINEAGE_STEPS = (
    "metric",
    "source_data",
    "quote",
    "pool_snapshot",
    "route_calculation",
    "risk_decision",
)


def build_data_provenance_report(
    *,
    metric_key: str | None,
    metrics: dict[str, Any],
    opportunity: dict[str, Any] | None,
    quotes: list[dict[str, Any]],
    pool_snapshots: list[dict[str, Any]],
    risk_decisions: list[dict[str, Any]],
    route_forensics: dict[str, Any] | None,
) -> dict[str, Any]:
    selected_key = metric_key if metric_key in METRIC_CATALOG else "route.expected_net_profit"
    selected = _metric_card(selected_key, metrics, opportunity)
    metric_cards = [_metric_card(key, metrics, opportunity) for key in METRIC_CATALOG]
    lineage = _lineage(selected, opportunity, quotes, pool_snapshots, risk_decisions, route_forensics)
    missing_steps = [step["label"] for step in lineage if step["status"] != "ok"]
    stored_records = [
        record
        for step in lineage
        for record in step["records"]
        if record.get("source") == "stored"
    ]
    route_hash = opportunity.get("route_hash") if opportunity else None
    return {
        "metrics": metric_cards,
        "selectedMetricKey": selected_key,
        "selectedMetric": selected,
        "lineage": lineage,
        "lineageOrder": list(LINEAGE_STEPS),
        "routeHash": route_hash,
        "complete": not missing_steps,
        "missingSteps": missing_steps,
        "source": "stored" if stored_records else "unavailable",
        "liveExecutionTouched": False,
        "signerCodeTouched": False,
        "safety": {
            "label": "Read-only provenance",
            "detail": "Tracing stored data only. No signer, hot wallet, or transaction submission path is touched.",
        },
    }


def _metric_card(key: str, metrics: dict[str, Any], opportunity: dict[str, Any] | None) -> dict[str, Any]:
    definition = METRIC_CATALOG[key]
    value = _metric_value(definition, metrics, opportunity)
    return {
        "key": key,
        "label": definition["label"],
        "value": _display_value(value),
        "rawValue": value,
        "unit": definition["unit"],
        "source": "stored" if value not in (None, "") else "unavailable",
        "status": "ok" if value not in (None, "") else "unavailable",
        "table": definition["table"],
        "field": definition["field"],
        "description": definition["description"],
    }


def _metric_value(definition: MetricDefinition, metrics: dict[str, Any], opportunity: dict[str, Any] | None) -> Any:
    entity = definition["entity"]
    if entity == "constant":
        return definition.get("constantValue")
    if entity == "opportunity":
        return _nested_value(opportunity or {}, definition["path"])
    return _nested_value(metrics, definition["path"])


def _lineage(
    selected: dict[str, Any],
    opportunity: dict[str, Any] | None,
    quotes: list[dict[str, Any]],
    pool_snapshots: list[dict[str, Any]],
    risk_decisions: list[dict[str, Any]],
    route_forensics: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    metric_record = {
        "label": selected["label"],
        "table": selected["table"],
        "field": selected["field"],
        "value": selected["value"],
        "source": selected["source"],
        "detail": selected["description"],
    }
    source_records = [_source_data_record(selected)]
    quote_records = [_quote_record(row) for row in quotes]
    snapshot_records = [_snapshot_record(row) for row in pool_snapshots]
    route_records = _route_records(opportunity, route_forensics)
    risk_records = [_risk_record(row) for row in risk_decisions]
    if route_forensics:
        risk_records.append(
            {
                "label": "Forensics risk result",
                "table": "route_forensics",
                "field": "risk_result_json",
                "value": _display_value(route_forensics.get("riskResult", {}).get("status") or route_forensics.get("riskResult", {}).get("approved")),
                "source": route_forensics.get("source", "stored"),
                "detail": route_forensics.get("rejectionReason") or "Risk result captured in route forensics.",
                "raw": route_forensics.get("riskResult", {}),
            }
        )
    return [
        _lineage_step("metric", "Metric", "Displayed dashboard value.", [metric_record]),
        _lineage_step("source_data", "Source Data", "Database field or aggregate used to compute the metric.", source_records),
        _lineage_step("quote", "Quote", "Quote-leg rows used by the route calculation.", quote_records),
        _lineage_step("pool_snapshot", "Pool Snapshot", "Pool reserve snapshots behind each quote leg.", snapshot_records),
        _lineage_step("route_calculation", "Route Calculation", "Opportunity and route-forensics math for the selected route.", route_records),
        _lineage_step("risk_decision", "Risk Decision", "Risk gate records tied to the route hash.", risk_records),
    ]


def _lineage_step(key: str, label: str, description: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    has_source = any(record.get("source") != "unavailable" for record in records)
    return {
        "key": key,
        "label": label,
        "description": description,
        "records": records,
        "status": "ok" if records and has_source else "missing",
        "source": "stored" if any(record.get("source") == "stored" for record in records) else "unavailable",
    }


def _source_data_record(selected: dict[str, Any]) -> dict[str, Any]:
    return {
        "label": selected["label"],
        "table": selected["table"],
        "field": selected["field"],
        "value": selected["value"],
        "source": selected["source"],
        "detail": f"{selected['description']} Unit: {selected['unit']}.",
    }


def _quote_record(row: dict[str, Any]) -> dict[str, Any]:
    leg = row.get("leg_index")
    return {
        "label": f"Quote leg {leg}",
        "table": "quotes",
        "recordId": row.get("id"),
        "field": "output_amount",
        "value": _display_value(row.get("output_amount")),
        "source": "stored",
        "detail": f"{row.get('venue_id')} / {row.get('pool_id')} / {row.get('input_asset_id')} -> {row.get('output_asset_id')}",
        "capturedAt": row.get("captured_at"),
        "raw": row,
    }


def _snapshot_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "label": str(row.get("pool_id") or "pool snapshot"),
        "table": "pool_snapshots",
        "recordId": row.get("id"),
        "field": "reserve_a/reserve_b",
        "value": f"{_display_value(row.get('reserve_a'))} / {_display_value(row.get('reserve_b'))}",
        "source": "stored",
        "detail": f"round {row.get('block_round')} / liquidity {_display_value(row.get('liquidity_estimate'))}",
        "capturedAt": row.get("captured_at"),
        "raw": row,
    }


def _route_records(opportunity: dict[str, Any] | None, route_forensics: dict[str, Any] | None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if opportunity:
        records.append(
            {
                "label": "Opportunity",
                "table": "opportunities",
                "recordId": opportunity.get("id"),
                "field": "expected_net_profit",
                "value": _display_value(opportunity.get("expected_net_profit")),
                "source": "stored",
                "detail": f"route {opportunity.get('route_hash')} / status {opportunity.get('status')}",
                "capturedAt": opportunity.get("created_at"),
                "raw": {
                    "route_hash": opportunity.get("route_hash"),
                    "route": opportunity.get("route"),
                    "gross_profit": opportunity.get("gross_profit"),
                    "estimated_network_fee": opportunity.get("estimated_network_fee"),
                    "total_dex_fees": opportunity.get("total_dex_fees"),
                    "slippage_buffer": opportunity.get("slippage_buffer"),
                    "expected_net_profit": opportunity.get("expected_net_profit"),
                    "expected_profit_bps": opportunity.get("expected_profit_bps"),
                    "confidence_score": opportunity.get("confidence_score"),
                    "status": opportunity.get("status"),
                    "skip_reason": opportunity.get("skip_reason"),
                },
            }
        )
    if route_forensics:
        records.append(
            {
                "label": "Route forensics",
                "table": "route_forensics",
                "recordId": route_forensics.get("id"),
                "field": "profitability_json/confidence_calculation_json",
                "value": _display_value(route_forensics.get("profitability", {}).get("expectedNetProfit")),
                "source": route_forensics.get("source", "stored"),
                "detail": route_forensics.get("routePathLabel") or "route path recorded",
                "capturedAt": route_forensics.get("createdAt"),
                "raw": {
                    "routePath": route_forensics.get("routePath"),
                    "profitability": route_forensics.get("profitability"),
                    "confidenceCalculation": route_forensics.get("confidenceCalculation"),
                    "decisionTree": route_forensics.get("decisionTree"),
                },
            }
        )
    return records


def _risk_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "label": "Risk decision",
        "table": "risk_decisions",
        "recordId": row.get("id"),
        "field": "approved/reason/rules_json",
        "value": "approved" if row.get("approved") else "rejected",
        "source": "stored",
        "detail": row.get("reason") or "all tracked risk rules passed",
        "capturedAt": row.get("created_at"),
        "raw": row,
    }


def _nested_value(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = data
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def _display_value(value: Any) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)
