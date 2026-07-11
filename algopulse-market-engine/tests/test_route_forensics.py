import sqlite3
import time

from algopulse.models import Opportunity, Pool
from algopulse.route_forensics import build_route_forensics
from algopulse.store import MarketStore


def _route(now: float) -> list[dict]:
    return [
        {
            "route_kind": "two_leg_venue_arb",
            "venue": "tinyman",
            "pool_id": "tinyman:ALGO-USDC",
            "app_id": 1001,
            "input_asset_id": 0,
            "output_asset_id": 31566704,
            "input_amount": 5.0,
            "expected_output": 1.05,
            "fee_amount": 0.015,
            "price_impact_bps": 12.0,
            "block_round": 9001,
            "captured_at": now,
            "expires_at": now + 5,
        },
        {
            "route_kind": "two_leg_venue_arb",
            "venue": "pact",
            "pool_id": "pact:ALGO-USDC",
            "app_id": 1002,
            "input_asset_id": 31566704,
            "output_asset_id": 0,
            "input_amount": 1.05,
            "expected_output": 5.42,
            "fee_amount": 0.003,
            "price_impact_bps": 9.0,
            "block_round": 9002,
            "captured_at": now,
            "expires_at": now + 5,
        },
    ]


def _opportunity(now: float, *, status: str = "approved", skip_reason: str | None = None) -> Opportunity:
    return Opportunity(
        route_hash="forensics-route",
        route=_route(now),
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=5.42,
        gross_profit=0.42,
        estimated_network_fee=0.006,
        total_dex_fees=0.018,
        total_price_impact_bps=21.0,
        slippage_buffer=0.05,
        expected_net_profit=0.364,
        expected_profit_bps=728.0,
        max_price_impact_bps=12.0,
        involved_pool_ids=["tinyman:ALGO-USDC", "pact:ALGO-USDC"],
        involved_asset_ids=[0, 31566704],
        status=status,
        skip_reason=skip_reason,
        confidence_score=88.0,
        risk_rules={
            "quote_freshness_ok": True,
            "net_profit_after_fees_ok": skip_reason != "net_profit_after_fees_ok",
            "profit_bps_ok": True,
            "price_impact_ok": True,
            "assets_allowlisted": True,
            "app_ids_allowlisted": True,
        },
        created_at=now,
    )


def _pool(pool_id: str, now: float) -> Pool:
    return Pool(
        pool_id=pool_id,
        venue_id=pool_id.split(":")[0],
        app_id=1,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=100_000.0,
        reserve_b=20_000.0,
        fee_bps=30,
        block_round=9000,
        captured_at=now,
    )


def test_route_forensics_builder_explains_rejected_route():
    now = time.time()
    opportunity = _opportunity(now, status="rejected", skip_reason="net_profit_after_fees_ok").to_dict()

    explanation = build_route_forensics(
        opportunity,
        opportunity_id=7,
        liquidity={"totalLiquidity": 200_000.0, "minLiquidity": 90_000.0, "poolCount": 2, "missingPoolIds": []},
        now=now,
    )

    assert explanation["routeHash"] == "forensics-route"
    assert len(explanation["routePath"]) == 2
    assert explanation["profitability"]["expectedNetProfit"] == 0.364
    assert explanation["quoteFreshness"]["fresh"] is True
    assert explanation["priceImpact"]["maxBps"] == 12.0
    assert explanation["liquidityScore"]["status"] == "ok"
    assert explanation["riskResult"]["approved"] is False
    assert explanation["approvalDecision"]["decision"] == "rejected"
    assert explanation["rejectionReason"] == "net_profit_after_fees_ok"
    assert explanation["confidenceCalculation"]["components"]
    assert {step["key"] for step in explanation["decisionTree"]} >= {
        "route_path",
        "quote_freshness",
        "profitability",
        "risk_result",
        "approval_decision",
    }
    assert explanation["completeness"]["complete"] is True


def test_store_records_route_forensics_for_every_opportunity(tmp_path):
    now = time.time()
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    store.record_pool_snapshots(
        [
            _pool("tinyman:ALGO-USDC", now),
            _pool("pact:ALGO-USDC", now),
        ]
    )
    store.record_opportunities([_opportunity(now)])

    routes = store.list_route_forensics()
    summary = store.route_forensics_summary()

    assert len(routes) == 1
    route = routes[0]
    assert route["routeHash"] == "forensics-route"
    assert route["routePathLabel"] == "0 -> 31566704 -> 0"
    assert route["profitability"]["expectedNetProfit"] == 0.364
    assert route["quoteFreshness"]["status"] == "fresh"
    assert route["riskResult"]["approved"] is True
    assert route["approvalDecision"]["decision"] == "approved"
    assert route["rejectionReason"] == "none"
    assert route["completeness"]["complete"] is True
    assert summary["routeCount"] == 1
    assert summary["completeCount"] == 1
    assert summary["approvedCount"] == 1


def test_store_backfills_missing_route_forensics(tmp_path):
    now = time.time()
    database_path = tmp_path / "market.db"
    store = MarketStore(database_path)
    store.initialize()
    store.record_opportunities([_opportunity(now, status="rejected", skip_reason="price_impact_ok")])

    with sqlite3.connect(database_path) as con:
        con.execute("delete from route_forensics")
        assert con.execute("select count(*) from route_forensics").fetchone()[0] == 0

    store.initialize()

    routes = store.list_route_forensics()
    assert len(routes) == 1
    assert routes[0]["rejectionReason"] == "price_impact_ok"
    assert routes[0]["decisionTree"]
