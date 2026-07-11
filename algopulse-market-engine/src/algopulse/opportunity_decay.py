from __future__ import annotations

import json
import time
from collections import defaultdict
from statistics import median
from typing import Any


DECAY_VIEWS = {
    "1h": {"seconds": 3_600, "bucketCount": 12},
    "24h": {"seconds": 86_400, "bucketCount": 24},
    "7d": {"seconds": 604_800, "bucketCount": 14},
}


def build_opportunity_decay_report(
    decay_rows: list[dict[str, Any]],
    *,
    view: str = "24h",
    now: float | None = None,
) -> dict[str, Any]:
    selected_view = view if view in DECAY_VIEWS else "24h"
    observed_at = float(now or time.time())
    config = DECAY_VIEWS[selected_view]
    window_seconds = int(config["seconds"])
    bucket_count = int(config["bucketCount"])
    bucket_seconds = max(1, window_seconds // bucket_count)
    start_at = observed_at - window_seconds

    records = [
        _decay_record(row)
        for row in decay_rows
        if start_at <= _number(row.get("detected_at") or row.get("created_at")) <= observed_at
    ]
    records.sort(key=lambda item: item["detectedAt"], reverse=True)

    return {
        "view": selected_view,
        "views": list(DECAY_VIEWS),
        "windowSeconds": window_seconds,
        "bucketSeconds": bucket_seconds,
        "generatedAt": observed_at,
        "summary": _summary(records),
        "timeline": _timeline(records, start_at, bucket_seconds, bucket_count, selected_view),
        "byPair": _group_summary(records, "pairLabel"),
        "byVenue": _group_venues(records),
        "byRouteType": _group_summary(records, "routeType"),
        "records": records[:25],
        "source": "stored" if records else "unavailable",
        "liveExecutionTouched": False,
        "signerCodeTouched": False,
    }


def _decay_record(row: dict[str, Any]) -> dict[str, Any]:
    initial_profit = _number(row.get("expected_profit") if row.get("expected_profit") is not None else row.get("expected_net_profit"))
    points = _profit_points(row, initial_profit)
    half_life, crossed = _half_life(points, initial_profit)
    latest_time, latest_profit = points[-1]
    profit_5s = _optional_number(row.get("expected_profit_5s"))
    profit_30s = _optional_number(row.get("expected_profit_30s"))
    profit_60s = _optional_number(row.get("expected_profit_60s"))
    quote_decay_5s = _optional_number(row.get("quote_decay_5s"))
    quote_decay_30s = _optional_number(row.get("quote_decay_30s"))
    quote_decay_60s = _optional_number(row.get("quote_decay_60s"))
    survived_5s = _survived(profit_5s)
    survived_30s = _survived(profit_30s)
    survived_60s = _survived(profit_60s)
    final_outcome, reason = _final_outcome(
        initial_profit=initial_profit,
        profit_5s=profit_5s,
        profit_30s=profit_30s,
        profit_60s=profit_60s,
    )
    return {
        "id": row.get("id"),
        "detectedAt": _number(row.get("detected_at") or row.get("created_at")),
        "routeHash": row.get("route_hash"),
        "pairKey": str(row.get("pair_key") or _pair_from_route(row).get("key") or "unknown"),
        "pairLabel": str(row.get("pair_label") or _pair_from_route(row).get("label") or "Unknown"),
        "pair": str(row.get("pair_label") or _pair_from_route(row).get("label") or "Unknown"),
        "venues": _venues(row),
        "routeType": str(row.get("route_type") or _route_type(row)),
        "expectedProfit": initial_profit,
        "expectedProfitAtT0": initial_profit,
        "expectedProfit5s": profit_5s,
        "expectedProfit30s": profit_30s,
        "expectedProfit60s": profit_60s,
        "simulatedProfitAtT5": profit_5s,
        "simulatedProfitAtT30": profit_30s,
        "simulatedProfitAtT60": profit_60s,
        "quoteDecayT5": quote_decay_5s,
        "quoteDecayT30": quote_decay_30s,
        "quoteDecayT60": quote_decay_60s,
        "survivedT5": survived_5s,
        "survivedT30": survived_30s,
        "survivedT60": survived_60s,
        "finalOutcome": final_outcome,
        "reason": reason,
        "halfLifeSeconds": half_life,
        "halfLifeObserved": crossed,
        "latestObservedSeconds": latest_time,
        "latestProfit": latest_profit,
        "profitRetainedRatio": 0.0 if initial_profit <= 0 else latest_profit / initial_profit,
        "decayRatio": 0.0 if initial_profit <= 0 else max(0.0, (initial_profit - latest_profit) / initial_profit),
        "actionable": latest_profit > 0,
        "source": str(row.get("source") or "stored"),
    }


def _profit_points(row: dict[str, Any], initial_profit: float) -> list[tuple[float, float]]:
    points = [(0.0, initial_profit)]
    for seconds, key in ((5.0, "expected_profit_5s"), (30.0, "expected_profit_30s"), (60.0, "expected_profit_60s")):
        value = row.get(key)
        if value is not None:
            points.append((seconds, _number(value)))
    return points


def _half_life(points: list[tuple[float, float]], initial_profit: float) -> tuple[float, bool]:
    if initial_profit <= 0:
        return 0.0, True
    threshold = initial_profit / 2
    previous_time, previous_profit = points[0]
    if previous_profit <= threshold:
        return 0.0, True
    for current_time, current_profit in points[1:]:
        if current_profit <= threshold:
            if previous_profit == current_profit:
                return current_time, True
            progress = (threshold - previous_profit) / (current_profit - previous_profit)
            estimated = previous_time + ((current_time - previous_time) * progress)
            return max(previous_time, min(current_time, estimated)), True
        previous_time, previous_profit = current_time, current_profit
    return points[-1][0], False


def _summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    half_lives = [float(item["halfLifeSeconds"]) for item in records]
    fastest = min(records, key=lambda item: item["halfLifeSeconds"], default=None)
    slowest = max(records, key=lambda item: item["halfLifeSeconds"], default=None)
    pair_survival = _pair_survival_summaries(records)
    resolved_pair_survival = [item for item in pair_survival if item["resolvedT30Count"] > 0]
    non_survival_reasons = [
        str(item["reason"])
        for item in records
        if item["finalOutcome"] != "survived" and item.get("reason")
    ]
    return {
        "opportunityCount": len(records),
        "totalOpportunities": len(records),
        "resolvedCount": sum(1 for item in records if item["latestObservedSeconds"] > 0),
        "observedHalfLifeCount": sum(1 for item in records if item["halfLifeObserved"]),
        "resolved60sCount": sum(1 for item in records if item["expectedProfit60s"] is not None),
        "survivedT5Count": sum(1 for item in records if item["survivedT5"] is True),
        "survivedT30Count": sum(1 for item in records if item["survivedT30"] is True),
        "survivedT60Count": sum(1 for item in records if item["survivedT60"] is True),
        "fadedCount": sum(1 for item in records if item["finalOutcome"] == "faded"),
        "rejectedCount": sum(1 for item in records if item["finalOutcome"] == "rejected"),
        "unknownCount": sum(1 for item in records if item["finalOutcome"] == "unknown"),
        "averageDecayT5": _average([item["quoteDecayT5"] for item in records if item["quoteDecayT5"] is not None]),
        "averageDecayT30": _average([item["quoteDecayT30"] for item in records if item["quoteDecayT30"] is not None]),
        "averageHalfLifeSeconds": _average(half_lives),
        "medianHalfLifeSeconds": median(half_lives) if half_lives else 0.0,
        "fastestDecay": _decay_summary(fastest),
        "slowestDecay": _decay_summary(slowest),
        "actionableCount": sum(1 for item in records if item["actionable"]),
        "averageDecayRatio": _average([float(item["decayRatio"]) for item in records]),
        "bestPairBySurvival": resolved_pair_survival[0] if resolved_pair_survival else None,
        "worstPairBySurvival": resolved_pair_survival[-1] if resolved_pair_survival else None,
        "mostCommonFadeReason": _most_common_reason(non_survival_reasons),
    }


def _timeline(records: list[dict[str, Any]], start_at: float, bucket_seconds: int, bucket_count: int, view: str) -> list[dict[str, Any]]:
    buckets = [
        {
            "index": index,
            "startAt": start_at + (index * bucket_seconds),
            "endAt": start_at + ((index + 1) * bucket_seconds),
            "label": _bucket_label(start_at + (index * bucket_seconds), view),
            "records": [],
        }
        for index in range(bucket_count)
    ]
    for record in records:
        index = min(bucket_count - 1, max(0, int((record["detectedAt"] - start_at) // bucket_seconds)))
        buckets[index]["records"].append(record)
    return [
        {
            "index": item["index"],
            "startAt": item["startAt"],
            "endAt": item["endAt"],
            "label": item["label"],
            "opportunityCount": len(item["records"]),
            "averageHalfLifeSeconds": _average([record["halfLifeSeconds"] for record in item["records"]]),
            "medianHalfLifeSeconds": median([record["halfLifeSeconds"] for record in item["records"]]) if item["records"] else 0.0,
            "averageDecayRatio": _average([record["decayRatio"] for record in item["records"]]),
        }
        for item in buckets
    ]


def _group_summary(records: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record.get(key) or "Unknown")].append(record)
    summaries = [_records_summary(label, items) for label, items in grouped.items()]
    summaries.sort(key=lambda item: (-item["opportunityCount"], item["label"]))
    return summaries[:12]


def _group_venues(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        for venue in record["venues"] or ["unknown"]:
            grouped[str(venue)].append(record)
    summaries = [_records_summary(label, items) for label, items in grouped.items()]
    summaries.sort(key=lambda item: (-item["opportunityCount"], item["label"]))
    return summaries[:12]


def _records_summary(label: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    half_lives = [float(item["halfLifeSeconds"]) for item in records]
    resolved_t30 = [item for item in records if item["survivedT30"] is not None]
    return {
        "label": label,
        "opportunityCount": len(records),
        "survivedT30Count": sum(1 for item in records if item["survivedT30"] is True),
        "fadedCount": sum(1 for item in records if item["finalOutcome"] == "faded"),
        "survivalRateT30": (
            0.0
            if not resolved_t30
            else sum(1 for item in resolved_t30 if item["survivedT30"] is True) / len(resolved_t30)
        ),
        "averageHalfLifeSeconds": _average(half_lives),
        "medianHalfLifeSeconds": median(half_lives) if half_lives else 0.0,
        "fastestHalfLifeSeconds": min(half_lives, default=0.0),
        "slowestHalfLifeSeconds": max(half_lives, default=0.0),
        "averageDecayRatio": _average([float(item["decayRatio"]) for item in records]),
        "actionableCount": sum(1 for item in records if item["actionable"]),
    }


def _decay_summary(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if record is None:
        return None
    return {
        "routeHash": record["routeHash"],
        "pairLabel": record["pairLabel"],
        "routeType": record["routeType"],
        "halfLifeSeconds": record["halfLifeSeconds"],
        "expectedProfit": record["expectedProfit"],
        "latestProfit": record["latestProfit"],
    }


def _pair_from_route(row: dict[str, Any]) -> dict[str, str]:
    route = _route(row)
    if not route:
        return {"key": "unknown", "label": "Unknown"}
    first = route[0] or {}
    left = _int_or_none(first.get("input_asset_id"))
    right = _int_or_none(first.get("output_asset_id"))
    if left is None or right is None:
        return {"key": "unknown", "label": "Unknown"}
    ordered = sorted({left, right})
    return {"key": "-".join(str(item) for item in ordered), "label": "/".join(str(item) for item in ordered)}


def _venues(row: dict[str, Any]) -> list[str]:
    raw = row.get("venues_json")
    if raw:
        try:
            venues = json.loads(str(raw))
            if isinstance(venues, list):
                return [str(item) for item in venues]
        except json.JSONDecodeError:
            pass
    venues = []
    for leg in _route(row):
        venue = str(leg.get("venue") or leg.get("venue_id") or "unknown")
        if venue not in venues:
            venues.append(venue)
    return venues or ["unknown"]


def _route_type(row: dict[str, Any]) -> str:
    route = _route(row)
    venues = _venues(row)
    if len(route) >= 3:
        return "triangle"
    if len(set(venues)) >= 2:
        return "venue_arbitrage"
    return "single_venue"


def _route(row: dict[str, Any]) -> list[dict[str, Any]]:
    route = row.get("route")
    if isinstance(route, list):
        return route
    raw = row.get("route_json")
    if not raw:
        return []
    try:
        parsed = json.loads(str(raw))
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _bucket_label(bucket_start: float, view: str) -> str:
    bucket_start = max(0.0, bucket_start)
    if view == "7d":
        return time.strftime("%m-%d", time.gmtime(bucket_start))
    return time.strftime("%H:%M", time.gmtime(bucket_start))


def _optional_number(value: Any) -> float | None:
    return None if value is None else _number(value)


def _survived(value: float | None) -> bool | None:
    return None if value is None else value > 0


def _final_outcome(
    *,
    initial_profit: float,
    profit_5s: float | None,
    profit_30s: float | None,
    profit_60s: float | None,
) -> tuple[str, str]:
    if initial_profit <= 0:
        return "rejected", "expected_profit_not_positive"
    if profit_30s is None:
        return "unknown", "missing_t30_evidence"
    if profit_30s <= 0:
        return "faded", "faded_by_t30"
    if profit_60s is not None and profit_60s <= 0:
        return "faded", "faded_by_t60"
    return "survived", "survived_t30"


def _pair_survival_summaries(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record.get("pairLabel") or "Unknown")].append(record)
    summaries = []
    for label, items in grouped.items():
        resolved = [item for item in items if item["survivedT30"] is not None]
        survival_rate = (
            0.0
            if not resolved
            else sum(1 for item in resolved if item["survivedT30"] is True) / len(resolved)
        )
        summaries.append(
            {
                "pair": label,
                "label": label,
                "totalOpportunities": len(items),
                "resolvedT30Count": len(resolved),
                "survivedT30Count": sum(1 for item in resolved if item["survivedT30"] is True),
                "fadedCount": sum(1 for item in items if item["finalOutcome"] == "faded"),
                "survivalRateT30": survival_rate,
            }
        )
    summaries.sort(key=lambda item: (-item["survivalRateT30"], -item["resolvedT30Count"], item["label"]))
    return summaries


def _most_common_reason(reasons: list[str]) -> dict[str, Any] | None:
    if not reasons:
        return None
    counts: dict[str, int] = defaultdict(int)
    for reason in reasons:
        counts[reason] += 1
    reason, count = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0]
    return {"reason": reason, "count": count}


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _int_or_none(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
