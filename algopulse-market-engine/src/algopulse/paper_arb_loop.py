from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import replace
from typing import Any

from algopulse.config import Settings, get_settings
from algopulse.models import Opportunity, Pool
from algopulse.risk import RiskEngine, policy_from_settings
from algopulse.scanner import MarketScanner
from algopulse.readonly_safety import ReadonlySafetyError, assert_readonly_profile_safe
from algopulse.route_optimizer import ProfitSeekingRouteOptimizer
from algopulse.store import MarketStore
from algopulse.liquidity_opportunity import (
    SKIP_LOW_CROSS_VENUE_LIQUIDITY,
    pools_for_pairs,
    rank_shared_pairs,
)
from algopulse.verified_pool_registry import build_verified_pool_registry, write_registry_report


OUTCOME_PAPER_CANDIDATE = "paper_candidate_created"
OUTCOME_SPREAD_BELOW = "spread_below_profit_threshold"
OUTCOME_ROUTE_REJECTED = "route_rejected_by_risk"
OUTCOME_NO_SHARED_PAIR = "no_shared_liquid_pair"
OUTCOME_CONNECTOR_UNAVAILABLE = "connector_unavailable"

# Legacy probe sizes kept for tests/backward-compat; live path uses adaptive ladder.
PAPER_TRADE_SIZES = (1.0, 5.0, 10.0)
ADAPTIVE_PROBE_SIZES = (0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0)
TESTNET_USDC = 10_458_941
MAINNET_USDC = 31_566_704
MAINNET_PNET = 3_169_177_585
PREFERRED_PAIR = (0, TESTNET_USDC)
MAINNET_PREFERRED_PAIRS = (
    (0, MAINNET_PNET),
    (0, MAINNET_USDC),
)

PROFIT_RULES = {
    "net_profit_after_fees_ok",
    "profit_bps_ok",
    "fee_buffer_ok",
}


def _rejection_distribution(opportunities: list[Opportunity]) -> list[dict]:
    counts: dict[str, int] = defaultdict(int)
    for item in opportunities:
        if item.status == "approved":
            counts["approved"] += 1
        else:
            counts[str(item.skip_reason or "rejected")] += 1
    total = max(1, sum(counts.values()))
    return [
        {"reason": reason, "count": count, "percent": round(100.0 * count / total, 2)}
        for reason, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    ]


def _best_routes_summary(opportunities: list[Opportunity], *, limit: int = 5) -> list[dict]:
    ordered = sorted(opportunities, key=lambda item: item.expected_net_profit, reverse=True)
    rows: list[dict] = []
    for item in ordered[:limit]:
        rows.append(
            {
                "routeHash": item.route_hash,
                "status": item.status,
                "skipReason": item.skip_reason,
                "inputAmount": item.input_amount,
                "expectedNetProfit": item.expected_net_profit,
                "expectedProfitBps": item.expected_profit_bps,
                "maxPriceImpactBps": item.max_price_impact_bps,
                "grossProfit": item.gross_profit,
                "totalDexFees": item.total_dex_fees,
                "slippageBuffer": item.slippage_buffer,
                "venues": [leg.get("venue") for leg in item.route],
                "riskRules": item.risk_rules,
            }
        )
    return rows


def _pair_key(left: int, right: int) -> tuple[int, int]:
    return tuple(sorted((int(left), int(right))))


def preferred_pairs_for_network(network: str) -> tuple[tuple[int, int], ...]:
    if (network or "").strip().lower() == "mainnet":
        return MAINNET_PREFERRED_PAIRS
    return (PREFERRED_PAIR,)


def shared_liquid_pairs(pools: list[Pool], *, network: str = "testnet") -> list[dict]:
    """Return dual-venue pairs ranked by cross-venue liquidity (not empty-PNET-first)."""
    ranked = rank_shared_pairs(
        pools,
        network=network,
        preferred_pairs=preferred_pairs_for_network(network),
        min_cross_venue_liquidity=0.0,
        min_venue_reserve=0.0,
    )
    # Compatibility: include both accepted and skipped shared venue pairs for diagnostics.
    return list(ranked["accepted"]) + list(ranked["skipped"])


def comparable_quotes_for_sizes(pools: list[Pool], sizes: tuple[float, ...] = PAPER_TRADE_SIZES) -> list[dict]:
    quotes: list[dict] = []
    for pool in pools:
        for size in sizes:
            for input_asset_id in (pool.asset_a_id, pool.asset_b_id):
                if input_asset_id != 0:
                    # Prefer ALGO-in quotes for the paper loop evidence.
                    continue
                quote = pool.quote(input_asset_id=input_asset_id, input_amount=float(size))
                if quote is None:
                    continue
                quotes.append(
                    {
                        "poolId": pool.pool_id,
                        "venueId": pool.venue_id,
                        "appId": pool.app_id,
                        "inputAssetId": quote.input_asset_id,
                        "outputAssetId": quote.output_asset_id,
                        "inputAmount": quote.input_amount,
                        "outputAmount": quote.output_amount,
                        "feeAmount": quote.fee_amount,
                        "priceImpactBps": quote.price_impact_bps,
                        "blockRound": pool.block_round,
                    }
                )
    return quotes


def classify_outcome(
    *,
    tinyman_status: str,
    pact_status: str,
    tinyman_pools: int,
    pact_pools: int,
    shared_pairs: list[dict],
    opportunities: list[Opportunity],
) -> tuple[str, str]:
    tinyman_down = tinyman_status == "error" and tinyman_pools <= 0
    pact_down = pact_status == "error" and pact_pools <= 0
    if tinyman_down and pact_down:
        return OUTCOME_CONNECTOR_UNAVAILABLE, "both_tinyman_and_pact_unavailable"
    if tinyman_down or pact_down:
        down = "tinyman" if tinyman_down else "pact"
        if not shared_pairs:
            return OUTCOME_CONNECTOR_UNAVAILABLE, f"{down}_unavailable_no_shared_pair"
    if not shared_pairs:
        return OUTCOME_NO_SHARED_PAIR, "no_pair_with_positive_reserves_on_both_venues"

    approved = [item for item in opportunities if item.status == "approved"]
    if approved:
        return OUTCOME_PAPER_CANDIDATE, "approved_route_recorded_for_paper"

    if not opportunities:
        return OUTCOME_SPREAD_BELOW, "shared_pair_exists_but_no_two_leg_route_built"

    profit_rejects = [
        item
        for item in opportunities
        if item.status == "rejected" and (item.skip_reason or "") in PROFIT_RULES
    ]
    if profit_rejects and len(profit_rejects) == len(opportunities):
        top = profit_rejects[0].skip_reason or "net_profit_after_fees_ok"
        return OUTCOME_SPREAD_BELOW, f"all_routes_rejected_for_profit_rules:{top}"

    # Any non-profit risk rejection (allowlist, impact, etc.)
    top = opportunities[0].skip_reason or "risk_rejected"
    return OUTCOME_ROUTE_REJECTED, f"routes_rejected_by_risk:{top}"


def settings_for_paper_loop(
    settings: Settings,
    pools: list[Pool],
    *,
    trade_sizes: tuple[float, ...] | None = None,
) -> Settings:
    """Scope trade sizes and assets for paper evidence.

    Does NOT mutate execution/signer allowed_app_ids. Paper app IDs come from the
    verified pool registry via RiskPolicy.paper_verified_app_ids only.
    """
    asset_ids = tuple(
        sorted(
            {
                asset_id
                for pool in pools
                for asset_id in (pool.asset_a_id, pool.asset_b_id)
            }
        )
    )
    allowed_assets = tuple(sorted(set(settings.allowed_asset_ids) | set(asset_ids) | {0}))
    sizes = trade_sizes if trade_sizes is not None else ADAPTIVE_PROBE_SIZES
    # Never exceed configured max live trade size / risk ceiling.
    max_size = min(float(settings.max_live_trade_size or 10.0), 10.0)
    clipped = tuple(size for size in sizes if 0 < float(size) <= max_size + 1e-12)
    if not clipped:
        clipped = (min(1.0, max_size),)
    return replace(
        settings,
        trade_sizes=clipped,
        allowed_asset_ids=allowed_assets,
        # Keep execution/signer allowlist exactly as configured (often empty).
        allowed_app_ids=tuple(settings.allowed_app_ids),
        require_app_id_allowlist=bool(settings.require_app_id_allowlist),
    )


def run_paper_arb_loop(
    *,
    settings: Settings | None = None,
    store: MarketStore | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    now_fn: Callable[[], float] = time.time,
    perform_rechecks: bool = True,
    recheck_delays: tuple[float, float] = (5.5, 25.0),
    scanner: MarketScanner | None = None,
) -> dict:
    """Execute one read-only paper-arbitrage evidence loop (TestNet or MainNet read-only)."""
    active_settings = settings or get_settings()
    assert_readonly_profile_safe(active_settings)
    active_store = store or MarketStore(active_settings.database_path)
    active_store.initialize(run_backfills=False)

    started_at = now_fn()
    loop_id = f"paper_arb_{uuid.uuid4().hex[:12]}"

    # Live pool collection: real connector snapshots only (no fabricated pools).
    discovery_scanner = scanner or MarketScanner(settings=active_settings, store=active_store)
    if hasattr(discovery_scanner, "collect_pools"):
        discovery_scan = discovery_scanner.collect_pools()
        pools = list(discovery_scan.pop("pool_objects", []) or [])
    else:
        discovery_scan = discovery_scanner.run_once()
        pools = []
        for connector in discovery_scanner.connectors:
            try:
                pools.extend(connector.list_pools())
            except Exception:
                continue

    tinyman_health = next(
        (item for item in discovery_scan.get("connector_health") or [] if item.get("connectorName") == "tinyman"),
        {"status": "unavailable", "poolCount": 0},
    )
    pact_health = next(
        (item for item in discovery_scan.get("connector_health") or [] if item.get("connectorName") == "pact"),
        {"status": "unavailable", "poolCount": 0},
    )

    # Verify every discovered pool on-chain; paper risk uses only accepted registry IDs.
    registry_report = build_verified_pool_registry(
        pools,
        settings=active_settings,
        store=active_store,
        now=now_fn(),
    )
    try:
        report_dir = active_settings.data_dir
        report_dir.mkdir(parents=True, exist_ok=True)
        write_registry_report(registry_report, str(report_dir / "verified_pool_registry_report.json"))
    except Exception:
        pass
    paper_verified_app_ids = tuple(int(app_id) for app_id in registry_report.get("acceptedAppIds") or [])
    verified_pools = [pool for pool in pools if int(pool.app_id) in set(paper_verified_app_ids)]
    candidate_pools = verified_pools if verified_pools else []

    # Liquidity-aware selection: evaluate every usable dual-venue pair; skip dust.
    min_reserve_floor = max(1.0, min(float(getattr(active_settings, "min_pool_reserve", 1000.0) or 1000.0) * 0.001, 50.0))
    ranked = rank_shared_pairs(
        candidate_pools,
        network=active_settings.network,
        preferred_pairs=preferred_pairs_for_network(active_settings.network),
        min_cross_venue_liquidity=min_reserve_floor,
        min_venue_reserve=min_reserve_floor,
    )
    accepted_pairs = ranked["accepted"]
    skipped_pairs = ranked["skipped"]
    shared = accepted_pairs + skipped_pairs
    selected = accepted_pairs[0] if accepted_pairs else None
    selected_pair = tuple(selected["pair"]) if selected else None

    # All accepted pairs (every fee tier on both venues) enter route search.
    evaluation_pairs = [tuple(item["pair"]) for item in accepted_pairs]
    selected_pools = pools_for_pairs(candidate_pools, evaluation_pairs) if evaluation_pairs else []
    selected_pools = [pool for pool in selected_pools if int(pool.app_id) in set(paper_verified_app_ids)]

    # Coarse probe sizes for comparable quotes only; optimizer owns fine size search.
    probe_sizes = (0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0)
    max_size = min(10.0, float(active_settings.max_live_trade_size or 10.0))
    probe_sizes = tuple(s for s in probe_sizes if s <= max_size + 1e-12)
    scoped_settings = settings_for_paper_loop(
        active_settings,
        selected_pools or candidate_pools or pools,
        trade_sizes=probe_sizes,
    )
    # Execution allowed_app_ids remain unchanged; paper uses verified registry only.
    risk_engine = RiskEngine(
        policy_from_settings(scoped_settings, paper_verified_app_ids=paper_verified_app_ids)
    )

    quotes = comparable_quotes_for_sizes(selected_pools or candidate_pools, tuple(scoped_settings.trade_sizes))

    # Profit-seeking optimizer: dedupe unique routes, coarse-to-fine sizes, selective paper.
    optimizer = ProfitSeekingRouteOptimizer(
        risk_engine,
        min_size=0.05,
        max_size=max_size,
    )
    opt_report = optimizer.optimize(selected_pools) if selected_pools else None
    opportunities = list(opt_report.paper_rows) if opt_report else []
    # Full unique-route set (best size each) for classification / best-route summary.
    all_optimized = [item.opportunity for item in (opt_report.optimized_routes if opt_report else [])]

    # Persist only paper-eligible rows (approved + best near-misses). Noise is aggregated.
    if opportunities:
        active_store.record_opportunities(opportunities)
        for opportunity in opportunities:
            would_execute = opportunity.status == "approved"
            notes = (
                "would_execute: risk approved; paper tracking before real funds"
                if would_execute
                else f"near_miss: {opportunity.skip_reason or 'unknown'}"
            )
            active_store.record_paper_trade(opportunity=opportunity, would_execute=would_execute, notes=notes)

    if opt_report is not None:
        active_store.record_service_health(
            "route_optimizer",
            "ok" if opt_report.any_risk_approved else "degraded",
            detail="paper_loop_optimize",
            metrics={
                "routesBeforeDedupe": opt_report.routes_before_dedupe,
                "routesAfterDedupe": opt_report.routes_after_dedupe,
                "paperRows": len(opt_report.paper_rows),
                "aggregateRejections": opt_report.aggregate_rejections,
                "bestNet": opt_report.best_net,
                "bestGross": opt_report.best_gross,
                "anyRiskApproved": opt_report.any_risk_approved,
            },
        )

    classify_ops = all_optimized if all_optimized else opportunities
    outcome, reason = classify_outcome(
        tinyman_status=str(tinyman_health.get("status") or "unavailable"),
        pact_status=str(pact_health.get("status") or "unavailable"),
        tinyman_pools=int(tinyman_health.get("poolCount") or 0),
        pact_pools=int(pact_health.get("poolCount") or 0),
        shared_pairs=accepted_pairs,
        opportunities=classify_ops,
    )
    if not accepted_pairs and skipped_pairs and outcome == OUTCOME_NO_SHARED_PAIR:
        reason = f"{SKIP_LOW_CROSS_VENUE_LIQUIDITY}:all_shared_pairs_unusable"

    recheck = {"checked_5s": 0, "checked_30s": 0, "checked_60s": 0, "errors": 0, "performed": False}
    if perform_rechecks and opportunities:
        recheck["performed"] = True
        # T+5
        sleep_fn(float(recheck_delays[0]))
        # Refresh pools for recheck simulation.
        refreshed: list[Pool] = []
        for connector in discovery_scanner.connectors:
            try:
                refreshed.extend(connector.list_pools())
            except Exception:
                continue
        if not refreshed:
            refreshed = selected_pools or pools
        result_5 = active_store.update_due_paper_trades(refreshed, now=now_fn())
        recheck["checked_5s"] += int(result_5.get("checked_5s") or 0)
        recheck["checked_30s"] += int(result_5.get("checked_30s") or 0)
        recheck["checked_60s"] += int(result_5.get("checked_60s") or 0)
        recheck["errors"] += int(result_5.get("errors") or 0)
        # Remaining delay to reach ~T+30 from create (no-op if already satisfied).
        sleep_fn(float(recheck_delays[1]))
        refreshed_30: list[Pool] = []
        for connector in discovery_scanner.connectors:
            try:
                refreshed_30.extend(connector.list_pools())
            except Exception:
                continue
        if not refreshed_30:
            refreshed_30 = refreshed
        result_30 = active_store.update_due_paper_trades(refreshed_30, now=now_fn())
        recheck["checked_5s"] += int(result_30.get("checked_5s") or 0)
        recheck["checked_30s"] += int(result_30.get("checked_30s") or 0)
        recheck["checked_60s"] += int(result_30.get("checked_60s") or 0)
        recheck["errors"] += int(result_30.get("errors") or 0)

    best = (sorted(classify_ops, key=lambda item: item.expected_net_profit, reverse=True)[0] if classify_ops else None)
    paper_rows = active_store.list_paper_trades(limit=20)
    freshness = active_store.quote_freshness_evidence(
        max_age_seconds=scoped_settings.max_route_age_seconds,
        limit=20,
    )

    completed_at = now_fn()
    result = {
        "loopId": loop_id,
        "startedAt": started_at,
        "completedAt": completed_at,
        "network": active_settings.network,
        "source": "live",
        "outcome": outcome,
        "reason": reason,
        "preferredPairs": [list(pair) for pair in preferred_pairs_for_network(active_settings.network)],
        "preferredPair": list(preferred_pairs_for_network(active_settings.network)[0]),
        "selectedPair": list(selected_pair) if selected_pair else None,
        "pairSelection": {
            "strategy": "liquidity_aware_cross_venue",
            "acceptedPairs": accepted_pairs,
            "skippedPairs": skipped_pairs,
            "skipReasonCode": SKIP_LOW_CROSS_VENUE_LIQUIDITY,
            "evaluatedPairCount": len(evaluation_pairs),
        },
        "profile": "mainnet-readonly" if active_settings.network == "mainnet" else "testnet",
        "sharedPairs": shared,
        "poolsInspected": [
            {
                "poolId": pool.pool_id,
                "venueId": pool.venue_id,
                "appId": pool.app_id,
                "assetA": pool.asset_a_id,
                "assetB": pool.asset_b_id,
                "reserveA": pool.reserve_a,
                "reserveB": pool.reserve_b,
                "feeBps": pool.fee_bps,
                "blockRound": pool.block_round,
                "capturedAt": pool.captured_at,
            }
            for pool in (selected_pools or pools)
        ],
        "connectors": {
            "tinyman": tinyman_health,
            "pact": pact_health,
        },
        "tradeSizes": list(scoped_settings.trade_sizes),
        "adaptiveSizing": {
            "probeSizes": list(probe_sizes),
            "refinedSizes": list(scoped_settings.trade_sizes),
            "minSize": 0.1,
            "maxSize": min(10.0, float(active_settings.max_live_trade_size or 10.0)),
        },
        "verifiedPoolRegistry": {
            "acceptedCount": registry_report.get("acceptedCount"),
            "rejectedCount": registry_report.get("rejectedCount"),
            "acceptedAppIds": registry_report.get("acceptedAppIds"),
            "rejectedAppIds": registry_report.get("rejectedAppIds"),
            "accepted": registry_report.get("accepted") or [],
            "rejected": registry_report.get("rejected") or [],
            "executionAllowlistUnchanged": True,
            "signerAllowlistUnchanged": True,
            "paperOnlyRegistry": True,
        },
        "rejectionDistribution": (
            [
                {"reason": reason, "count": count, "percent": round(100.0 * count / max(1, sum((opt_report.aggregate_rejections or {}).values())), 2)}
                for reason, count in (opt_report.aggregate_rejections or {}).items()
            ]
            if opt_report is not None
            else _rejection_distribution(classify_ops)
        ),
        "routeOptimizer": None
        if opt_report is None
        else {
            "routesBeforeDedupe": opt_report.routes_before_dedupe,
            "routesAfterDedupe": opt_report.routes_after_dedupe,
            "paperRowCount": len(opt_report.paper_rows),
            "bestGrossProfit": opt_report.best_gross,
            "bestNetProfit": opt_report.best_net,
            "anyRiskApproved": opt_report.any_risk_approved,
            "topNearMisses": opt_report.near_misses[:5],
            "aggregateRejections": opt_report.aggregate_rejections,
            "riskLimitsUnchanged": True,
        },
        "bestEconomicallyEvaluatedRoutes": _best_routes_summary(classify_ops, limit=5),
        "comparableQuotes": quotes,
        "quoteFreshness": {
            "quoteCount": freshness.get("quoteCount"),
            "freshCount": freshness.get("freshCount"),
            "staleCount": freshness.get("staleCount"),
            "source": freshness.get("source"),
        },
        "route": None
        if best is None
        else {
            "routeHash": best.route_hash,
            "status": best.status,
            "skipReason": best.skip_reason,
            "inputAssetId": best.input_asset_id,
            "inputAmount": best.input_amount,
            "expectedFinalAmount": best.expected_final_amount,
            "grossProfit": best.gross_profit,
            "totalDexFees": best.total_dex_fees,
            "estimatedNetworkFee": best.estimated_network_fee,
            "slippageBuffer": best.slippage_buffer,
            "expectedNetProfit": best.expected_net_profit,
            "expectedProfitBps": best.expected_profit_bps,
            "maxPriceImpactBps": best.max_price_impact_bps,
            "riskRules": best.risk_rules,
            "legs": best.route,
        },
        "opportunityCount": len(classify_ops),
        "approvedCount": sum(1 for item in classify_ops if item.status == "approved"),
        "rejectedCount": sum(1 for item in classify_ops if item.status == "rejected"),
        "paper": {
            "recordedCount": len(opportunities),
            "recent": paper_rows[:5],
            "recheck": recheck,
        },
        "scan": {
            "pools": discovery_scan.get("pools"),
            "opportunities": discovery_scan.get("opportunities"),
            "status": discovery_scan.get("status"),
        },
        "productionReady": False,
        "liveExecutionLocked": True,
        "signingEnabled": False,
        "submissionEnabled": False,
    }

    # Store a compact public-safe evidence row for Control Room / ops consumers.
    active_store.record_service_health(
        "paper_arb_loop",
        "ok" if outcome == OUTCOME_PAPER_CANDIDATE else "degraded" if outcome != OUTCOME_CONNECTOR_UNAVAILABLE else "error",
        detail=outcome,
        metrics={
            "loopId": loop_id,
            "outcome": outcome,
            "reason": reason,
            "selectedPair": result["selectedPair"],
            "opportunityCount": len(opportunities),
            "approvedCount": result["approvedCount"],
            "rejectedCount": result["rejectedCount"],
            "quoteCount": len(quotes),
            "recheck5s": recheck["checked_5s"],
            "recheck30s": recheck["checked_30s"],
            "productionReady": False,
        },
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AlgoPulse first real TestNet paper-arbitrage loop (read-only, no signing)."
    )
    parser.add_argument(
        "--skip-rechecks",
        action="store_true",
        help="Skip T+5/T+30 waits (deterministic tests / fast local dry evidence).",
    )
    parser.add_argument(
        "--recheck-delay-5s",
        type=float,
        default=5.5,
        help="Seconds to wait before first paper recheck (default 5.5).",
    )
    parser.add_argument(
        "--recheck-delay-30s",
        type=float,
        default=25.0,
        help="Additional seconds after T+5 before T+30 recheck (default 25).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_paper_arb_loop(
            perform_rechecks=not args.skip_rechecks,
            recheck_delays=(args.recheck_delay_5s, args.recheck_delay_30s),
        )
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        return 0
    except ReadonlySafetyError as exc:
        print(json.dumps({"ok": False, "error": "safety", "detail": str(exc)}, indent=2))
        return 2
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "detail": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
