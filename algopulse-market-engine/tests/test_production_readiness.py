from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

import algopulse.api as api_module
from algopulse.algorand import display_to_raw
from algopulse.algorand import raw_to_display
from algopulse.api import LOCAL_REVIEW_ADMIN_WALLET
from algopulse.api import app
from algopulse.risk import RiskEvaluationInput
from algopulse.risk import evaluate_risk_rules
from algopulse.route_math import canonical_route_hash
from algopulse.route_math import constant_product_quote
from algopulse.route_math import route_profit_breakdown


def _risk_input(**overrides) -> RiskEvaluationInput:
    values = {
        "input_amount": 10.0,
        "expected_net_profit": 0.7,
        "expected_profit_bps": 700.0,
        "max_price_impact_bps": 10.0,
        "expected_total_fees": 0.03,
        "quote_age_seconds": 1.0,
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
    }
    values.update(overrides)
    return RiskEvaluationInput(**values)


def test_decimal_conversion_uses_asset_decimals():
    assert raw_to_display(12_345_678, 6) == 12.345678
    assert display_to_raw(12.345678, 6) == 12_345_678
    assert raw_to_display(123_456_789, 8) == 1.23456789
    assert display_to_raw(1.23456789, 8) == 123_456_789


def test_route_math_fee_and_price_impact_are_deterministic():
    quote = constant_product_quote(
        reserve_in=1_000.0,
        reserve_out=200.0,
        input_amount=10.0,
        fee_bps=30,
    )

    assert quote is not None
    assert quote.fee_amount == pytest.approx(0.03)
    assert quote.output_amount == pytest.approx(1.9743160687)
    assert quote.price_impact_bps == pytest.approx(128.419656)


def test_profit_bps_calculation_uses_net_after_fees_and_buffer():
    breakdown = route_profit_breakdown(
        input_amount=10.0,
        final_amount=10.8,
        dex_fee_amounts=[0.03, 0.024],
        price_impact_bps=[20.0, 18.0],
        estimated_network_fee=0.006,
        safety_buffer_bps=15.0,
        minimum_safety_buffer=0.0625,
    )

    assert breakdown.gross_profit == pytest.approx(0.8)
    assert breakdown.total_dex_fees == pytest.approx(0.054)
    assert breakdown.expected_net_profit == pytest.approx(0.7315)
    assert breakdown.expected_profit_bps == pytest.approx(731.5)


def test_route_hash_is_stable_for_same_route_intent():
    route = [
        {"venue": "tinyman", "pool_id": "one", "input_asset_id": 0, "output_asset_id": 31566704},
        {"venue": "pact", "pool_id": "two", "input_asset_id": 31566704, "output_asset_id": 0},
    ]
    same_intent = [
        {"output_asset_id": 31566704, "input_asset_id": 0, "pool_id": "one", "venue": "tinyman"},
        {"output_asset_id": 0, "input_asset_id": 31566704, "pool_id": "two", "venue": "pact"},
    ]

    assert canonical_route_hash(route) == canonical_route_hash(same_intent)
    assert canonical_route_hash(route) != canonical_route_hash(list(reversed(route)))


def test_quote_freshness_rejection_is_first_failed_rule():
    decision = evaluate_risk_rules(_risk_input(quote_age_seconds=6.0, quote_max_age_seconds=5.0))

    assert decision.approved is False
    assert decision.reason == "quote_freshness_ok"


def test_asset_allowlist_rejection_is_explicit():
    decision = evaluate_risk_rules(_risk_input(assets_allowlisted=False))

    assert decision.approved is False
    assert decision.reason == "assets_allowlisted"


def test_app_id_allowlist_rejection_is_explicit():
    decision = evaluate_risk_rules(_risk_input(app_ids_allowlisted=False))

    assert decision.approved is False
    assert decision.reason == "app_ids_allowlisted"


def test_max_trade_size_rejection_is_explicit():
    decision = evaluate_risk_rules(_risk_input(input_amount=25.0, trade_size_limit=10.0))

    assert decision.approved is False
    assert decision.reason == "trade_size_ok"


def test_kill_switch_rejects_admin_live_arm_request(monkeypatch):
    monkeypatch.setattr(
        api_module,
        "settings",
        replace(api_module.settings, enable_live_execution=True, signer_kill_switch=True),
    )

    response = TestClient(app).post(
        "/api/admin/live/arm",
        headers={"X-Algopulse-Role": "admin", "X-Algopulse-Wallet": LOCAL_REVIEW_ADMIN_WALLET},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "KILL_SWITCH_ACTIVE"


def test_non_admin_admin_endpoint_rejection():
    response = TestClient(app).post(
        "/api/admin/scan-now",
        headers={"X-Algopulse-Role": "user", "X-Algopulse-Wallet": "USER7R3VIEWWALLET"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "NOT_AUTHORIZED"
