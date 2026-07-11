from __future__ import annotations

import math
import time
from collections import defaultdict
from typing import Any


HEATMAP_VIEWS = {
    "1h": {"seconds": 3_600, "bucketCount": 12},
    "6h": {"seconds": 21_600, "bucketCount": 12},
    "24h": {"seconds": 86_400, "bucketCount": 24},
    "7d": {"seconds": 604_800, "bucketCount": 14},
}


def build_market_pulse_heatmap(
    opportunities: list[dict[str, Any]],
    paper_trades: list[dict[str, Any]],
    *,
    view: str = "24h",
    now: float | None = None,
) -> dict[str, Any]:
    selected_view = view if view in HEATMAP_VIEWS else "24h"
    observed_at = float(now or time.time())
    config = HEATMAP_VIEWS[selected_view]
    window_seconds = int(config["seconds"])
    bucket_count = int(config["bucketCount"])
    bucket_seconds = max(1, window_seconds // bucket_count)
    start_at = observed_at - window_seconds
    bucket_starts = [start_at + (index * bucket_seconds) for index in range(bucket_count)]
    paper_by_route = _paper_by_route(paper_trades)
    aggregates: dict[tuple[str, str, int], dict[str, Any]] = {}

    for opportunity in opportunities:
        created_at = _number(opportunity.get("created_at"))
        if created_at < start_at or created_at > observed_at:
            continue
        route = opportunity.get("route") or []
        if not isinstance(route, list):
            route = []
        pair = _pair_from_route(route, opportunity)
        venues = _venues_from_route(route)
        bucket_index = min(bucket_count - 1, max(0, int((created_at - start_at) // bucket_seconds)))
        bucket_start = bucket_starts[bucket_index]
        route_paper = paper_by_route.get(str(opportunity.get("route_hash") or ""), [])
        paper_stats = _paper_stats(route_paper)
        half_life = _opportunity_half_life(route, route_paper)

        for venue in venues:
            key = (pair["key"], venue, bucket_index)
            if key not in aggregates:
                aggregates[key] = _empty_aggregate(pair, venue, bucket_index, bucket_start, bucket_seconds)
            _add_opportunity(aggregates[key], opportunity, route, half_life, paper_stats)

    cells = [_finalize_cell(item) for item in aggregates.values()]
    max_density = max((cell["opportunityCount"] for cell in cells), default=0)
    for cell in cells:
        cell["intensity"] = 0.0 if max_density <= 0 else cell["opportunityCount"] / max_density
        cell["densityLabel"] = _density_label(cell["intensity"])

    cells.sort(key=lambda item: (-item["opportunityCount"], item["pairLabel"], item["venue"], item["bucketIndex"]))
    pair_summaries = _summaries(cells, "pairKey", "pairLabel")
    venue_summaries = _summaries(cells, "venue", "venue")
    time_buckets = [
        {
            "index": index,
            "startAt": bucket_start,
            "endAt": bucket_start + bucket_seconds,
            "label": _bucket_label(bucket_start, bucket_seconds, selected_view),
        }
        for index, bucket_start in enumerate(bucket_starts)
    ]
    totals = _totals(cells)
    return {
        "view": selected_view,
        "views": list(HEATMAP_VIEWS),
        "windowSeconds": window_seconds,
        "bucketSeconds": bucket_seconds,
        "generatedAt": observed_at,
        "timeBuckets": time_buckets,
        "cells": cells,
        "pairSummaries": pair_summaries,
        "venueSummaries": venue_summaries,
        "totals": totals,
        "source": "stored" if cells else "unavailable",
        "liveExecutionTouched": False,
        "signerCodeTouched": False,
    }


def _empty_aggregate(pair: dict[str, Any], venue: str, bucket_index: int, bucket_start: float, bucket_seconds: int) -> dict:
    return {
        "pairKey": pair["key"],
        "pairLabel": pair["label"],
        "assetIds": pair["assetIds"],
        "venue": venue,
        "bucketIndex": bucket_index,
        "bucketStart": bucket_start,
        "bucketEnd": bucket_start + bucket_seconds,
        "bucketSeconds": bucket_seconds,
        "opportunityCount": 0,
        "spreadCount": 0,
        "spreadBpsTotal": 0.0,
        "routeLegTotal": 0.0,
        "halfLifeTotal": 0.0,
        "paperCount": 0,
        "paperWinCount": 0,
        "paperExpectedTotal": 0.0,
        "paperSimulated30sTotal": 0.0,
        "paperQuoteDecayTotal": 0.0,
    }


def _add_opportunity(
    aggregate: dict[str, Any],
    opportunity: dict[str, Any],
    route: list[dict[str, Any]],
    half_life: float,
    paper_stats: dict[str, Any],
) -> None:
    spread_bps = _number(opportunity.get("expected_profit_bps"))
    expected_net = _number(opportunity.get("expected_net_profit"))
    aggregate["opportunityCount"] += 1
    aggregate["spreadBpsTotal"] += spread_bps
    aggregate["routeLegTotal"] += max(1, len(route))
    aggregate["halfLifeTotal"] += half_life
    if spread_bps > 0 or expected_net > 0:
        aggregate["spreadCount"] += 1
    aggregate["paperCount"] += paper_stats["count"]
    aggregate["paperWinCount"] += paper_stats["winCount"]
    aggregate["paperExpectedTotal"] += paper_stats["expectedTotal"]
    aggregate["paperSimulated30sTotal"] += paper_stats["simulated30sTotal"]
    aggregate["paperQuoteDecayTotal"] += paper_stats["quoteDecayTotal"]


def _finalize_cell(aggregate: dict[str, Any]) -> dict[str, Any]:
    count = max(1, int(aggregate["opportunityCount"]))
    bucket_hours = max(aggregate["bucketSeconds"] / 3_600, 1 / 60)
    paper_count = int(aggregate["paperCount"])
    paper_performance = {
        "count": paper_count,
        "winRate": 0.0 if paper_count <= 0 else aggregate["paperWinCount"] / paper_count,
        "averageExpectedNet": _safe_average(aggregate["paperExpectedTotal"], paper_count),
        "averageSimulated30s": _safe_average(aggregate["paperSimulated30sTotal"], paper_count),
        "averageQuoteDecay30s": _safe_average(aggregate["paperQuoteDecayTotal"], paper_count),
    }
    return {
        "pairKey": aggregate["pairKey"],
        "pairLabel": aggregate["pairLabel"],
        "assetIds": aggregate["assetIds"],
        "venue": aggregate["venue"],
        "bucketIndex": aggregate["bucketIndex"],
        "bucketStart": aggregate["bucketStart"],
        "bucketEnd": aggregate["bucketEnd"],
        "opportunityCount": int(aggregate["opportunityCount"]),
        "opportunityDensity": aggregate["opportunityCount"] / bucket_hours,
        "spreadFrequency": aggregate["spreadCount"] / bucket_hours,
        "averageSpreadBps": aggregate["spreadBpsTotal"] / count,
        "averageRouteCount": aggregate["routeLegTotal"] / count,
        "opportunityHalfLifeSeconds": aggregate["halfLifeTotal"] / count,
        "paperTradePerformance": paper_performance,
        "source": "stored",
    }


def _summaries(cells: list[dict[str, Any]], key_field: str, label_field: str) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for cell in cells:
        key = str(cell[key_field])
        if key not in grouped:
            grouped[key] = {
                "key": key,
                "label": str(cell[label_field]),
                "opportunityCount": 0,
                "spreadBpsTotal": 0.0,
                "paperCount": 0,
                "paperSimulated30sTotal": 0.0,
                "halfLifeTotal": 0.0,
                "cellCount": 0,
            }
        grouped[key]["opportunityCount"] += int(cell["opportunityCount"])
        grouped[key]["spreadBpsTotal"] += float(cell["averageSpreadBps"]) * int(cell["opportunityCount"])
        grouped[key]["paperCount"] += int(cell["paperTradePerformance"]["count"])
        grouped[key]["paperSimulated30sTotal"] += float(cell["paperTradePerformance"]["averageSimulated30s"]) * int(
            cell["paperTradePerformance"]["count"]
        )
        grouped[key]["halfLifeTotal"] += float(cell["opportunityHalfLifeSeconds"])
        grouped[key]["cellCount"] += 1
    summaries = []
    for item in grouped.values():
        count = max(1, int(item["opportunityCount"]))
        paper_count = int(item["paperCount"])
        summaries.append(
            {
                "key": item["key"],
                "label": item["label"],
                "opportunityCount": int(item["opportunityCount"]),
                "averageSpreadBps": item["spreadBpsTotal"] / count,
                "averageHalfLifeSeconds": item["halfLifeTotal"] / max(1, int(item["cellCount"])),
                "paperCount": paper_count,
                "averagePaperSimulated30s": _safe_average(item["paperSimulated30sTotal"], paper_count),
            }
        )
    summaries.sort(key=lambda item: (-item["opportunityCount"], item["label"]))
    return summaries[:12]


def _totals(cells: list[dict[str, Any]]) -> dict[str, Any]:
    opportunity_count = sum(int(cell["opportunityCount"]) for cell in cells)
    paper_count = sum(int(cell["paperTradePerformance"]["count"]) for cell in cells)
    paper_wins = sum(int(round(cell["paperTradePerformance"]["winRate"] * cell["paperTradePerformance"]["count"])) for cell in cells)
    spread_total = sum(float(cell["averageSpreadBps"]) * int(cell["opportunityCount"]) for cell in cells)
    half_life_total = sum(float(cell["opportunityHalfLifeSeconds"]) for cell in cells)
    return {
        "opportunityCount": opportunity_count,
        "activeCells": len(cells),
        "pairCount": len({cell["pairKey"] for cell in cells}),
        "venueCount": len({cell["venue"] for cell in cells}),
        "averageSpreadBps": _safe_average(spread_total, opportunity_count),
        "averageHalfLifeSeconds": _safe_average(half_life_total, len(cells)),
        "paperTradeCount": paper_count,
        "paperWinRate": 0.0 if paper_count <= 0 else paper_wins / paper_count,
    }


def _paper_by_route(paper_trades: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in paper_trades:
        route_hash = str(trade.get("route_hash") or trade.get("opportunity_hash") or "")
        if route_hash:
            grouped[route_hash].append(trade)
    return grouped


def _paper_stats(paper_trades: list[dict[str, Any]]) -> dict[str, Any]:
    stats = {
        "count": 0,
        "winCount": 0,
        "expectedTotal": 0.0,
        "simulated30sTotal": 0.0,
        "quoteDecayTotal": 0.0,
    }
    for trade in paper_trades:
        simulated = _number(trade.get("simulated_profit_30s"))
        stats["count"] += 1
        stats["winCount"] += 1 if simulated > 0 else 0
        stats["expectedTotal"] += _number(trade.get("expected_net_profit") or trade.get("expected_profit"))
        stats["simulated30sTotal"] += simulated
        stats["quoteDecayTotal"] += _number(trade.get("quote_decay_30s"))
    return stats


def _opportunity_half_life(route: list[dict[str, Any]], paper_trades: list[dict[str, Any]]) -> float:
    paper_lives = [_paper_half_life(trade) for trade in paper_trades]
    paper_lives = [value for value in paper_lives if value is not None]
    if paper_lives:
        return sum(paper_lives) / len(paper_lives)
    ttls = []
    for leg in route:
        captured_at = _number(leg.get("captured_at"))
        expires_at = _number(leg.get("expires_at"))
        if captured_at and expires_at and expires_at >= captured_at:
            ttls.append(expires_at - captured_at)
    if ttls:
        return sum(ttls) / len(ttls)
    return 0.0


def _paper_half_life(trade: dict[str, Any]) -> float | None:
    expected = _number(trade.get("expected_net_profit") or trade.get("expected_profit"))
    if expected <= 0:
        return 0.0
    sim_5 = trade.get("simulated_profit_5s")
    sim_30 = trade.get("simulated_profit_30s")
    ratio_5 = None if sim_5 is None else _number(sim_5) / expected
    ratio_30 = None if sim_30 is None else _number(sim_30) / expected
    if ratio_5 is not None and ratio_5 <= 0.5:
        return 5.0
    if ratio_30 is not None and ratio_30 >= 0.5:
        return 30.0
    if ratio_5 is not None and ratio_30 is not None:
        if math.isclose(ratio_5, ratio_30):
            return 30.0 if ratio_30 > 0.5 else 5.0
        slope = (ratio_30 - ratio_5) / 25.0
        if slope == 0:
            return 30.0
        estimated = 5.0 + ((0.5 - ratio_5) / slope)
        return max(5.0, min(30.0, estimated))
    return None


def _pair_from_route(route: list[dict[str, Any]], opportunity: dict[str, Any]) -> dict[str, Any]:
    if route:
        first = route[0] or {}
        left = _int_or_none(first.get("input_asset_id"))
        right = _int_or_none(first.get("output_asset_id"))
    else:
        left = _int_or_none(opportunity.get("input_asset_id"))
        involved = opportunity.get("involved_asset_ids") or []
        right = next((int(asset_id) for asset_id in involved if int(asset_id) != left), left)
    if left is None:
        left = 0
    if right is None:
        right = left
    ordered = sorted({left, right})
    key = "-".join(str(asset_id) for asset_id in ordered)
    return {"key": key, "label": "/".join(str(asset_id) for asset_id in ordered), "assetIds": ordered}


def _venues_from_route(route: list[dict[str, Any]]) -> list[str]:
    venues = []
    for leg in route:
        venue = str(leg.get("venue") or leg.get("venue_id") or "unknown")
        if venue not in venues:
            venues.append(venue)
    return venues or ["unknown"]


def _bucket_label(bucket_start: float, bucket_seconds: int, view: str) -> str:
    if view == "7d":
        return time.strftime("%m-%d %H:%M", time.gmtime(bucket_start))
    if bucket_seconds >= 3_600:
        return time.strftime("%H:%M", time.gmtime(bucket_start))
    return time.strftime("%H:%M", time.gmtime(bucket_start))


def _density_label(intensity: float) -> str:
    if intensity >= 0.75:
        return "hot"
    if intensity >= 0.4:
        return "active"
    if intensity > 0:
        return "watch"
    return "quiet"


def _safe_average(total: float, count: int) -> float:
    return 0.0 if count <= 0 else total / count


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _int_or_none(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
