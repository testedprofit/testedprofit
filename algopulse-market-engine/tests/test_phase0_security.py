from dataclasses import replace

from fastapi.testclient import TestClient

import algopulse.api as api_module
from algopulse.api import LOCAL_REVIEW_ADMIN_WALLET
from algopulse.api import app
from algopulse.models import Opportunity
from algopulse.models import Pool
from algopulse.risk import RiskEngine
from algopulse.risk import RiskPolicy


def _profitable_opportunity(**overrides) -> Opportunity:
    values = {
        "route": [],
        "input_asset_id": 0,
        "input_amount": 10.0,
        "expected_final_amount": 11.0,
        "expected_net_profit": 0.7,
        "expected_profit_bps": 700.0,
        "max_price_impact_bps": 10.0,
        "involved_pool_ids": ["pool"],
        "involved_asset_ids": [0, 31566704],
        "estimated_network_fee": 0.006,
        "total_dex_fees": 0.02,
    }
    values.update(overrides)
    return Opportunity.from_route(**values)


def _pool(**overrides) -> Pool:
    values = {
        "pool_id": "pool",
        "venue_id": "tinyman",
        "app_id": 1001001,
        "asset_a_id": 0,
        "asset_b_id": 31566704,
        "reserve_a": 100_000.0,
        "reserve_b": 20_000.0,
        "fee_bps": 30,
        "block_round": 123,
    }
    values.update(overrides)
    return Pool(**values)


def test_non_admin_cannot_call_admin_endpoints():
    client = TestClient(app)

    response = client.post(
        "/api/admin/dry-run/build",
        headers={"X-Algopulse-Role": "user", "X-Algopulse-Wallet": "USER7R3VIEWWALLET"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "NOT_AUTHORIZED"


def test_frontend_role_header_does_not_grant_backend_admin_role():
    client = TestClient(app)

    response = client.post(
        "/api/admin/scan-now",
        headers={"X-Algopulse-Role": "admin", "X-Algopulse-Wallet": "NOT_ALLOWLISTED"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "NOT_AUTHORIZED"
    assert response.json()["error"]["details"]["walletAllowlisted"] is False


def test_unknown_app_id_rejected_by_risk_policy():
    decision = RiskEngine(
        RiskPolicy(
            allowed_asset_ids=(0, 31566704),
            allowed_app_ids=(1001001,),
            require_app_id_allowlist=True,
        )
    ).assess(_profitable_opportunity(), [_pool(app_id=999999)])

    assert decision.approved is False
    assert decision.reason == "app_ids_allowlisted"


def test_unknown_asset_rejected_by_risk_policy():
    decision = RiskEngine(
        RiskPolicy(allowed_asset_ids=(0, 31566704), allowed_app_ids=(1001001,))
    ).assess(
        _profitable_opportunity(involved_asset_ids=[0, 999999999]),
        [_pool(asset_b_id=999999999)],
    )

    assert decision.approved is False
    assert decision.reason == "assets_allowlisted"


def test_over_limit_trade_rejected_by_risk_policy():
    decision = RiskEngine(
        RiskPolicy(
            max_trade_size=10.0,
            allowed_asset_ids=(0, 31566704),
            allowed_app_ids=(1001001,),
        )
    ).assess(_profitable_opportunity(input_amount=25.0), [_pool()])

    assert decision.approved is False
    assert decision.reason == "trade_size_ok"


def test_kill_switch_blocks_execution_requests(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(
        api_module,
        "settings",
        replace(api_module.settings, enable_live_execution=True, signer_kill_switch=True),
    )

    response = client.post(
        "/api/admin/live/arm",
        headers={"X-Algopulse-Role": "admin", "X-Algopulse-Wallet": LOCAL_REVIEW_ADMIN_WALLET},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "KILL_SWITCH_ACTIVE"
