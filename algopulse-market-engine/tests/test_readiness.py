from dataclasses import replace
from pathlib import Path
import time

from algopulse.config import STANDARD_QUOTE_SIZES, Settings
from algopulse.connectors.mock import MockMarketConnector
from algopulse.models import Opportunity
from algopulse.readiness import build_live_readiness_report
from algopulse.store import MarketStore


def _settings(tmp_path: Path, connector_mode: str) -> Settings:
    return Settings(
        env="test",
        data_dir=tmp_path,
        database_path=tmp_path / "market.db",
        connector_mode=connector_mode,
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


def _seed_mock_market(store: MarketStore) -> None:
    connector = MockMarketConnector()
    store.upsert_assets(connector.list_assets())
    store.upsert_venues(connector.list_venues())
    store.record_pool_snapshots(connector.list_pools())


def test_readiness_marks_mock_only_as_not_live_ready(tmp_path):
    settings = _settings(tmp_path, "mock")
    store = MarketStore(settings.database_path)
    store.initialize()
    _seed_mock_market(store)

    report = build_live_readiness_report(
        settings=settings,
        store=store,
        check_wallet=False,
        build_execution_plan=False,
    )

    live_check = next(check for check in report["checks"] if check["name"] == "live_connectors_configured")
    assert report["mode"] == "live-market-readiness"
    assert report["verdict"] == "not_live_ready"
    assert not live_check["ok"]
    assert report["risk"]["volume_only_trading_allowed"] is False


def test_readiness_reports_live_market_scanner_ready_but_wallet_needed(tmp_path):
    settings = _settings(tmp_path, "tinyman,pact")
    store = MarketStore(settings.database_path)
    store.initialize()
    _seed_mock_market(store)

    report = build_live_readiness_report(
        settings=settings,
        store=store,
        check_wallet=False,
        build_execution_plan=False,
    )

    assert report["connectors"]["live"] == ["pact", "tinyman"]
    assert report["verdict"] == "watch_ready_wallet_needed"
    assert report["readiness_score"] >= 50
    assert report["risk"]["max_tx_group_size"] == 16
    assert report["execution_flags"]["unsigned_executor_only"] is True
    assert report["signer"]["enabled"] is False
    assert report["signer"]["kill_switch"] is True
    assert report["signer"]["main_executor_can_sign"] is False
    assert report["tiny_live"]["enabled"] is False
    assert any(check["name"] == "profit_guard_configured" and check["ok"] for check in report["checks"])
    assert any(check["name"] == "unsigned_executor_only" and check["ok"] for check in report["checks"])
    assert any(check["name"] == "isolated_signer_boundary" and check["ok"] for check in report["checks"])


def test_readiness_blocks_live_ready_status_without_reviewed_app_ids(tmp_path):
    settings = replace(_settings(tmp_path, "tinyman,pact"), require_app_id_allowlist=True, allowed_app_ids=())
    store = MarketStore(settings.database_path)
    store.initialize()
    _seed_mock_market(store)

    report = build_live_readiness_report(
        settings=settings,
        store=store,
        check_wallet=False,
        build_execution_plan=False,
    )

    app_check = next(check for check in report["checks"] if check["name"] == "app_id_allowlist")
    assert report["verdict"] == "not_live_ready"
    assert app_check["ok"] is False


def test_readiness_does_not_surface_stale_approved_routes(tmp_path):
    settings = _settings(tmp_path, "tinyman,pact")
    store = MarketStore(settings.database_path)
    store.initialize()
    _seed_mock_market(store)
    store.record_opportunities(
        [
            Opportunity(
                route_hash="old-route",
                route=[
                    {
                        "venue": "pact",
                        "pool_id": "pact:ALGO-USDC",
                        "input_asset_id": 0,
                        "output_asset_id": 31566704,
                        "input_amount": 5.0,
                        "expected_output": 1.0,
                    },
                    {
                        "venue": "tinyman",
                        "pool_id": "tinyman:ALGO-USDC",
                        "input_asset_id": 31566704,
                        "output_asset_id": 0,
                        "input_amount": 1.0,
                        "expected_output": 5.5,
                    },
                ],
                input_asset_id=0,
                input_amount=5.0,
                expected_final_amount=5.5,
                expected_net_profit=0.49,
                expected_profit_bps=980.0,
                max_price_impact_bps=10.0,
                involved_pool_ids=["pact:ALGO-USDC", "tinyman:ALGO-USDC"],
                involved_asset_ids=[0, 31566704],
                status="approved",
                risk_rules={"net_profit_after_fees_ok": True},
                created_at=time.time() - 3_600,
            )
        ]
    )

    report = build_live_readiness_report(
        settings=settings,
        store=store,
        check_wallet=False,
        build_execution_plan=False,
    )

    assert report["best_approved_route"] is None
    assert next(check for check in report["checks"] if check["name"] == "profitable_route_available")["ok"] is False


def test_tiny_live_mode_blocks_non_tiny_scope_and_limits(tmp_path):
    settings = replace(
        _settings(tmp_path, "tinyman,pact"),
        tiny_live_mode=True,
        asset_pairs=((0, 31566704), (0, 3169177585)),
        allowed_asset_ids=(0, 31566704, 3169177585),
        max_live_trade_size=25.0,
    )
    store = MarketStore(settings.database_path)
    store.initialize()
    _seed_mock_market(store)

    report = build_live_readiness_report(
        settings=settings,
        store=store,
        check_wallet=False,
        build_execution_plan=False,
    )

    assert report["tiny_live"]["enabled"] is True
    assert report["tiny_live"]["scope_ok"] is False
    assert report["tiny_live"]["limits_ok"] is False
    assert next(check for check in report["checks"] if check["name"] == "tiny_live_scope")["ok"] is False
    assert next(check for check in report["checks"] if check["name"] == "tiny_live_limits")["ok"] is False


def test_tiny_live_mode_reports_manual_lora_and_reconciliation_gates(tmp_path):
    settings = replace(
        _settings(tmp_path, "tinyman,pact"),
        tiny_live_mode=True,
        max_live_trade_size=10.0,
        tiny_live_allow_automation=True,
        tiny_live_manual_route_hash="reviewed-route",
        tiny_live_lora_txid="TXID",
        tiny_live_reconciliation_confirmed=True,
    )
    store = MarketStore(settings.database_path)
    store.initialize()
    _seed_mock_market(store)

    report = build_live_readiness_report(
        settings=settings,
        store=store,
        check_wallet=False,
        build_execution_plan=False,
    )

    assert report["tiny_live"]["scope_ok"] is True
    assert report["tiny_live"]["limits_ok"] is True
    assert report["tiny_live"]["post_first_trade_proof_ok"] is True
    assert report["tiny_live"]["manual_first_route_ok"] is False
    assert report["tiny_live"]["automation_gate_ok"] is False
