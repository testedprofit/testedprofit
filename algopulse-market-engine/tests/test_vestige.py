from pathlib import Path
from dataclasses import replace

from algopulse.config import STANDARD_QUOTE_SIZES, Settings
from algopulse.vestige import VestigeDiscovery


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        env="test",
        data_dir=tmp_path,
        database_path=tmp_path / "market.db",
        connector_mode="tinyman,pact",
        scanner_interval_seconds=15,
        public_delay_seconds=0,
        network="mainnet",
        asset_pairs=((0, 3169177585),),
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
        use_vestige_discovery=True,
        target_asset_id=3169177585,
        vestige_pinned_pair_asset_ids=(),
        vestige_include_fallback_pairs=True,
        vestige_top_pool_count=4,
        vestige_min_target_reserve=500_000.0,
        vestige_protocol_ids=(2, 3),
    )


def test_vestige_composition_discovers_large_target_pairs(tmp_path):
    discovery = VestigeDiscovery(_settings(tmp_path))
    composition = {
        "2": {
            "0": 3_300_000,
            "31566704": 400_000,
            "111": 2_000_000,
        },
        "3": {
            "31566704": 1_200_000,
            "222": 250_000,
        },
    }

    pairs = discovery._pairs_from_composition(composition)

    assert [pair.other_asset_id for pair in pairs] == [0, 31566704, 111]
    assert pairs[1].target_reserve == 1_600_000
    assert pairs[1].protocol_ids == [2, 3]


def test_vestige_pinned_pairs_preserve_requested_order_and_ignore_reserve_floor(tmp_path):
    settings = replace(
        _settings(tmp_path),
        vestige_pinned_pair_asset_ids=(222, 0, 111),
        vestige_include_fallback_pairs=False,
        vestige_min_target_reserve=500_000.0,
    )
    discovery = VestigeDiscovery(settings)
    composition = {
        "2": {
            "0": 3_300_000,
            "111": 2_000_000,
        },
        "3": {
            "222": 250_000,
            "111": 200_000,
        },
    }

    pairs = discovery._pairs_from_composition(composition)

    assert [pair.other_asset_id for pair in pairs] == [222, 0, 111]
    assert pairs[0].target_reserve == 250_000
    assert pairs[0].protocol_ids == [3]
