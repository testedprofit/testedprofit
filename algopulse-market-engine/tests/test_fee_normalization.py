from __future__ import annotations

import pytest

from algopulse.models import Pool
from algopulse.route_math import (
    convert_amount_to_asset,
    normalize_dex_fees_to_input_asset,
    route_profit_breakdown,
)
from algopulse.engine import RouteEngine
from algopulse.risk import RiskEngine, RiskPolicy
from dataclasses import replace


def _pool(a: int, b: int, ra: float, rb: float, app_id: int = 1) -> Pool:
    lo, hi = sorted((a, b))
    if a == lo:
        reserve_a, reserve_b = ra, rb
    else:
        reserve_a, reserve_b = rb, ra
        a, b = lo, hi
    return Pool(
        pool_id=f"p:{app_id}:{a}-{b}",
        venue_id="pact",
        app_id=app_id,
        asset_a_id=a,
        asset_b_id=b,
        reserve_a=reserve_a,
        reserve_b=reserve_b,
        fee_bps=30,
        block_round=10,
    )


def test_does_not_sum_mixed_asset_fee_amounts_raw():
    # 1 ALGO fee + 1 USDC fee must NOT become 2 in either unit.
    algo_usdc = _pool(0, 31566704, 1000.0, 200.0)  # 1 ALGO = 0.2 USDC mid
    total, evidence, ok = normalize_dex_fees_to_input_asset(
        fee_legs=[(1.0, 0), (1.0, 31566704)],
        input_asset_id=0,
        pools=[algo_usdc],
    )
    assert ok is True
    assert evidence[0]["asset_id"] == 0
    assert evidence[0]["amount"] == 1.0
    assert evidence[1]["asset_id"] == 31566704
    # 1 USDC -> ALGO at mid: reserve_algo/reserve_usdc = 1000/200 = 5
    assert evidence[1]["amount_in_input_asset"] == pytest.approx(5.0)
    assert total == pytest.approx(6.0)
    assert total != pytest.approx(2.0)


def test_route_profit_does_not_double_subtract_dex_fees():
    breakdown = route_profit_breakdown(
        input_amount=10.0,
        final_amount=10.8,  # already after AMM fees
        dex_fee_legs=[(0.03, 0), (0.5, 31566704)],
        fee_pools=[_pool(0, 31566704, 1000.0, 200.0)],
        leg_input_amounts=[10.0, 1.95],  # path quote: 10 ALGO -> 1.95 USDC
        input_asset_id=0,
        price_impact_bps=[10.0, 12.0],
        estimated_network_fee=0.006,
        safety_buffer_bps=15.0,
        minimum_safety_buffer=0.0625,
        network_fee_asset_id=0,
    )
    # Net ignores DEX fee sum; only network + slippage leave gross.
    assert breakdown.expected_net_profit == pytest.approx(0.8 - 0.006 - 0.0625)
    assert breakdown.dex_fees_embedded_in_output is True
    assert breakdown.fee_unit_asset_id == 0
    # Path conversion: 0.5 USDC fee * (10 / 1.95) ALGO
    assert breakdown.total_dex_fees == pytest.approx(0.03 + 0.5 * (10.0 / 1.95))
    assert breakdown.dex_fee_evidence[1]["conversionMethod"] == "route_path_quote"


def test_route_path_fee_conversion_preferred_over_mid():
    total, evidence, ok = normalize_dex_fees_to_input_asset(
        fee_legs=[(1.0, 31566704)],
        input_asset_id=0,
        pools=[_pool(0, 31566704, 1000.0, 200.0)],  # mid would give 5 ALGO
        route_input_amount=10.0,
        leg_input_amounts=[2.0],  # path: 1 USDC fee -> 10/2 = 5 ALGO same mid; change inputs
    )
    assert ok is True
    # With path amounts 10 route / 2 leg = 5
    assert total == pytest.approx(5.0)
    assert evidence[0]["conversionMethod"] == "route_path_quote"


def test_missing_pool_captured_at_rejects_quote_unavailable():
    pool_a = Pool(
        pool_id="t",
        venue_id="tinyman",
        app_id=1,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=100_000,
        reserve_b=20_000,
        fee_bps=30,
        block_round=5,
        captured_at=0.0,
    )
    pool_b = Pool(
        pool_id="p",
        venue_id="pact",
        app_id=2,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=100_000,
        reserve_b=21_000,
        fee_bps=5,
        block_round=5,
        captured_at=1_700_000_000.0,
    )
    engine = RouteEngine(
        RiskEngine(RiskPolicy(min_profit_absolute=-1, min_profit_bps=-1, max_price_impact_bps=10_000, min_fee_buffer_multiplier=0)),
        trade_sizes=[1.0],
    )
    opps = engine.find_opportunities([pool_a, pool_b])
    assert opps
    assert all(o.skip_reason == "quote_unavailable" for o in opps)
    assert all(leg.get("captured_at") is None for o in opps for leg in o.route if leg["pool_id"] == "t")


def test_unconvertible_fee_rejects_fee_conversion_unavailable():
    total, evidence, ok = normalize_dex_fees_to_input_asset(
        fee_legs=[(1.0, 999999999)],  # unknown ASA, empty pools for conversion
        input_asset_id=0,
        pools=[],
        route_input_amount=None,
        leg_input_amounts=None,
    )
    assert ok is False
    assert total is None
    assert evidence[0]["conversionOk"] is False
    assert evidence[0]["amount_in_input_asset"] is None  # never zero-fill
    assert convert_amount_to_asset(1.0, 999999999, 0, []) is None


def test_pools_from_store_rows_never_fills_missing_captured_at():
    from algopulse.route_optimizer import pools_from_store_rows

    rows = [
        {
            "pool_id": "p1",
            "venue_id": "pact",
            "app_id": 1,
            "asset_a_id": 0,
            "asset_b_id": 31566704,
            "reserve_a": 10.0,
            "reserve_b": 10.0,
            "fee_bps": 30,
            "block_round": 1,
            # missing captured_at
        },
        {
            "pool_id": "p2",
            "venue_id": "pact",
            "app_id": 2,
            "asset_a_id": 0,
            "asset_b_id": 31566704,
            "reserve_a": 10.0,
            "reserve_b": 10.0,
            "fee_bps": 30,
            "block_round": 1,
            "captured_at": 1_700_000_000.0,
        },
    ]
    pools = pools_from_store_rows(rows)
    assert len(pools) == 1
    assert pools[0].pool_id == "p2"
    assert pools[0].captured_at == 1_700_000_000.0


def test_engine_attaches_fee_asset_and_normalized_fields():
    pools = [
        Pool(
            pool_id="t",
            venue_id="tinyman",
            app_id=1,
            asset_a_id=0,
            asset_b_id=31566704,
            reserve_a=100_000,
            reserve_b=20_000,
            fee_bps=30,
            block_round=5,
            captured_at=1_700_000_000.0,
        ),
        Pool(
            pool_id="p",
            venue_id="pact",
            app_id=2,
            asset_a_id=0,
            asset_b_id=31566704,
            reserve_a=100_000,
            reserve_b=21_000,
            fee_bps=5,
            block_round=5,
            captured_at=1_700_000_000.0,
        ),
    ]
    engine = RouteEngine(
        RiskEngine(
            RiskPolicy(
                min_profit_absolute=-1,
                min_profit_bps=-1,
                max_price_impact_bps=10_000,
                min_fee_buffer_multiplier=0,
            )
        ),
        trade_sizes=[1.0],
    )
    opps = engine.find_opportunities(pools)
    assert opps
    for leg in opps[0].route:
        assert "fee_asset_id" in leg
        assert "fee_amount_in_input_asset" in leg
    assert opps[0].risk_rules.get("fee_unit_asset_id") == 0
    assert opps[0].risk_rules.get("fee_unit_consistent") is True
    assert opps[0].risk_rules.get("fee_conversion_ok") is True
