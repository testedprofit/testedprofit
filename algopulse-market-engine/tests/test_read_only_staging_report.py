import json
import time

from algopulse.models import Opportunity
from algopulse.models import Pool
from algopulse.store import MarketStore


def _pool(captured_at: float) -> Pool:
    return Pool(
        pool_id="tinyman:ALGO-USDC",
        venue_id="tinyman",
        app_id=1001,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=100_000.0,
        reserve_b=20_000.0,
        fee_bps=30,
        block_round=12_000,
        captured_at=captured_at,
    )


def _opportunity(route_hash: str, now: float, *, status: str = "approved", skip_reason: str | None = None) -> Opportunity:
    route = [
        {
            "venue": "tinyman",
            "pool_id": "tinyman:ALGO-USDC",
            "input_asset_id": 0,
            "output_asset_id": 31566704,
            "input_amount": 5.0,
            "expected_output": 1.0,
            "fee_amount": 0.015,
            "price_impact_bps": 10.0,
            "block_round": 12_000,
            "captured_at": now - 1,
            "expires_at": now + 30,
        }
    ]
    return Opportunity(
        route_hash=route_hash,
        route=route,
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=5.5,
        gross_profit=0.5,
        estimated_network_fee=0.006,
        total_dex_fees=0.015,
        total_price_impact_bps=10.0,
        slippage_buffer=0.0,
        expected_net_profit=0.45,
        expected_profit_bps=900.0,
        max_price_impact_bps=10.0,
        involved_pool_ids=["tinyman:ALGO-USDC"],
        involved_asset_ids=[0, 31566704],
        status=status,
        skip_reason=skip_reason,
        confidence_score=90.0,
        risk_rules={
            "assets_allowlisted": True,
            "app_ids_allowlisted": True,
            "quote_freshness_ok": True,
            "net_profit_after_fees_ok": status == "approved",
        },
        created_at=now - 1,
    )


def _seed_complete_read_only_store(tmp_path) -> tuple[MarketStore, float]:
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    now = time.time()
    store.record_pool_snapshots([_pool(now - 23 * 60 * 60), _pool(now - 1)])
    approved = _opportunity("approved-route", now)
    rejected = _opportunity("rejected-route", now, status="rejected", skip_reason="profit_bps_ok")
    store.record_opportunities([approved, rejected])
    store.record_service_health(
        "connector:tinyman",
        "ok",
        metrics={"connector": "tinyman", "connectorType": "dex", "freshCount24h": 2},
    )
    store.record_paper_trade(approved, would_execute=True, notes="paper check")
    store.update_due_paper_trades([_pool(now)], now=now + 31)
    return store, now


def test_read_only_staging_report_counts_stored_evidence_without_live_execution(tmp_path):
    store, now = _seed_complete_read_only_store(tmp_path)

    report = store.read_only_staging_report(now=now, max_quote_age_seconds=5)

    assert report["mode"] == "read_only_staging"
    assert report["source"] == "stored"
    assert report["scanner"]["poolsMonitored"] == 1
    assert report["scanner"]["snapshotCount"] == 2
    assert report["scanner"]["uptimeSeconds"] >= (23 * 60 * 60) - 5
    assert report["quotes"]["recorded"] == 2
    assert report["quotes"]["fresh"] == 2
    assert report["quotes"]["stale"] == 0
    assert report["connectors"]["okCount"] >= 1
    assert report["connectors"]["downCount"] == 0
    assert report["routes"]["candidateCount"] == 2
    assert report["routes"]["approvedCount"] == 1
    assert report["routes"]["rejectedCount"] == 1
    assert report["routes"]["rejectedByReason"] == [{"reason": "profit_bps_ok", "count": 1}]
    assert report["risk"]["decisionCount"] == 2
    assert report["paper"]["tradeCount"] == 1
    assert report["paper"]["checked5sCount"] == 1
    assert report["paper"]["checked30sCount"] == 1
    assert report["paper"]["survivedT5Count"] in {0, 1}
    assert report["paper"]["survivedT30Count"] in {0, 1}
    assert report["paper"]["complete"] is True
    assert report["evidenceSamples"]["source"] == "stored"
    assert report["evidenceSamples"]["maxSamplesPerType"] == 5
    assert report["evidenceSamples"]["scannerUptime"][0]["poolId"] == "tinyman:ALGO-USDC"
    assert report["evidenceSamples"]["scannerUptime"][0]["source"] == "stored"
    assert report["evidenceSamples"]["quoteFreshness"][0]["readinessEligible"] is True
    assert report["evidenceSamples"]["connectorState"][0]["connectorName"] == "tinyman"
    assert {item["routeHash"] for item in report["evidenceSamples"]["routeDecisions"]} == {
        "approved-route",
        "rejected-route",
    }
    risk_by_route = {item["routeHash"]: item for item in report["evidenceSamples"]["riskDecisions"]}
    assert risk_by_route["approved-route"]["decision"] == "approved"
    assert risk_by_route["rejected-route"]["decision"] == "rejected"
    assert risk_by_route["rejected-route"]["reason"] == "profit_bps_ok"
    assert report["evidenceSamples"]["paperTradeSurvival"][0]["routeHash"] == "approved-route"
    assert report["evidenceSamples"]["paperTradeSurvival"][0]["survivedT30"] in {True, False}
    assert report["evidenceSamples"]["liveExecutionTouched"] is False
    assert report["evidenceSamples"]["signerCodeTouched"] is False
    assert report["liveExecutionRequired"] is False
    assert report["dryRunRequired"] is False
    serialized = json.dumps(report).lower()
    assert "raw_route_json" not in serialized
    assert "route_json" not in serialized
    assert "execution_queue" not in serialized
    assert "hot_wallet" not in serialized
    assert "submission_payload" not in serialized
    assert "signed_txn" not in serialized


def test_read_only_staging_report_surfaces_stale_quote_and_down_connector_blockers(tmp_path):
    store, now = _seed_complete_read_only_store(tmp_path)
    with store._connect() as con:
        con.execute("update quotes set captured_at = ?, expires_at = ? where route_hash = ?", (now - 30, now - 20, "rejected-route"))
    store.record_service_health(
        "connector:pact",
        "error",
        detail="timeout",
        metrics={"connector": "pact", "connectorType": "dex"},
    )

    report = store.read_only_staging_report(now=now, max_quote_age_seconds=5)
    blocker_codes = {item["code"] for item in report["blockers"]}

    assert report["status"] == "blocked"
    assert report["quotes"]["stale"] == 1
    assert any(item["freshnessStatus"] == "stale" for item in report["evidenceSamples"]["quoteFreshness"])
    assert report["connectors"]["downCount"] == 1
    assert any(item["status"] == "down" for item in report["evidenceSamples"]["connectorState"])
    assert "stale_quotes_present" in blocker_codes
    assert "connector_down" in blocker_codes
    assert report["nextRequiredGate"] in {
        "restore connector reliability",
        "clear connector readiness blockers",
        "stabilize fresh quote capture",
    }


def test_read_only_staging_report_marks_missing_paper_evidence_incomplete(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    now = time.time()
    store.record_pool_snapshots([_pool(now - 1)])
    store.record_opportunities([_opportunity("approved-route", now)])
    store.record_service_health(
        "connector:tinyman",
        "ok",
        metrics={"connector": "tinyman", "connectorType": "dex", "freshCount24h": 1},
    )

    report = store.read_only_staging_report(now=now, max_quote_age_seconds=5)
    blocker_codes = {item["code"] for item in report["blockers"]}

    assert report["paper"]["tradeCount"] == 0
    assert report["paper"]["complete"] is False
    assert "missing_paper_evidence" in blocker_codes
    assert report["nextRequiredGate"] == "collect paper-trading evidence"
    assert report["liveExecutionRequired"] is False
    assert report["dryRunRequired"] is False
