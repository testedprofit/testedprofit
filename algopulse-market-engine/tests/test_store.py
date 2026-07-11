import json
import sqlite3
import time

from algopulse.algorand import display_to_raw
from algopulse.models import Asset, Opportunity, Pool
from algopulse.store import MarketStore


def _pool(pool_id: str, asset_a_id: int, asset_b_id: int, captured_at: float) -> Pool:
    return Pool(
        pool_id=pool_id,
        venue_id="pact",
        app_id=1,
        asset_a_id=asset_a_id,
        asset_b_id=asset_b_id,
        reserve_a=10_000.0,
        reserve_b=10_000.0,
        fee_bps=30,
        block_round=1,
        captured_at=captured_at,
    )


def _opportunity(route_hash: str, involved_asset_ids: list[int], status: str, created_at: float) -> Opportunity:
    return Opportunity(
        route_hash=route_hash,
        route=[],
        input_asset_id=involved_asset_ids[0],
        input_amount=5.0,
        expected_final_amount=5.5,
        expected_net_profit=0.5,
        expected_profit_bps=1_000.0,
        max_price_impact_bps=10.0,
        involved_pool_ids=[route_hash],
        involved_asset_ids=involved_asset_ids,
        status=status,
        created_at=created_at,
    )


def _route_readiness_opportunity(
    route_hash: str,
    *,
    venue: str = "tinyman",
    status: str = "approved",
    skip_reason: str | None = None,
    captured_at: float,
    expires_at: float,
) -> Opportunity:
    route = [
        {
            "venue": venue,
            "pool_id": f"{venue}:ALGO-USDC",
            "input_asset_id": 0,
            "output_asset_id": 31566704,
            "input_amount": 5.0,
            "expected_output": 1.0,
            "fee_amount": 0.015,
            "price_impact_bps": 10.0,
            "block_round": 12_500,
            "captured_at": captured_at,
            "expires_at": expires_at,
        }
    ]
    return Opportunity(
        route_hash=route_hash,
        route=route,
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=5.4,
        expected_net_profit=0.4,
        expected_profit_bps=800.0,
        max_price_impact_bps=10.0,
        involved_pool_ids=[f"{venue}:ALGO-USDC"],
        involved_asset_ids=[0, 31566704],
        gross_profit=0.4,
        estimated_network_fee=0.006,
        total_dex_fees=0.015,
        total_price_impact_bps=10.0,
        slippage_buffer=0.0,
        status=status,
        skip_reason=skip_reason,
        confidence_score=90.0,
        risk_rules={"route_ready_fixture": status == "approved"},
        created_at=captured_at,
    )


def _record_connector_health(
    store: MarketStore,
    connector: str,
    status: str = "ok",
    *,
    connector_type: str = "dex",
    detail: str | None = None,
    metrics: dict | None = None,
) -> None:
    payload = {"connector": connector, "connectorType": connector_type}
    payload.update(metrics or {})
    store.record_service_health(f"connector:{connector}", status, detail=detail, metrics=payload)


def test_store_initializes_minimum_production_tables(tmp_path):
    database_path = tmp_path / "market.db"
    store = MarketStore(database_path)
    store.initialize()

    with sqlite3.connect(database_path) as con:
        tables = {
            row[0]
            for row in con.execute(
                """
                select name
                from sqlite_master
                where type = 'table'
                """
            ).fetchall()
        }

    assert {
        "assets",
        "venues",
        "pools",
        "pool_snapshots",
        "quotes",
        "opportunities",
        "paper_trades",
        "risk_decisions",
        "route_forensics",
        "live_trades",
        "service_health",
        "alerts",
        "production_gates",
        "production_evidence",
        "evidence_records",
        "market_intelligence_reports",
        "opportunity_decay",
        "user_actions",
        "decision_events",
    }.issubset(tables)
    with sqlite3.connect(database_path) as con:
        snapshot_columns = {
            row[1]
            for row in con.execute(
                """
                pragma table_info(pool_snapshots)
                """
            ).fetchall()
        }
        quote_columns = {
            row[1]
            for row in con.execute(
                """
                pragma table_info(quotes)
                """
            ).fetchall()
        }
        opportunity_columns = {
            row[1]
            for row in con.execute(
                """
                pragma table_info(opportunities)
                """
            ).fetchall()
        }
        paper_columns = {
            row[1]
            for row in con.execute(
                """
                pragma table_info(paper_trades)
                """
            ).fetchall()
        }
        decay_columns = {
            row[1]
            for row in con.execute(
                """
                pragma table_info(opportunity_decay)
                """
            ).fetchall()
        }
        forensics_columns = {
            row[1]
            for row in con.execute(
                """
                pragma table_info(route_forensics)
                """
            ).fetchall()
        }
        user_action_columns = {
            row[1]
            for row in con.execute(
                """
                pragma table_info(user_actions)
                """
            ).fetchall()
        }
        decision_columns = {
            row[1]
            for row in con.execute(
                """
                pragma table_info(decision_events)
                """
            ).fetchall()
        }
        production_gate_count = con.execute("select count(*) from production_gates").fetchone()[0]
    assert {"liquidity_estimate", "data_freshness_seconds"}.issubset(snapshot_columns)
    assert {
        "venue_id",
        "pool_id",
        "input_asset_id",
        "output_asset_id",
        "input_amount",
        "output_amount",
        "price_impact_bps",
        "fee_amount",
        "block_round",
        "captured_at",
        "expires_at",
    }.issubset(quote_columns)
    assert {
        "gross_profit",
        "estimated_network_fee",
        "total_dex_fees",
        "total_price_impact_bps",
        "slippage_buffer",
        "expected_net_profit",
        "confidence_score",
        "skip_reason",
    }.issubset(opportunity_columns)
    assert {
        "opportunity_status",
        "skip_reason",
        "input_asset_id",
        "input_amount",
        "expected_final_amount",
        "expected_net_profit",
        "route_json",
        "quote_captured_at",
        "check_5s_due_at",
        "check_30s_due_at",
        "check_60s_due_at",
        "checked_5s_at",
        "checked_30s_at",
        "checked_60s_at",
        "simulated_final_amount_5s",
        "simulated_final_amount_30s",
        "simulated_final_amount_60s",
        "quote_decay_5s",
        "quote_decay_30s",
        "quote_decay_60s",
        "expected_vs_simulated_profit_5s",
        "expected_vs_simulated_profit_30s",
        "expected_vs_simulated_profit_60s",
        "last_error",
        "simulated_profit_60s",
        "confidence_score",
        "success",
    }.issubset(paper_columns)
    assert {
        "detected_at",
        "route_hash",
        "expected_profit",
        "expected_profit_5s",
        "expected_profit_30s",
        "expected_profit_60s",
        "pair_label",
        "venues_json",
        "route_type",
    }.issubset(decay_columns)
    assert {
        "route_hash",
        "opportunity_id",
        "route_path_json",
        "profitability_json",
        "quote_freshness_json",
        "price_impact_json",
        "liquidity_score_json",
        "risk_result_json",
        "approval_decision_json",
        "rejection_reason",
        "confidence_calculation_json",
        "decision_tree_json",
        "completeness_json",
    }.issubset(forensics_columns)
    assert {
        "action_type",
        "timestamp",
        "user_role",
        "wallet_connected",
        "source_page",
        "metadata_json",
    }.issubset(user_action_columns)
    assert {
        "decision_id",
        "action_type",
        "user_role",
        "page",
        "evidence_source",
        "created_at",
    }.issubset(decision_columns)
    assert production_gate_count > 0


def test_store_migrates_existing_pool_snapshot_columns(tmp_path):
    database_path = tmp_path / "market.db"
    with sqlite3.connect(database_path) as con:
        con.execute(
            """
            create table pool_snapshots (
                id integer primary key autoincrement,
                pool_id text not null,
                venue_id text not null,
                app_id integer not null,
                asset_a_id integer not null,
                asset_b_id integer not null,
                reserve_a real not null,
                reserve_b real not null,
                fee_bps integer not null,
                price_a_in_b real not null,
                price_b_in_a real not null,
                block_round integer not null,
                captured_at real not null
            )
            """
        )

    store = MarketStore(database_path)
    store.initialize()

    with sqlite3.connect(database_path) as con:
        snapshot_columns = {row[1] for row in con.execute("pragma table_info(pool_snapshots)").fetchall()}

    assert {"liquidity_estimate", "data_freshness_seconds"}.issubset(snapshot_columns)


def test_store_records_user_actions_and_decision_events(tmp_path):
    database_path = tmp_path / "market.db"
    store = MarketStore(database_path)
    store.initialize()
    now = time.time()

    pulse = store.record_user_action(
        action_type="viewed_market_pulse",
        user_role="guest",
        wallet_connected=False,
        source_page="pulse",
        metadata={"session_id": "guest-1"},
        timestamp=now,
    )
    route = store.record_user_action(
        action_type="opened_route",
        user_role="user",
        wallet_connected=True,
        source_page="routes",
        metadata={"session_id": "user-1", "pnet_user": True, "evidence_source": "route_details"},
        timestamp=now + 1,
    )
    store.record_user_action(
        action_type="opened_daily_report",
        user_role="user",
        wallet_connected=True,
        source_page="research",
        metadata={"session_id": "user-1", "pnet_user": True},
        timestamp=now + 86_500,
    )

    assert pulse["decisionRecorded"] is False
    assert route["decisionRecorded"] is True
    report = store.product_validation_report(window_days=2, now=now + 86_600)

    assert report["source"] == "stored"
    assert report["summary"]["totalActions"] == 3
    assert report["summary"]["decisionCount"] == 2
    assert report["summary"]["repeatUsers"] == 1
    assert next(item for item in report["funnel"] if item["key"] == "pnet_user")["users"] == 1
    assert next(item for item in report["featureUtility"] if item["feature"] == "Route Intelligence")["decisionCount"] == 1
    assert report["liveExecutionTouched"] is False
    assert report["signerCodeTouched"] is False


def test_store_migrates_existing_quote_columns(tmp_path):
    database_path = tmp_path / "market.db"
    with sqlite3.connect(database_path) as con:
        con.execute(
            """
            create table quotes (
                id integer primary key autoincrement,
                route_hash text,
                opportunity_id integer,
                leg_index integer not null,
                pool_id text not null,
                venue_id text not null,
                input_asset_id integer not null,
                output_asset_id integer not null,
                input_amount real not null,
                output_amount real not null,
                fee_amount real,
                price_impact_bps real,
                captured_at real not null
            )
            """
        )

    store = MarketStore(database_path)
    store.initialize()

    with sqlite3.connect(database_path) as con:
        quote_columns = {row[1] for row in con.execute("pragma table_info(quotes)").fetchall()}

    assert {"block_round", "expires_at"}.issubset(quote_columns)


def test_store_migrates_existing_opportunity_breakdown_columns(tmp_path):
    database_path = tmp_path / "market.db"
    with sqlite3.connect(database_path) as con:
        con.execute(
            """
            create table opportunities (
                id integer primary key autoincrement,
                route_hash text not null,
                route_json text not null,
                input_asset_id integer not null,
                input_amount real not null,
                expected_final_amount real not null,
                expected_net_profit real not null,
                expected_profit_bps real not null,
                max_price_impact_bps real not null,
                involved_pool_ids_json text not null,
                involved_asset_ids_json text not null,
                status text not null,
                skip_reason text,
                confidence_score real not null,
                risk_rules_json text not null,
                created_at real not null
            )
            """
        )
        con.execute(
            """
            insert into opportunities (
                route_hash, route_json, input_asset_id, input_amount,
                expected_final_amount, expected_net_profit, expected_profit_bps,
                max_price_impact_bps, involved_pool_ids_json, involved_asset_ids_json,
                status, skip_reason, confidence_score, risk_rules_json, created_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-route",
                json.dumps(
                    [
                        {"fee_amount": 0.01, "price_impact_bps": 10.0},
                        {"fee_amount": 0.02, "price_impact_bps": 12.0},
                    ]
                ),
                0,
                5.0,
                5.5,
                0.4,
                800.0,
                12.0,
                json.dumps(["pool-a", "pool-b"]),
                json.dumps([0, 31566704]),
                "rejected",
                "profit_bps_ok",
                88.0,
                json.dumps({"profit_bps_ok": False}),
                time.time(),
            ),
        )

    store = MarketStore(database_path)
    store.initialize()

    with sqlite3.connect(database_path) as con:
        con.row_factory = sqlite3.Row
        opportunity_columns = {row[1] for row in con.execute("pragma table_info(opportunities)").fetchall()}
        legacy = con.execute("select * from opportunities where route_hash = 'legacy-route'").fetchone()

    assert {
        "gross_profit",
        "estimated_network_fee",
        "total_dex_fees",
        "total_price_impact_bps",
        "slippage_buffer",
    }.issubset(opportunity_columns)
    assert legacy["gross_profit"] == 0.5
    assert legacy["estimated_network_fee"] == 0.006
    assert round(legacy["total_dex_fees"], 6) == 0.03
    assert legacy["total_price_impact_bps"] == 22.0
    assert round(legacy["slippage_buffer"], 6) == 0.094


def test_target_asset_filter_keeps_old_market_data_out_of_pulse(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    now = time.time()
    target_asset_id = 3169177585

    store.record_pool_snapshots(
        [
            _pool("old-algo-usdc", 0, 31566704, now - 30),
            _pool("pnet-usdc", target_asset_id, 31566704, now),
        ]
    )
    store.record_opportunities(
        [
            _opportunity("old-approved", [0, 31566704], "approved", now),
            _opportunity("pnet-rejected", [target_asset_id, 31566704], "rejected", now),
        ]
    )

    all_pulse = store.get_pulse(public_delay_seconds=0)
    target_pulse = store.get_pulse(public_delay_seconds=0, required_asset_id=target_asset_id)
    target_pools = store.list_latest_pools(required_asset_id=target_asset_id)
    target_opportunities = store.list_opportunities(required_asset_id=target_asset_id)
    target_best = store.get_best_approved_opportunity(required_asset_id=target_asset_id)
    with sqlite3.connect(tmp_path / "market.db") as con:
        pool_count = con.execute("select count(*) from pools").fetchone()[0]
        risk_decision_count = con.execute("select count(*) from risk_decisions").fetchone()[0]

    assert all_pulse["pools_monitored"] == 2
    assert all_pulse["approved_24h"] == 1
    assert target_pulse["pools_monitored"] == 1
    assert target_pulse["opportunities_24h"] == 1
    assert target_pulse["approved_24h"] == 0
    assert target_pulse["last_scan_at"] == now
    assert [pool["pool_id"] for pool in target_pools] == ["pnet-usdc"]
    assert target_pools[0]["liquidity_estimate"] == 10_000.0
    assert target_pools[0]["data_freshness_seconds"] >= 0
    assert target_pools[0]["snapshot_age_seconds"] >= 0
    assert [opportunity["route_hash"] for opportunity in target_opportunities] == ["pnet-rejected"]
    assert target_best is None
    assert pool_count == 2
    assert risk_decision_count == 2


def test_store_records_quote_rows_risk_decisions_and_service_health(tmp_path):
    database_path = tmp_path / "market.db"
    store = MarketStore(database_path)
    store.initialize()
    now = time.time()
    expires_at = now + 5
    opportunity = Opportunity(
        route_hash="route-with-quotes",
        route=[
            {
                "venue": "tinyman",
                "pool_id": "tinyman:ALGO-USDC",
                "input_asset_id": 0,
                "output_asset_id": 31566704,
                "input_amount": 5.0,
                "expected_output": 1.25,
                "fee_amount": 0.015,
                "price_impact_bps": 12.5,
                "block_round": 777,
                "captured_at": now,
                "expires_at": expires_at,
            },
            {
                "venue": "pact",
                "pool_id": "pact:ALGO-USDC",
                "input_asset_id": 31566704,
                "output_asset_id": 0,
                "input_amount": 1.25,
                "expected_output": 5.2,
                "fee_amount": 0.00375,
                "price_impact_bps": 10.0,
                "block_round": 778,
                "captured_at": now,
                "expires_at": expires_at,
            },
        ],
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=5.2,
        expected_net_profit=0.18,
        expected_profit_bps=360.0,
        max_price_impact_bps=12.5,
        involved_pool_ids=["tinyman:ALGO-USDC", "pact:ALGO-USDC"],
        involved_asset_ids=[0, 31566704],
        gross_profit=0.2,
        estimated_network_fee=0.006,
        total_dex_fees=0.01875,
        total_price_impact_bps=22.5,
        slippage_buffer=0.014,
        status="approved",
        risk_rules={"net_profit_after_fees_ok": True},
        created_at=now,
    )

    store.record_opportunities([opportunity])
    store.record_service_health("market_scanner", "ok", metrics={"opportunities": 1})

    with sqlite3.connect(database_path) as con:
        con.row_factory = sqlite3.Row
        opportunity_row = con.execute("select * from opportunities where route_hash = ?", (opportunity.route_hash,)).fetchone()
        quote_rows = con.execute("select * from quotes order by leg_index").fetchall()
        risk_row = con.execute("select approved, reason, rules_json from risk_decisions").fetchone()
        health_row = con.execute("select service_name, status, metrics_json from service_health").fetchone()

    assert opportunity_row["gross_profit"] == 0.2
    assert opportunity_row["estimated_network_fee"] == 0.006
    assert opportunity_row["total_dex_fees"] == 0.01875
    assert opportunity_row["total_price_impact_bps"] == 22.5
    assert opportunity_row["slippage_buffer"] == 0.014
    assert opportunity_row["expected_net_profit"] == 0.18
    assert opportunity_row["confidence_score"] == 0.0
    assert opportunity_row["skip_reason"] is None
    assert len(quote_rows) == 2
    assert quote_rows[0]["venue_id"] == "tinyman"
    assert quote_rows[0]["pool_id"] == "tinyman:ALGO-USDC"
    assert quote_rows[0]["input_asset_id"] == 0
    assert quote_rows[0]["output_asset_id"] == 31566704
    assert quote_rows[0]["input_amount"] == 5.0
    assert quote_rows[0]["output_amount"] == 1.25
    assert quote_rows[0]["fee_amount"] == 0.015
    assert quote_rows[0]["price_impact_bps"] == 12.5
    assert quote_rows[0]["block_round"] == 777
    assert quote_rows[0]["captured_at"] == now
    assert quote_rows[0]["expires_at"] == expires_at
    assert risk_row["approved"] == 1
    assert risk_row["reason"] is None
    assert "net_profit_after_fees_ok" in risk_row["rules_json"]
    assert health_row["service_name"] == "market_scanner"
    assert health_row["status"] == "ok"
    assert '"opportunities": 1' in health_row["metrics_json"]
    freshness = store.quote_freshness_evidence(max_age_seconds=5.0, now=now + 1)
    assert freshness["source"] == "stored"
    assert freshness["quoteCount"] == 2
    assert freshness["freshCount"] == 2
    assert freshness["freshQuoteCount"] == 2
    assert freshness["agingQuoteCount"] == 0
    assert freshness["staleCount"] == 0
    assert freshness["staleQuoteCount"] == 0
    assert freshness["unavailableQuoteCount"] == 0
    assert freshness["readinessEligibleQuoteCount"] == 2
    assert freshness["readinessExcludedQuoteCount"] == 0
    assert freshness["rejectedQuoteCount"] == 0
    assert freshness["rejectedReasons"] == []
    assert freshness["venuesRepresented"] == ["pact", "tinyman"]
    assert freshness["pairsRepresented"] == ["0/31566704"]
    assert freshness["freshnessStatus"] == "ok"
    assert freshness["blocksReadiness"] is False
    quote_record = freshness["quotes"][0]
    assert quote_record["venue"] == "pact"
    assert quote_record["pair"] == "0/31566704"
    assert quote_record["poolId"] == "pact:ALGO-USDC"
    assert quote_record["inputAssetId"] == 31566704
    assert quote_record["outputAssetId"] == 0
    assert quote_record["inputAmount"] == 1.25
    assert quote_record["inputAmount"] != display_to_raw(1.25, 6)
    assert quote_record["expectedOutput"] == 5.2
    assert quote_record["blockRound"] == 778
    assert quote_record["freshnessStatus"] == "fresh"
    assert quote_record["readinessEligible"] is True
    assert quote_record["rejectionReason"] is None
    assert quote_record["source"] == "stored"


def test_quote_freshness_rejects_expired_and_missing_captured_at_quotes(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    now = time.time()

    with sqlite3.connect(store.database_path) as con:
        con.executemany(
            """
            insert into quotes (
                route_hash, opportunity_id, leg_index, pool_id, venue_id,
                input_asset_id, output_asset_id, input_amount, output_amount,
                fee_amount, price_impact_bps, block_round, captured_at, expires_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "expired-route",
                    None,
                    0,
                    "tinyman:ALGO-USDC",
                    "tinyman",
                    0,
                    31566704,
                    5.0,
                    1.2,
                    0.015,
                    10.0,
                    100,
                    now - 2,
                    now - 1,
                ),
                (
                    "stale-route",
                    None,
                    0,
                    "tinyman:ALGO-USDC",
                    "tinyman",
                    0,
                    31566704,
                    5.0,
                    1.15,
                    0.015,
                    10.0,
                    102,
                    now - 10,
                    now + 10,
                ),
                (
                    "missing-captured-at",
                    None,
                    0,
                    "pact:ALGO-USDC",
                    "pact",
                    0,
                    31566704,
                    5.0,
                    1.1,
                    0.015,
                    10.0,
                    101,
                    0,
                    0,
                ),
            ],
        )

    evidence = store.quote_freshness_evidence(max_age_seconds=5.0, now=now, limit=10)
    by_hash = {item["routeHash"]: item for item in evidence["quotes"]}

    assert evidence["quoteCount"] == 3
    assert evidence["freshCount"] == 0
    assert evidence["freshQuoteCount"] == 0
    assert evidence["agingCount"] == 0
    assert evidence["agingQuoteCount"] == 0
    assert evidence["staleCount"] == 2
    assert evidence["staleQuoteCount"] == 2
    assert evidence["unavailableCount"] == 1
    assert evidence["unavailableQuoteCount"] == 1
    assert evidence["readinessEligibleQuoteCount"] == 0
    assert evidence["readinessExcludedQuoteCount"] == 3
    assert evidence["rejectedQuoteCount"] == 3
    assert evidence["rejectedReasons"] == [
        {"reason": "quote_expired", "count": 1},
        {"reason": "quote_stale", "count": 1},
        {"reason": "quote_unavailable", "count": 1},
    ]
    assert "quote_freshness_ok" not in {item["reason"] for item in evidence["rejectedReasons"]}
    assert evidence["venuesRepresented"] == ["pact", "tinyman"]
    assert evidence["pairsRepresented"] == ["0/31566704"]
    assert evidence["freshnessStatus"] == "blocked"
    assert evidence["blocksReadiness"] is True
    assert by_hash["expired-route"]["freshnessStatus"] == "stale"
    assert by_hash["expired-route"]["reason"] == "quote_expired"
    assert by_hash["expired-route"]["rejectionReason"] == "quote_expired"
    assert by_hash["expired-route"]["readinessEligible"] is False
    assert by_hash["stale-route"]["freshnessStatus"] == "stale"
    assert by_hash["stale-route"]["reason"] == "quote_stale"
    assert by_hash["stale-route"]["rejectionReason"] == "quote_stale"
    assert by_hash["stale-route"]["readinessEligible"] is False
    assert by_hash["missing-captured-at"]["freshnessStatus"] == "unavailable"
    assert by_hash["missing-captured-at"]["reason"] == "quote_unavailable"
    assert by_hash["missing-captured-at"]["rejectionReason"] == "quote_unavailable"
    assert by_hash["missing-captured-at"]["readinessEligible"] is False
    assert all(item["rejectionReason"] != "quote_freshness_ok" for item in by_hash.values())


def test_connector_reliability_evidence_reports_success_and_error_states(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()

    store.record_service_health("connector:tinyman", "ok", metrics={"connector": "tinyman"})
    store.record_service_health("connector:pact", "error", detail="timeout", metrics={"connector": "pact"})

    evidence = store.connector_reliability_evidence()
    by_connector = {item["connector"]: item for item in evidence["connectors"]}

    assert evidence["source"] == "stored"
    assert evidence["status"] == "degraded"
    assert evidence["connectorCount"] == 2
    assert evidence["healthyConnectorCount"] == 1
    assert evidence["errorConnectorCount"] == 1
    assert by_connector["tinyman"]["status"] == "ok"
    assert by_connector["tinyman"]["successCount"] == 1
    assert by_connector["pact"]["status"] == "down"
    assert by_connector["pact"]["errorCount"] == 1
    assert by_connector["pact"]["lastError"] == "timeout"
    assert evidence["liveExecutionTouched"] is False
    assert evidence["signerCodeTouched"] is False


def test_connector_reliability_blocks_when_connector_data_is_down(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()

    store.record_service_health("connector:pact", "error", detail="timeout", metrics={"connector": "pact"})

    evidence = store.connector_reliability_evidence()
    connector = evidence["connectors"][0]

    assert evidence["status"] == "down"
    assert evidence["blocksReadiness"] is True
    assert evidence["healthyConnectorCount"] == 0
    assert evidence["errorConnectorCount"] == 1
    assert connector["connector"] == "pact"
    assert connector["status"] == "down"
    assert connector["lastFailureAt"] is not None


def test_connector_degradation_evidence_distinguishes_live_dependency_states(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()

    store.record_service_health(
        "connector:tinyman",
        "ok",
        metrics={
            "connector": "tinyman",
            "connectorType": "dex",
            "latencyMs": 90,
            "freshCount24h": 12,
            "staleCount24h": 0,
        },
    )
    store.record_service_health(
        "connector:pact",
        "error",
        detail="timeout",
        metrics={"connector": "pact", "connectorType": "dex", "latencyMs": 850},
    )
    store.record_service_health(
        "connector:algod",
        "ok",
        metrics={
            "connector": "algod",
            "connectorType": "algod",
            "latencyMs": 55,
            "latestRound": 12_500,
            "expectedMinRound": 12_400,
        },
    )
    store.record_service_health(
        "connector:indexer",
        "ok",
        metrics={
            "connector": "indexer",
            "connectorType": "indexer",
            "latencyMs": 120,
            "latestRound": 12_250,
            "expectedMinRound": 12_400,
        },
    )
    store.record_service_health(
        "connector:mock",
        "ok",
        metrics={"connector": "mock", "connectorType": "dex", "freshCount24h": 3},
    )

    evidence = store.connector_reliability_evidence()
    by_connector = {item["connectorName"]: item for item in evidence["connectors"]}

    assert evidence["source"] == "stored"
    assert evidence["status"] == "degraded"
    assert evidence["blocksReadiness"] is True
    assert evidence["connectorCount"] == 5
    assert evidence["healthyConnectorCount"] == 2
    assert evidence["errorConnectorCount"] == 1
    assert evidence["waitingConnectorCount"] == 2
    assert evidence["blockedConnectorCount"] == 1

    tinyman = by_connector["tinyman"]
    assert tinyman["connectorType"] == "dex"
    assert tinyman["status"] == "ok"
    assert tinyman["readinessImpact"] == "ok"
    assert tinyman["productionReady"] is True
    assert tinyman["freshCount24h"] == 12
    assert tinyman["staleCount24h"] == 0
    assert tinyman["degradationReason"] is None

    pact = by_connector["pact"]
    assert pact["connectorType"] == "dex"
    assert pact["status"] == "down"
    assert pact["readinessImpact"] == "blocked"
    assert pact["degradationReason"] == "timeout"
    assert pact["errorCount24h"] == 1

    algod = by_connector["algod"]
    assert algod["connectorType"] == "algod"
    assert algod["status"] == "ok"
    assert algod["readinessImpact"] == "ok"
    assert algod["latestRound"] == 12_500
    assert algod["expectedMinRound"] == 12_400

    indexer = by_connector["indexer"]
    assert indexer["connectorType"] == "indexer"
    assert indexer["status"] == "degraded"
    assert indexer["readinessImpact"] == "wait"
    assert indexer["degradationReason"] == "indexer_round_stale"
    assert indexer["latestRound"] == 12_250
    assert indexer["expectedMinRound"] == 12_400

    mock = by_connector["mock"]
    assert mock["status"] == "mock"
    assert mock["readinessImpact"] == "wait"
    assert mock["productionReady"] is False
    assert mock["degradationReason"] == "mock_connector_not_production_ready"

    serialized = json.dumps(evidence).lower()
    forbidden_artifacts = (
        "mnemonic",
        "private_key",
        "seed_phrase",
        "hot_wallet",
        "signed_txn",
        "submission_payload",
        "execution_queue",
    )
    assert all(fragment not in serialized for fragment in forbidden_artifacts)


def test_connector_degradation_marks_stale_dex_quotes_as_stale(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()

    store.record_service_health(
        "connector:tinyman",
        "ok",
        metrics={
            "connector": "tinyman",
            "connectorType": "dex",
            "freshCount24h": 0,
            "staleCount24h": 4,
        },
    )

    evidence = store.connector_reliability_evidence()
    connector = evidence["connectors"][0]

    assert evidence["status"] == "degraded"
    assert evidence["waitingConnectorCount"] == 1
    assert evidence["blockedConnectorCount"] == 0
    assert connector["connectorName"] == "tinyman"
    assert connector["status"] == "stale"
    assert connector["readinessImpact"] == "wait"
    assert connector["degradationReason"] == "connector_quotes_stale"
    assert connector["freshCount24h"] == 0
    assert connector["staleCount24h"] == 4


def test_connector_degradation_blocks_when_algod_is_down_or_stale(tmp_path):
    down_store = MarketStore(tmp_path / "down.db")
    down_store.initialize()
    down_store.record_service_health(
        "connector:algod",
        "error",
        detail="algod unavailable",
        metrics={"connector": "algod", "connectorType": "algod"},
    )

    down_evidence = down_store.connector_reliability_evidence()
    down_algod = down_evidence["connectors"][0]

    assert down_evidence["status"] == "down"
    assert down_evidence["blocksReadiness"] is True
    assert down_algod["status"] == "down"
    assert down_algod["readinessImpact"] == "blocked"
    assert down_algod["degradationReason"] == "algod unavailable"

    stale_store = MarketStore(tmp_path / "stale.db")
    stale_store.initialize()
    stale_store.record_service_health(
        "connector:algod",
        "ok",
        metrics={
            "connector": "algod",
            "connectorType": "algod",
            "latestRound": 19_900,
            "expectedMinRound": 20_000,
        },
    )

    stale_evidence = stale_store.connector_reliability_evidence()
    stale_algod = stale_evidence["connectors"][0]

    assert stale_evidence["status"] == "down"
    assert stale_evidence["blocksReadiness"] is True
    assert stale_algod["status"] == "stale"
    assert stale_algod["readinessImpact"] == "blocked"
    assert stale_algod["degradationReason"] == "algod_round_stale"


def test_route_readiness_allows_fresh_quote_with_ok_connectors(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    now = time.time()
    opportunity = _route_readiness_opportunity(
        "ready-route",
        captured_at=now - 1,
        expires_at=now + 30,
    )
    store.record_opportunities([opportunity])
    _record_connector_health(store, "tinyman")

    evidence = store.route_readiness_evidence(now=now, max_quote_age_seconds=5)
    route = evidence["routes"][0]

    assert evidence["source"] == "stored"
    assert evidence["readyCount"] == 1
    assert evidence["waitCount"] == 0
    assert evidence["blockedCount"] == 0
    assert evidence["overallReadiness"] == "ready"
    assert route["routeHash"] == "ready-route"
    assert route["pair"] == "0/31566704"
    assert route["venues"] == ["tinyman"]
    assert route["readinessStatus"] == "ready"
    assert route["quoteFreshnessStatus"] == "fresh"
    assert route["connectorReadinessStatus"] == "ok"
    assert route["riskStatus"] == "approved"
    assert route["reasons"] == []
    assert route["productionReady"] is True


def test_route_readiness_blocks_stale_expired_and_missing_quote_evidence(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    now = time.time()
    opportunities = [
        _route_readiness_opportunity(
            "stale-route",
            captured_at=now - 30,
            expires_at=now + 30,
        ),
        _route_readiness_opportunity(
            "expired-route",
            captured_at=now - 1,
            expires_at=now - 0.1,
        ),
        _route_readiness_opportunity(
            "missing-captured-at-route",
            captured_at=now - 1,
            expires_at=now + 30,
        ),
        _opportunity("no-quote-route", [0, 31566704], "approved", now),
    ]
    store.record_opportunities(opportunities)
    with sqlite3.connect(store.database_path) as con:
        con.execute("update quotes set captured_at = 0 where route_hash = ?", ("missing-captured-at-route",))
    _record_connector_health(store, "tinyman")

    evidence = store.route_readiness_evidence(now=now, max_quote_age_seconds=5)
    by_hash = {route["routeHash"]: route for route in evidence["routes"]}

    assert evidence["readyCount"] == 0
    assert evidence["blockedCount"] == 4
    assert by_hash["stale-route"]["readinessStatus"] == "blocked"
    assert by_hash["stale-route"]["quoteFreshnessStatus"] == "stale"
    assert "quote_stale" in by_hash["stale-route"]["reasons"]
    assert by_hash["expired-route"]["readinessStatus"] == "blocked"
    assert by_hash["expired-route"]["quoteFreshnessStatus"] == "stale"
    assert "quote_expired" in by_hash["expired-route"]["reasons"]
    assert by_hash["missing-captured-at-route"]["readinessStatus"] == "blocked"
    assert by_hash["missing-captured-at-route"]["quoteFreshnessStatus"] == "unavailable"
    assert "quote_unavailable" in by_hash["missing-captured-at-route"]["reasons"]
    assert by_hash["no-quote-route"]["readinessStatus"] == "blocked"
    assert by_hash["no-quote-route"]["quoteFreshnessStatus"] == "unavailable"
    assert "quote_evidence_unavailable" in by_hash["no-quote-route"]["reasons"]
    assert all(route["reasons"] for route in evidence["routes"] if route["readinessStatus"] != "ready")


def test_route_readiness_blocks_down_connector_and_stale_algod(tmp_path):
    down_store = MarketStore(tmp_path / "down.db")
    down_store.initialize()
    now = time.time()
    down_store.record_opportunities(
        [
            _route_readiness_opportunity(
                "pact-down-route",
                venue="pact",
                captured_at=now - 1,
                expires_at=now + 30,
            )
        ]
    )
    _record_connector_health(down_store, "pact", "error", detail="timeout")

    down_evidence = down_store.route_readiness_evidence(now=now, max_quote_age_seconds=5)
    down_route = down_evidence["routes"][0]

    assert down_route["readinessStatus"] == "blocked"
    assert down_route["connectorReadinessStatus"] == "blocked"
    assert any(reason.startswith("connector_down:pact") for reason in down_route["reasons"])

    stale_algod_store = MarketStore(tmp_path / "stale-algod.db")
    stale_algod_store.initialize()
    stale_algod_store.record_opportunities(
        [
            _route_readiness_opportunity(
                "stale-algod-route",
                captured_at=now - 1,
                expires_at=now + 30,
            )
        ]
    )
    _record_connector_health(stale_algod_store, "tinyman")
    _record_connector_health(
        stale_algod_store,
        "algod",
        connector_type="algod",
        metrics={"latestRound": 19_900, "expectedMinRound": 20_000},
    )

    stale_algod_evidence = stale_algod_store.route_readiness_evidence(now=now, max_quote_age_seconds=5)
    stale_algod_route = stale_algod_evidence["routes"][0]

    assert stale_algod_route["readinessStatus"] == "blocked"
    assert stale_algod_route["connectorReadinessStatus"] == "blocked"
    assert "algod_round_stale" in stale_algod_route["reasons"]
    assert all(route["reasons"] for route in down_evidence["routes"] + stale_algod_evidence["routes"] if route["readinessStatus"] != "ready")


def test_route_readiness_waits_on_stale_indexer_and_mock_data(tmp_path):
    now = time.time()
    stale_indexer_store = MarketStore(tmp_path / "stale-indexer.db")
    stale_indexer_store.initialize()
    stale_indexer_store.record_opportunities(
        [
            _route_readiness_opportunity(
                "stale-indexer-route",
                captured_at=now - 1,
                expires_at=now + 30,
            )
        ]
    )
    _record_connector_health(stale_indexer_store, "tinyman")
    _record_connector_health(
        stale_indexer_store,
        "algod",
        connector_type="algod",
        metrics={"latestRound": 20_000, "expectedMinRound": 19_900},
    )
    _record_connector_health(
        stale_indexer_store,
        "indexer",
        connector_type="indexer",
        metrics={"latestRound": 19_800, "expectedMinRound": 19_900},
    )

    stale_indexer_evidence = stale_indexer_store.route_readiness_evidence(now=now, max_quote_age_seconds=5)
    stale_indexer_route = stale_indexer_evidence["routes"][0]

    assert stale_indexer_route["readinessStatus"] == "wait"
    assert stale_indexer_route["connectorReadinessStatus"] == "wait"
    assert stale_indexer_route["productionReady"] is False
    assert "indexer_round_stale" in stale_indexer_route["reasons"]

    mock_store = MarketStore(tmp_path / "mock.db")
    mock_store.initialize()
    mock_store.record_opportunities(
        [
            _route_readiness_opportunity(
                "mock-route",
                venue="mock",
                captured_at=now - 1,
                expires_at=now + 30,
            )
        ]
    )
    _record_connector_health(mock_store, "mock")

    mock_evidence = mock_store.route_readiness_evidence(now=now, max_quote_age_seconds=5)
    mock_route = mock_evidence["routes"][0]

    assert mock_route["readinessStatus"] == "wait"
    assert mock_route["connectorReadinessStatus"] == "wait"
    assert mock_route["productionReady"] is False
    assert "mock_connector_not_production_ready" in mock_route["reasons"]
    assert all(route["reasons"] for route in stale_indexer_evidence["routes"] + mock_evidence["routes"] if route["readinessStatus"] != "ready")


def test_route_readiness_evidence_excludes_execution_artifacts(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    now = time.time()
    store.record_opportunities(
        [
            _route_readiness_opportunity(
                "safe-evidence-route",
                captured_at=now - 1,
                expires_at=now + 30,
            )
        ]
    )
    _record_connector_health(store, "tinyman")

    evidence = store.route_readiness_evidence(now=now, max_quote_age_seconds=5)
    serialized = json.dumps(evidence).lower()

    forbidden_artifacts = (
        "mnemonic",
        "private_key",
        "seed_phrase",
        "hot_wallet",
        "signed_txn",
        "submission_payload",
        "execution_queue",
    )
    assert all(fragment not in serialized for fragment in forbidden_artifacts)
    assert evidence["liveExecutionTouched"] is False
    assert evidence["signerCodeTouched"] is False


def test_route_decision_forensics_explains_approved_rejected_and_paper_routes(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    now = time.time()
    approved = _route_readiness_opportunity(
        "approved-forensics-route",
        captured_at=now - 1,
        expires_at=now + 30,
    )
    rejected = _route_readiness_opportunity(
        "rejected-forensics-route",
        status="rejected",
        skip_reason="min_profit_not_met",
        captured_at=now - 1,
        expires_at=now + 30,
    )
    paper = _route_readiness_opportunity(
        "paper-forensics-route",
        captured_at=now - 1,
        expires_at=now + 30,
    )
    store.record_opportunities([approved, rejected, paper])
    store.record_paper_trade(paper, would_execute=True, notes="paper evidence only")
    _record_connector_health(store, "tinyman")

    records = store.list_route_decision_forensics(now=now, max_quote_age_seconds=5)
    by_hash = {record["routeHash"]: record for record in records}

    approved_record = by_hash["approved-forensics-route"]
    assert approved_record["finalDecision"] == "approved"
    assert approved_record["finalReasons"] == ["route_ready_for_paper_or_dry_run"]
    assert approved_record["riskDecision"]["approved"] is True
    assert approved_record["quoteFreshness"]["readinessStatus"] == "fresh"
    assert approved_record["connectorReadiness"]["status"] == "ok"
    assert approved_record["inputAmount"] == 5.0
    assert approved_record["expectedOutput"] == 5.4
    assert approved_record["grossProfit"] == 0.4
    assert approved_record["fees"]["network"] == 0.006
    assert approved_record["fees"]["dex"] == 0.015
    assert approved_record["safetyBuffer"] == 0.0
    assert approved_record["netExpectedProfit"] == 0.4
    assert approved_record["path"]
    assert approved_record["venues"] == ["tinyman"]

    rejected_record = by_hash["rejected-forensics-route"]
    assert rejected_record["finalDecision"] == "rejected"
    assert rejected_record["riskDecision"]["status"] == "rejected"
    assert "risk_rejected:min_profit_not_met" in rejected_record["finalReasons"]

    paper_record = by_hash["paper-forensics-route"]
    assert paper_record["finalDecision"] == "paper_only"
    assert "paper_evidence_available" in paper_record["finalReasons"]
    assert paper_record["paperDecision"]["available"] is True
    assert paper_record["paperDecision"]["status"] == "would_execute"
    assert paper_record["paperDecision"]["wouldExecute"] is True

    assert all(record["finalDecision"] for record in records)
    assert all(record["finalReasons"] for record in records)


def test_route_decision_forensics_explains_stale_down_and_wait_routes(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    now = time.time()
    stale = _route_readiness_opportunity(
        "stale-forensics-route",
        captured_at=now - 30,
        expires_at=now + 30,
    )
    down = _route_readiness_opportunity(
        "down-forensics-route",
        venue="pact",
        captured_at=now - 1,
        expires_at=now + 30,
    )
    wait = _route_readiness_opportunity(
        "wait-forensics-route",
        venue="mock",
        captured_at=now - 1,
        expires_at=now + 30,
    )
    store.record_opportunities([stale, down, wait])
    _record_connector_health(store, "tinyman")
    _record_connector_health(store, "pact", "error", detail="timeout")
    _record_connector_health(store, "mock")

    records = store.list_route_decision_forensics(now=now, max_quote_age_seconds=5)
    by_hash = {record["routeHash"]: record for record in records}

    stale_record = by_hash["stale-forensics-route"]
    assert stale_record["finalDecision"] == "rejected"
    assert stale_record["quoteFreshness"]["readinessStatus"] == "stale"
    assert "quote_stale" in stale_record["quoteFreshness"]["reasons"]
    assert "quote_stale" in stale_record["finalReasons"]

    down_record = by_hash["down-forensics-route"]
    assert down_record["finalDecision"] == "rejected"
    assert down_record["connectorReadiness"]["status"] == "blocked"
    assert any(reason.startswith("connector_down:pact") for reason in down_record["connectorReadiness"]["reasons"])
    assert any(reason.startswith("connector_down:pact") for reason in down_record["finalReasons"])

    wait_record = by_hash["wait-forensics-route"]
    assert wait_record["finalDecision"] == "wait"
    assert wait_record["connectorReadiness"]["status"] == "wait"
    assert "mock_connector_not_production_ready" in wait_record["finalReasons"]

    assert all(record["finalDecision"] for record in records)
    assert all(record["finalReasons"] for record in records)


def test_store_records_and_rechecks_paper_trade_candidates(tmp_path):
    database_path = tmp_path / "market.db"
    store = MarketStore(database_path)
    store.initialize()
    now = time.time()
    route = [
        {
            "venue": "tinyman",
            "pool_id": "tinyman:ALGO-USDC",
            "input_asset_id": 0,
            "output_asset_id": 31566704,
            "input_amount": 5.0,
            "expected_output": 1.0,
            "fee_amount": 0.015,
            "price_impact_bps": 30.0,
        },
        {
            "venue": "pact",
            "pool_id": "pact:ALGO-USDC",
            "input_asset_id": 31566704,
            "output_asset_id": 0,
            "input_amount": 1.0,
            "expected_output": 5.2,
            "fee_amount": 0.003,
            "price_impact_bps": 25.0,
        },
    ]
    opportunity = Opportunity(
        route_hash="paper-route",
        route=route,
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=5.2,
        gross_profit=0.2,
        estimated_network_fee=0.006,
        total_dex_fees=0.018,
        total_price_impact_bps=55.0,
        slippage_buffer=0.014,
        expected_net_profit=0.18,
        expected_profit_bps=360.0,
        max_price_impact_bps=30.0,
        involved_pool_ids=["tinyman:ALGO-USDC", "pact:ALGO-USDC"],
        involved_asset_ids=[0, 31566704],
        status="rejected",
        skip_reason="profit_bps_ok",
        confidence_score=70.0,
        created_at=now,
    )
    pools = [
        Pool(
            pool_id="tinyman:ALGO-USDC",
            venue_id="tinyman",
            app_id=1,
            asset_a_id=0,
            asset_b_id=31566704,
            reserve_a=100_000.0,
            reserve_b=20_000.0,
            fee_bps=30,
            block_round=100,
        ),
        Pool(
            pool_id="pact:ALGO-USDC",
            venue_id="pact",
            app_id=2,
            asset_a_id=0,
            asset_b_id=31566704,
            reserve_a=105_000.0,
            reserve_b=20_000.0,
            fee_bps=30,
            block_round=100,
        ),
    ]

    store.record_paper_trade(opportunity, would_execute=False, notes="skip: profit_bps_ok")
    result = store.update_due_paper_trades(pools, now=now + 31)

    with sqlite3.connect(database_path) as con:
        con.row_factory = sqlite3.Row
        row = con.execute("select * from paper_trades where route_hash = ?", (opportunity.route_hash,)).fetchone()

    assert result == {"checked_5s": 1, "checked_30s": 1, "checked_60s": 0, "errors": 0}
    assert row["would_execute"] == 0
    assert row["opportunity_status"] == "rejected"
    assert row["skip_reason"] == "profit_bps_ok"
    assert row["checked_5s_at"] == now + 31
    assert row["checked_30s_at"] == now + 31
    assert row["checked_60s_at"] is None
    assert row["simulated_final_amount_5s"] is not None
    assert row["simulated_final_amount_30s"] == row["simulated_final_amount_5s"]
    assert row["quote_decay_5s"] == row["expected_final_amount"] - row["simulated_final_amount_5s"]
    assert row["expected_vs_simulated_profit_5s"] == row["simulated_profit_5s"] - row["expected_net_profit"]
    assert row["quote_decay_30s"] == row["expected_final_amount"] - row["simulated_final_amount_30s"]
    assert row["expected_vs_simulated_profit_30s"] == row["simulated_profit_30s"] - row["expected_net_profit"]
    assert row["confidence_score"] == 70.0
    assert row["success"] in {0, 1}
    assert row["last_error"] is None

    evidence = store.paper_trading_evidence_summary(limit=5, lookback_seconds=86_400)
    sample = evidence["recentEvidence"][0]
    assert evidence["source"] == "stored"
    assert evidence["candidateCount"] == 1
    assert evidence["checked5sCount"] == 1
    assert evidence["checked30sCount"] == 1
    assert evidence["expectedNetAlgo"] == row["expected_net_profit"]
    assert evidence["simulatedNetAlgo5s"] == row["simulated_profit_5s"]
    assert evidence["simulatedNetAlgo30s"] == row["simulated_profit_30s"]
    assert evidence["averageQuoteDecay5s"] == row["quote_decay_5s"]
    assert evidence["averageQuoteDecay30s"] == row["quote_decay_30s"]
    assert sample["detectedAt"] == opportunity.created_at
    assert sample["routeHash"] == "paper-route"
    assert sample["inputAmount"] == 5.0
    assert sample["expectedOutput"] == 5.2
    assert sample["expectedProfit"] == 0.18
    assert sample["t5SimulatedOutput"] == row["simulated_final_amount_5s"]
    assert sample["t30SimulatedOutput"] == row["simulated_final_amount_30s"]
    assert sample["quoteDecay5s"] == row["quote_decay_5s"]
    assert sample["quoteDecay30s"] == row["quote_decay_30s"]
    assert sample["expectedVsSimulatedProfit30s"] == row["expected_vs_simulated_profit_30s"]
    assert sample["wouldExecute"] is False
    assert sample["skipOrFailureReason"] == "profit_bps_ok"
    assert sample["source"] == "stored"

    calibration = store.confidence_calibration_report()
    assert calibration["summary"]["resolvedCount"] == 1
    assert calibration["summary"]["paperTradeCount"] == 1
    assert any(bucket["label"] == "0.70-0.79" and bucket["count"] == 1 for bucket in calibration["buckets"])

    result_60 = store.update_due_paper_trades(pools, now=now + 61)
    with sqlite3.connect(database_path) as con:
        con.row_factory = sqlite3.Row
        row = con.execute("select * from paper_trades where route_hash = ?", (opportunity.route_hash,)).fetchone()
        decay = con.execute("select * from opportunity_decay where route_hash = ?", (opportunity.route_hash,)).fetchone()

    assert result_60 == {"checked_5s": 0, "checked_30s": 0, "checked_60s": 1, "errors": 0}
    assert row["checked_60s_at"] == now + 61
    assert row["simulated_profit_60s"] == row["simulated_profit_5s"]
    assert decay["detected_at"] == opportunity.created_at
    assert decay["expected_profit"] == opportunity.expected_net_profit
    assert decay["expected_profit_5s"] == row["simulated_profit_5s"]
    assert decay["expected_profit_30s"] == row["simulated_profit_30s"]
    assert decay["expected_profit_60s"] == row["simulated_profit_60s"]

    decay_report = store.opportunity_decay_dashboard(view="24h", now=now + 62)
    assert decay_report["source"] == "stored"
    assert decay_report["summary"]["opportunityCount"] == 1
    assert decay_report["summary"]["totalOpportunities"] == 1
    assert decay_report["summary"]["resolved60sCount"] == 1
    assert decay_report["summary"]["survivedT5Count"] in {0, 1}
    assert decay_report["summary"]["averageDecayT5"] == row["quote_decay_5s"]
    assert decay_report["summary"]["averageDecayT30"] == row["quote_decay_30s"]
    assert decay_report["summary"]["bestPairBySurvival"] is not None
    decay_sample = decay_report["records"][0]
    assert decay_sample["routeHash"] == opportunity.route_hash
    assert decay_sample["expectedProfitAtT0"] == opportunity.expected_net_profit
    assert decay_sample["simulatedProfitAtT5"] == row["simulated_profit_5s"]
    assert decay_sample["simulatedProfitAtT30"] == row["simulated_profit_30s"]
    assert decay_sample["simulatedProfitAtT60"] == row["simulated_profit_60s"]
    assert decay_sample["quoteDecayT5"] == row["quote_decay_5s"]
    assert decay_sample["quoteDecayT30"] == row["quote_decay_30s"]
    assert decay_sample["quoteDecayT60"] == row["quote_decay_60s"]
    assert decay_sample["survivedT30"] == (row["simulated_profit_30s"] > 0)
    assert decay_sample["finalOutcome"] in {"survived", "faded"}
    assert decay_sample["reason"]

    store.record_paper_trade(opportunity, would_execute=False, notes="new pending candidate")
    listed = store.list_paper_trades(limit=2)
    assert listed[0]["checked_30s_at"] == now + 31
    assert listed[1]["checked_30s_at"] is None


def test_store_builds_paper_daily_report(tmp_path):
    database_path = tmp_path / "market.db"
    store = MarketStore(database_path)
    store.initialize()
    now = time.time()
    route = [
        {
            "venue": "tinyman",
            "pool_id": "tinyman:ALGO-USDC",
            "input_asset_id": 0,
            "output_asset_id": 31566704,
            "input_amount": 5.0,
            "expected_output": 1.0,
        },
        {
            "venue": "pact",
            "pool_id": "pact:ALGO-USDC",
            "input_asset_id": 31566704,
            "output_asset_id": 0,
            "input_amount": 1.0,
            "expected_output": 5.2,
        },
    ]
    opportunity = Opportunity(
        route_hash="paper-report-route",
        route=route,
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=5.2,
        expected_net_profit=0.18,
        expected_profit_bps=360.0,
        max_price_impact_bps=30.0,
        involved_pool_ids=["tinyman:ALGO-USDC", "pact:ALGO-USDC"],
        involved_asset_ids=[0, 31566704],
        status="approved",
        created_at=now,
    )
    pools = [
        Pool(
            pool_id="tinyman:ALGO-USDC",
            venue_id="tinyman",
            app_id=1,
            asset_a_id=0,
            asset_b_id=31566704,
            reserve_a=100_000.0,
            reserve_b=20_000.0,
            fee_bps=30,
            block_round=100,
        ),
        Pool(
            pool_id="pact:ALGO-USDC",
            venue_id="pact",
            app_id=2,
            asset_a_id=0,
            asset_b_id=31566704,
            reserve_a=105_000.0,
            reserve_b=20_000.0,
            fee_bps=30,
            block_round=100,
        ),
    ]

    store.record_paper_trade(opportunity, would_execute=True, notes="would_execute")
    store.update_due_paper_trades(pools, now=now + 31)
    report = store.paper_daily_report()

    assert report["candidates"] == 1
    assert report["wouldExecute"] == 1
    assert report["skipped"] == 0
    assert report["checked5s"] == 1
    assert report["checked30s"] == 1
    assert report["completionRate30s"] == 1.0
    assert report["daysCollected"] == 1
    assert report["expectedNetProfit"] == 0.18
    assert report["simulatedProfit30s"] != 0
    assert report["bestRoute"]["route_hash"] == "paper-report-route"


def test_store_generates_and_lists_market_intelligence_reports(tmp_path):
    database_path = tmp_path / "market.db"
    store = MarketStore(database_path)
    store.initialize()
    now = time.time()
    report_date = time.strftime("%Y-%m-%d", time.gmtime(now))
    route = [
        {
            "venue": "tinyman",
            "pool_id": "tinyman:ALGO-USDC",
            "input_asset_id": 0,
            "output_asset_id": 31566704,
            "input_amount": 5.0,
            "expected_output": 1.0,
        },
        {
            "venue": "pact",
            "pool_id": "pact:ALGO-USDC",
            "input_asset_id": 31566704,
            "output_asset_id": 0,
            "input_amount": 1.0,
            "expected_output": 5.2,
        },
    ]
    opportunity = Opportunity(
        route_hash="market-report-route",
        route=route,
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=5.2,
        expected_net_profit=0.18,
        expected_profit_bps=360.0,
        max_price_impact_bps=30.0,
        involved_pool_ids=["tinyman:ALGO-USDC", "pact:ALGO-USDC"],
        involved_asset_ids=[0, 31566704],
        status="rejected",
        skip_reason="profit_bps_ok",
        created_at=now,
    )
    pools = [
        Pool(
            pool_id="tinyman:ALGO-USDC",
            venue_id="tinyman",
            app_id=1,
            asset_a_id=0,
            asset_b_id=31566704,
            reserve_a=100_000.0,
            reserve_b=20_000.0,
            fee_bps=30,
            block_round=100,
            captured_at=now - 10,
        ),
        Pool(
            pool_id="tinyman:ALGO-USDC",
            venue_id="tinyman",
            app_id=1,
            asset_a_id=0,
            asset_b_id=31566704,
            reserve_a=110_000.0,
            reserve_b=21_000.0,
            fee_bps=30,
            block_round=101,
            captured_at=now,
        ),
    ]
    store.upsert_assets([Asset(0, "ALGO", "Algorand", 6), Asset(31566704, "USDC", "USD Coin", 6)])
    store.record_pool_snapshots(pools)
    store.record_opportunities([opportunity])
    store.record_paper_trade(opportunity, would_execute=False, notes="daily report")
    store.record_service_health("market_scanner", "ok", detail="daily report test", metrics={"opportunities": 1})

    report = store.generate_market_intelligence_report(report_date=report_date, now=now + 1)
    archive = store.list_market_intelligence_reports()
    loaded = store.get_market_intelligence_report(report_date=report_date)

    assert report["reportDate"] == report_date
    assert report["source"] == "stored"
    assert report["marketSummary"]["opportunityCount"] == 1
    assert report["topPairs"][0]["pairLabel"] == "ALGO/USDC"
    assert "## Risk Events" in report["markdown"]
    assert archive[0]["reportDate"] == report_date
    assert archive[0]["summary"]["opportunityCount"] == 1
    assert loaded is not None
    assert loaded["markdown"].startswith("# AlgoPulse Market Intelligence Report")


def test_store_records_payment_verification_receipts(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    result = {
        "ok": True,
        "status": "verified",
        "reason": None,
        "txid": "TXID",
        "asset_id": 0,
        "expected": {
            "receiver": "RECEIVER",
            "amount_raw": 5_000_000,
        },
        "observed": {
            "sender": "SENDER",
            "receiver": "RECEIVER",
            "amount_raw": 5_000_000,
            "confirmed_round": 123,
            "confirmations": 3,
        },
        "checks": {"amount": True},
    }

    store.record_payment_verification(result)

    receipts = store.list_payment_verifications()
    assert len(receipts) == 1
    assert receipts[0]["ok"] is True
    assert receipts[0]["txid"] == "TXID"
    assert receipts[0]["expected_amount_raw"] == 5_000_000
    assert receipts[0]["result"]["checks"] == {"amount": True}


def test_store_records_and_updates_refund_cases(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    decision = {
        "payment_verification_id": 1,
        "source_txid": "PAYTXID",
        "status": "refund_ready",
        "failure_type": "service_failure",
        "reason": "service did not complete",
        "refund_address": "SENDER",
        "asset_id": 0,
        "asset_decimals": 6,
        "amount_raw": 5_000_000,
        "amount_display": 5.0,
        "operator_action": "manual_refund_ready",
        "operator_note": "operator checked failure",
        "guardrails": ["manual refund only; no automatic send"],
    }

    created = store.record_refund_case(decision)
    updated = store.update_refund_case_status(
        created["id"],
        status="resolved",
        resolution_txid="REFUNDTXID",
        resolution_note="manual refund sent",
    )
    cases = store.list_refund_cases()

    assert created["status"] == "refund_ready"
    assert created["guardrails"] == ["manual refund only; no automatic send"]
    assert created["decision"]["source_txid"] == "PAYTXID"
    assert updated is not None
    assert updated["status"] == "resolved"
    assert updated["resolution_txid"] == "REFUNDTXID"
    assert updated["resolved_at"] is not None
    assert cases[0]["id"] == created["id"]
