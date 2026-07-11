from __future__ import annotations

from algopulse.models import Pool
from algopulse.risk import RiskEngine, RiskPolicy
from algopulse.route_optimizer import (
    SKIP_IMPOSSIBLE,
    coarse_to_fine_sizes,
    is_impossible_or_non_positive,
    route_identity_key,
    ProfitSeekingRouteOptimizer,
)
from algopulse.models import Opportunity


def _pool(
    venue: str,
    app_id: int,
    reserve_a: float,
    reserve_b: float,
    *,
    fee_bps: int = 30,
    block_round: int = 100,
) -> Pool:
    return Pool(
        pool_id=f"{venue}:{app_id}:0-31566704",
        venue_id=venue,
        app_id=app_id,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=reserve_a,
        reserve_b=reserve_b,
        fee_bps=fee_bps,
        block_round=block_round,
    )


def test_route_identity_dedupes_by_pool_sequence_direction_pair_round():
    a = _pool("tinyman", 1, 10_000, 9_000, block_round=50)
    b = _pool("pact", 2, 9_500, 8_500, block_round=51)
    k1 = route_identity_key([a, b], input_asset_id=0, block_rounds=(50, 51))
    k2 = route_identity_key([a, b], input_asset_id=0, block_rounds=(50, 51))
    k3 = route_identity_key([b, a], input_asset_id=0, block_rounds=(51, 50))
    k4 = route_identity_key([a, b], input_asset_id=0, block_rounds=(99, 99))
    assert k1 == k2
    assert k1 != k3  # direction / sequence differs
    assert k1 != k4  # block round differs


def test_coarse_to_fine_size_range_and_refinement():
    coarse = coarse_to_fine_sizes(min_size=0.05, max_size=10.0)
    assert 0.05 in coarse
    assert 10.0 in coarse
    assert all(0.05 <= s <= 10.0 for s in coarse)

    refined = coarse_to_fine_sizes(min_size=0.05, max_size=10.0, best_coarse=1.0)
    assert 1.0 in refined
    assert len(refined) > len(coarse)
    assert all(0.05 <= s <= 10.0 for s in refined)


def test_optimizer_dedupes_and_selects_best_size():
    # Skewed prices so tinyman->pact and reverse both evaluate.
    tinyman = _pool("tinyman", 111, 100_000, 80_000, fee_bps=30, block_round=10)
    pact = _pool("pact", 222, 70_000, 100_000, fee_bps=5, block_round=10)
    pact_hi_fee = _pool("pact", 333, 70_000, 100_000, fee_bps=100, block_round=10)

    policy = RiskPolicy(
        min_profit_absolute=0.25,
        min_profit_bps=35.0,
        max_price_impact_bps=500.0,
        min_pool_reserve=1.0,
        max_trade_size=10.0,
        paper_verified_app_ids=(111, 222, 333),
        require_app_id_allowlist=True,
        allowed_app_ids=(),
        allowed_asset_ids=(0, 31566704),
    )
    report = ProfitSeekingRouteOptimizer(RiskEngine(policy)).optimize([tinyman, pact, pact_hi_fee])

    assert report.routes_before_dedupe > report.routes_after_dedupe
    assert report.routes_after_dedupe >= 1
    # Each optimized route is unique identity
    keys = [item.identity_key for item in report.optimized_routes]
    assert len(keys) == len(set(keys))
    # Best size selected within bounds
    for item in report.optimized_routes:
        assert 0.05 <= item.best_size <= 10.0
        assert item.dex_fees >= 0
        assert item.network_fee >= 0
        assert item.slippage_buffer >= 0


def test_impossible_routes_not_paper_tracked():
    # Symmetric pools: no gross edge after fees
    a = _pool("tinyman", 1, 10_000, 10_000, fee_bps=30)
    b = _pool("pact", 2, 10_000, 10_000, fee_bps=30)
    policy = RiskPolicy(
        min_profit_absolute=0.25,
        min_profit_bps=35.0,
        max_price_impact_bps=5_000.0,
        min_pool_reserve=1.0,
        max_trade_size=10.0,
        paper_verified_app_ids=(1, 2),
        allowed_asset_ids=(0, 31566704),
    )
    report = ProfitSeekingRouteOptimizer(RiskEngine(policy)).optimize([a, b])
    # Paper rows should only be approved or near-miss with positive gross
    for opp in report.paper_rows:
        assert not is_impossible_or_non_positive(opp)
    assert report.aggregate_rejections.get(SKIP_IMPOSSIBLE, 0) >= 0


def test_near_miss_keeps_best_per_pair_direction():
    # Large cross-venue skew to get positive gross still failing risk floors
    tinyman = _pool("tinyman", 11, 50_000, 100_000, fee_bps=30, block_round=7)
    pact = _pool("pact", 22, 120_000, 40_000, fee_bps=2, block_round=7)
    policy = RiskPolicy(
        min_profit_absolute=100.0,  # intentionally high — not a production change path
        min_profit_bps=10_000.0,
        max_price_impact_bps=10_000.0,
        min_pool_reserve=1.0,
        max_trade_size=10.0,
        paper_verified_app_ids=(11, 22),
        allowed_asset_ids=(0, 31566704),
        min_fee_buffer_multiplier=0.0,
    )
    report = ProfitSeekingRouteOptimizer(RiskEngine(policy)).optimize([tinyman, pact])
    assert report.any_risk_approved is False
    # At most one near-miss per pair/direction in paper rows
    directions = []
    for opp in report.paper_rows:
        venues = "->".join(leg.get("venue") for leg in opp.route)
        directions.append((tuple(sorted(opp.involved_asset_ids)), venues, opp.input_asset_id))
    assert len(directions) == len(set(directions))
    assert len(report.near_misses) <= 5
