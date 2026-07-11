from __future__ import annotations

import time
from collections import Counter
from collections import defaultdict
from typing import Any


MARKET_CONTEXT_TITLE = "External cached market context"
MARKET_CONTEXT_SOURCE_LABEL = "CoinMarketCap cached context"
MARKET_CONTEXT_NOTICE = (
    "External cached market context only. Informational only; not investment or trading advice."
)
MARKET_CONTEXT_SCOPE = "internal/dev/research delayed report context only"
DEFAULT_ASSET_SYMBOLS = {
    0: "ALGO",
    31566704: "USDC",
    3169177585: "PNET",
}
PNET_ASSET_ID = 3169177585


def build_daily_market_intelligence_report(
    *,
    report_date: str,
    window_start: float,
    window_end: float,
    generated_at: float | None = None,
    opportunities: list[dict[str, Any]],
    pool_snapshots: list[dict[str, Any]],
    paper_trades: list[dict[str, Any]],
    risk_decisions: list[dict[str, Any]],
    service_health: list[dict[str, Any]],
    assets: list[dict[str, Any]] | None = None,
    cached_market_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    observed_at = float(generated_at or time.time())
    symbol_map = _symbol_map(assets or [])
    opportunity_items = [_decorate_opportunity(item, symbol_map) for item in opportunities]
    liquidity_changes = _liquidity_changes(pool_snapshots, symbol_map)
    pnet_liquidity_watchlist = _pnet_liquidity_watchlist(pool_snapshots, symbol_map)
    top_pairs = _top_pairs(opportunity_items, paper_trades)
    paper_performance = _paper_trade_performance(paper_trades)
    opportunity_counts = _opportunity_counts(opportunity_items, window_start, window_end)
    route_performance = _route_performance(opportunity_items)
    scanner_health = _scanner_health(pool_snapshots, service_health)
    risk_events = _risk_events(risk_decisions, opportunity_items)
    market_summary = _market_summary(
        opportunity_items=opportunity_items,
        liquidity_changes=liquidity_changes,
        paper_performance=paper_performance,
        scanner_health=scanner_health,
        top_pairs=top_pairs,
    )
    market_context_ribbon = _market_context_ribbon(cached_market_context, observed_at=observed_at)
    source = "stored" if _has_records(opportunity_items, pool_snapshots, paper_trades, risk_decisions, service_health) else "unavailable"
    return {
        "reportDate": report_date,
        "windowStart": float(window_start),
        "windowEnd": float(window_end),
        "generatedAt": observed_at,
        "source": source,
        "publicSafe": True,
        "liveExecutionTouched": False,
        "signerCodeTouched": False,
        "marketSummary": market_summary,
        "marketContextRibbon": market_context_ribbon,
        "summary": {
            "headline": market_summary["headline"],
            "topPair": market_summary["topPair"],
            "opportunityCount": market_summary["opportunityCount"],
            "paperWinRate30s": market_summary["paperWinRate30s"],
            "scannerStatus": market_summary["scannerStatus"],
        },
        "topPairs": top_pairs,
        "pnetLiquidityWatchlist": pnet_liquidity_watchlist,
        "topSpreads": _top_spreads(opportunity_items),
        "liquidityChanges": liquidity_changes,
        "opportunityCounts": opportunity_counts,
        "routePerformance": route_performance,
        "paperTradePerformance": paper_performance,
        "scannerHealth": scanner_health,
        "riskEvents": risk_events,
        "exports": {
            "json": f"/api/reports/market/daily/export?date={report_date}&format=json",
            "markdown": f"/api/reports/market/daily/export?date={report_date}&format=markdown",
        },
    }


def render_market_intelligence_markdown(report: dict[str, Any]) -> str:
    summary = report.get("marketSummary") or {}
    counts = report.get("opportunityCounts") or {}
    paper = report.get("paperTradePerformance") or {}
    scanner = report.get("scannerHealth") or {}
    route = report.get("routePerformance") or {}
    lines = [
        f"# AlgoPulse Market Intelligence Report - {report.get('reportDate', 'unknown')}",
        "",
        "## Market Summary",
        f"- {summary.get('headline', 'No market summary available.')}",
        f"- {summary.get('narrative', 'No stored records were available for this day.')}",
        f"- Source: {report.get('source', 'unavailable')}",
        f"- Live execution touched: {str(report.get('liveExecutionTouched', False)).lower()}",
        f"- Signer code touched: {str(report.get('signerCodeTouched', False)).lower()}",
        "",
        *_market_context_markdown_lines(report.get("marketContextRibbon")),
        "",
        "## Top Pairs",
        *_table_lines(
            ["Pair", "Opportunities", "Avg spread bps", "Best spread bps", "Paper win 30s"],
            [
                [
                    item.get("pairLabel", ""),
                    item.get("opportunityCount", 0),
                    _fmt(item.get("averageSpreadBps", 0.0)),
                    _fmt(item.get("bestSpreadBps", 0.0)),
                    f"{_fmt(float(item.get('paperWinRate30s', 0.0)) * 100)}%",
                ]
                for item in report.get("topPairs", [])
            ],
        ),
        "",
        "## PNET Liquidity Watchlist",
        f"- {report.get('pnetLiquidityWatchlist', {}).get('notice', 'Informational only; not investment or trading advice.')}",
        *_table_lines(
            ["Pool", "Pair", "Venue", "PNET reserve", "Other reserve", "LP note"],
            [
                [
                    item.get("poolId", ""),
                    item.get("pairLabel", ""),
                    item.get("venue", ""),
                    _fmt(item.get("pnetReserve", 0.0)),
                    _fmt(item.get("otherReserve", 0.0)),
                    item.get("lpVisibilityNote", ""),
                ]
                for item in (report.get("pnetLiquidityWatchlist") or {}).get("pools", [])
            ],
        ),
        "",
        "## Top Spreads",
        *_table_lines(
            ["Pair", "Venues", "Spread bps", "Net", "Status", "Reason"],
            [
                [
                    item.get("pairLabel", ""),
                    item.get("venues", ""),
                    _fmt(item.get("expectedProfitBps", 0.0)),
                    _fmt(item.get("expectedNetProfit", 0.0)),
                    item.get("status", ""),
                    item.get("skipReason") or "none",
                ]
                for item in report.get("topSpreads", [])
            ],
        ),
        "",
        "## Liquidity Changes",
        *_table_lines(
            ["Pool", "Pair", "Venue", "Start", "End", "Change"],
            [
                [
                    item.get("poolId", ""),
                    item.get("pairLabel", ""),
                    item.get("venue", ""),
                    _fmt(item.get("startLiquidity", 0.0)),
                    _fmt(item.get("endLiquidity", 0.0)),
                    f"{_fmt(item.get('changePct', 0.0))}%",
                ]
                for item in report.get("liquidityChanges", [])
            ],
        ),
        "",
        "## Opportunity Counts",
        f"- Total: {counts.get('total', 0)}",
        f"- Approved: {counts.get('approved', 0)}",
        f"- Rejected: {counts.get('rejected', 0)}",
        f"- Positive expected spreads: {counts.get('positiveSpreadCount', 0)}",
        "",
        "## Route Performance",
        f"- Average route length: {_fmt(route.get('averageRouteLength', 0.0))}",
        f"- Average confidence: {_fmt(route.get('averageConfidence', 0.0))}",
        f"- Total expected net: {_fmt(route.get('totalExpectedNetProfit', 0.0))}",
        "",
        "## Paper Trade Performance",
        f"- Candidates: {paper.get('candidates', 0)}",
        f"- 30s checks: {paper.get('checked30s', 0)}",
        f"- 30s win rate: {_fmt(float(paper.get('winRate30s', 0.0)) * 100)}%",
        f"- Simulated 30s net: {_fmt(paper.get('simulatedProfit30s', 0.0))}",
        "",
        "## Scanner Health",
        f"- Status: {scanner.get('status', 'unavailable')}",
        f"- Pools scanned: {scanner.get('poolsScanned', 0)}",
        f"- Snapshots: {scanner.get('snapshotCount', 0)}",
        f"- Latest detail: {scanner.get('latestDetail') or 'none'}",
        "",
        "## Risk Events",
        *_table_lines(
            ["Reason", "Count", "Approved"],
            [
                [item.get("reason", ""), item.get("count", 0), item.get("approved", False)]
                for item in report.get("riskEvents", [])
            ],
        ),
        "",
        "_Generated from stored scanner, route, paper-trade, risk, and service-health evidence. This report is market intelligence only; it does not submit, sign, queue, or arm transactions._",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _market_context_ribbon(cached_market_context: dict[str, Any] | None, *, observed_at: float) -> dict[str, Any]:
    change_24h = _algo_24h_change(cached_market_context)
    snapshot_age = _snapshot_age_seconds(cached_market_context, observed_at=observed_at)
    availability = "available" if change_24h is not None else "unavailable"
    return {
        "title": MARKET_CONTEXT_TITLE,
        "symbol": "ALGO",
        "change24hPct": change_24h,
        "contextLabel": _algo_context_label(change_24h),
        "snapshotAgeSeconds": snapshot_age,
        "snapshotAgeLabel": _snapshot_age_label(snapshot_age),
        "sourceLabel": MARKET_CONTEXT_SOURCE_LABEL,
        "availability": availability,
        "cached": change_24h is not None,
        "external": True,
        "scope": MARKET_CONTEXT_SCOPE,
        "notice": MARKET_CONTEXT_NOTICE,
    }


def _market_context_markdown_lines(ribbon: dict[str, Any] | None) -> list[str]:
    if not isinstance(ribbon, dict):
        ribbon = _market_context_ribbon(None, observed_at=time.time())
    change = ribbon.get("change24hPct")
    change_label = "unavailable" if change is None else f"{_signed_fmt(change)}%"
    return [
        "## Market Context Ribbon",
        f"- Label: {ribbon.get('title') or MARKET_CONTEXT_TITLE}",
        f"- ALGO 24h change: {change_label}",
        f"- Context label: {ribbon.get('contextLabel') or 'unavailable'}",
        f"- Snapshot age: {ribbon.get('snapshotAgeLabel') or 'unavailable'}",
        f"- Source: {ribbon.get('sourceLabel') or MARKET_CONTEXT_SOURCE_LABEL}",
        f"- Notice: {ribbon.get('notice') or MARKET_CONTEXT_NOTICE}",
    ]


def _algo_24h_change(cached_market_context: dict[str, Any] | None) -> float | None:
    if not isinstance(cached_market_context, dict):
        return None
    direct = _first_optional_number(
        cached_market_context.get("algo24hChangePct"),
        cached_market_context.get("algo_24h_change_pct"),
        cached_market_context.get("change24hPct"),
        cached_market_context.get("percent_change_24h"),
    )
    if direct is not None:
        return direct
    algo_context = _algo_asset_context(cached_market_context.get("assets"))
    if algo_context is None:
        algo_context = _algo_asset_context(cached_market_context.get("quotes"))
    if algo_context is None:
        return None
    return _first_optional_number(
        algo_context.get("change24hPct"),
        algo_context.get("percent_change_24h"),
        algo_context.get("percentChange24h"),
        algo_context.get("change_24h_pct"),
    )


def _algo_asset_context(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).upper() == "ALGO" and isinstance(item, dict):
                return item
        for item in value.values():
            if isinstance(item, dict) and str(item.get("symbol") or "").upper() == "ALGO":
                return item
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict) and str(item.get("symbol") or "").upper() == "ALGO":
                return item
    return None


def _snapshot_age_seconds(cached_market_context: dict[str, Any] | None, *, observed_at: float) -> float | None:
    if not isinstance(cached_market_context, dict):
        return None
    direct_age = _first_optional_number(
        cached_market_context.get("snapshotAgeSeconds"),
        cached_market_context.get("snapshot_age_seconds"),
        cached_market_context.get("ageSeconds"),
        cached_market_context.get("age_seconds"),
    )
    if direct_age is not None:
        return max(0.0, direct_age)
    snapshot_at = _first_optional_number(
        cached_market_context.get("snapshotAt"),
        cached_market_context.get("snapshot_at"),
        cached_market_context.get("updatedAt"),
        cached_market_context.get("updated_at"),
    )
    if snapshot_at is None or snapshot_at <= 0:
        return None
    return max(0.0, observed_at - snapshot_at)


def _algo_context_label(change_24h: float | None) -> str:
    if change_24h is None:
        return "unavailable"
    if change_24h >= 2.0:
        return "risk-on"
    if change_24h <= -2.0:
        return "risk-off"
    return "neutral"


def _snapshot_age_label(snapshot_age_seconds: float | None) -> str:
    if snapshot_age_seconds is None:
        return "unavailable"
    if snapshot_age_seconds < 60:
        return f"{int(round(snapshot_age_seconds))}s old"
    if snapshot_age_seconds < 3_600:
        return f"{int(round(snapshot_age_seconds / 60))}m old"
    return f"{int(round(snapshot_age_seconds / 3_600))}h old"


def _first_optional_number(*values: Any) -> float | None:
    for value in values:
        if value is None or value == "":
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _decorate_opportunity(opportunity: dict[str, Any], symbol_map: dict[int, str]) -> dict[str, Any]:
    route = opportunity.get("route") or []
    if not isinstance(route, list):
        route = []
    pair_ids = _pair_ids_from_route(route, opportunity)
    venues = []
    for leg in route:
        venue = str(leg.get("venue") or leg.get("venue_id") or "")
        if venue and venue not in venues:
            venues.append(venue)
    return {
        **opportunity,
        "route": route,
        "pairIds": pair_ids,
        "pairKey": "-".join(str(item) for item in pair_ids),
        "pairLabel": _pair_label(pair_ids, symbol_map),
        "venues": venues or ["unknown"],
        "venuePath": " -> ".join(venues or ["unknown"]),
        "routeLength": max(1, len(route)),
    }


def _pair_ids_from_route(route: list[dict[str, Any]], opportunity: dict[str, Any]) -> list[int]:
    if route:
        first = route[0] or {}
        left = _int(first.get("input_asset_id"), 0)
        right = _int(first.get("output_asset_id"), left)
    else:
        involved = opportunity.get("involved_asset_ids") or []
        left = _int(opportunity.get("input_asset_id"), _int(involved[0], 0) if involved else 0)
        right = next((_int(item, left) for item in involved if _int(item, left) != left), left)
    return sorted({left, right})


def _top_pairs(opportunities: list[dict[str, Any]], paper_trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paper_by_route = defaultdict(list)
    for trade in paper_trades:
        route_hash = str(trade.get("route_hash") or trade.get("opportunity_hash") or "")
        if route_hash:
            paper_by_route[route_hash].append(trade)
    grouped: dict[str, dict[str, Any]] = {}
    for opportunity in opportunities:
        key = opportunity["pairKey"]
        item = grouped.setdefault(
            key,
            {
                "pairKey": key,
                "pairLabel": opportunity["pairLabel"],
                "opportunityCount": 0,
                "spreadBpsTotal": 0.0,
                "bestSpreadBps": None,
                "expectedNetTotal": 0.0,
                "approvedCount": 0,
                "rejectedCount": 0,
                "paperKeys": set(),
                "paperWins30s": 0,
            },
        )
        spread = _number(opportunity.get("expected_profit_bps"))
        route_hash = str(opportunity.get("route_hash") or "")
        route_paper = paper_by_route.get(route_hash, [])
        item["opportunityCount"] += 1
        item["spreadBpsTotal"] += spread
        item["bestSpreadBps"] = spread if item["bestSpreadBps"] is None else max(float(item["bestSpreadBps"]), spread)
        item["expectedNetTotal"] += _number(opportunity.get("expected_net_profit"))
        if opportunity.get("status") == "approved":
            item["approvedCount"] += 1
        else:
            item["rejectedCount"] += 1
        for trade in route_paper:
            paper_key = str(trade.get("id") or f"{route_hash}:{trade.get('created_at')}:{trade.get('expected_net_profit')}")
            if paper_key in item["paperKeys"]:
                continue
            item["paperKeys"].add(paper_key)
            if _number(trade.get("simulated_profit_30s")) > 0:
                item["paperWins30s"] += 1
    rows = []
    for item in grouped.values():
        count = max(1, int(item["opportunityCount"]))
        paper_count = len(item["paperKeys"])
        rows.append(
            {
                "pairKey": item["pairKey"],
                "pairLabel": item["pairLabel"],
                "opportunityCount": int(item["opportunityCount"]),
                "averageSpreadBps": item["spreadBpsTotal"] / count,
                "bestSpreadBps": float(item["bestSpreadBps"] or 0.0),
                "expectedNetProfit": float(item["expectedNetTotal"]),
                "approvedCount": int(item["approvedCount"]),
                "rejectedCount": int(item["rejectedCount"]),
                "paperCount": paper_count,
                "paperWinRate30s": 0.0 if paper_count <= 0 else item["paperWins30s"] / paper_count,
            }
        )
    rows.sort(key=lambda item: (-item["opportunityCount"], -item["bestSpreadBps"], item["pairLabel"]))
    return rows[:10]


def _top_spreads(opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = sorted(
        opportunities,
        key=lambda item: (_number(item.get("expected_profit_bps")), _number(item.get("expected_net_profit"))),
        reverse=True,
    )[:10]
    return [
        {
            "pairLabel": item["pairLabel"],
            "venues": item["venuePath"],
            "expectedProfitBps": _number(item.get("expected_profit_bps")),
            "expectedNetProfit": _number(item.get("expected_net_profit")),
            "grossProfit": _number(item.get("gross_profit")),
            "priceImpactBps": _number(item.get("total_price_impact_bps") or item.get("max_price_impact_bps")),
            "status": item.get("status") or "unknown",
            "skipReason": item.get("skip_reason") or "none",
            "confidenceScore": _number(item.get("confidence_score")),
            "createdAt": _number(item.get("created_at")),
        }
        for item in rows
    ]


def _liquidity_changes(pool_snapshots: list[dict[str, Any]], symbol_map: dict[int, str]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for snapshot in pool_snapshots:
        grouped[str(snapshot.get("pool_id") or "unknown")].append(snapshot)
    rows = []
    for pool_id, snapshots in grouped.items():
        ordered = sorted(snapshots, key=lambda item: _number(item.get("captured_at")))
        if not ordered:
            continue
        first = ordered[0]
        last = ordered[-1]
        start_liquidity = _number(first.get("liquidity_estimate"))
        end_liquidity = _number(last.get("liquidity_estimate"))
        change = end_liquidity - start_liquidity
        change_pct = 0.0 if start_liquidity <= 0 else (change / start_liquidity) * 100
        pair_ids = sorted({_int(last.get("asset_a_id"), 0), _int(last.get("asset_b_id"), 0)})
        rows.append(
            {
                "poolId": pool_id,
                "venue": str(last.get("venue_id") or "unknown"),
                "appId": _int(last.get("app_id"), 0),
                "pairLabel": _pair_label(pair_ids, symbol_map),
                "startLiquidity": start_liquidity,
                "endLiquidity": end_liquidity,
                "change": change,
                "changePct": change_pct,
                "snapshotCount": len(ordered),
                "firstSeenAt": _number(first.get("captured_at")),
                "lastSeenAt": _number(last.get("captured_at")),
            }
        )
    rows.sort(key=lambda item: abs(float(item["changePct"])), reverse=True)
    return rows[:10]


def _pnet_liquidity_watchlist(pool_snapshots: list[dict[str, Any]], symbol_map: dict[int, str]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for snapshot in pool_snapshots:
        asset_a = _int(snapshot.get("asset_a_id"), 0)
        asset_b = _int(snapshot.get("asset_b_id"), 0)
        if PNET_ASSET_ID not in {asset_a, asset_b}:
            continue
        grouped[str(snapshot.get("pool_id") or "unknown")].append(snapshot)

    pools = []
    for pool_id, snapshots in grouped.items():
        ordered = sorted(snapshots, key=lambda item: _number(item.get("captured_at")))
        if not ordered:
            continue
        first = ordered[0]
        last = ordered[-1]
        asset_a = _int(last.get("asset_a_id"), 0)
        asset_b = _int(last.get("asset_b_id"), 0)
        pnet_is_a = asset_a == PNET_ASSET_ID
        other_asset_id = asset_b if pnet_is_a else asset_a
        pnet_reserve = _number(last.get("reserve_a") if pnet_is_a else last.get("reserve_b"))
        other_reserve = _number(last.get("reserve_b") if pnet_is_a else last.get("reserve_a"))
        start_liquidity = _number(first.get("liquidity_estimate"))
        end_liquidity = _number(last.get("liquidity_estimate"))
        liquidity_change_pct = 0.0 if start_liquidity <= 0 else ((end_liquidity - start_liquidity) / start_liquidity) * 100
        pair_ids = sorted({PNET_ASSET_ID, int(other_asset_id or 0)})
        pools.append(
            {
                "poolId": pool_id,
                "venue": str(last.get("venue_id") or "unknown"),
                "appId": _int(last.get("app_id"), 0),
                "pairLabel": _pair_label(pair_ids, symbol_map),
                "pnetAssetId": PNET_ASSET_ID,
                "otherAssetId": int(other_asset_id or 0),
                "otherSymbol": symbol_map.get(int(other_asset_id or 0), str(other_asset_id or "unknown")),
                "pnetReserve": pnet_reserve,
                "otherReserve": other_reserve,
                "liquidityEstimate": end_liquidity,
                "liquidityChangePct": liquidity_change_pct,
                "feeBps": _int(last.get("fee_bps"), 0),
                "snapshotCount": len(ordered),
                "firstSeenAt": _number(first.get("captured_at")),
                "lastSeenAt": _number(last.get("captured_at")),
                "opportunityRequired": False,
                "lpVisibilityNote": "Observed PNET liquidity surface; LP participation has risk and needs independent review.",
            }
        )

    pools.sort(key=lambda item: (-float(item["pnetReserve"]), item["pairLabel"], item["venue"]))
    return {
        "assetId": PNET_ASSET_ID,
        "symbol": "PNET",
        "poolCount": len(pools),
        "totalPnetReserve": sum(float(item["pnetReserve"]) for item in pools),
        "source": "pool_snapshots",
        "listedWithoutOpportunity": True,
        "publicSafe": True,
        "notice": "PNET pool visibility is informational only; it is not investment advice, ROI guidance, or a request to trade.",
        "lpRiskNotice": "Adding liquidity can lose value through price movement, fees, and impermanent loss. Review pool terms independently.",
        "pools": pools[:12],
    }


def _opportunity_counts(opportunities: list[dict[str, Any]], window_start: float, window_end: float) -> dict[str, Any]:
    status_counts = Counter(str(item.get("status") or "unknown") for item in opportunities)
    reason_counts = Counter(str(item.get("skip_reason") or "none") for item in opportunities)
    by_hour = _hour_counts(opportunities, window_start, window_end)
    total = len(opportunities)
    approved = int(status_counts.get("approved", 0))
    return {
        "total": total,
        "approved": approved,
        "rejected": total - approved,
        "positiveSpreadCount": sum(1 for item in opportunities if _number(item.get("expected_profit_bps")) > 0),
        "byStatus": [{"status": key, "count": value} for key, value in status_counts.most_common()],
        "bySkipReason": [{"reason": key, "count": value} for key, value in reason_counts.most_common()],
        "byHour": by_hour,
    }


def _route_performance(opportunities: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(opportunities)
    rejection_counts = Counter(str(item.get("skip_reason") or "none") for item in opportunities if item.get("status") != "approved")
    return {
        "routeCount": count,
        "approvedCount": sum(1 for item in opportunities if item.get("status") == "approved"),
        "rejectedCount": sum(1 for item in opportunities if item.get("status") != "approved"),
        "averageRouteLength": _average(_number(item.get("routeLength"), 1) for item in opportunities),
        "averageConfidence": _average(_number(item.get("confidence_score")) for item in opportunities),
        "averageExpectedProfitBps": _average(_number(item.get("expected_profit_bps")) for item in opportunities),
        "totalExpectedNetProfit": sum(_number(item.get("expected_net_profit")) for item in opportunities),
        "topRejectionReasons": [{"reason": reason, "count": count} for reason, count in rejection_counts.most_common(8)],
    }


def _paper_trade_performance(paper_trades: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = len(paper_trades)
    checked_5s = [trade for trade in paper_trades if trade.get("checked_5s_at") is not None]
    checked_30s = [trade for trade in paper_trades if trade.get("checked_30s_at") is not None]
    wins_5s = sum(1 for trade in checked_5s if _number(trade.get("simulated_profit_5s")) > 0)
    wins_30s = sum(1 for trade in checked_30s if _number(trade.get("simulated_profit_30s")) > 0)
    return {
        "candidates": candidates,
        "wouldExecute": sum(1 for trade in paper_trades if bool(trade.get("would_execute"))),
        "skipped": sum(1 for trade in paper_trades if not bool(trade.get("would_execute"))),
        "checked5s": len(checked_5s),
        "checked30s": len(checked_30s),
        "winRate5s": 0.0 if not checked_5s else wins_5s / len(checked_5s),
        "winRate30s": 0.0 if not checked_30s else wins_30s / len(checked_30s),
        "expectedNetProfit": sum(_number(trade.get("expected_net_profit") or trade.get("expected_profit")) for trade in paper_trades),
        "simulatedProfit5s": sum(_number(trade.get("simulated_profit_5s")) for trade in checked_5s),
        "simulatedProfit30s": sum(_number(trade.get("simulated_profit_30s")) for trade in checked_30s),
        "averageQuoteDecay5s": _average(_number(trade.get("quote_decay_5s")) for trade in checked_5s),
        "averageQuoteDecay30s": _average(_number(trade.get("quote_decay_30s")) for trade in checked_30s),
        "averageProfitDelta30s": _average(_number(trade.get("expected_vs_simulated_profit_30s")) for trade in checked_30s),
    }


def _scanner_health(pool_snapshots: list[dict[str, Any]], service_health: list[dict[str, Any]]) -> dict[str, Any]:
    scanner_rows = [
        row
        for row in service_health
        if str(row.get("service_name") or row.get("serviceName") or "").lower() in {"market_scanner", "scanner"}
    ]
    latest = max(scanner_rows, key=lambda item: _number(item.get("checked_at")), default=None)
    status_counts = Counter(str(row.get("status") or "unknown") for row in scanner_rows)
    snapshot_count = len(pool_snapshots)
    pools_scanned = len({str(row.get("pool_id") or "") for row in pool_snapshots if row.get("pool_id")})
    latest_snapshot = max((_number(row.get("captured_at")) for row in pool_snapshots), default=0.0)
    return {
        "status": str(latest.get("status") if latest else ("ok" if snapshot_count else "unavailable")),
        "latestDetail": latest.get("detail") if latest else None,
        "lastRunAt": _number(latest.get("checked_at")) if latest else latest_snapshot,
        "okCount": int(status_counts.get("ok", 0)),
        "errorCount": sum(count for status, count in status_counts.items() if status not in {"ok", "wait"}),
        "checks": len(scanner_rows),
        "snapshotCount": snapshot_count,
        "poolsScanned": pools_scanned,
        "latestSnapshotAt": latest_snapshot,
    }


def _risk_events(risk_decisions: list[dict[str, Any]], opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if risk_decisions:
        grouped: dict[str, dict[str, Any]] = {}
        for decision in risk_decisions:
            reason = str(decision.get("reason") or ("approved" if bool(decision.get("approved")) else "unknown"))
            item = grouped.setdefault(reason, {"reason": reason, "count": 0, "approved": bool(decision.get("approved")), "latestAt": 0.0})
            item["count"] += 1
            item["latestAt"] = max(float(item["latestAt"]), _number(decision.get("created_at")))
        rows = list(grouped.values())
    else:
        reason_counts = Counter(str(item.get("skip_reason") or ("approved" if item.get("status") == "approved" else "unknown")) for item in opportunities)
        rows = [{"reason": reason, "count": count, "approved": reason == "approved", "latestAt": 0.0} for reason, count in reason_counts.items()]
    rows.sort(key=lambda item: (-int(item["count"]), str(item["reason"])))
    return rows[:12]


def _market_summary(
    *,
    opportunity_items: list[dict[str, Any]],
    liquidity_changes: list[dict[str, Any]],
    paper_performance: dict[str, Any],
    scanner_health: dict[str, Any],
    top_pairs: list[dict[str, Any]],
) -> dict[str, Any]:
    opportunity_count = len(opportunity_items)
    pair_count = len({item["pairKey"] for item in opportunity_items})
    venue_count = len({venue for item in opportunity_items for venue in item["venues"]})
    positive_count = sum(1 for item in opportunity_items if _number(item.get("expected_profit_bps")) > 0)
    top_pair = top_pairs[0]["pairLabel"] if top_pairs else "none"
    largest_liquidity_move = liquidity_changes[0] if liquidity_changes else None
    headline = f"{opportunity_count} opportunities across {pair_count} pairs"
    narrative = (
        f"Scanner status {scanner_health.get('status', 'unavailable')} with {scanner_health.get('poolsScanned', 0)} pools scanned. "
        f"Top activity centered on {top_pair}. "
        f"{positive_count} routes showed positive expected spreads before risk and paper checks. "
        f"30s paper win rate was {_fmt(float(paper_performance.get('winRate30s', 0.0)) * 100)}%."
    )
    return {
        "headline": headline,
        "narrative": narrative,
        "opportunityCount": opportunity_count,
        "pairCount": pair_count,
        "venueCount": venue_count,
        "topPair": top_pair,
        "positiveSpreadCount": positive_count,
        "largestLiquidityMove": largest_liquidity_move,
        "scannerStatus": scanner_health.get("status", "unavailable"),
        "paperWinRate30s": paper_performance.get("winRate30s", 0.0),
    }


def _hour_counts(opportunities: list[dict[str, Any]], window_start: float, window_end: float) -> list[dict[str, Any]]:
    bucket_seconds = max(1, int((window_end - window_start) // 24) or 3_600)
    buckets = [{"hour": index, "startAt": window_start + (index * bucket_seconds), "count": 0} for index in range(24)]
    for item in opportunities:
        created_at = _number(item.get("created_at"))
        index = int((created_at - window_start) // bucket_seconds) if created_at >= window_start else 0
        index = max(0, min(23, index))
        buckets[index]["count"] += 1
    return buckets


def _symbol_map(assets: list[dict[str, Any]]) -> dict[int, str]:
    symbols = dict(DEFAULT_ASSET_SYMBOLS)
    for asset in assets:
        asset_id = _int(asset.get("asset_id"), None)
        symbol = str(asset.get("symbol") or "").strip()
        if asset_id is not None and symbol:
            symbols[asset_id] = symbol
    return symbols


def _pair_label(asset_ids: list[int], symbol_map: dict[int, str]) -> str:
    return "/".join(symbol_map.get(asset_id, str(asset_id)) for asset_id in asset_ids)


def _has_records(*groups: list[Any]) -> bool:
    return any(bool(group) for group in groups)


def _table_lines(headers: list[str], rows: list[list[Any]]) -> list[str]:
    if not rows:
        return ["- No stored records for this section."]
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(str(value) for value in row) + " |" for row in rows],
    ]


def _average(values: Any) -> float:
    items = [float(value) for value in values]
    return 0.0 if not items else sum(items) / len(items)


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _int(value: Any, default: int | None = 0) -> int | None:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _fmt(value: Any) -> str:
    number = _number(value)
    return f"{number:,.4f}".rstrip("0").rstrip(".")


def _signed_fmt(value: Any) -> str:
    number = _number(value)
    sign = "+" if number > 0 else ""
    return f"{sign}{_fmt(number)}"
