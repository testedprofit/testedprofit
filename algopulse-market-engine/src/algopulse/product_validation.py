from __future__ import annotations

import json
import time
from collections import Counter
from collections import defaultdict
from datetime import datetime
from datetime import timezone
from typing import Any


ACTION_TAXONOMY = {
    "viewed_market_pulse": {
        "label": "Viewed Market Pulse",
        "feature": "Market Pulse",
        "personas": ["Trader", "Researcher"],
        "decision": False,
        "evidenceSource": "market_pulse",
    },
    "opened_route": {
        "label": "Opened Route",
        "feature": "Route Intelligence",
        "personas": ["Trader", "Builder"],
        "decision": True,
        "evidenceSource": "route_details",
    },
    "inspected_route_forensics": {
        "label": "Inspected Route Forensics",
        "feature": "Route Forensics",
        "personas": ["Trader", "Builder", "Researcher"],
        "decision": True,
        "evidenceSource": "route_forensics",
    },
    "viewed_liquidity_health": {
        "label": "Viewed Liquidity Health",
        "feature": "Liquidity Health",
        "personas": ["Project Founder", "Liquidity Provider"],
        "decision": True,
        "evidenceSource": "liquidity_health",
    },
    "opened_opportunity_replay": {
        "label": "Opened Opportunity Replay",
        "feature": "Replay Lab",
        "personas": ["Trader", "Researcher"],
        "decision": True,
        "evidenceSource": "opportunity_replay",
    },
    "viewed_receipt": {
        "label": "Viewed Receipt",
        "feature": "Receipts",
        "personas": ["Project Founder", "Researcher"],
        "decision": True,
        "evidenceSource": "receipt",
    },
    "opened_daily_report": {
        "label": "Opened Daily Report",
        "feature": "Reports",
        "personas": ["Project Founder", "Researcher", "Builder"],
        "decision": True,
        "evidenceSource": "daily_report",
    },
    "requested_scan": {
        "label": "Requested Scan",
        "feature": "Market Scans",
        "personas": ["Trader", "Project Founder", "Liquidity Provider"],
        "decision": True,
        "evidenceSource": "scan_request",
    },
    "generated_simulation": {
        "label": "Generated Simulation",
        "feature": "Route Simulation",
        "personas": ["Trader", "Builder"],
        "decision": True,
        "evidenceSource": "simulation",
    },
    "viewed_project_page": {
        "label": "Viewed Project Page",
        "feature": "Project Pages",
        "personas": ["Project Founder", "Liquidity Provider"],
        "decision": True,
        "evidenceSource": "project_page",
    },
    "created_alert": {
        "label": "Created Alert",
        "feature": "Alerts",
        "personas": ["Trader", "Project Founder", "Liquidity Provider", "Builder"],
        "decision": True,
        "evidenceSource": "alert",
    },
    "exported_data": {
        "label": "Exported Data",
        "feature": "API / Exports",
        "personas": ["Builder", "Researcher"],
        "decision": True,
        "evidenceSource": "export",
    },
}

FEATURE_CATALOG = [
    "Market Pulse",
    "Route Intelligence",
    "Route Forensics",
    "Liquidity Health",
    "Replay Lab",
    "Reports",
    "Receipts",
    "Alerts",
    "API / Exports",
    "Market Scans",
    "Route Simulation",
    "Project Pages",
]

PERSONAS = ["Trader", "Builder", "Project Founder", "Liquidity Provider", "Researcher"]

FUNNEL_STEPS = [
    ("guest", "Guest"),
    ("connected_user", "Connected User"),
    ("pnet_user", "PNET User"),
    ("report_user", "Report User"),
    ("repeat_user", "Repeat User"),
]


def is_decision_action(action_type: str) -> bool:
    return bool(ACTION_TAXONOMY.get(action_type, {}).get("decision"))


def default_evidence_source(action_type: str) -> str:
    return str(ACTION_TAXONOMY.get(action_type, {}).get("evidenceSource") or action_type)


def build_product_validation_report(
    user_actions: list[dict[str, Any]],
    decision_events: list[dict[str, Any]],
    *,
    now: float | None = None,
    window_days: int = 30,
) -> dict[str, Any]:
    observed_at = float(now or time.time())
    window_seconds = max(1, int(window_days) * 86_400)
    window_start = observed_at - window_seconds
    actions = [_normalize_action(row) for row in user_actions if _number(row.get("timestamp")) >= window_start]
    decisions = [_normalize_decision(row) for row in decision_events if _number(row.get("created_at")) >= window_start]
    sessions = _session_groups(actions)
    repeat_sessions = {
        session_id
        for session_id, rows in sessions.items()
        if len({_day_bucket(item["timestamp"]) for item in rows}) >= 2
    }

    return {
        "source": "stored" if actions or decisions else "unavailable",
        "windowDays": int(window_days),
        "generatedAt": observed_at,
        "summary": {
            "totalActions": len(actions),
            "activeUsers": len(sessions),
            "repeatUsers": len(repeat_sessions),
            "repeatRate": _ratio(len(repeat_sessions), len(sessions)),
            "decisionCount": len(decisions),
            "decisionRate": _ratio(len(decisions), len(actions)),
            "topPhase1Recommendation": _phase_one_recommendation(actions, decisions),
        },
        "actionTaxonomy": _taxonomy_payload(),
        "funnel": _funnel(actions, sessions, repeat_sessions),
        "personas": _persona_validation(actions, decisions, sessions, repeat_sessions),
        "featureUtility": _feature_utility(actions, decisions, sessions, repeat_sessions),
        "deadFeatures": _dead_feature_detector(actions, decisions, observed_at),
        "whyUsersReturn": _why_users_return(actions, decisions, sessions, repeat_sessions),
        "decisionRules": {
            "metricName": "Daily Evidence-Backed Decisions",
            "includedActions": sorted(action for action in ACTION_TAXONOMY if is_decision_action(action)),
            "excludedExamples": ["page_load", "scroll", "idle_time"],
            "definition": "A decision is recorded only when a user interacts with evidence such as route details, reports, replay, exports, scans, alerts, receipts, or liquidity health.",
        },
        "liveExecutionTouched": False,
        "signerCodeTouched": False,
    }


def _taxonomy_payload() -> list[dict[str, Any]]:
    return [
        {
            "actionType": action_type,
            "label": config["label"],
            "feature": config["feature"],
            "personas": config["personas"],
            "decisionEligible": bool(config["decision"]),
            "evidenceSource": config["evidenceSource"],
        }
        for action_type, config in ACTION_TAXONOMY.items()
    ]


def _funnel(
    actions: list[dict[str, Any]],
    sessions: dict[str, list[dict[str, Any]]],
    repeat_sessions: set[str],
) -> list[dict[str, Any]]:
    session_ids = set(sessions)
    step_sessions = {
        "guest": {session_id for session_id, rows in sessions.items() if any(item["userRole"] == "guest" for item in rows)},
        "connected_user": {
            session_id for session_id, rows in sessions.items() if any(item["walletConnected"] for item in rows)
        },
        "pnet_user": {
            session_id for session_id, rows in sessions.items() if any(_is_pnet_user(item) for item in rows)
        },
        "report_user": {
            session_id
            for session_id, rows in sessions.items()
            if any(item["actionType"] in {"opened_daily_report", "exported_data"} for item in rows)
        },
        "repeat_user": repeat_sessions,
    }
    total_sessions = max(1, len(session_ids))
    result = []
    for key, label in FUNNEL_STEPS:
        count = len(step_sessions[key])
        result.append(
            {
                "key": key,
                "label": label,
                "users": count,
                "conversionRate": _ratio(count, total_sessions),
                "dropOff": max(0, total_sessions - count),
                "source": "stored" if actions else "unavailable",
            }
        )
    return result


def _persona_validation(
    actions: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    sessions: dict[str, list[dict[str, Any]]],
    repeat_sessions: set[str],
) -> list[dict[str, Any]]:
    result = []
    for persona in PERSONAS:
        persona_actions = [item for item in actions if persona in _personas_for_action(item["actionType"], item["metadata"])]
        persona_sessions = {item["sessionId"] for item in persona_actions}
        persona_decisions = [
            item
            for item in decisions
            if persona in _personas_for_action(item["actionType"], _metadata(item.get("metadata_json")))
        ]
        result.append(
            {
                "persona": persona,
                "activeUsers": len(persona_sessions),
                "topActions": _top_counts([item["actionType"] for item in persona_actions], limit=5),
                "repeatRate": _ratio(len(persona_sessions & repeat_sessions), len(persona_sessions)),
                "averageSessionDepth": _average(
                    [
                        sum(1 for item in rows if persona in _personas_for_action(item["actionType"], item["metadata"]))
                        for session_id, rows in sessions.items()
                        if session_id in persona_sessions
                    ]
                ),
                "evidenceBackedDecisions": len(persona_decisions),
                "source": "stored" if persona_actions or persona_decisions else "unavailable",
            }
        )
    result.sort(key=lambda item: (-item["evidenceBackedDecisions"], -item["activeUsers"], item["persona"]))
    return result


def _feature_utility(
    actions: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    sessions: dict[str, list[dict[str, Any]]],
    repeat_sessions: set[str],
) -> list[dict[str, Any]]:
    total_sessions = len(sessions)
    total_decisions = len(decisions)
    decision_by_feature = Counter(_feature_for_action(item["actionType"]) for item in decisions)
    rows = []
    for feature in FEATURE_CATALOG:
        feature_actions = [item for item in actions if _feature_for_action(item["actionType"]) == feature]
        feature_sessions = {item["sessionId"] for item in feature_actions}
        rows.append(
            {
                "feature": feature,
                "opens": len(feature_actions),
                "repeatOpens": sum(1 for item in feature_actions if item["sessionId"] in repeat_sessions),
                "sessionContribution": _ratio(len(feature_sessions), total_sessions),
                "decisionContribution": _ratio(decision_by_feature[feature], total_decisions),
                "decisionCount": decision_by_feature[feature],
                "source": "stored" if feature_actions or decision_by_feature[feature] else "unavailable",
            }
        )
    rows.sort(key=lambda item: (-item["decisionContribution"], -item["opens"], item["feature"]))
    return rows


def _dead_feature_detector(
    actions: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    observed_at: float,
) -> list[dict[str, Any]]:
    decision_by_feature = Counter(_feature_for_action(item["actionType"]) for item in decisions)
    rows = []
    for feature in FEATURE_CATALOG:
        feature_actions = [item for item in actions if _feature_for_action(item["actionType"]) == feature]
        last_used = max([item["timestamp"] for item in feature_actions], default=None)
        monthly_activity = len(feature_actions)
        decision_count = decision_by_feature[feature]
        days_since_use = None if last_used is None else max(0, int((observed_at - last_used) // 86_400))
        if monthly_activity == 0:
            recommendation = "investigate"
        elif days_since_use is not None and days_since_use >= 30 and decision_count == 0:
            recommendation = "remove"
        elif monthly_activity < 3 or decision_count == 0:
            recommendation = "improve"
        else:
            recommendation = "keep"
        rows.append(
            {
                "feature": feature,
                "daysSinceUse": days_since_use,
                "monthlyActivity": monthly_activity,
                "decisionCount": decision_count,
                "recommendation": recommendation,
                "source": "stored" if feature_actions else "unavailable",
            }
        )
    rows.sort(key=lambda item: (item["recommendation"] != "investigate", item["monthlyActivity"], item["feature"]))
    return rows


def _why_users_return(
    actions: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    sessions: dict[str, list[dict[str, Any]]],
    repeat_sessions: set[str],
) -> dict[str, Any]:
    page_counter = Counter(item["page"] for item in decisions if item["page"])
    persona_counter = Counter()
    for item in decisions:
        for persona in _personas_for_action(item["actionType"], _metadata(item.get("metadata_json"))):
            persona_counter[persona] += 1
    return {
        "topActions": _top_counts([item["actionType"] for item in actions], limit=6),
        "topPersonas": [{"label": key, "count": value} for key, value in persona_counter.most_common(5)],
        "mostValuablePages": [{"label": key, "count": value} for key, value in page_counter.most_common(6)],
        "repeatUserMetrics": {
            "activeUsers": len(sessions),
            "repeatUsers": len(repeat_sessions),
            "repeatRate": _ratio(len(repeat_sessions), len(sessions)),
        },
        "decisionMetrics": {
            "decisionCount": len(decisions),
            "decisionsPerActiveUser": _ratio(len(decisions), len(sessions)),
            "dailyEvidenceBackedDecisions": _daily_decision_counts(decisions),
        },
    }


def _phase_one_recommendation(actions: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> str:
    if not actions and not decisions:
        return "Collect product-validation events before choosing Phase 1 priorities."
    feature_counts = Counter(_feature_for_action(item["actionType"]) for item in decisions)
    if feature_counts:
        feature, count = feature_counts.most_common(1)[0]
        return f"Prioritize Phase 1 around {feature}; it generated {count} evidence-backed decisions in this window."
    action_counts = Counter(item["actionType"] for item in actions)
    action, count = action_counts.most_common(1)[0]
    return f"Improve the {ACTION_TAXONOMY.get(action, {}).get('feature', action)} path; it has {count} actions but no decision contribution yet."


def _normalize_action(row: dict[str, Any]) -> dict[str, Any]:
    metadata = _metadata(row.get("metadata_json") or row.get("metadata"))
    action_type = str(row.get("action_type") or row.get("actionType") or "unknown")
    return {
        "id": row.get("id"),
        "actionType": action_type,
        "timestamp": _number(row.get("timestamp") or row.get("created_at")),
        "userRole": str(row.get("user_role") or row.get("userRole") or "guest"),
        "walletConnected": bool(row.get("wallet_connected") or row.get("walletConnected")),
        "page": str(row.get("source_page") or row.get("page") or "unknown"),
        "metadata": metadata,
        "sessionId": str(metadata.get("session_id") or metadata.get("sessionId") or f"anonymous:{row.get('id', 'unknown')}"),
    }


def _normalize_decision(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "actionType": str(row.get("action_type") or row.get("actionType") or "unknown"),
        "page": str(row.get("page") or row.get("source_page") or "unknown"),
        "created_at": _number(row.get("created_at")),
    }


def _session_groups(actions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for action in actions:
        grouped[action["sessionId"]].append(action)
    return grouped


def _top_counts(values: list[str], limit: int = 5) -> list[dict[str, Any]]:
    return [{"label": key, "count": value} for key, value in Counter(values).most_common(limit)]


def _daily_decision_counts(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter = Counter(_day_bucket(item["created_at"]) for item in decisions)
    return [{"date": key, "count": value} for key, value in sorted(counter.items())[-14:]]


def _personas_for_action(action_type: str, metadata: dict[str, Any] | None = None) -> list[str]:
    metadata = metadata or {}
    hinted = metadata.get("persona") or metadata.get("persona_hint") or metadata.get("personaHint")
    if hinted:
        value = str(hinted)
        return [value] if value in PERSONAS else []
    return list(ACTION_TAXONOMY.get(action_type, {}).get("personas") or [])


def _feature_for_action(action_type: str) -> str:
    return str(ACTION_TAXONOMY.get(action_type, {}).get("feature") or "Unmapped")


def _is_pnet_user(action: dict[str, Any]) -> bool:
    metadata = action["metadata"]
    return bool(
        metadata.get("pnet_user")
        or metadata.get("pnetUser")
        or metadata.get("opted_in")
        or metadata.get("optedIn")
        or _number(metadata.get("pnet_balance") or metadata.get("pnetBalance")) > 0
        or _number(metadata.get("credits")) > 0
    )


def _metadata(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _day_bucket(timestamp: float) -> str:
    return datetime.fromtimestamp(max(0.0, float(timestamp)), tz=timezone.utc).strftime("%Y-%m-%d")


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _ratio(numerator: int | float, denominator: int | float) -> float:
    denominator = float(denominator or 0)
    if denominator <= 0:
        return 0.0
    return float(numerator) / denominator
