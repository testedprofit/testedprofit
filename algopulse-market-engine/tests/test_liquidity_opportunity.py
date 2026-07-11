from __future__ import annotations

from algopulse.liquidity_opportunity import (
    SKIP_LOW_CROSS_VENUE_LIQUIDITY,
    adaptive_trade_sizes,
    rank_shared_pairs,
)
from algopulse.models import Opportunity, Pool


def _pool(venue: str, app_id: int, reserve_a: float, reserve_b: float, asset_b: int = 31566704) -> Pool:
    return Pool(
        pool_id=f"{venue}:{app_id}",
        venue_id=venue,
        app_id=app_id,
        asset_a_id=0,
        asset_b_id=asset_b,
        reserve_a=reserve_a,
        reserve_b=reserve_b,
        fee_bps=30,
        block_round=1,
    )


def test_rank_skips_low_cross_venue_liquidity_dust_pair():
    pools = [
        _pool("tinyman", 1, 10_000, 25_000, asset_b=3169177585),
        _pool("pact", 2, 0.000024, 0.05, asset_b=3169177585),  # effectively empty
        _pool("tinyman", 3, 50_000, 40_000, asset_b=31566704),
        _pool("pact", 4, 45_000, 38_000, asset_b=31566704),
    ]
    ranked = rank_shared_pairs(
        pools,
        preferred_pairs=((0, 3169177585), (0, 31566704)),
        min_cross_venue_liquidity=1.0,
        min_venue_reserve=1.0,
    )
    assert ranked["selected"]["pair"] == [0, 31566704]
    assert any(item["skipReason"] == SKIP_LOW_CROSS_VENUE_LIQUIDITY for item in ranked["skipped"])
    # Preferred PNET is not selected when the other venue is empty dust.
    assert ranked["selected"]["pair"] != [0, 3169177585]


def test_rank_prefers_deeper_liquidity_over_preferred_empty_pair():
    pools = [
        _pool("tinyman", 1, 100, 100, asset_b=1),
        _pool("pact", 2, 100, 100, asset_b=1),
        _pool("tinyman", 3, 1_000_000, 900_000, asset_b=2),
        _pool("pact", 4, 800_000, 700_000, asset_b=2),
    ]
    ranked = rank_shared_pairs(
        pools,
        preferred_pairs=((0, 1), (0, 2)),
        min_cross_venue_liquidity=1.0,
        min_venue_reserve=1.0,
    )
    assert ranked["selected"]["pair"] == [0, 2]


def test_adaptive_trade_sizes_probe_and_refine():
    probes = adaptive_trade_sizes(max_size=10.0)
    assert 0.1 in probes
    assert 10.0 in probes
    assert all(0.1 <= size <= 10.0 for size in probes)

    best = Opportunity.from_route(
        route=[],
        input_asset_id=0,
        input_amount=2.0,
        expected_final_amount=2.1,
        expected_net_profit=0.1,
        expected_profit_bps=50.0,
        max_price_impact_bps=10.0,
        involved_pool_ids=["a"],
        involved_asset_ids=[0, 1],
    )
    refined = adaptive_trade_sizes(max_size=10.0, opportunities=[best])
    assert 2.0 in refined
    assert any(size != 2.0 for size in refined)
