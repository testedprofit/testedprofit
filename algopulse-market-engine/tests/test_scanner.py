from dataclasses import replace
import json
from pathlib import Path
import sqlite3
import time

from algopulse.config import STANDARD_QUOTE_SIZES, Settings
from algopulse.models import Asset, Opportunity, Pool, Venue
from algopulse.risk import RiskEngine, RiskPolicy
from algopulse.scanner import MarketScanner, _merge_asset_pairs
from algopulse.store import MarketStore


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        env="test",
        data_dir=tmp_path,
        database_path=tmp_path / "market.db",
        connector_mode="mock",
        scanner_interval_seconds=15,
        public_delay_seconds=0,
        network="mainnet",
        asset_pairs=((0, 31566704),),
        slippage_bps=50,
        enable_live_execution=False,
        execute_approved=False,
        allow_api_execution=False,
        allow_non_algo_starting_routes=False,
        allow_non_algo_live_submission=False,
        unsigned_executor_only=True,
        signer_enabled=False,
        signer_kill_switch=True,
        signer_allowed_route_hashes=(),
        signer_audit_log_path=tmp_path / "signer-audit.jsonl",
        signer_min_wallet_reserve_algos=0.2,
        tiny_live_mode=False,
        tiny_live_allow_automation=False,
        tiny_live_manual_route_hash="",
        tiny_live_lora_txid="",
        tiny_live_reconciliation_confirmed=False,
        tiny_live_min_wallet_algos=100.0,
        tiny_live_max_wallet_algos=250.0,
        trader_mnemonic="",
        trader_address="",
        max_live_trade_size=25.0,
        trade_sizes=STANDARD_QUOTE_SIZES,
        max_route_age_seconds=5.0,
        max_route_legs=3,
        own_funds_only=True,
        allowed_asset_ids=(),
        allowed_app_ids=(),
        require_app_id_allowlist=False,
        min_fee_buffer_multiplier=2.0,
        min_net_profit_algos=0.25,
        min_net_profit_input_units=0.25,
        min_profit_bps=35.0,
        max_price_impact_bps=50.0,
        min_pool_reserve=1_000.0,
        estimated_network_fee_algos=0.006,
        safety_buffer_bps=15.0,
        max_daily_loss=20.0,
        max_daily_trades=20,
        max_concurrent_execution=1,
        max_group_fee_algos=0.05,
        algod_url="https://mainnet-api.algonode.cloud",
        indexer_url="https://mainnet-idx.algonode.cloud",
        algod_token="",
        indexer_token="",
        vestige_api_url="https://api.vestigelabs.org",
        use_vestige_discovery=False,
        target_asset_id=3169177585,
        vestige_pinned_pair_asset_ids=(),
        vestige_include_fallback_pairs=True,
        vestige_top_pool_count=8,
        vestige_min_target_reserve=500_000.0,
        vestige_protocol_ids=(2, 3),
    )


class DeterministicMarketConnector:
    name = "deterministic"

    def list_assets(self) -> list[Asset]:
        return [
            Asset(asset_id=0, symbol="ALGO", name="Algorand", decimals=6, is_verified=True, is_allowlisted=True),
            Asset(asset_id=31566704, symbol="USDC", name="USDC", decimals=6, is_verified=True, is_allowlisted=True),
        ]

    def list_venues(self) -> list[Venue]:
        return [
            Venue(venue_id="tinyman", name="Tinyman", kind="amm"),
            Venue(venue_id="pact", name="Pact", kind="amm"),
        ]

    def list_pools(self) -> list[Pool]:
        captured_at = time.time()
        return [
            Pool(
                pool_id="tinyman:ALGO-USDC",
                venue_id="tinyman",
                app_id=1001001,
                asset_a_id=0,
                asset_b_id=31566704,
                reserve_a=1_000_000.0,
                reserve_b=300_000.0,
                fee_bps=30,
                block_round=100,
                captured_at=captured_at,
            ),
            Pool(
                pool_id="pact:ALGO-USDC",
                venue_id="pact",
                app_id=2001001,
                asset_a_id=0,
                asset_b_id=31566704,
                reserve_a=1_000_000.0,
                reserve_b=200_000.0,
                fee_bps=30,
                block_round=100,
                captured_at=captured_at,
            ),
        ]


class FailingMarketConnector:
    name = "failing"

    def list_assets(self) -> list[Asset]:
        return []

    def list_venues(self) -> list[Venue]:
        return [Venue(venue_id="failing", name="Failing", kind="amm")]

    def list_pools(self) -> list[Pool]:
        raise TimeoutError("deterministic connector timeout")


class DegradedMarketConnector(FailingMarketConnector):
    name = "degraded"

    def list_pools(self) -> list[Pool]:
        return []

    def health_evidence(self) -> dict:
        return {
            "status": "degraded",
            "detail": "partial_pair_failure",
            "metrics": {"connector": self.name, "failedPairCount": 1},
        }


def _assessed_negative_opportunity(
    *,
    pool: Pool,
    output_asset_id: int,
    captured_at: float,
    expires_at: float,
    policy: RiskPolicy,
) -> Opportunity:
    route = [
        {
            "route_kind": "deterministic_negative_case",
            "venue": pool.venue_id,
            "pool_id": pool.pool_id,
            "input_asset_id": 0,
            "output_asset_id": output_asset_id,
            "input_amount": 5.0,
            "expected_output": 6.0,
            "fee_amount": 0.015,
            "price_impact_bps": 10.0,
            "block_round": pool.block_round,
            "captured_at": captured_at,
            "expires_at": expires_at,
        }
    ]
    opportunity = Opportunity.from_route(
        route=route,
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=6.0,
        expected_net_profit=0.5,
        expected_profit_bps=1000.0,
        max_price_impact_bps=10.0,
        involved_pool_ids=[pool.pool_id],
        involved_asset_ids=[0, output_asset_id],
        estimated_network_fee=0.006,
        total_dex_fees=0.015,
    )
    decision = RiskEngine(policy).assess(opportunity, [pool])
    opportunity.status = "approved" if decision.approved else "rejected"
    opportunity.skip_reason = None if decision.approved else decision.reason
    opportunity.risk_rules = decision.rules
    return opportunity


def test_read_only_scanner_runs_without_keys_and_without_live_executor(tmp_path):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    scanner = MarketScanner(settings=settings, store=store)

    assert scanner._live_executor is None

    result = scanner.run_once()

    assert result["pools"] > 0
    assert result["connectors"] == ["mock"]
    assert scanner._live_executor is None
    with sqlite3.connect(settings.database_path) as con:
        pool_count = con.execute("select count(*) from pool_snapshots").fetchone()[0]
        opportunity_count = con.execute("select count(*) from opportunities").fetchone()[0]
        paper_count = con.execute("select count(*) from paper_trades").fetchone()[0]
        health_count = con.execute("select count(*) from service_health where service_name = 'market_scanner'").fetchone()[0]

    assert pool_count > 0
    assert opportunity_count == result["opportunities"]
    assert paper_count == result["opportunities"]
    assert result["paper_candidates"] == result["opportunities"]
    assert health_count == 1


def test_scanner_records_partial_connector_failure_as_degraded_evidence(tmp_path):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    scanner = MarketScanner(settings=settings, store=store)
    scanner.connectors = [DeterministicMarketConnector(), FailingMarketConnector(), DegradedMarketConnector()]

    result = scanner.run_once()
    reliability = store.connector_reliability_evidence()
    by_name = {item["connectorName"]: item for item in reliability["connectors"]}

    assert result["status"] == "degraded"
    assert result["connector_error_count"] == 1
    assert result["connector_degraded_count"] == 1
    assert {item["connectorName"] for item in result["connector_health"]} == {
        "deterministic",
        "failing",
        "degraded",
    }
    assert by_name["deterministic"]["status"] == "ok"
    assert by_name["failing"]["status"] == "down"
    assert by_name["failing"]["degradationReason"] == "connector_call_failed"
    assert by_name["degraded"]["status"] == "degraded"
    assert by_name["degraded"]["readinessImpact"] == "wait"
    assert by_name["degraded"]["degradationReason"] == "partial_pair_failure"
    assert "market_scanner" not in by_name
    assert scanner._live_executor is None


def test_deterministic_scanner_quote_route_risk_paper_flow_produces_evidence(tmp_path):
    settings = replace(
        _settings(tmp_path),
        trade_sizes=(5.0,),
        min_net_profit_algos=0.01,
        min_net_profit_input_units=0.01,
    )
    store = MarketStore(settings.database_path)
    scanner = MarketScanner(settings=settings, store=store)
    connector = DeterministicMarketConnector()
    scanner.connectors = [connector]
    scanner.route_engine.trade_sizes = [5.0]

    result = scanner.run_once()

    assert result["connectors"] == ["deterministic"]
    assert result["pools"] == 2
    assert result["opportunities"] > 0
    assert result["approved"] > 0
    assert result["paper_candidates"] == result["opportunities"]
    assert scanner._live_executor is None

    with sqlite3.connect(settings.database_path) as con:
        con.row_factory = sqlite3.Row
        pool_count = con.execute("select count(*) from pool_snapshots").fetchone()[0]
        quote_count = con.execute("select count(*) from quotes").fetchone()[0]
        opportunity_count = con.execute("select count(*) from opportunities").fetchone()[0]
        risk_count = con.execute("select count(*) from risk_decisions").fetchone()[0]
        paper_count = con.execute("select count(*) from paper_trades").fetchone()[0]
        forensics_count = con.execute("select count(*) from route_forensics").fetchone()[0]
        approved_risk_count = con.execute("select count(*) from risk_decisions where approved = 1").fetchone()[0]
        due_at = con.execute("select max(check_30s_due_at) from paper_trades").fetchone()[0]

    assert pool_count == 2
    assert opportunity_count == result["opportunities"]
    assert quote_count >= opportunity_count * 2
    assert risk_count == opportunity_count
    assert approved_risk_count == result["approved"]
    assert paper_count == opportunity_count
    assert forensics_count == opportunity_count

    paper_updates = store.update_due_paper_trades(connector.list_pools(), now=due_at)
    evidence = store.paper_trading_evidence_summary(limit=5, lookback_seconds=86_400)
    pipeline = store.scanner_to_paper_pipeline_evidence(limit=5, lookback_seconds=86_400)
    executable_sample = next(item for item in evidence["recentEvidence"] if item["wouldExecute"])

    assert paper_updates["checked_5s"] == paper_count
    assert paper_updates["checked_30s"] == paper_count
    assert paper_updates["errors"] == 0
    assert evidence["source"] == "stored"
    assert evidence["candidateCount"] == paper_count
    assert evidence["checked5sCount"] == paper_count
    assert evidence["checked30sCount"] == paper_count
    assert evidence["survived30sCount"] > 0
    assert evidence["survivalRate30s"] > 0
    assert evidence["expectedNetAlgo"] > 0
    assert evidence["simulatedNetAlgo30s"] > 0
    assert executable_sample["detectedAt"] > 0
    assert executable_sample["routeHash"]
    assert executable_sample["inputAmount"] == 5.0
    assert executable_sample["expectedOutput"] > 5.0
    assert executable_sample["expectedProfit"] > 0
    assert executable_sample["t5SimulatedOutput"] is not None
    assert executable_sample["t30SimulatedOutput"] is not None
    assert executable_sample["quoteDecay30s"] == executable_sample["expectedOutput"] - executable_sample["t30SimulatedOutput"]
    assert executable_sample["wouldExecute"] is True
    assert executable_sample["skipOrFailureReason"] == "would_execute"
    assert executable_sample["source"] == "stored"
    assert scanner._live_executor is None
    assert pipeline["source"] == "stored"
    assert pipeline["scanner"]["hasEvidence"] is True
    assert pipeline["scanner"]["poolSnapshotCount"] == 2
    assert pipeline["scanner"]["poolCount"] == 2
    assert pipeline["scanner"]["venues"] == ["pact", "tinyman"]
    assert pipeline["quotes"]["hasComparableQuotes"] is True
    assert pipeline["quotes"]["hasFreshQuotes"] is True
    assert pipeline["quotes"]["quoteCount"] == quote_count
    assert pipeline["quoteFreshness"]["source"] == "stored"
    assert pipeline["quoteFreshness"]["quoteCount"] == quote_count
    assert pipeline["quoteFreshness"]["freshCount"] == quote_count
    assert pipeline["quoteFreshness"]["staleCount"] == 0
    assert pipeline["quoteFreshness"]["readinessEligibleQuoteCount"] == quote_count
    assert pipeline["quoteFreshness"]["readinessExcludedQuoteCount"] == 0
    assert pipeline["quoteFreshness"]["freshnessStatus"] == "ok"
    assert pipeline["quoteFreshness"]["blocksReadiness"] is False
    assert {item["venueId"] for item in pipeline["quoteFreshness"]["venues"]} == {"pact", "tinyman"}
    assert all(item["status"] == "ok" for item in pipeline["quoteFreshness"]["venues"])
    assert pipeline["connectorReliability"]["source"] == "stored"
    assert pipeline["connectorReliability"]["healthyConnectorCount"] == 1
    connector_health = pipeline["connectorReliability"]["connectors"][0]
    assert connector_health["connector"] == "deterministic"
    assert connector_health["status"] == "ok"
    assert connector_health["scanCount"] == 1
    assert connector_health["successCount"] == 1
    assert connector_health["errorCount"] == 0
    comparable_algo_usdc = next(
        group
        for group in pipeline["quotes"]["comparableGroups"]
        if group["inputAssetId"] == 0 and group["outputAssetId"] == 31566704 and group["inputAmount"] == 5.0
    )
    assert comparable_algo_usdc["venues"] == ["pact", "tinyman"]
    assert comparable_algo_usdc["quoteCount"] >= 2
    assert comparable_algo_usdc["maxOutputAmount"] > comparable_algo_usdc["minOutputAmount"]
    assert pipeline["routes"]["hasCandidates"] is True
    assert pipeline["routes"]["candidateCount"] == opportunity_count
    assert pipeline["routes"]["routesLinkedToQuotes"] == opportunity_count
    assert pipeline["routes"]["rejectedWithReasonCount"] > 0
    assert all(item["reason"] != "unknown" for item in pipeline["routes"]["rejections"])
    assert pipeline["risk"]["hasDecisions"] is True
    assert pipeline["risk"]["decisionCount"] == risk_count
    assert pipeline["risk"]["approvedCount"] == approved_risk_count
    assert pipeline["routeReadiness"]["source"] == "stored"
    assert pipeline["routeReadiness"]["readyCount"] > 0
    assert pipeline["routeReadiness"]["blockedCount"] > 0
    assert all(
        route["reasons"]
        for route in pipeline["routeReadiness"]["routes"]
        if route["readinessStatus"] != "ready"
    )
    assert pipeline["paper"]["candidateCount"] == paper_count
    assert pipeline["paper"]["checked5sCount"] == paper_count
    assert pipeline["paper"]["checked30sCount"] == paper_count
    assert any(item["wouldExecute"] for item in pipeline["paper"]["recentEvidence"])
    assert pipeline["proof"] == {
        "scannerToQuotes": True,
        "quoteFreshness": True,
        "connectorReliability": True,
        "routeReadiness": True,
        "quotesToRoutes": True,
        "routesToRisk": True,
        "riskToPaper": True,
        "paperRechecks": True,
        "endToEnd": True,
    }
    assert pipeline["liveExecutionTouched"] is False
    assert pipeline["signerCodeTouched"] is False
    serialized_pipeline = json.dumps(pipeline).lower()
    forbidden_artifacts = (
        "mnemonic",
        "private_key",
        "hot_wallet",
        "signed_txn",
        "signed_transaction",
        "submission_payload",
        "submitted_txid",
        "execution_queue",
        "raw_route_json",
        "route_json",
    )
    assert all(fragment not in serialized_pipeline for fragment in forbidden_artifacts)


def test_pipeline_evidence_includes_stale_and_unknown_asset_rejection_reasons(tmp_path):
    settings = replace(
        _settings(tmp_path),
        trade_sizes=(5.0,),
        min_net_profit_algos=0.01,
        min_net_profit_input_units=0.01,
    )
    store = MarketStore(settings.database_path)
    scanner = MarketScanner(settings=settings, store=store)
    connector = DeterministicMarketConnector()
    scanner.connectors = [connector]
    scanner.route_engine.trade_sizes = [5.0]

    scanner.run_once()
    with sqlite3.connect(settings.database_path) as con:
        due_at = con.execute("select max(check_30s_due_at) from paper_trades").fetchone()[0]
    store.update_due_paper_trades(connector.list_pools(), now=due_at)

    now = time.time()
    stale_at = now - 60
    stale_pool = Pool(
        pool_id="negative:stale-quote",
        venue_id="tinyman",
        app_id=3001001,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=100_000.0,
        reserve_b=30_000.0,
        fee_bps=30,
        block_round=50,
        captured_at=stale_at,
    )
    unknown_asset_pool = Pool(
        pool_id="negative:unknown-asset",
        venue_id="pact",
        app_id=3001002,
        asset_a_id=0,
        asset_b_id=999999999,
        reserve_a=100_000.0,
        reserve_b=30_000.0,
        fee_bps=30,
        block_round=51,
        captured_at=now,
    )
    policy = RiskPolicy(
        min_profit_absolute=0.01,
        min_profit_bps=1.0,
        max_route_age_seconds=5.0,
        min_pool_reserve=1.0,
        min_fee_buffer_multiplier=0.0,
        allowed_asset_ids=(0, 31566704),
    )
    stale_opportunity = _assessed_negative_opportunity(
        pool=stale_pool,
        output_asset_id=31566704,
        captured_at=stale_at,
        expires_at=stale_at + 5,
        policy=policy,
    )
    unknown_asset_opportunity = _assessed_negative_opportunity(
        pool=unknown_asset_pool,
        output_asset_id=999999999,
        captured_at=now,
        expires_at=now + 5,
        policy=policy,
    )

    store.record_pool_snapshots([stale_pool, unknown_asset_pool])
    store.record_opportunities([stale_opportunity, unknown_asset_opportunity])

    pipeline = store.scanner_to_paper_pipeline_evidence(limit=10, lookback_seconds=86_400)
    rejection_reasons = {item["reason"] for item in pipeline["routes"]["rejections"]}
    stale_samples = pipeline["quoteFreshness"]["staleSamples"]

    assert stale_opportunity.status == "rejected"
    assert stale_opportunity.skip_reason == "quote_freshness_ok"
    assert unknown_asset_opportunity.status == "rejected"
    assert unknown_asset_opportunity.skip_reason == "assets_allowlisted"
    assert {"quote_freshness_ok", "assets_allowlisted"}.issubset(rejection_reasons)
    assert pipeline["routes"]["rejectedWithReasonCount"] >= 2
    assert pipeline["routes"]["hasRejectedReasons"] is True
    assert pipeline["risk"]["rejectedCount"] >= 2
    assert pipeline["quoteFreshness"]["freshCount"] > 0
    assert pipeline["quoteFreshness"]["staleCount"] > 0
    assert pipeline["quoteFreshness"]["readinessExcludedQuoteCount"] == pipeline["quoteFreshness"]["staleCount"]
    assert pipeline["quoteFreshness"]["freshnessStatus"] == "degraded"
    assert any(item["reason"] == "quote_expired" for item in stale_samples)
    assert all(item["reason"] != "quote_freshness_ok" for item in stale_samples)
    assert any(item["poolId"] == "negative:stale-quote" for item in stale_samples)
    assert pipeline["connectorReliability"]["healthyConnectorCount"] == 1
    assert pipeline["proof"]["quotesToRoutes"] is True
    assert pipeline["proof"]["routesToRisk"] is True


def test_scanner_asset_pair_merge_preserves_routing_anchors():
    pairs = _merge_asset_pairs(
        (
            (3169177585, 31566704),
            (0, 3169177585),
            (31566704, 0),
            (0, 31566704),
        )
    )

    assert pairs == (
        (31566704, 3169177585),
        (0, 3169177585),
        (0, 31566704),
    )


def test_scanner_rejects_concurrent_execution(tmp_path):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    scanner = MarketScanner(settings=settings, store=store)
    scanner._execution_slots.acquire()
    try:
        result = scanner.execute_best_once()
    finally:
        scanner._execution_slots.release()

    assert result["executed"] is False
    assert result["reason"] == "max concurrent execution reached"
    assert scanner._live_executor is None


def test_scanner_rejects_execution_after_daily_trade_limit(tmp_path, monkeypatch):
    settings = replace(_settings(tmp_path), max_daily_trades=1)
    store = MarketStore(settings.database_path)
    scanner = MarketScanner(settings=settings, store=store)
    monkeypatch.setattr(scanner, "run_once", lambda: {"opportunities": 1})
    monkeypatch.setattr(store, "get_best_approved_opportunity", lambda **_kwargs: {"route_hash": "route"})
    monkeypatch.setattr(store, "get_submitted_live_profit_24h", lambda: 0.0)
    monkeypatch.setattr(store, "get_submitted_live_trade_count_24h", lambda: 1)

    result = scanner.execute_best_once()

    assert result["executed"] is False
    assert result["reason"] == "daily trade limit reached"
    assert result["daily_submitted_trades_24h"] == 1
    assert scanner._live_executor is None
