import pytest

from algopulse.route_math import canonical_route_hash
from algopulse.route_math import constant_product_quote
from algopulse.route_math import route_profit_breakdown


def test_constant_product_quote_calculates_fee_output_and_impact():
    quote = constant_product_quote(
        reserve_in=1_000.0,
        reserve_out=200.0,
        input_amount=10.0,
        fee_bps=30,
    )

    assert quote is not None
    assert quote.fee_amount == pytest.approx(0.03)
    assert quote.output_amount == pytest.approx(1.974316, rel=1e-6)
    assert quote.price_impact_bps == pytest.approx(128.419656, rel=1e-6)


def test_constant_product_quote_rejects_invalid_pool_state():
    assert constant_product_quote(reserve_in=0, reserve_out=200, input_amount=10, fee_bps=30) is None
    assert constant_product_quote(reserve_in=1_000, reserve_out=200, input_amount=0, fee_bps=30) is None


def test_route_profit_breakdown_does_not_double_subtract_dex_fees():
    breakdown = route_profit_breakdown(
        input_amount=10.0,
        final_amount=10.8,
        dex_fee_amounts=[0.03, 0.024],
        price_impact_bps=[12.0, 18.0],
        estimated_network_fee=0.006,
        safety_buffer_bps=15.0,
        minimum_safety_buffer=0.0625,
    )

    assert breakdown.gross_profit == pytest.approx(0.8)
    assert breakdown.total_dex_fees == pytest.approx(0.054)
    assert breakdown.total_price_impact_bps == pytest.approx(30.0)
    assert breakdown.max_price_impact_bps == pytest.approx(18.0)
    assert breakdown.slippage_buffer == pytest.approx(0.0625)
    assert breakdown.expected_net_profit == pytest.approx(0.7315)
    assert breakdown.expected_profit_bps == pytest.approx(731.5)


def test_route_profit_breakdown_uses_bps_buffer_when_larger():
    breakdown = route_profit_breakdown(
        input_amount=100.0,
        final_amount=101.0,
        dex_fee_amounts=[],
        price_impact_bps=[],
        estimated_network_fee=0.006,
        safety_buffer_bps=50.0,
        minimum_safety_buffer=0.0625,
    )

    assert breakdown.slippage_buffer == pytest.approx(0.5)
    assert breakdown.expected_net_profit == pytest.approx(0.494)


def test_route_hash_is_stable_for_key_order_but_changes_for_route_order():
    route_a = [
        {"pool_id": "one", "input_asset_id": 0, "output_asset_id": 31566704},
        {"pool_id": "two", "input_asset_id": 31566704, "output_asset_id": 0},
    ]
    route_a_key_order_changed = [
        {"output_asset_id": 31566704, "input_asset_id": 0, "pool_id": "one"},
        {"output_asset_id": 0, "input_asset_id": 31566704, "pool_id": "two"},
    ]
    route_b = list(reversed(route_a))

    assert canonical_route_hash(route_a) == canonical_route_hash(route_a_key_order_changed)
    assert canonical_route_hash(route_a) != canonical_route_hash(route_b)


def test_route_profit_breakdown_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        route_profit_breakdown(
            input_amount=0,
            final_amount=10,
            dex_fee_amounts=[],
            price_impact_bps=[],
            estimated_network_fee=0.006,
            safety_buffer_bps=15,
            minimum_safety_buffer=0,
        )
