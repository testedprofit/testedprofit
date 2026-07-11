"""MainNet triangle opportunity engine (max three swaps).

Paths:
  ALGO -> USDC -> major ASA -> ALGO
  ALGO -> major ASA -> USDC -> ALGO

Uses real Tinyman/Pact pools, existing liquidity + verification gates, and
adaptive coarse-to-fine sizing. Does not loosen risk limits.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import Any

from algopulse.config import Settings, get_settings
from algopulse.engine import RouteEngine
from algopulse.liquidity_opportunity import min_reserve, pool_liquidity_estimate
from algopulse.models import Opportunity, Pool, Quote
from algopulse.risk import RiskEngine, policy_from_settings
from algopulse.route_optimizer import (
    SKIP_IMPOSSIBLE,
    coarse_to_fine_sizes,
    is_impossible_or_non_positive,
    pools_from_store_rows,
)
from algopulse.store import MarketStore
from algopulse.verified_pool_registry import (
    build_verified_pool_registry,
    load_paper_verified_app_ids,
)


ALGO = 0
USDC = 31_566_704
PNET = 3_169_177_585
# Folks / goBridge MainNet ASA IDs
GOBTC = 386_192_725
GOETH = 386_195_940

CANDIDATE_MAJOR_ASAS: tuple[tuple[int, str], ...] = (
    (PNET, "PNET"),
    (GOBTC, "goBTC"),
    (GOETH, "goETH"),
)

MAX_LEGS = 3
MIN_SIZE = 0.05
MAX_SIZE = 10.0


@dataclass
class TrianglePath:
    asset_path: tuple[int, ...]
    label: str
    major_asa: int
    major_symbol: str


@dataclass
class TriangleResult:
    path: TrianglePath
    opportunity: Opportunity
    pools: list[Pool]
    best_size: float
    gross_profit: float
    net_profit: float
    dex_fees: float
    network_fee: float
    price_impact_bps: float
    slippage_buffer: float
    safety_buffer_bps: float
    paper_eligible: bool
    paper_reason: str


@dataclass
class TriangleEngineReport:
    assets_discovered: list[dict] = field(default_factory=list)
    pools_discovered: list[dict] = field(default_factory=list)
    qualified_major_asas: list[dict] = field(default_factory=list)
    skipped_major_asas: list[dict] = field(default_factory=list)
    paths_evaluated: int = 0
    skeleton_count: int = 0
    sizes_evaluated: int = 0
    unique_triangles: int = 0
    paper_rows: list[Opportunity] = field(default_factory=list)
    results: list[TriangleResult] = field(default_factory=list)
    near_misses: list[dict] = field(default_factory=list)
    aggregate_rejections: dict[str, int] = field(default_factory=dict)
    best_gross: float = 0.0
    best_net: float = 0.0
    best_size: float | None = None
    best_path: list[int] | None = None
    any_risk_approved: bool = False

    def to_dict(self) -> dict:
        best = self.results[0] if self.results else None
        return {
            "assetsDiscovered": self.assets_discovered,
            "poolsDiscovered": self.pools_discovered,
            "qualifiedMajorAsas": self.qualified_major_asas,
            "skippedMajorAsas": self.skipped_major_asas,
            "trianglePathsEvaluated": self.paths_evaluated,
            "skeletonCount": self.skeleton_count,
            "sizesEvaluated": self.sizes_evaluated,
            "uniqueTriangles": self.unique_triangles,
            "paperRowCount": len(self.paper_rows),
            "bestGrossProfit": self.best_gross,
            "bestNetProfit": self.best_net,
            "bestInputSize": self.best_size,
            "bestPath": self.best_path,
            "bestPathLabel": best.path.label if best else None,
            "bestVenues": [leg.get("venue") for leg in best.opportunity.route] if best else None,
            "bestPoolIds": best.opportunity.involved_pool_ids if best else None,
            "bestRiskStatus": best.opportunity.status if best else None,
            "bestSkipReason": best.opportunity.skip_reason if best else None,
            "bestRiskRules": best.opportunity.risk_rules if best else None,
            "anyRiskApproved": self.any_risk_approved,
            "topNearMisses": self.near_misses[:5],
            "aggregateRejections": self.aggregate_rejections,
            "riskLimitsUnchanged": True,
            "maxSwaps": MAX_LEGS,
            "productionReady": False,
            "signingEnabled": False,
        }


def _pair_key(a: int, b: int) -> tuple[int, int]:
    return tuple(sorted((int(a), int(b))))


def _asset_symbol(asset_id: int) -> str:
    known = {ALGO: "ALGO", USDC: "USDC", PNET: "PNET", GOBTC: "goBTC", GOETH: "goETH"}
    return known.get(int(asset_id), f"ASA{asset_id}")


def build_pool_graph(pools: list[Pool]) -> dict[tuple[int, int], list[Pool]]:
    graph: dict[tuple[int, int], list[Pool]] = defaultdict(list)
    for pool in pools:
        if pool.reserve_a <= 0 or pool.reserve_b <= 0:
            continue
        graph[pool.asset_pair].append(pool)
    return graph


def leg_pools_qualified(
    pools: list[Pool],
    *,
    min_venue_reserve: float,
    verified_app_ids: set[int] | None,
) -> list[Pool]:
    """Apply liquidity + optional paper-verified app gates to a leg's candidate pools."""
    qualified: list[Pool] = []
    for pool in pools:
        if min_reserve(pool) < min_venue_reserve:
            continue
        if pool_liquidity_estimate(pool) <= 0:
            continue
        if verified_app_ids is not None and verified_app_ids and int(pool.app_id) not in verified_app_ids:
            continue
        qualified.append(pool)
    return qualified


def major_asa_is_qualified(
    graph: dict[tuple[int, int], list[Pool]],
    major_asa: int,
    *,
    min_venue_reserve: float,
    verified_app_ids: set[int] | None,
) -> tuple[bool, str | None, dict[str, list[Pool]]]:
    """Every required edge for both triangle orientations must have a liquid verified pool.

    Required undirected edges: ALGO-USDC, ALGO-ASA, USDC-ASA.
    """
    edges = {
        "algo_usdc": _pair_key(ALGO, USDC),
        "algo_asa": _pair_key(ALGO, major_asa),
        "usdc_asa": _pair_key(USDC, major_asa),
    }
    qualified_edges: dict[str, list[Pool]] = {}
    for name, pair in edges.items():
        pools = leg_pools_qualified(
            graph.get(pair, []),
            min_venue_reserve=min_venue_reserve,
            verified_app_ids=verified_app_ids,
        )
        if not pools:
            return False, f"missing_or_unqualified_edge:{name}:{pair[0]}-{pair[1]}", qualified_edges
        qualified_edges[name] = pools
    return True, None, qualified_edges


def triangle_paths_for_asa(major_asa: int, symbol: str) -> list[TrianglePath]:
    return [
        TrianglePath(
            asset_path=(ALGO, USDC, major_asa, ALGO),
            label=f"ALGO->USDC->{symbol}->ALGO",
            major_asa=major_asa,
            major_symbol=symbol,
        ),
        TrianglePath(
            asset_path=(ALGO, major_asa, USDC, ALGO),
            label=f"ALGO->{symbol}->USDC->ALGO",
            major_asa=major_asa,
            major_symbol=symbol,
        ),
    ]


def _no_pool_reuse(pools: list[Pool]) -> bool:
    ids = [p.pool_id for p in pools]
    return len(ids) == len(set(ids))


class TriangleOpportunityEngine:
    def __init__(
        self,
        risk_engine: RiskEngine,
        *,
        min_size: float = MIN_SIZE,
        max_size: float | None = None,
        min_venue_reserve: float = 1.0,
        verified_app_ids: tuple[int, ...] | set[int] | None = None,
        candidate_asas: tuple[tuple[int, str], ...] = CANDIDATE_MAJOR_ASAS,
    ) -> None:
        self.risk_engine = risk_engine
        policy_max = float(risk_engine.policy.max_trade_size or MAX_SIZE)
        self.min_size = max(MIN_SIZE, float(min_size))
        self.max_size = min(MAX_SIZE, policy_max if max_size is None else float(max_size))
        self.min_venue_reserve = float(min_venue_reserve)
        self.verified_app_ids = set(int(a) for a in verified_app_ids) if verified_app_ids else None
        self.candidate_asas = candidate_asas
        self._engine = RouteEngine(risk_engine=risk_engine, trade_sizes=[self.min_size])

    def search(self, pools: list[Pool]) -> TriangleEngineReport:
        graph = build_pool_graph(pools)
        report = TriangleEngineReport()

        assets = sorted({a for p in pools for a in (p.asset_a_id, p.asset_b_id)})
        report.assets_discovered = [
            {"assetId": asset_id, "symbol": _asset_symbol(asset_id)} for asset_id in assets
        ]
        report.pools_discovered = [
            {
                "poolId": p.pool_id,
                "venueId": p.venue_id,
                "appId": p.app_id,
                "pair": list(p.asset_pair),
                "feeBps": p.fee_bps,
                "reserveA": p.reserve_a,
                "reserveB": p.reserve_b,
                "liquidity": pool_liquidity_estimate(p),
                "blockRound": p.block_round,
            }
            for p in pools
        ]

        # Always need ALGO-USDC base edge.
        algo_usdc = leg_pools_qualified(
            graph.get(_pair_key(ALGO, USDC), []),
            min_venue_reserve=self.min_venue_reserve,
            verified_app_ids=self.verified_app_ids,
        )
        if not algo_usdc:
            report.aggregate_rejections["missing_algo_usdc_edge"] = 1
            return report

        best_by_key: dict[tuple, TriangleResult] = {}
        sizes_evaluated = 0
        skeleton_count = 0
        paths_evaluated = 0

        for major_asa, symbol in self.candidate_asas:
            ok, reason, _edges = major_asa_is_qualified(
                graph,
                major_asa,
                min_venue_reserve=self.min_venue_reserve,
                verified_app_ids=self.verified_app_ids,
            )
            if not ok:
                report.skipped_major_asas.append(
                    {"assetId": major_asa, "symbol": symbol, "reason": reason}
                )
                continue
            report.qualified_major_asas.append({"assetId": major_asa, "symbol": symbol})

            for path in triangle_paths_for_asa(major_asa, symbol):
                paths_evaluated += 1
                leg_sets = []
                incomplete = False
                for left, right in zip(path.asset_path, path.asset_path[1:]):
                    candidates = leg_pools_qualified(
                        graph.get(_pair_key(left, right), []),
                        min_venue_reserve=self.min_venue_reserve,
                        verified_app_ids=self.verified_app_ids,
                    )
                    if not candidates:
                        incomplete = True
                        break
                    leg_sets.append(candidates)
                if incomplete or len(leg_sets) != MAX_LEGS:
                    report.aggregate_rejections["incomplete_path_legs"] = (
                        report.aggregate_rejections.get("incomplete_path_legs", 0) + 1
                    )
                    continue

                for route_pools in product(*leg_sets):
                    route_list = list(route_pools)
                    if len(route_list) > MAX_LEGS:
                        continue
                    if not _no_pool_reuse(route_list):
                        report.aggregate_rejections["pool_reuse_forbidden"] = (
                            report.aggregate_rejections.get("pool_reuse_forbidden", 0) + 1
                        )
                        continue
                    skeleton_count += 1
                    # Coarse-to-fine size optimization (reuse existing ladder).
                    coarse = coarse_to_fine_sizes(min_size=self.min_size, max_size=self.max_size)
                    best_opp: Opportunity | None = None
                    best_size = coarse[0]
                    for size in coarse:
                        sizes_evaluated += 1
                        opp = self._evaluate_path(path.asset_path, route_list, size)
                        if opp is None:
                            report.aggregate_rejections["quote_unavailable"] = (
                                report.aggregate_rejections.get("quote_unavailable", 0) + 1
                            )
                            continue
                        if best_opp is None or opp.expected_net_profit > best_opp.expected_net_profit:
                            best_opp = opp
                            best_size = size
                    if best_opp is None:
                        continue
                    fine = coarse_to_fine_sizes(
                        min_size=self.min_size,
                        max_size=self.max_size,
                        best_coarse=best_size,
                    )
                    for size in fine:
                        if size in coarse:
                            continue
                        sizes_evaluated += 1
                        opp = self._evaluate_path(path.asset_path, route_list, size)
                        if opp is None:
                            continue
                        if opp.expected_net_profit > best_opp.expected_net_profit:
                            best_opp = opp
                            best_size = size

                    identity = (
                        tuple(p.pool_id for p in route_list),
                        path.asset_path,
                        tuple(int(p.block_round) for p in route_list),
                    )
                    result = TriangleResult(
                        path=path,
                        opportunity=best_opp,
                        pools=route_list,
                        best_size=float(best_size),
                        gross_profit=float(best_opp.gross_profit),
                        net_profit=float(best_opp.expected_net_profit),
                        dex_fees=float(best_opp.total_dex_fees),
                        network_fee=float(best_opp.estimated_network_fee),
                        price_impact_bps=float(best_opp.max_price_impact_bps),
                        slippage_buffer=float(best_opp.slippage_buffer),
                        safety_buffer_bps=float(self.risk_engine.policy.safety_buffer_bps),
                        paper_eligible=False,
                        paper_reason="",
                    )
                    existing = best_by_key.get(identity)
                    if existing is None or result.net_profit > existing.net_profit:
                        best_by_key[identity] = result

        results = sorted(best_by_key.values(), key=lambda item: item.net_profit, reverse=True)
        report.paths_evaluated = paths_evaluated
        report.skeleton_count = skeleton_count
        report.sizes_evaluated = sizes_evaluated
        report.unique_triangles = len(results)
        report.results = results

        # Paper: approved + best near-miss per path label
        paper: list[Opportunity] = []
        near_miss_by_path: dict[str, TriangleResult] = {}
        for item in results:
            opp = item.opportunity
            if is_impossible_or_non_positive(opp):
                report.aggregate_rejections[SKIP_IMPOSSIBLE] = (
                    report.aggregate_rejections.get(SKIP_IMPOSSIBLE, 0) + 1
                )
                item.paper_reason = SKIP_IMPOSSIBLE
                continue
            if opp.status == "approved":
                item.paper_eligible = True
                item.paper_reason = "risk_approved"
                paper.append(opp)
                continue
            reason = opp.skip_reason or "risk_rejected"
            report.aggregate_rejections[reason] = report.aggregate_rejections.get(reason, 0) + 1
            key = item.path.label
            cur = near_miss_by_path.get(key)
            if cur is None or item.net_profit > cur.net_profit:
                near_miss_by_path[key] = item

        for item in sorted(near_miss_by_path.values(), key=lambda r: r.net_profit, reverse=True):
            reason = item.opportunity.skip_reason or "risk_rejected"
            if report.aggregate_rejections.get(reason, 0) > 0:
                report.aggregate_rejections[reason] -= 1
                if report.aggregate_rejections[reason] <= 0:
                    report.aggregate_rejections.pop(reason, None)
            item.paper_eligible = True
            item.paper_reason = f"near_miss:{reason}"
            paper.append(item.opportunity)

        report.paper_rows = paper
        report.near_misses = [
            {
                "path": item.path.label,
                "assetPath": list(item.path.asset_path),
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
            }
            for item in sorted(near_miss_by_path.values(), key=lambda r: r.net_profit, reverse=True)[:5]
        ]
        report.best_gross = max((r.gross_profit for r in results), default=0.0)
        report.best_net = max((r.net_profit for r in results), default=0.0)
        if results:
            report.best_size = results[0].best_size
            report.best_path = list(results[0].path.asset_path)
        report.any_risk_approved = any(r.opportunity.status == "approved" for r in results)
        return report

    def _evaluate_path(
        self,
        asset_path: tuple[int, ...],
        pools: list[Pool],
        trade_size: float,
    ) -> Opportunity | None:
        if len(pools) != len(asset_path) - 1 or len(pools) > MAX_LEGS:
            return None
        if not _no_pool_reuse(pools):
            return None
        quotes: list[Quote] = []
        amount = float(trade_size)
        for pool, input_asset_id, output_asset_id in zip(pools, asset_path, asset_path[1:]):
            quote = pool.quote(input_asset_id=int(input_asset_id), input_amount=amount)
            if quote is None or int(quote.output_asset_id) != int(output_asset_id):
                return None
            quotes.append(quote)
            amount = quote.output_amount
        if len(quotes) != MAX_LEGS:
            return None
        return self._engine._build_opportunity(
            pools=pools,
            quotes=quotes,
            input_asset_id=int(asset_path[0]),
            input_amount=float(trade_size),
            route_kind="three_leg_triangle",
        )


def _discover_extra_pools(settings: Settings, pairs: list[tuple[int, int]]) -> list[Pool]:
    """Optional live connector fetch for missing candidate edges (canary only)."""
    if not pairs:
        return []
    from dataclasses import replace
    from algopulse.connectors.tinyman import TinymanConnector
    from algopulse.connectors.pact import PactConnector

    scoped = replace(settings, asset_pairs=tuple(sorted({_pair_key(a, b) for a, b in pairs})))
    found: list[Pool] = []
    for cls in (TinymanConnector, PactConnector):
        try:
            connector = cls(scoped)
            found.extend(connector.list_pools())
        except Exception:
            continue
    return found


def run_triangle_canary(
    *,
    settings: Settings | None = None,
    store: MarketStore | None = None,
    persist: bool = True,
    discover_missing: bool = True,
) -> dict:
    active = settings or get_settings()
    active_store = store or MarketStore(active.database_path)
    active_store.initialize(run_backfills=False)

    rows = active_store.list_latest_pools(limit=500)
    pools = pools_from_store_rows(rows)

    # Discover missing edges for candidate ASAs so goBTC/goETH can qualify if liquid.
    if discover_missing:
        needed: list[tuple[int, int]] = [(ALGO, USDC)]
        for asa, _sym in CANDIDATE_MAJOR_ASAS:
            needed.extend([(ALGO, asa), (USDC, asa)])
        have = {p.asset_pair for p in pools}
        missing = [pair for pair in needed if _pair_key(*pair) not in have]
        if missing:
            extra = _discover_extra_pools(active, missing)
            # de-dupe by pool_id
            by_id = {p.pool_id: p for p in pools}
            for p in extra:
                by_id[p.pool_id] = p
            pools = list(by_id.values())
            if extra:
                active_store.record_pool_snapshots(extra)

    # Verify on-chain; paper risk uses accepted IDs only.
    registry = build_verified_pool_registry(pools, settings=active, store=active_store)
    verified_ids = tuple(int(a) for a in (registry.get("acceptedAppIds") or []))
    if verified_ids:
        pools = [p for p in pools if int(p.app_id) in set(verified_ids)]

    asset_ids = sorted({a for p in pools for a in (p.asset_a_id, p.asset_b_id)} | {ALGO, USDC})
    from dataclasses import replace

    risk_settings = replace(
        active,
        allowed_asset_ids=tuple(sorted(set(active.allowed_asset_ids) | set(asset_ids))),
        allowed_app_ids=tuple(active.allowed_app_ids),
        require_app_id_allowlist=bool(active.require_app_id_allowlist),
    )
    risk_engine = RiskEngine(
        policy_from_settings(risk_settings, paper_verified_app_ids=verified_ids)
    )
    min_floor = max(
        1.0,
        min(float(getattr(active, "min_pool_reserve", 1000.0) or 1000.0) * 0.001, 50.0),
    )
    engine = TriangleOpportunityEngine(
        risk_engine,
        min_venue_reserve=min_floor,
        verified_app_ids=verified_ids if verified_ids else None,
    )
    report = engine.search(pools)

    if persist and report.paper_rows:
        active_store.record_opportunities(report.paper_rows)
        for opportunity in report.paper_rows:
            would_execute = opportunity.status == "approved"
            notes = (
                "would_execute: risk approved; triangle paper track"
                if would_execute
                else f"near_miss triangle: {opportunity.skip_reason or 'risk'}"
            )
            active_store.record_paper_trade(
                opportunity=opportunity,
                would_execute=would_execute,
                notes=notes,
            )

    payload = report.to_dict()
    payload.update(
        {
            "source": "mainnet_triangle_canary",
            "databasePath": str(active.database_path),
            "verifiedAppIds": list(verified_ids),
            "registryAcceptedCount": registry.get("acceptedCount"),
            "poolsUsed": len(pools),
        }
    )
    active_store.record_service_health(
        "triangle_engine",
        "ok" if report.any_risk_approved else "degraded",
        detail="triangle_canary",
        metrics={
            "pathsEvaluated": report.paths_evaluated,
            "uniqueTriangles": report.unique_triangles,
            "paperRows": len(report.paper_rows),
            "bestNet": report.best_net,
            "bestGross": report.best_gross,
            "bestSize": report.best_size,
            "anyRiskApproved": report.any_risk_approved,
            "qualifiedAsas": report.qualified_major_asas,
            "skippedAsas": report.skipped_major_asas,
        },
    )
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MainNet triangle opportunity engine canary.")
    parser.add_argument("--data-dir", type=str, default="data/mainnet-live-scanner")
    parser.add_argument("--no-persist", action="store_true")
    parser.add_argument("--no-discover", action="store_true", help="Use store pools only.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    if args.data_dir:
        from dataclasses import replace

        data_dir = Path(args.data_dir).resolve()
        settings = replace(settings, data_dir=data_dir, database_path=data_dir / "market.db")
    result = run_triangle_canary(
        settings=settings,
        persist=not args.no_persist,
        discover_missing=not args.no_discover,
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
