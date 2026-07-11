import time
from dataclasses import replace

from algopulse.config import get_settings
from algopulse.models import Opportunity, Pool
from algopulse.store import MarketStore


def _settings():
    return replace(
        get_settings(),
        enable_live_execution=False,
        execute_approved=False,
        signer_enabled=False,
        signer_kill_switch=True,
        allowed_asset_ids=(0, 31566704),
        allowed_app_ids=(10_001, 10_002),
        require_app_id_allowlist=True,
        max_route_age_seconds=5,
    )


def _pool(index: int, captured_at: float) -> Pool:
    venue = "tinyman" if index % 2 == 0 else "pact"
    return Pool(
        pool_id=f"{venue}:ALGO-USDC:{index}",
        venue_id=venue,
        app_id=10_001 if venue == "tinyman" else 10_002,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=100_000.0 + index,
        reserve_b=20_000.0 + index,
        fee_bps=30,
        block_round=1_000 + index,
        captured_at=captured_at,
    )


def _opportunity(index: int, now: float) -> Opportunity:
    route = [
        {
            "route_kind": "two_leg_venue_arb",
            "venue": "tinyman",
            "pool_id": f"tinyman:ALGO-USDC:{index * 2}",
            "app_id": 10_001,
            "input_asset_id": 0,
            "output_asset_id": 31566704,
            "input_amount": 5.0,
            "expected_output": 1.05,
            "fee_amount": 0.015,
            "price_impact_bps": 12.0,
            "block_round": 1_000,
            "captured_at": now,
            "expires_at": now + 5,
        },
        {
            "route_kind": "two_leg_venue_arb",
            "venue": "pact",
            "pool_id": f"pact:ALGO-USDC:{index * 2 + 1}",
            "app_id": 10_002,
            "input_asset_id": 31566704,
            "output_asset_id": 0,
            "input_amount": 1.05,
            "expected_output": 5.12,
            "fee_amount": 0.003,
            "price_impact_bps": 9.0,
            "block_round": 1_001,
            "captured_at": now,
            "expires_at": now + 5,
        },
    ]
    return Opportunity(
        route_hash=f"evidence-route-{index}",
        route=route,
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=5.12,
        gross_profit=0.12,
        estimated_network_fee=0.006,
        total_dex_fees=0.018,
        total_price_impact_bps=21.0,
        slippage_buffer=0.05,
        expected_net_profit=0.046,
        expected_profit_bps=92.0,
        max_price_impact_bps=12.0,
        involved_pool_ids=[route[0]["pool_id"], route[1]["pool_id"]],
        involved_asset_ids=[0, 31566704],
        status="rejected",
        skip_reason="profit_buffer",
        confidence_score=72.0,
        risk_rules={
            "quote_freshness_ok": True,
            "net_profit_after_fees_ok": False,
            "profit_bps_ok": True,
            "price_impact_ok": True,
            "assets_allowlisted": True,
            "app_ids_allowlisted": True,
        },
        created_at=now,
    )


def test_evidence_records_are_generated_and_filterable(tmp_path):
    now = time.time()
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    store.record_pool_snapshots([_pool(index, now - 90_000 + index) for index in range(100)])
    store.record_opportunities([_opportunity(index, now) for index in range(50)])
    store.record_paper_trade(_opportunity(0, now), would_execute=False, notes="paper-only evidence")
    store.generate_market_intelligence_report(now=now)

    report = store.evidence_records_report(_settings(), now=now)

    assert report["source"] == "stored"
    assert report["liveExecutionTouched"] is False
    assert report["signerCodeTouched"] is False
    assert report["summary"]["total"] >= 20
    assert set(report["summary"]["categories"]) == {
        "scanner",
        "quotes",
        "routes",
        "paper_trading",
        "risk",
        "dry_run",
        "execution",
        "receipts",
    }
    by_id = {item["evidenceId"]: item for item in report["records"]}
    assert by_id["scanner.pools_100"]["status"] == "pass"
    assert by_id["routes.opportunities_50"]["status"] == "pass"
    assert by_id["routes.rejection_reasons_100"]["status"] == "pass"
    assert by_id["risk.decisions_recorded"]["status"] == "pass"
    assert by_id["execution.live_disarmed"]["status"] == "pass"
    assert by_id["execution.kill_switch_active"]["metadata"]["liveExecutionTouched"] is False

    route_report = store.evidence_records_report(_settings(), category="routes", now=now)
    assert route_report["filters"]["category"] == "routes"
    assert {item["category"] for item in route_report["records"]} == {"routes"}

    pass_report = store.evidence_records_report(_settings(), status="pass", now=now)
    assert pass_report["records"]
    assert {item["status"] for item in pass_report["records"]} == {"pass"}


def test_empty_evidence_records_explain_pending_work(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()

    report = store.evidence_records_report(_settings(), now=time.time())
    by_id = {item["evidenceId"]: item for item in report["records"]}

    assert by_id["scanner.pools_100"]["status"] == "pending"
    assert by_id["dry_run.receipts_recorded"]["status"] == "pending"
    assert by_id["execution.live_disarmed"]["status"] == "pass"
    assert by_id["execution.kill_switch_active"]["status"] == "pass"
