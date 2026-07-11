import sqlite3

import pytest

from algopulse.algorand import display_to_raw
from algopulse.algorand import raw_to_display
from algopulse.engine import RouteEngine
from algopulse.models import Pool
from algopulse.risk import RiskEngine, RiskPolicy
from algopulse.route_math import canonical_route_hash
from algopulse.route_math import constant_product_quote
from algopulse.route_math import route_profit_breakdown


def test_decimal_conversion_round_trips_display_and_raw_units():
    assert raw_to_display(12_345_678, 6) == 12.345678
    assert display_to_raw(12.345678, 6) == 12_345_678
    assert display_to_raw(0.0000014, 6) == 1
    assert display_to_raw(0.0000016, 6) == 2


def test_quote_normalization_uses_display_units_and_stable_fields():
    pool = Pool(
        pool_id="tinyman:ALGO-USDC",
        venue_id="tinyman",
        app_id=1001001,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=1_000.0,
        reserve_b=200.0,
        fee_bps=30,
        block_round=123,
    )

    quote = pool.quote(input_asset_id=0, input_amount=10.0)

    assert quote is not None
    assert quote.to_dict() == {
        "pool_id": "tinyman:ALGO-USDC",
        "venue_id": "tinyman",
        "input_asset_id": 0,
        "output_asset_id": 31566704,
        "input_amount": 10.0,
        "output_amount": pytest.approx(1.974316, rel=1e-6),
        "fee_amount": pytest.approx(0.03),
        "price_impact_bps": pytest.approx(128.419656, rel=1e-6),
    }


def test_gross_net_profit_fee_and_price_impact_calculation():
    quote = constant_product_quote(
        reserve_in=1_000.0,
        reserve_out=200.0,
        input_amount=10.0,
        fee_bps=30,
    )
    assert quote is not None

    breakdown = route_profit_breakdown(
        input_amount=10.0,
        final_amount=10.8,
        dex_fee_amounts=[quote.fee_amount, 0.024],
        price_impact_bps=[quote.price_impact_bps, 18.0],
        estimated_network_fee=0.006,
        safety_buffer_bps=15.0,
        minimum_safety_buffer=0.0625,
    )

    assert quote.fee_amount == pytest.approx(0.03)
    assert quote.price_impact_bps == pytest.approx(128.419656, rel=1e-6)
    assert breakdown.gross_profit == pytest.approx(0.8)
    assert breakdown.total_dex_fees == pytest.approx(0.054)
    assert breakdown.slippage_buffer == pytest.approx(0.0625)
    assert breakdown.expected_net_profit == pytest.approx(0.7315)
    assert breakdown.expected_profit_bps == pytest.approx(731.5)


def test_route_hash_stability_ignores_dict_key_order_only():
    route = [
        {"pool_id": "one", "input_asset_id": 0, "output_asset_id": 31566704},
        {"pool_id": "two", "input_asset_id": 31566704, "output_asset_id": 0},
    ]
    reordered_keys = [
        {"output_asset_id": 31566704, "pool_id": "one", "input_asset_id": 0},
        {"output_asset_id": 0, "pool_id": "two", "input_asset_id": 31566704},
    ]

    assert canonical_route_hash(route) == canonical_route_hash(reordered_keys)
    assert canonical_route_hash(route) != canonical_route_hash(list(reversed(route)))


def test_algo_usdc_quotes_keep_display_units_separate_from_raw_units():
    pool = Pool(
        pool_id="tinyman:ALGO-USDC",
        venue_id="tinyman",
        app_id=1001001,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=1_000_000.0,
        reserve_b=300_000.0,
        fee_bps=30,
        block_round=123,
    )
    display_input_algo = 5.0
    raw_input_microalgos = display_to_raw(display_input_algo, 6)

    quote = pool.quote(input_asset_id=0, input_amount=display_input_algo)

    assert quote is not None
    assert raw_input_microalgos == 5_000_000
    assert raw_to_display(raw_input_microalgos, 6) == display_input_algo
    assert quote.input_amount == display_input_algo
    assert quote.input_amount != raw_input_microalgos
    assert 0 < quote.output_amount < 10
    assert quote.output_amount == pytest.approx(1.495492, rel=1e-6)
    assert display_to_raw(quote.output_amount, 6) == pytest.approx(1_495_492, abs=1)


def test_route_profit_math_stays_in_display_units_for_algo_denominated_routes():
    breakdown = route_profit_breakdown(
        input_amount=5.0,
        final_amount=5.31,
        dex_fee_amounts=[0.015, 0.0045],
        price_impact_bps=[3.5, 4.5],
        estimated_network_fee=0.006,
        safety_buffer_bps=15.0,
        minimum_safety_buffer=0.0025,
    )

    assert breakdown.gross_profit == pytest.approx(0.31)
    assert breakdown.slippage_buffer == pytest.approx(0.0075)
    assert breakdown.expected_net_profit == pytest.approx(0.2965)
    assert breakdown.expected_profit_bps == pytest.approx(593.0)
    assert display_to_raw(breakdown.expected_net_profit, 6) == pytest.approx(296_500, abs=1)
    assert breakdown.expected_net_profit < 1


def test_route_engine_pipeline_amounts_remain_human_readable_display_units():
    pools = [
        Pool(
            pool_id="tinyman:ALGO-USDC",
            venue_id="tinyman",
            app_id=1001001,
            asset_a_id=0,
            asset_b_id=31566704,
            reserve_a=1_000_000.0,
            reserve_b=300_000.0,
            fee_bps=30,
            block_round=123,
        ),
        Pool(
            pool_id="pact:ALGO-USDC",
            venue_id="pact",
            app_id=2001001,
            asset_a_id=0,
            asset_b_id=31566704,
            reserve_a=1_000_000.0,
            reserve_b=200_000.0,
            fee_bps=30,
            block_round=124,
        ),
    ]
    policy = RiskPolicy(
        min_profit_absolute=0.01,
        min_profit_bps=1.0,
        max_price_impact_bps=50.0,
        min_fee_buffer_multiplier=0.0,
    )
    engine = RouteEngine(risk_engine=RiskEngine(policy=policy), trade_sizes=[5.0])

    opportunity = next(item for item in engine.find_opportunities(pools) if item.status == "approved")

    assert opportunity.input_amount == 5.0
    assert opportunity.input_amount != display_to_raw(5.0, 6)
    assert 5.0 < opportunity.expected_final_amount < 10.0
    assert 0.0 < opportunity.expected_net_profit < 5.0
    assert opportunity.expected_net_profit == pytest.approx(
        opportunity.gross_profit - opportunity.estimated_network_fee - opportunity.slippage_buffer
    )
    assert opportunity.expected_profit_bps == pytest.approx(
        (opportunity.expected_net_profit / opportunity.input_amount) * 10_000
    )
    for leg in opportunity.route:
        assert leg["input_amount"] < 10
        assert leg["expected_output"] < 10
