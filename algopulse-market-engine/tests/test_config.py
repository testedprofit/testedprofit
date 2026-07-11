from pathlib import Path

import pytest

from algopulse.config import get_settings


def test_get_settings_accepts_operator_env_aliases(tmp_path, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ALGO_PULSE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("ALGORAND_NETWORK", "testnet")
    monkeypatch.setenv("ALGOD_URL", "https://algod.example")
    monkeypatch.setenv("ALGOD_TOKEN", "algod-token")
    monkeypatch.setenv("INDEXER_URL", "https://indexer.example")
    monkeypatch.setenv("INDEXER_TOKEN", "indexer-token")
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/algopulse")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("ENABLE_SCANNER", "true")
    monkeypatch.setenv("ENABLE_EXECUTION", "false")
    monkeypatch.setenv("ENABLE_SIGNER", "false")
    monkeypatch.setenv("KILL_SWITCH", "true")
    monkeypatch.setenv("MAX_TRADE_ALGO", "10")
    monkeypatch.setenv("MAX_DAILY_LOSS_ALGO", "20")
    monkeypatch.setenv("MAX_DAILY_TRADES", "20")
    monkeypatch.setenv("MAX_ROUTE_LENGTH", "3")
    monkeypatch.setenv("MIN_PROFIT_ALGO", "0.25")
    monkeypatch.setenv("MIN_PROFIT_BPS", "35")
    monkeypatch.setenv("MAX_PRICE_IMPACT_BPS", "50")
    monkeypatch.setenv("QUOTE_MAX_AGE_SECONDS", "5")
    monkeypatch.setenv("APP_ENV", "review")
    monkeypatch.setenv("APP_NAME", "AlgoPulse Market Engine")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("PNET_ASA_ID", "3169177585")
    monkeypatch.setenv("PNET_FEE_RECEIVER_ADDRESS", "PNET_FEE_RECEIVER_REVIEW")
    monkeypatch.setenv("PNET_FEE_APP_ID", "12345")
    monkeypatch.setenv("ADMIN_WALLET_ALLOWLIST", "ADMIN_ONE,ADMIN_TWO")
    monkeypatch.setenv("PUBLIC_ROUTE_DELAY_SECONDS", "900")

    settings = get_settings()

    assert settings.env == "review"
    assert settings.app_name == "AlgoPulse Market Engine"
    assert settings.log_level == "debug"
    assert settings.network == "testnet"
    assert settings.algod_url == "https://algod.example"
    assert settings.algod_token == "algod-token"
    assert settings.indexer_url == "https://indexer.example"
    assert settings.indexer_token == "indexer-token"
    assert settings.database_url == "postgresql://postgres:postgres@localhost:5432/algopulse"
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.enable_scanner is True
    assert settings.enable_live_execution is False
    assert settings.signer_enabled is False
    assert settings.signer_kill_switch is True
    assert settings.max_live_trade_size == 10.0
    assert settings.max_daily_loss == 20.0
    assert settings.max_daily_trades == 20
    assert settings.max_route_legs == 3
    assert settings.min_net_profit_algos == 0.25
    assert settings.min_profit_bps == 35.0
    assert settings.max_price_impact_bps == 50.0
    assert settings.max_route_age_seconds == 5.0
    assert settings.target_asset_id == 3169177585
    assert settings.pnet_fee_receiver_address == "PNET_FEE_RECEIVER_REVIEW"
    assert settings.pnet_fee_app_id == "12345"
    assert settings.admin_wallet_allowlist == ("ADMIN_ONE", "ADMIN_TWO")
    assert settings.public_delay_seconds == 900

    get_settings.cache_clear()


def test_get_settings_loads_signer_secret_from_external_file(tmp_path, monkeypatch):
    get_settings.cache_clear()
    secret_file = tmp_path / "signer-secret.txt"
    secret_file.write_text("not-a-real-secret\n", encoding="utf-8")
    monkeypatch.setenv("ALGO_PULSE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("ALGO_PULSE_SIGNER_SECRET", raising=False)
    monkeypatch.setenv("ALGO_PULSE_SIGNER_SECRET_FILE", str(secret_file))

    settings = get_settings()

    assert settings.trader_mnemonic == "not-a-real-secret"

    get_settings.cache_clear()


def test_get_settings_rejects_repo_local_signer_secret_file(tmp_path, monkeypatch):
    get_settings.cache_clear()
    repo_file = Path(__file__).resolve().parents[1] / "pyproject.toml"
    monkeypatch.setenv("ALGO_PULSE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("ALGO_PULSE_SIGNER_SECRET", raising=False)
    monkeypatch.setenv("ALGO_PULSE_SIGNER_SECRET_FILE", str(repo_file))

    with pytest.raises(ValueError, match="outside the project repo"):
        get_settings()

    get_settings.cache_clear()


def test_get_settings_defaults_public_routes_to_fifteen_minute_delay(tmp_path, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ALGO_PULSE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("PUBLIC_ROUTE_DELAY_SECONDS", raising=False)
    monkeypatch.delenv("ALGO_PULSE_PUBLIC_DELAY_SECONDS", raising=False)

    settings = get_settings()

    assert settings.public_delay_seconds == 900

    get_settings.cache_clear()
