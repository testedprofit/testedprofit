"""Profit-seeking route optimizer over real pool snapshots.

Deduplicates unique routes, coarse-to-fine size search, exact P&L breakdown.
Does not loosen risk limits. Does not touch scanner/collector lifecycle.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from itertools import permutations
from pathlib import Path
from typing import Any

from algopulse.config import Settings, get_settings
from algopulse.engine import RouteEngine
from algopulse.models import Opportunity, Pool
from algopulse.risk import RiskEngine, policy_from_settings
from algopulse.store import MarketStore
from algopulse.verified_pool_registry import load_paper_verified_app_ids


ALGO_ASSET_ID = 0
COARSE_SIZES = (0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0)
MIN_SIZE = 0.05
MAX_SIZE = 10.0

# Routes with no economic edge are never paper-tracked.
SKIP_IMPOSSIBLE = "impossible_or_non_positive_gross"
SKIP_NEGATIVE = "negative_net_discarded_pre_paper"


@dataclass
class OptimizedRoute:
    identity_key: tuple
    opportunity: Opportunity
    pools: list[Pool]
    pair: tuple[int, int]
    direction: str
    best_size: float
    gross_profit: float
    net_profit: float
    dex_fees: float
    network_fee: float
    price_impact_bps: float
    slippage_buffer: float
    safety_buffer_bps: float
    block_round: int
    paper_eligible: bool
    paper_reason: str


@dataclass
class OptimizerReport:
    routes_before_dedupe: int
    routes_after_dedupe: int
    sizes_evaluated: int
    paper_rows: list[Opportunity] = field(default_factory=list)
    optimized_routes: list[OptimizedRoute] = field(default_factory=list)
    near_misses: list[dict] = field(default_factory=list)
    aggregate_rejections: dict[str, int] = field(default_factory=dict)
    best_gross: float = 0.0
    best_net: float = 0.0
    any_risk_approved: bool = False
    selected_pair: list[int] | None = None

    def to_dict(self) -> dict:
        return {
            "routesBeforeDedupe": self.routes_before_dedupe,
            "routesAfterDedupe": self.routes_after_dedupe,
            "sizesEvaluated": self.sizes_evaluated,
            "paperRowCount": len(self.paper_rows),
            "aggregateRejections": dict(self.aggregate_rejections),
            "bestGrossProfit": self.best_gross,
            "bestNetProfit": self.best_net,
            "anyRiskApproved": self.any_risk_approved,
            "selectedPair": self.selected_pair,
            "bestSizePerRoute": [
                {
                    "identity": _identity_label(item.identity_key),
                    "pair": list(item.pair),
                    "direction": item.direction,
                    "bestSize": item.best_size,
                    "grossProfit": item.gross_profit,
                    "netProfit": item.net_profit,
                    "dexFees": item.dex_fees,
                    "networkFee": item.network_fee,
                    "priceImpactBps": item.price_impact_bps,
                    "slippageBuffer": item.slippage_buffer,
                    "safetyBufferBps": item.safety_buffer_bps,
                    "blockRound": item.block_round,
                    "status": item.opportunity.status,
                    "skipReason": item.opportunity.skip_reason,
                    "paperEligible": item.paper_eligible,
                    "venues": [leg.get("venue") for leg in item.opportunity.route],
                    "poolIds": item.opportunity.involved_pool_ids,
                }
                for item in self.optimized_routes
            ],
            "topNearMisses": self.near_misses[:5],
            "riskLimitsUnchanged": True,
            "productionReady": False,
            "signingEnabled": False,
        }


def route_identity_key(
    pools: list[Pool],
    *,
    input_asset_id: int,
    block_rounds: tuple[int, ...],
) -> tuple:
    """Unique route: pool sequence, direction (input asset), pair, block rounds."""
    pool_seq = tuple(str(p.pool_id) for p in pools)
    pair = tuple(sorted({a for p in pools for a in (p.asset_a_id, p.asset_b_id)}))
    if len(pair) >= 2:
        pair_key = (pair[0], pair[1])
    else:
        pair_key = (pair[0], pair[0]) if pair else (0, 0)
    return (pool_seq, int(input_asset_id), pair_key, tuple(int(r) for r in block_rounds))


def _identity_label(key: tuple) -> str:
    pool_seq, input_asset, pair, rounds = key
    return f"{'->'.join(pool_seq)}|in={input_asset}|pair={pair[0]}-{pair[1]}|r={','.join(map(str, rounds))}"


def direction_label(pools: list[Pool], input_asset_id: int) -> str:
    venues = "->".join(p.venue_id for p in pools)
    return f"{venues}|in={int(input_asset_id)}"


def coarse_to_fine_sizes(
    *,
    min_size: float = MIN_SIZE,
    max_size: float = MAX_SIZE,
    best_coarse: float | None = None,
) -> tuple[float, ...]:
    ceiling = max(min_size, min(float(max_size), MAX_SIZE))
    floor = max(MIN_SIZE, float(min_size))
    coarse = tuple(s for s in COARSE_SIZES if floor - 1e-12 <= s <= ceiling + 1e-12)
    if not coarse:
        return (floor,)
    if best_coarse is None:
        return coarse
    refined = {round(s, 6) for s in coarse}
    center = float(best_coarse)
    for candidate in (
        center,
        max(floor, center * 0.5),
        min(ceiling, center * 1.5),
        max(floor, center - 0.05),
        min(ceiling, center + 0.05),
        max(floor, center - 0.1),
        min(ceiling, center + 0.1),
        max(floor, center * 0.75),
        min(ceiling, center * 1.25),
        max(floor, center * 0.9),
        min(ceiling, center * 1.1),
    ):
        if floor - 1e-12 <= candidate <= ceiling + 1e-12:
            refined.add(round(candidate, 6))
    return tuple(sorted(refined))


def is_impossible_or_non_positive(opportunity: Opportunity) -> bool:
    if opportunity.expected_final_amount <= 0:
        return True
    if opportunity.gross_profit <= 0:
        return True
    return False


class ProfitSeekingRouteOptimizer:
    def __init__(
        self,
        risk_engine: RiskEngine,
        *,
        min_size: float = MIN_SIZE,
        max_size: float | None = None,
    ) -> None:
        self.risk_engine = risk_engine
        policy_max = float(risk_engine.policy.max_trade_size or MAX_SIZE)
        self.min_size = max(MIN_SIZE, float(min_size))
        self.max_size = min(MAX_SIZE, policy_max if max_size is None else float(max_size))
        self._engine = RouteEngine(risk_engine=risk_engine, trade_sizes=[self.min_size])

    def optimize(self, pools: list[Pool]) -> OptimizerReport:
        skeletons = self._enumerate_two_leg_skeletons(pools)
        sizes_evaluated = 0
        routes_before = 0
        best_by_identity: dict[tuple, OptimizedRoute] = {}
        raw_rejection_noise: dict[str, int] = defaultdict(int)

        for first, second, input_asset_id in skeletons:
            route_pools = [first, second]
            rounds = (int(first.block_round), int(second.block_round))
            identity = route_identity_key(route_pools, input_asset_id=input_asset_id, block_rounds=rounds)
            pair = tuple(sorted((first.asset_a_id, first.asset_b_id)))
            direction = direction_label(route_pools, input_asset_id)

            # Coarse pass
            coarse = coarse_to_fine_sizes(min_size=self.min_size, max_size=self.max_size)
            best_opp: Opportunity | None = None
            best_size = coarse[0]
            for size in coarse:
                routes_before += 1
                sizes_evaluated += 1
                opp = self._evaluate_two_leg(first, second, input_asset_id, size)
                if opp is None:
                    raw_rejection_noise["quote_unavailable"] += 1
                    continue
                if best_opp is None or opp.expected_net_profit > best_opp.expected_net_profit:
                    best_opp = opp
                    best_size = size

            if best_opp is None:
                continue

            # Fine pass around best coarse size
            fine = coarse_to_fine_sizes(
                min_size=self.min_size,
                max_size=self.max_size,
                best_coarse=best_size,
            )
            for size in fine:
                if size in coarse:
                    continue
                routes_before += 1
                sizes_evaluated += 1
                opp = self._evaluate_two_leg(first, second, input_asset_id, size)
                if opp is None:
                    raw_rejection_noise["quote_unavailable"] += 1
                    continue
                if opp.expected_net_profit > best_opp.expected_net_profit:
                    best_opp = opp
                    best_size = size

            # One unique route after size selection
            optimized = OptimizedRoute(
                identity_key=identity,
                opportunity=best_opp,
                pools=route_pools,
                pair=(int(pair[0]), int(pair[1])),
                direction=direction,
                best_size=float(best_size),
                gross_profit=float(best_opp.gross_profit),
                net_profit=float(best_opp.expected_net_profit),
                dex_fees=float(best_opp.total_dex_fees),
                network_fee=float(best_opp.estimated_network_fee),
                price_impact_bps=float(best_opp.max_price_impact_bps),
                slippage_buffer=float(best_opp.slippage_buffer),
                safety_buffer_bps=float(self.risk_engine.policy.safety_buffer_bps),
                block_round=max(rounds),
                paper_eligible=False,
                paper_reason="",
            )
            existing = best_by_identity.get(identity)
            if existing is None or optimized.net_profit > existing.net_profit:
                best_by_identity[identity] = optimized

        optimized_list = sorted(best_by_identity.values(), key=lambda item: item.net_profit, reverse=True)

        # Paper selection: all approved + best near-miss per pair/direction
        paper_rows: list[Opportunity] = []
        near_miss_by_key: dict[tuple, OptimizedRoute] = {}
        aggregate: dict[str, int] = defaultdict(int)
        for noise_key, count in raw_rejection_noise.items():
            aggregate[noise_key] += count

        for item in optimized_list:
            opp = item.opportunity
            skip = str(opp.skip_reason or "")
            if skip in {"quote_unavailable", "fee_conversion_unavailable"}:
                aggregate[skip] += 1
                item.paper_eligible = False
                item.paper_reason = skip
                continue
            if is_impossible_or_non_positive(opp):
                aggregate[SKIP_IMPOSSIBLE] += 1
                item.paper_eligible = False
                item.paper_reason = SKIP_IMPOSSIBLE
                continue
            if opp.status == "approved":
                item.paper_eligible = True
                item.paper_reason = "risk_approved"
                paper_rows.append(opp)
                continue
            # Candidate near-miss (risk rejected but positive gross)
            nm_key = (item.pair, item.direction)
            current = near_miss_by_key.get(nm_key)
            if current is None or item.net_profit > current.net_profit:
                near_miss_by_key[nm_key] = item
            reason = opp.skip_reason or "risk_rejected"
            aggregate[reason] += 1
            item.paper_eligible = False
            item.paper_reason = reason

        near_misses_sorted = sorted(near_miss_by_key.values(), key=lambda item: item.net_profit, reverse=True)
        for item in near_misses_sorted:
            # Paper-track best near-miss; subtract from noise aggregate for that reason once
            reason = item.opportunity.skip_reason or "risk_rejected"
            if aggregate.get(reason, 0) > 0:
                aggregate[reason] -= 1
                if aggregate[reason] <= 0:
                    aggregate.pop(reason, None)
            item.paper_eligible = True
            item.paper_reason = f"near_miss:{reason}"
            paper_rows.append(item.opportunity)
            # Remaining non-near-miss routes already counted in aggregate

        # Routes that were risk-rejected but not selected as near-miss stay in aggregate only
        near_miss_ids = {id(item) for item in near_misses_sorted}
        for item in optimized_list:
            if item.opportunity.status == "approved":
                continue
            if is_impossible_or_non_positive(item.opportunity):
                continue
            if id(item) in near_miss_ids:
                continue
            # already counted in aggregate when first scanned

        best_gross = max((item.gross_profit for item in optimized_list), default=0.0)
        best_net = max((item.net_profit for item in optimized_list), default=0.0)
        any_approved = any(item.opportunity.status == "approved" for item in optimized_list)
        selected_pair = list(optimized_list[0].pair) if optimized_list else None

        near_miss_public = [
            {
                "pair": list(item.pair),
                "direction": item.direction,
                "bestSize": item.best_size,
                "grossProfit": item.gross_profit,
                "netProfit": item.net_profit,
                "dexFees": item.dex_fees,
                "networkFee": item.network_fee,
                "priceImpactBps": item.price_impact_bps,
                "slippageBuffer": item.slippage_buffer,
                "skipReason": item.opportunity.skip_reason,
                "riskRules": item.opportunity.risk_rules,
                "venues": [leg.get("venue") for leg in item.opportunity.route],
                "poolIds": item.opportunity.involved_pool_ids,
                "blockRound": item.block_round,
            }
            for item in near_misses_sorted[:5]
        ]

        return OptimizerReport(
            routes_before_dedupe=routes_before,
            routes_after_dedupe=len(optimized_list),
            sizes_evaluated=sizes_evaluated,
            paper_rows=paper_rows,
            optimized_routes=optimized_list,
            near_misses=near_miss_public,
            aggregate_rejections=dict(sorted(aggregate.items(), key=lambda kv: (-kv[1], kv[0]))),
            best_gross=best_gross,
            best_net=best_net,
            any_risk_approved=any_approved,
            selected_pair=selected_pair,
        )

    def _enumerate_two_leg_skeletons(self, pools: list[Pool]) -> list[tuple[Pool, Pool, int]]:
        grouped: dict[tuple[int, int], list[Pool]] = defaultdict(list)
        for pool in pools:
            if pool.reserve_a <= 0 or pool.reserve_b <= 0:
                continue
            grouped[pool.asset_pair].append(pool)

        skeletons: list[tuple[Pool, Pool, int]] = []
        for pair_pools in grouped.values():
            if len(pair_pools) < 2:
                continue
            # Every fee tier / venue combination, both directions (first->second).
            for first, second in permutations(pair_pools, 2):
                if first.pool_id == second.pool_id:
                    continue
                # ALGO-in when pair includes ALGO; otherwise both assets.
                if ALGO_ASSET_ID in first.asset_pair:
                    input_assets = [ALGO_ASSET_ID]
                else:
                    input_assets = [first.asset_a_id, first.asset_b_id]
                for input_asset_id in input_assets:
                    skeletons.append((first, second, int(input_asset_id)))
        return skeletons

    def _evaluate_two_leg(
        self,
        first: Pool,
        second: Pool,
        input_asset_id: int,
        trade_size: float,
    ) -> Opportunity | None:
        first_quote = first.quote(input_asset_id=input_asset_id, input_amount=float(trade_size))
        if first_quote is None:
            return None
        second_quote = second.quote(
            input_asset_id=first_quote.output_asset_id,
            input_amount=first_quote.output_amount,
        )
        if second_quote is None:
            return None
        return self._engine._build_opportunity(
            pools=[first, second],
            quotes=[first_quote, second_quote],
            input_asset_id=input_asset_id,
            input_amount=float(trade_size),
            route_kind="two_leg_venue_arb",
        )


def pools_from_store_rows(rows: list[dict]) -> list[Pool]:
    """Hydrate pools from store rows. Never invents captured_at with wall clock."""
    pools: list[Pool] = []
    for row in rows:
        raw_capture = row.get("captured_at", row.get("capturedAt", None))
        if raw_capture is None:
            # Fail closed: skip rows without source capture (do not time.time()).
            continue
        try:
            captured_at = float(raw_capture)
        except (TypeError, ValueError):
            continue
        if captured_at <= 0:
            continue
        pools.append(
            Pool(
                pool_id=str(row.get("pool_id") or row.get("poolId") or ""),
                venue_id=str(row.get("venue_id") or row.get("venue") or ""),
                app_id=int(row.get("app_id") or row.get("appId") or 0),
                asset_a_id=int(row.get("asset_a_id") or (row.get("assets") or [0, 0])[0] or 0),
                asset_b_id=int(row.get("asset_b_id") or (row.get("assets") or [0, 0])[1] or 0),
                reserve_a=float(row.get("reserve_a") or (row.get("reserves") or {}).get("a") or 0.0),
                reserve_b=float(row.get("reserve_b") or (row.get("reserves") or {}).get("b") or 0.0),
                fee_bps=int(row.get("fee_bps") or row.get("feeTier") or 0),
                block_round=int(row.get("block_round") or row.get("blockRound") or 0),
                captured_at=captured_at,
            )
        )
    return [p for p in pools if p.pool_id and p.reserve_a > 0 and p.reserve_b > 0]


def run_optimizer_on_store(
    *,
    settings: Settings | None = None,
    store: MarketStore | None = None,
    persist: bool = True,
) -> dict:
    """Optimize routes from latest stored snapshots (no live connector required)."""
    active = settings or get_settings()
    active_store = store or MarketStore(active.database_path)
    active_store.initialize(run_backfills=False)

    paper_before = len(active_store.list_paper_trades(limit=10_000))
    rows = active_store.list_latest_pools(limit=200)
    pools = pools_from_store_rows(rows)

    verified_ids = load_paper_verified_app_ids(active_store, network=active.network)
    if verified_ids:
        pools = [p for p in pools if int(p.app_id) in set(verified_ids)]

    risk_engine = RiskEngine(
        policy_from_settings(active, paper_verified_app_ids=verified_ids if verified_ids else None)
    )
    # Prefer liquid ALGO/USDC when thin PNET is present: filter by min reserve floor
    from algopulse.liquidity_opportunity import rank_shared_pairs, pools_for_pairs

    min_floor = max(1.0, min(float(getattr(active, "min_pool_reserve", 1000.0) or 1000.0) * 0.001, 50.0))
    ranked = rank_shared_pairs(
        pools,
        network=active.network,
        preferred_pairs=((0, 31_566_704), (0, 3_169_177_585)),
        min_cross_venue_liquidity=min_floor,
        min_venue_reserve=min_floor,
    )
    accepted = ranked["accepted"]
    eval_pools = pools
    if accepted:
        eval_pools = pools_for_pairs(pools, [tuple(item["pair"]) for item in accepted])

    optimizer = ProfitSeekingRouteOptimizer(risk_engine)
    report = optimizer.optimize(eval_pools)
    if accepted:
        report.selected_pair = list(accepted[0]["pair"])

    if persist and report.paper_rows:
        active_store.record_opportunities(report.paper_rows)
        for opportunity in report.paper_rows:
            would_execute = opportunity.status == "approved"
            notes = (
                "would_execute: risk approved; optimizer paper track"
                if would_execute
                else f"near_miss: {opportunity.skip_reason or 'risk'}; optimizer paper track"
            )
            active_store.record_paper_trade(
                opportunity=opportunity,
                would_execute=would_execute,
                notes=notes,
            )

    paper_after = len(active_store.list_paper_trades(limit=10_000))
    result = report.to_dict()
    result.update(
        {
            "paperRowsBefore": paper_before,
            "paperRowsAfter": paper_after,
            "paperRowsAdded": max(0, paper_after - paper_before),
            "poolsUsed": len(eval_pools),
            "skippedPairs": ranked.get("skipped") or [],
            "source": "stored_mainnet_snapshots",
            "databasePath": str(active.database_path),
        }
    )
    active_store.record_service_health(
        "route_optimizer",
        "ok" if report.any_risk_approved else "degraded",
        detail="profit_seeking_optimize",
        metrics={
            "routesBeforeDedupe": report.routes_before_dedupe,
            "routesAfterDedupe": report.routes_after_dedupe,
            "paperRows": len(report.paper_rows),
            "bestNet": report.best_net,
            "anyRiskApproved": report.any_risk_approved,
            "aggregateRejections": report.aggregate_rejections,
        },
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Profit-seeking route optimizer (stored snapshots).")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="",
        help="Data directory containing market.db (e.g. data/mainnet-live-scanner).",
    )
    parser.add_argument("--no-persist", action="store_true", help="Do not write paper rows.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    if args.data_dir:
        data_dir = Path(args.data_dir).resolve()
        from dataclasses import replace

        settings = replace(
            settings,
            data_dir=data_dir,
            database_path=data_dir / "market.db",
        )
    result = run_optimizer_on_store(settings=settings, persist=not args.no_persist)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
