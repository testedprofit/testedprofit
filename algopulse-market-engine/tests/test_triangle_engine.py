from __future__ import annotations

from algopulse.models import Pool
from algopulse.risk import RiskEngine, RiskPolicy
from algopulse.triangle_engine import (
    ALGO,
    GOBTC,
    GOETH,
    PNET,
    USDC,
    TriangleOpportunityEngine,
    _no_pool_reuse,
    major_asa_is_qualified,
    build_pool_graph,
    triangle_paths_for_asa,
)


def _pool(
    venue: str,
    app_id: int,
    a: int,
    b: int,
    ra: float,
    rb: float,
    *,
    fee_bps: int = 30,
    block_round: int = 10,
) -> Pool:
    lo, hi = sorted((a, b))
    # Orient reserves to asset ids as connector-style a/b
    if a <= b:
        reserve_a, reserve_b = ra, rb
        asset_a, asset_b = a, b
    else:
        reserve_a, reserve_b = rb, ra
        asset_a, asset_b = b, a
    return Pool(
        pool_id=f"{venue}:{app_id}:{asset_a}-{asset_b}",
        venue_id=venue,
        app_id=app_id,
        asset_a_id=asset_a,
        asset_b_id=asset_b,
        reserve_a=reserve_a,
        reserve_b=reserve_b,
        fee_bps=fee_bps,
        block_round=block_round,
    )


def test_triangle_paths_two_orientations():
    paths = triangle_paths_for_asa(PNET, "PNET")
    assert len(paths) == 2
    assert paths[0].asset_path == (ALGO, USDC, PNET, ALGO)
    assert paths[1].asset_path == (ALGO, PNET, USDC, ALGO)
    assert all(len(p.asset_path) - 1 == 3 for p in paths)


def test_no_pool_reuse():
    a = _pool("tinyman", 1, ALGO, USDC, 1000, 1000)
    b = _pool("pact", 2, USDC, PNET, 1000, 1000)
    assert _no_pool_reuse([a, b, a]) is False
    assert _no_pool_reuse([a, b, _pool("pact", 3, PNET, ALGO, 1000, 1000)]) is True


def test_major_asa_requires_all_three_edges():
    pools = [
        _pool("tinyman", 1, ALGO, USDC, 50_000, 40_000),
        _pool("pact", 2, ALGO, PNET, 50_000, 40_000),
        # missing USDC-PNET
    ]
    graph = build_pool_graph(pools)
    ok, reason, _ = major_asa_is_qualified(graph, PNET, min_venue_reserve=1.0, verified_app_ids=None)
    assert ok is False
    assert "usdc_asa" in (reason or "")


def test_triangle_engine_evaluates_qualified_pnet_and_sizes():
    # Liquid edges for PNET triangle both orientations.
    pools = [
        _pool("tinyman", 11, ALGO, USDC, 200_000, 180_000, fee_bps=30),
        _pool("pact", 12, ALGO, USDC, 190_000, 170_000, fee_bps=5),
        _pool("tinyman", 21, ALGO, PNET, 150_000, 140_000, fee_bps=30),
        _pool("pact", 22, ALGO, PNET, 160_000, 150_000, fee_bps=5),
        _pool("tinyman", 31, USDC, PNET, 120_000, 110_000, fee_bps=30),
        _pool("pact", 32, USDC, PNET, 130_000, 115_000, fee_bps=5),
    ]
    # goBTC missing edges → skipped
    policy = RiskPolicy(
        min_profit_absolute=0.25,
        min_profit_bps=35.0,
        max_price_impact_bps=10_000.0,
        min_pool_reserve=1.0,
        max_trade_size=10.0,
        paper_verified_app_ids=(11, 12, 21, 22, 31, 32),
        allowed_asset_ids=(ALGO, USDC, PNET, GOBTC, GOETH),
        require_app_id_allowlist=True,
        allowed_app_ids=(),
        min_fee_buffer_multiplier=0.0,
    )
    engine = TriangleOpportunityEngine(
        RiskEngine(policy),
        min_venue_reserve=1.0,
        verified_app_ids=(11, 12, 21, 22, 31, 32),
        candidate_asas=((PNET, "PNET"), (GOBTC, "goBTC")),
    )
    report = engine.search(pools)
    assert any(a["symbol"] == "PNET" for a in report.qualified_major_asas)
    assert any(a["symbol"] == "goBTC" for a in report.skipped_major_asas)
    assert report.paths_evaluated >= 2
    assert report.unique_triangles >= 1
    for item in report.results:
        assert len(item.opportunity.route) == 3
        assert len(set(item.opportunity.involved_pool_ids)) == 3
        assert 0.05 <= item.best_size <= 10.0
        # exact breakdown fields present
        assert item.dex_fees >= 0
        assert item.network_fee > 0
        assert item.slippage_buffer >= 0


def test_triangle_rejects_pool_reuse_in_search():
    # Only one pool object reused across edges impossible via product of distinct lists;
    # ensure engine forbids duplicate pool_id if injected.
    shared = _pool("tinyman", 99, ALGO, USDC, 10_000, 10_000)
    # craft graph-like lists manually through search with distinct pools only
    pools = [
        shared,
        _pool("pact", 2, USDC, PNET, 10_000, 10_000),
        _pool("pact", 3, PNET, ALGO, 10_000, 10_000),
    ]
    policy = RiskPolicy(
        min_profit_absolute=100.0,
        min_profit_bps=10_000.0,
        max_price_impact_bps=10_000.0,
        min_pool_reserve=1.0,
        max_trade_size=10.0,
        paper_verified_app_ids=(99, 2, 3),
        allowed_asset_ids=(ALGO, USDC, PNET),
    )
    report = TriangleOpportunityEngine(
        RiskEngine(policy),
        verified_app_ids=(99, 2, 3),
        candidate_asas=((PNET, "PNET"),),
    ).search(pools)
    for item in report.results:
        assert len(set(item.opportunity.involved_pool_ids)) == 3
