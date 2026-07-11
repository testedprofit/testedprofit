import time

from algopulse.models import Opportunity, Pool
from algopulse.store import MarketStore


def _pool(pool_id: str, now: float) -> Pool:
    return Pool(
        pool_id=pool_id,
        venue_id=pool_id.split(":")[0],
        app_id=10_001 if pool_id.startswith("tinyman") else 10_002,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=100_000.0,
        reserve_b=20_000.0,
        fee_bps=30,
        block_round=123_456,
        captured_at=now,
    )


def _opportunity(now: float) -> Opportunity:
    route = [
        {
            "route_kind": "two_leg_venue_arb",
            "venue": "tinyman",
            "pool_id": "tinyman:ALGO-USDC",
            "app_id": 10_001,
            "input_asset_id": 0,
            "output_asset_id": 31566704,
            "input_amount": 5.0,
            "expected_output": 1.05,
            "fee_amount": 0.015,
            "price_impact_bps": 12.0,
            "block_round": 123_456,
            "captured_at": now,
            "expires_at": now + 5,
        },
        {
            "route_kind": "two_leg_venue_arb",
            "venue": "pact",
            "pool_id": "pact:ALGO-USDC",
            "app_id": 10_002,
            "input_asset_id": 31566704,
            "output_asset_id": 0,
            "input_amount": 1.05,
            "expected_output": 5.42,
            "fee_amount": 0.003,
            "price_impact_bps": 9.0,
            "block_round": 123_457,
            "captured_at": now,
            "expires_at": now + 5,
        },
    ]
    return Opportunity(
        route_hash="provenance-route",
        route=route,
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
        status="approved",
        confidence_score=88.0,
        risk_rules={
            "quote_freshness_ok": True,
            "net_profit_after_fees_ok": True,
            "profit_bps_ok": True,
            "price_impact_ok": True,
            "assets_allowlisted": True,
            "app_ids_allowlisted": True,
        },
        created_at=now,
    )


def test_data_provenance_traces_metric_to_quote_snapshot_route_and_risk(tmp_path):
    now = time.time()
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    store.record_pool_snapshots([_pool("tinyman:ALGO-USDC", now), _pool("pact:ALGO-USDC", now)])
    store.record_opportunities([_opportunity(now)])

    report = store.data_provenance_report(metric_key="route.expected_net_profit", route_hash="provenance-route")

    assert report["selectedMetric"]["key"] == "route.expected_net_profit"
    assert report["selectedMetric"]["value"] == "0.364"
    assert report["routeHash"] == "provenance-route"
    assert report["complete"] is True
    assert report["liveExecutionTouched"] is False
    assert report["signerCodeTouched"] is False
    lineage = {step["key"]: step for step in report["lineage"]}
    assert set(lineage) == {"metric", "source_data", "quote", "pool_snapshot", "route_calculation", "risk_decision"}
    assert len(lineage["quote"]["records"]) == 2
    assert len(lineage["pool_snapshot"]["records"]) == 2
    assert lineage["route_calculation"]["records"][0]["table"] == "opportunities"
    assert lineage["risk_decision"]["records"][0]["table"] == "risk_decisions"
    assert {metric["key"] for metric in report["metrics"]} >= {
        "scanner.pool_count",
        "quote.count",
        "route.count",
        "route.expected_net_profit",
        "risk.decision_count",
    }


def test_data_provenance_reports_missing_lineage_when_store_is_empty(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()

    report = store.data_provenance_report(metric_key="route.expected_net_profit")

    assert report["complete"] is False
    assert "Quote" in report["missingSteps"]
    assert "Pool Snapshot" in report["missingSteps"]
    assert "Route Calculation" in report["missingSteps"]
    assert "Risk Decision" in report["missingSteps"]
    assert report["source"] in {"stored", "unavailable"}
    assert report["liveExecutionTouched"] is False
    assert report["signerCodeTouched"] is False
