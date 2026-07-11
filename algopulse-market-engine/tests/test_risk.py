from types import SimpleNamespace
import time

from algopulse.models import Opportunity, Pool
from algopulse.risk import RiskEngine, RiskPolicy, policy_from_settings


def test_risk_rejects_unknown_asset():
    opportunity = Opportunity.from_route(
        route=[],
        input_asset_id=0,
        input_amount=10.0,
        expected_final_amount=11.0,
        expected_net_profit=1.0,
        expected_profit_bps=1000.0,
        max_price_impact_bps=10.0,
        involved_pool_ids=["pool"],
        involved_asset_ids=[0, 999999999],
    )
    pool = Pool(
        pool_id="pool",
        venue_id="venue",
        app_id=1,
        asset_a_id=0,
        asset_b_id=999999999,
        reserve_a=10_000.0,
        reserve_b=10_000.0,
        fee_bps=30,
        block_round=1,
    )

    decision = RiskEngine().assess(opportunity, [pool])

    assert not decision.approved
    assert decision.reason == "assets_allowlisted"


def test_policy_from_settings_applies_profit_guard():
    settings = SimpleNamespace(
        asset_pairs=((0, 3169177585), (31566704, 3169177585)),
        max_live_trade_size=10.0,
        min_net_profit_algos=0.42,
        min_net_profit_input_units=0.42,
        min_profit_bps=55.0,
        max_price_impact_bps=70.0,
        min_pool_reserve=5_000.0,
        estimated_network_fee_algos=0.01,
        safety_buffer_bps=20.0,
        max_route_age_seconds=4.0,
        max_route_legs=3,
        own_funds_only=True,
        allowed_asset_ids=(0, 31566704, 3169177585),
        allowed_app_ids=(1, 2),
        require_app_id_allowlist=True,
        min_fee_buffer_multiplier=2.5,
    )

    policy = policy_from_settings(settings)
    public_policy = policy.to_public_dict()

    assert policy.min_profit_absolute == 0.42
    assert policy.min_profit_bps == 55.0
    assert policy.max_price_impact_bps == 70.0
    assert policy.min_pool_reserve == 5_000.0
    assert policy.estimated_network_fee == 0.01
    assert policy.safety_buffer_bps == 20.0
    assert policy.max_route_age_seconds == 4.0
    assert policy.max_route_legs == 3
    assert policy.max_trade_size == 10.0
    assert policy.min_fee_buffer_multiplier == 2.5
    assert policy.allowed_asset_ids == (0, 31566704, 3169177585)
    assert policy.allowed_app_ids == (1, 2)
    assert policy.require_app_id_allowlist is True
    assert public_policy["max_route_age_seconds"] == 4.0
    assert public_policy["app_id_allowlist_required"] is True
    assert public_policy["requires_positive_net_after_fees"] is True


def test_risk_rejects_route_below_net_profit_floor():
    opportunity = Opportunity.from_route(
        route=[],
        input_asset_id=0,
        input_amount=10.0,
        expected_final_amount=10.1,
        expected_net_profit=0.1,
        expected_profit_bps=100.0,
        max_price_impact_bps=10.0,
        involved_pool_ids=["pool"],
        involved_asset_ids=[0, 31566704],
    )
    pool = Pool(
        pool_id="pool",
        venue_id="venue",
        app_id=1,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=10_000.0,
        reserve_b=10_000.0,
        fee_bps=30,
        block_round=1,
    )

    decision = RiskEngine().assess(opportunity, [pool])

    assert not decision.approved
    assert decision.reason == "net_profit_after_fees_ok"


def test_risk_rejects_stale_quotes():
    stale = time.time() - 10
    opportunity = Opportunity.from_route(
        route=[
            {
                "pool_id": "pool",
                "input_asset_id": 0,
                "output_asset_id": 31566704,
                "captured_at": stale,
                "expires_at": stale + 5,
            }
        ],
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=6.0,
        expected_net_profit=1.0,
        expected_profit_bps=2_000.0,
        max_price_impact_bps=10.0,
        involved_pool_ids=["pool"],
        involved_asset_ids=[0, 31566704],
    )
    pool = Pool(
        pool_id="pool",
        venue_id="venue",
        app_id=1,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=10_000.0,
        reserve_b=10_000.0,
        fee_bps=30,
        block_round=1,
    )

    decision = RiskEngine(RiskPolicy(max_route_age_seconds=5.0)).assess(opportunity, [pool])

    assert not decision.approved
    assert decision.reason == "quote_freshness_ok"


def test_risk_requires_reviewed_app_ids_when_enabled():
    opportunity = Opportunity.from_route(
        route=[],
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=6.0,
        expected_net_profit=1.0,
        expected_profit_bps=2_000.0,
        max_price_impact_bps=10.0,
        involved_pool_ids=["pool"],
        involved_asset_ids=[0, 31566704],
    )
    pool = Pool(
        pool_id="pool",
        venue_id="venue",
        app_id=123,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=10_000.0,
        reserve_b=10_000.0,
        fee_bps=30,
        block_round=1,
    )

    decision = RiskEngine(
        RiskPolicy(require_app_id_allowlist=True, allowed_app_ids=(999,))
    ).assess(opportunity, [pool])

    assert not decision.approved
    assert decision.reason == "app_ids_allowlisted"


def test_risk_rejects_profit_that_does_not_cover_two_times_expected_fees():
    opportunity = Opportunity.from_route(
        route=[],
        input_asset_id=0,
        input_amount=10.0,
        expected_final_amount=10.5,
        expected_net_profit=0.5,
        expected_profit_bps=500.0,
        max_price_impact_bps=10.0,
        involved_pool_ids=["pool"],
        involved_asset_ids=[0, 31566704],
        estimated_network_fee=0.1,
        total_dex_fees=0.2,
    )
    pool = Pool(
        pool_id="pool",
        venue_id="venue",
        app_id=1,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=10_000.0,
        reserve_b=10_000.0,
        fee_bps=30,
        block_round=1,
    )

    decision = RiskEngine(RiskPolicy(min_fee_buffer_multiplier=2.0)).assess(opportunity, [pool])

    assert not decision.approved
    assert decision.reason == "fee_buffer_ok"


def test_risk_rejects_routes_longer_than_three_swaps():
    opportunity = Opportunity.from_route(
        route=[
            {"pool_id": "one", "input_asset_id": 0, "output_asset_id": 1},
            {"pool_id": "two", "input_asset_id": 1, "output_asset_id": 2},
            {"pool_id": "three", "input_asset_id": 2, "output_asset_id": 3},
            {"pool_id": "four", "input_asset_id": 3, "output_asset_id": 0},
        ],
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=6.0,
        expected_net_profit=1.0,
        expected_profit_bps=2_000.0,
        max_price_impact_bps=10.0,
        involved_pool_ids=["one", "two", "three", "four"],
        involved_asset_ids=[0, 1, 2, 3],
    )

    decision = RiskEngine(
        RiskPolicy(max_route_legs=3, allowed_asset_ids=(0, 1, 2, 3))
    ).assess(opportunity, [])

    assert not decision.approved
    assert decision.reason == "route_leg_count_ok"
