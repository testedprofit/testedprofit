from algopulse.connectors.mock import MockMarketConnector
from algopulse.config import STANDARD_QUOTE_SIZES
from algopulse.engine import RouteEngine
from algopulse.models import Pool
from algopulse.risk import RiskEngine, RiskPolicy


def _pool(
    pool_id: str,
    venue_id: str,
    asset_a_id: int,
    asset_b_id: int,
    reserve_a: float,
    reserve_b: float,
) -> Pool:
    return Pool(
        pool_id=pool_id,
        venue_id=venue_id,
        app_id=abs(hash(pool_id)) % 1_000_000,
        asset_a_id=asset_a_id,
        asset_b_id=asset_b_id,
        reserve_a=reserve_a,
        reserve_b=reserve_b,
        fee_bps=30,
        block_round=123,
    )


def test_route_engine_uses_standard_quote_sizes_by_default():
    engine = RouteEngine(risk_engine=RiskEngine())

    assert tuple(engine.trade_sizes) == STANDARD_QUOTE_SIZES
    assert tuple(engine.trade_sizes) == (1.0, 5.0, 10.0, 25.0, 50.0, 100.0)


def test_route_engine_produces_ranked_opportunities():
    pools = MockMarketConnector().list_pools()
    engine = RouteEngine(risk_engine=RiskEngine())

    opportunities = engine.find_opportunities(pools)

    assert opportunities
    assert opportunities == sorted(opportunities, key=lambda item: item.expected_net_profit, reverse=True)
    assert all(item.route_hash for item in opportunities)


def test_route_engine_generates_two_leg_venue_arb_examples():
    pools = [
        _pool("tinyman:ALGO-USDC", "tinyman", 0, 31566704, 100_000.0, 20_000.0),
        _pool("pact:ALGO-USDC", "pact", 0, 31566704, 100_000.0, 21_000.0),
        _pool("tinyman:ALGO-CHIPS", "tinyman", 0, 388592191, 50_000.0, 20_000_000.0),
        _pool("pact:ALGO-CHIPS", "pact", 0, 388592191, 50_000.0, 19_500_000.0),
    ]
    engine = RouteEngine(risk_engine=RiskEngine(), trade_sizes=[1.0])

    opportunities = engine.find_opportunities(pools)
    signatures = [
        [(leg["input_asset_id"], leg["output_asset_id"], leg["venue"]) for leg in opportunity.route]
        for opportunity in opportunities
    ]

    assert [(0, 31566704, "tinyman"), (31566704, 0, "pact")] in signatures
    assert [(0, 388592191, "pact"), (388592191, 0, "tinyman")] in signatures
    assert all(leg["route_kind"] == "two_leg_venue_arb" for opportunity in opportunities for leg in opportunity.route)


def test_route_engine_generates_algo_asa_usdc_triangle():
    pools = [
        _pool("tinyman:ALGO-CHIPS", "tinyman", 0, 388592191, 50_000.0, 20_000_000.0),
        _pool("pact:CHIPS-USDC", "pact", 31566704, 388592191, 20_000.0, 20_000_000.0),
        _pool("tinyman:ALGO-USDC", "tinyman", 0, 31566704, 100_000.0, 20_000.0),
    ]
    engine = RouteEngine(risk_engine=RiskEngine(), trade_sizes=[1.0])

    opportunities = engine.find_opportunities(pools)
    triangle_signatures = [
        [(leg["input_asset_id"], leg["output_asset_id"], leg["venue"]) for leg in opportunity.route]
        for opportunity in opportunities
        if len(opportunity.route) == 3
    ]

    assert [(0, 388592191, "tinyman"), (388592191, 31566704, "pact"), (31566704, 0, "tinyman")] in triangle_signatures
    assert any(
        all(leg["route_kind"] == "three_leg_triangle" for leg in opportunity.route)
        for opportunity in opportunities
        if len(opportunity.route) == 3
    )


def test_route_engine_attaches_quote_storage_metadata():
    pools = MockMarketConnector().list_pools()
    policy = RiskPolicy(max_route_age_seconds=7.0)
    engine = RouteEngine(risk_engine=RiskEngine(policy=policy))

    opportunities = engine.find_opportunities(pools)

    assert opportunities
    for leg in opportunities[0].route:
        assert {
            "venue",
            "pool_id",
            "input_asset_id",
            "output_asset_id",
            "input_amount",
            "expected_output",
            "price_impact_bps",
            "fee_amount",
            "block_round",
            "captured_at",
            "expires_at",
        }.issubset(leg)
        assert leg["block_round"] > 0
        assert leg["expires_at"] == leg["captured_at"] + policy.max_route_age_seconds


def test_route_engine_calculates_opportunity_breakdown():
    pools = [
        _pool("tinyman:ALGO-USDC", "tinyman", 0, 31566704, 100_000.0, 20_000.0),
        _pool("pact:ALGO-USDC", "pact", 0, 31566704, 100_000.0, 21_000.0),
    ]
    policy = RiskPolicy(
        estimated_network_fee=0.006,
        safety_buffer_bps=10.0,
        min_profit_absolute=0.2,
    )
    engine = RouteEngine(risk_engine=RiskEngine(policy=policy), trade_sizes=[5.0])

    opportunity = engine.find_opportunities(pools)[0]

    assert opportunity.gross_profit == opportunity.expected_final_amount - opportunity.input_amount
    assert opportunity.estimated_network_fee == 0.006
    # DEX fees normalized to route input asset (not raw sum of mixed ASA amounts).
    assert opportunity.total_dex_fees == sum(
        float(leg.get("fee_amount_in_input_asset") or 0.0) for leg in opportunity.route
    )
    assert all("fee_asset_id" in leg for leg in opportunity.route)
    assert opportunity.total_price_impact_bps == sum(leg["price_impact_bps"] for leg in opportunity.route)
    assert opportunity.slippage_buffer == max(0.05, 5.0 * policy.safety_buffer_bps / 10_000)
    # AMM outputs already embed DEX fees — net does not re-subtract them.
    assert opportunity.expected_net_profit == (
        opportunity.gross_profit - opportunity.estimated_network_fee - opportunity.slippage_buffer
    )
    assert opportunity.risk_rules.get("dex_fees_embedded_in_output") is True
    assert opportunity.confidence_score == max(0.0, min(100.0, 100.0 - opportunity.max_price_impact_bps))
    assert opportunity.skip_reason


def test_route_engine_can_approve_with_permissive_policy():
    pools = MockMarketConnector().list_pools()
    policy = RiskPolicy(
        min_profit_absolute=-10.0,
        min_profit_bps=-10_000.0,
        max_price_impact_bps=300.0,
        min_fee_buffer_multiplier=0.0,
    )
    engine = RouteEngine(risk_engine=RiskEngine(policy=policy))

    opportunities = engine.find_opportunities(pools)

    assert any(item.status == "approved" for item in opportunities)
