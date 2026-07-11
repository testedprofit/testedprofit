import pytest

from algopulse.risk import ALGORAND_TX_GROUP_LIMIT
from algopulse.risk import RiskEvaluationInput
from algopulse.risk import evaluate_risk_rules


def _safe_input(**overrides) -> RiskEvaluationInput:
    values = {
        "input_amount": 10.0,
        "expected_net_profit": 0.75,
        "expected_profit_bps": 75.0,
        "max_price_impact_bps": 25.0,
        "expected_total_fees": 0.1,
        "quote_age_seconds": 2.0,
        "route_leg_count": 2,
        "trade_size_limit": 25.0,
        "max_route_legs": 3,
        "min_profit_absolute": 0.25,
        "min_profit_bps": 35.0,
        "max_price_impact_bps_limit": 50.0,
        "min_fee_buffer_multiplier": 2.0,
        "own_funds_only": True,
        "assets_allowlisted": True,
        "app_ids_allowlisted": True,
        "pool_reserves_ok": True,
        "quote_max_age_seconds": 5.0,
        "daily_loss": 0.0,
        "max_daily_loss": 20.0,
        "daily_trades": 0,
        "max_daily_trades": 20,
        "concurrent_executions": 0,
        "max_concurrent_execution": 1,
        "connector_readiness_ok": True,
        "tx_group_size": ALGORAND_TX_GROUP_LIMIT,
        "max_tx_group_size": ALGORAND_TX_GROUP_LIMIT,
        "transaction_types_allowlisted": True,
        "kill_switch_active": False,
    }
    values.update(overrides)
    return RiskEvaluationInput(**values)


@pytest.mark.parametrize(
    ("case_name", "overrides", "expected_reason"),
    [
        ("unknown asset", {"assets_allowlisted": False}, "assets_allowlisted"),
        ("unknown app ID", {"app_ids_allowlisted": False}, "app_ids_allowlisted"),
        ("stale quote", {"quote_age_seconds": 6.0}, "quote_freshness_ok"),
        ("connector down", {"connector_readiness_ok": False}, "connector_readiness_ok"),
        ("low liquidity", {"pool_reserves_ok": False}, "pool_reserves_ok"),
        ("excessive price impact", {"max_price_impact_bps": 51.0}, "price_impact_ok"),
        ("below minimum net profit", {"expected_net_profit": 0.01}, "net_profit_after_fees_ok"),
        ("route length too long", {"route_leg_count": 4}, "route_leg_count_ok"),
        (
            "Algorand group size exceeded",
            {"tx_group_size": ALGORAND_TX_GROUP_LIMIT + 1},
            "tx_group_size_ok",
        ),
        (
            "unsupported transaction type",
            {"transaction_types_allowlisted": False},
            "transaction_types_allowlisted",
        ),
        ("kill switch active", {"kill_switch_active": True}, "kill_switch_inactive"),
    ],
)
def test_risk_engine_torture_rejects_unsafe_routes_with_machine_readable_reason(
    case_name,
    overrides,
    expected_reason,
):
    decision = evaluate_risk_rules(_safe_input(**overrides))

    assert decision.approved is False, case_name
    assert decision.reason == expected_reason
    assert decision.reason in decision.rules
    assert decision.rules[decision.reason] is False
    assert decision.reason.strip() == decision.reason
    assert " " not in decision.reason


def test_risk_engine_torture_approval_has_explicit_evidence():
    decision = evaluate_risk_rules(_safe_input())

    assert decision.approved is True
    assert decision.reason is None
    assert decision.rules["assets_allowlisted"] is True
    assert decision.rules["app_ids_allowlisted"] is True
    assert decision.rules["quote_freshness_ok"] is True
    assert decision.rules["connector_readiness_ok"] is True
    assert decision.rules["price_impact_ok"] is True
    assert decision.rules["net_profit_after_fees_ok"] is True
    assert decision.rules["route_leg_count_ok"] is True
    assert decision.rules["tx_group_size_ok"] is True
    assert decision.rules["transaction_types_allowlisted"] is True
    assert decision.rules["kill_switch_inactive"] is True
    assert all(decision.rules.values())


def test_risk_engine_torture_never_returns_blank_rejection_reason():
    rejection_inputs = [
        _safe_input(assets_allowlisted=False),
        _safe_input(app_ids_allowlisted=False),
        _safe_input(quote_age_seconds=99.0),
        _safe_input(connector_readiness_ok=False),
        _safe_input(pool_reserves_ok=False),
        _safe_input(max_price_impact_bps=99.0),
        _safe_input(expected_net_profit=0.0),
        _safe_input(route_leg_count=99),
        _safe_input(tx_group_size=ALGORAND_TX_GROUP_LIMIT + 1),
        _safe_input(transaction_types_allowlisted=False),
        _safe_input(kill_switch_active=True),
    ]

    for input_data in rejection_inputs:
        decision = evaluate_risk_rules(input_data)

        assert decision.approved is False
        assert decision.reason
        assert decision.reason in decision.rules
        assert decision.rules[decision.reason] is False
