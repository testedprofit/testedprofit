from __future__ import annotations

from algopulse.realtime_decision_loop import classify_route_venues
from algopulse.paper_outcome_loop import _simulate_exact_route
from algopulse.models import Pool


def test_classify_route_venues_cross_same_triangle():
    cross = [
        {"venue": "tinyman", "pool_id": "a", "route_kind": "two_leg_venue_arb"},
        {"venue": "pact", "pool_id": "b", "route_kind": "two_leg_venue_arb"},
    ]
    same = [
        {"venue": "pact", "pool_id": "a"},
        {"venue": "pact", "pool_id": "b"},
    ]
    tri = [
        {"venue": "tinyman", "pool_id": "a", "route_kind": "three_leg_triangle"},
        {"venue": "pact", "pool_id": "b", "route_kind": "three_leg_triangle"},
        {"venue": "tinyman", "pool_id": "c", "route_kind": "three_leg_triangle"},
    ]
    assert classify_route_venues(cross) == "cross_venue_tinyman_pact"
    assert classify_route_venues(same) == "same_venue_pact"
    assert classify_route_venues(tri) == "triangle"


def test_simulate_exact_route_does_not_swap_pools():
    p1 = Pool(
        pool_id="p1",
        venue_id="tinyman",
        app_id=1,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=10_000,
        reserve_b=20_000,
        fee_bps=30,
        block_round=1,
        captured_at=100.0,
    )
    p2 = Pool(
        pool_id="p2",
        venue_id="pact",
        app_id=2,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=12_000,
        reserve_b=18_000,
        fee_bps=5,
        block_round=1,
        captured_at=100.0,
    )
    route = [
        {
            "pool_id": "p1",
            "venue": "tinyman",
            "input_asset_id": 0,
            "output_asset_id": 31566704,
        },
        {
            "pool_id": "p2",
            "venue": "pact",
            "input_asset_id": 31566704,
            "output_asset_id": 0,
        },
    ]
    sim = _simulate_exact_route(route, [p1, p2], 1.0)
    assert sim["ok"] is True
    assert sim["legs"][0]["poolId"] == "p1"
    assert sim["legs"][1]["poolId"] == "p2"
    # Missing pool fails rather than substituting
    bad = _simulate_exact_route(route, [p1], 1.0)
    assert bad["ok"] is False
    assert "missing_pool" in bad["reason"]
