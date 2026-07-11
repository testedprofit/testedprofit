import sqlite3

from fastapi.testclient import TestClient

from algopulse.api import app
from algopulse.connectors.mock import MockMarketConnector
from algopulse.engine import RouteEngine
from algopulse.risk import RiskEngine
from algopulse.store import MarketStore


def test_mock_connector_exposes_tinyman_and_pact_market_data():
    connector = MockMarketConnector()

    venues = {venue.venue_id for venue in connector.list_venues()}
    pools = connector.list_pools()
    pool_venues = {pool.venue_id for pool in pools}

    assert {"tinyman", "pact"} == venues
    assert {"tinyman", "pact"}.issubset(pool_venues)
    assert any(pool.pool_id.startswith("tinyman:") for pool in pools)
    assert any(pool.pool_id.startswith("pact:") for pool in pools)


def test_route_generation_records_and_reconstructs_stored_quotes(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    pools = MockMarketConnector().list_pools()
    engine = RouteEngine(risk_engine=RiskEngine(), trade_sizes=[1.0])
    opportunities = engine.find_opportunities(pools)

    store.record_opportunities(opportunities[:3])
    stored = store.list_opportunities(limit=3)

    with sqlite3.connect(tmp_path / "market.db") as con:
        con.row_factory = sqlite3.Row
        quote_rows = con.execute(
            """
            select route_hash, venue_id, pool_id, input_asset_id, output_asset_id,
                   input_amount, output_amount, fee_amount, price_impact_bps,
                   block_round, captured_at, expires_at
            from quotes
            order by route_hash, leg_index
            """
        ).fetchall()

    assert stored
    assert quote_rows
    assert {row["route_hash"] for row in quote_rows}.issubset({item["route_hash"] for item in stored})
    for row in quote_rows:
        assert row["venue_id"] in {"tinyman", "pact"}
        assert row["pool_id"]
        assert row["input_amount"] > 0
        assert row["output_amount"] > 0
        assert row["fee_amount"] >= 0
        assert row["price_impact_bps"] >= 0
        assert row["block_round"] > 0
        assert row["expires_at"] >= row["captured_at"]


def test_paper_trade_logging_from_generated_route(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    pools = MockMarketConnector().list_pools()
    engine = RouteEngine(risk_engine=RiskEngine(), trade_sizes=[1.0])
    opportunity = engine.find_opportunities(pools)[0]

    store.record_paper_trade(
        opportunity=opportunity,
        would_execute=opportunity.status == "approved",
        notes=f"skip: {opportunity.skip_reason or 'approved'}",
    )
    rows = store.list_paper_trades(limit=1)

    assert rows[0]["route_hash"] == opportunity.route_hash
    assert rows[0]["opportunity_status"] == opportunity.status
    assert rows[0]["input_amount"] == opportunity.input_amount
    assert rows[0]["expected_final_amount"] == opportunity.expected_final_amount
    assert rows[0]["confidence_score"] == opportunity.confidence_score
    assert rows[0]["success"] is None
    assert rows[0]["check_60s_due_at"] > rows[0]["check_30s_due_at"]
    assert rows[0]["route_json"] != "[]"

    decay = store.opportunity_decay_dashboard(view="24h")
    assert decay["source"] == "stored"
    assert decay["summary"]["opportunityCount"] == 1
    assert decay["records"][0]["routeHash"] == opportunity.route_hash


def test_opportunity_replay_lab_uses_paper_trade_history(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    connector = MockMarketConnector()
    pools = connector.list_pools()
    store.upsert_assets(connector.list_assets())
    store.upsert_venues(connector.list_venues())
    store.record_pool_snapshots(pools)
    engine = RouteEngine(risk_engine=RiskEngine(), trade_sizes=[1.0])
    opportunity = engine.find_opportunities(pools)[0]

    store.record_paper_trade(
        opportunity=opportunity,
        would_execute=opportunity.status == "approved",
        notes=f"skip: {opportunity.skip_reason or 'approved'}",
    )
    replays = store.list_opportunity_replays(limit=1)

    assert len(replays) == 1
    replay = replays[0]
    assert replay["routeHash"] == opportunity.route_hash
    assert replay["expectedProfit"] == opportunity.expected_net_profit
    assert replay["priceImpactBps"] >= 0
    assert replay["routeConfidence"] >= 0
    assert [item["label"] for item in replay["timeline"]] == [
        "T0 detected",
        "T+5s recheck",
        "T+30s recheck",
    ]
    assert replay["verdict"] in {"would_execute", "would_skip", "unsafe", "stale"}


def test_admin_preflight_and_user_pnet_access_endpoints():
    client = TestClient(app)
    admin = "ADMIN6H2ZREVIEWWALLET9KX4CONTROL"

    preflight = client.get(
        "/api/admin/preflight",
        headers={"X-Algopulse-Role": "admin", "X-Algopulse-Wallet": admin},
    )
    fee_quote = client.post(
        "/api/user/pnet/fee-quote",
        json={"wallet": "USER7R3VIEWWALLET", "action": "run_simulation", "pair": "PNET/USDC"},
    )

    assert preflight.status_code == 200
    assert preflight.json()["data"]["checklist"]
    assert fee_quote.status_code == 200
    assert fee_quote.json()["data"]["action"] == "run_simulation"
    assert fee_quote.json()["data"]["feeAmountAtomic"] == "24000000"
