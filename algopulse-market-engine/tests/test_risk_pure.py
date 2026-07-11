from algopulse.risk import RiskEvaluationInput
from algopulse.risk import evaluate_risk_rules


def _safe_input(**overrides) -> RiskEvaluationInput:
    values = {
        "input_amount": 10.0,
        "expected_net_profit": 0.5,
        "expected_profit_bps": 500.0,
        "max_price_impact_bps": 25.0,
        "expected_total_fees": 0.1,
        "quote_age_seconds": 2.0,
        "route_leg_count": 2,
        "trade_size_limit": 10.0,
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
    }
    values.update(overrides)
    return RiskEvaluationInput(**values)


def test_pure_risk_rules_approve_only_when_all_gates_pass():
    decision = evaluate_risk_rules(_safe_input())

    assert decision.approved is True
    assert decision.reason is None
    assert all(decision.rules.values())


def test_pure_risk_rules_reject_stale_quotes():
    decision = evaluate_risk_rules(_safe_input(quote_age_seconds=6.0))

    assert decision.approved is False
    assert decision.reason == "quote_freshness_ok"


def test_pure_risk_rules_reject_volume_only_trade_below_profit_floor():
    decision = evaluate_risk_rules(_safe_input(expected_net_profit=0.01, expected_profit_bps=500.0))

    assert decision.approved is False
    assert decision.reason == "net_profit_after_fees_ok"


def test_pure_risk_rules_reject_when_profit_does_not_cover_fee_buffer():
    decision = evaluate_risk_rules(_safe_input(expected_net_profit=0.3, expected_total_fees=0.2))

    assert decision.approved is False
    assert decision.reason == "fee_buffer_ok"


def test_pure_risk_rules_reject_daily_trade_and_loss_caps():
    trade_cap = evaluate_risk_rules(_safe_input(daily_trades=20))
    loss_cap = evaluate_risk_rules(_safe_input(daily_loss=-20.0))

    assert trade_cap.approved is False
    assert trade_cap.reason == "daily_trade_count_ok"
    assert loss_cap.approved is False
    assert loss_cap.reason == "daily_loss_ok"


def test_pure_risk_rules_reject_concurrent_execution():
    decision = evaluate_risk_rules(_safe_input(concurrent_executions=1, max_concurrent_execution=1))

    assert decision.approved is False
    assert decision.reason == "concurrent_execution_ok"
