from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


STANDARD_QUOTE_SIZES = (1.0, 5.0, 10.0, 25.0, 50.0, 100.0)
STANDARD_QUOTE_SIZES_ENV = ",".join(str(int(size)) for size in STANDARD_QUOTE_SIZES)


def _env(name: str, default: str = "", *aliases: str) -> str:
    for key in (name, *aliases):
        value = os.getenv(key)
        if value is not None:
            return value
    return default


def _bool_env(name: str, default: bool, *aliases: str) -> bool:
    value = _env(name, "", *aliases)
    if value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int, *aliases: str) -> int:
    value = _env(name, "", *aliases)
    if value == "":
        return default
    return int(value)


def _float_env(name: str, default: float, *aliases: str) -> float:
    value = _env(name, "", *aliases)
    if value == "":
        return default
    return float(value)


def _path_env(name: str, default: str, *aliases: str) -> Path:
    return Path(_env(name, default, *aliases)).resolve()


@dataclass(frozen=True)
class Settings:
    env: str
    data_dir: Path
    database_path: Path
    connector_mode: str
    scanner_interval_seconds: int
    public_delay_seconds: int
    network: str
    asset_pairs: tuple[tuple[int, int], ...]
    slippage_bps: int
    enable_live_execution: bool
    execute_approved: bool
    allow_api_execution: bool
    allow_non_algo_starting_routes: bool
    allow_non_algo_live_submission: bool
    unsigned_executor_only: bool
    signer_enabled: bool
    signer_kill_switch: bool
    signer_allowed_route_hashes: tuple[str, ...]
    signer_audit_log_path: Path
    signer_min_wallet_reserve_algos: float
    tiny_live_mode: bool
    tiny_live_allow_automation: bool
    tiny_live_manual_route_hash: str
    tiny_live_lora_txid: str
    tiny_live_reconciliation_confirmed: bool
    tiny_live_min_wallet_algos: float
    tiny_live_max_wallet_algos: float
    trader_mnemonic: str
    trader_address: str
    max_live_trade_size: float
    trade_sizes: tuple[float, ...]
    max_route_age_seconds: float
    max_route_legs: int
    own_funds_only: bool
    allowed_asset_ids: tuple[int, ...]
    allowed_app_ids: tuple[int, ...]
    require_app_id_allowlist: bool
    min_fee_buffer_multiplier: float
    min_net_profit_algos: float
    min_net_profit_input_units: float
    min_profit_bps: float
    max_price_impact_bps: float
    min_pool_reserve: float
    estimated_network_fee_algos: float
    safety_buffer_bps: float
    max_daily_loss: float
    max_daily_trades: int
    max_concurrent_execution: int
    max_group_fee_algos: float
    algod_url: str
    indexer_url: str
    algod_token: str
    indexer_token: str
    vestige_api_url: str
    use_vestige_discovery: bool
    target_asset_id: int
    vestige_pinned_pair_asset_ids: tuple[int, ...]
    vestige_include_fallback_pairs: bool
    vestige_top_pool_count: int
    vestige_min_target_reserve: float
    vestige_protocol_ids: tuple[int, ...]
    app_name: str = "AlgoPulse Market Engine"
    log_level: str = "info"
    pnet_fee_receiver_address: str = "PLATFORM_FEE_WALLET_REVIEW"
    pnet_fee_app_id: str = "pending"
    admin_wallet_allowlist: tuple[str, ...] = ()
    database_url: str = ""
    redis_url: str = ""
    enable_scanner: bool = True


def _asset_pairs_env(name: str, default: str) -> tuple[tuple[int, int], ...]:
    value = os.getenv(name, default)
    pairs: list[tuple[int, int]] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        left, right = item.replace(":", "-").split("-", 1)
        pairs.append((int(left), int(right)))
    return tuple(pairs)


def _int_tuple_env(name: str, default: str) -> tuple[int, ...]:
    value = os.getenv(name, default)
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def _float_tuple_env(name: str, default: str) -> tuple[float, ...]:
    value = os.getenv(name, default)
    return tuple(float(part.strip()) for part in value.split(",") if part.strip())


def _str_tuple_env(name: str, default: str, *aliases: str) -> tuple[str, ...]:
    value = _env(name, default, *aliases)
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _load_signer_secret() -> str:
    secret = _env("ALGO_PULSE_SIGNER_SECRET", "").strip()
    if secret:
        return secret

    secret_file = _env("ALGO_PULSE_SIGNER_SECRET_FILE", "").strip()
    if not secret_file:
        return ""

    path = Path(secret_file).expanduser().resolve()
    repo_root = Path(__file__).resolve().parents[2]
    try:
        path.relative_to(repo_root)
    except ValueError:
        return path.read_text(encoding="utf-8").strip()
    raise ValueError("Signer secret file must live outside the project repo")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv()
    data_dir = _path_env("ALGO_PULSE_DATA_DIR", "./data")
    database_path = _path_env("ALGO_PULSE_DATABASE", str(data_dir / "market.db"))
    min_net_profit_algos = _float_env("MIN_PROFIT_ALGO", 0.25, "ALGO_PULSE_MIN_NET_PROFIT_ALGOS")
    data_dir.mkdir(parents=True, exist_ok=True)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    return Settings(
        app_name=_env("APP_NAME", "AlgoPulse Market Engine", "ALGO_PULSE_APP_NAME"),
        log_level=_env("LOG_LEVEL", "info", "ALGO_PULSE_LOG_LEVEL").strip().lower(),
        env=_env("APP_ENV", "local", "ALGO_PULSE_ENV"),
        data_dir=data_dir,
        database_path=database_path,
        connector_mode=os.getenv("ALGO_PULSE_CONNECTORS", "mock"),
        scanner_interval_seconds=_int_env("ALGO_PULSE_SCANNER_INTERVAL_SECONDS", 15),
        public_delay_seconds=_int_env("PUBLIC_ROUTE_DELAY_SECONDS", 900, "ALGO_PULSE_PUBLIC_DELAY_SECONDS"),
        network=_env("ALGORAND_NETWORK", "mainnet", "ALGO_PULSE_NETWORK").strip().lower(),
        asset_pairs=_asset_pairs_env("ALGO_PULSE_ASSET_PAIRS", "0-31566704"),
        slippage_bps=_int_env("ALGO_PULSE_SLIPPAGE_BPS", 50),
        enable_live_execution=_bool_env("ENABLE_EXECUTION", False, "ALGO_PULSE_ENABLE_LIVE_EXECUTION"),
        execute_approved=_bool_env("ALGO_PULSE_EXECUTE_APPROVED", False),
        allow_api_execution=_bool_env("ALGO_PULSE_ALLOW_API_EXECUTION", False),
        allow_non_algo_starting_routes=_bool_env("ALGO_PULSE_ALLOW_NON_ALGO_STARTING_ROUTES", False),
        allow_non_algo_live_submission=_bool_env("ALGO_PULSE_ALLOW_NON_ALGO_LIVE_SUBMISSION", False),
        unsigned_executor_only=_bool_env("ALGO_PULSE_UNSIGNED_EXECUTOR_ONLY", True),
        signer_enabled=_bool_env("ENABLE_SIGNER", False, "ALGO_PULSE_SIGNER_ENABLED"),
        signer_kill_switch=_bool_env("KILL_SWITCH", True, "ALGO_PULSE_SIGNER_KILL_SWITCH"),
        signer_allowed_route_hashes=_str_tuple_env("ALGO_PULSE_SIGNER_ALLOWED_ROUTE_HASHES", ""),
        signer_audit_log_path=Path(
            os.getenv("ALGO_PULSE_SIGNER_AUDIT_LOG", str(data_dir / "signer-audit.jsonl"))
        ).resolve(),
        signer_min_wallet_reserve_algos=_float_env("ALGO_PULSE_SIGNER_MIN_WALLET_RESERVE_ALGOS", 0.2),
        tiny_live_mode=_bool_env("ALGO_PULSE_TINY_LIVE_MODE", False),
        tiny_live_allow_automation=_bool_env("ALGO_PULSE_TINY_LIVE_ALLOW_AUTOMATION", False),
        tiny_live_manual_route_hash=os.getenv("ALGO_PULSE_TINY_LIVE_MANUAL_ROUTE_HASH", "").strip(),
        tiny_live_lora_txid=os.getenv("ALGO_PULSE_TINY_LIVE_LORA_TXID", "").strip(),
        tiny_live_reconciliation_confirmed=_bool_env("ALGO_PULSE_TINY_LIVE_RECONCILIATION_CONFIRMED", False),
        tiny_live_min_wallet_algos=_float_env("ALGO_PULSE_TINY_LIVE_MIN_WALLET_ALGOS", 100.0),
        tiny_live_max_wallet_algos=_float_env("ALGO_PULSE_TINY_LIVE_MAX_WALLET_ALGOS", 250.0),
        trader_mnemonic=_load_signer_secret(),
        trader_address=os.getenv("ALGO_PULSE_TRADER_ADDRESS", ""),
        max_live_trade_size=_float_env("MAX_TRADE_ALGO", 10.0, "ALGO_PULSE_MAX_LIVE_TRADE_SIZE"),
        trade_sizes=_float_tuple_env("ALGO_PULSE_TRADE_SIZES", STANDARD_QUOTE_SIZES_ENV),
        max_route_age_seconds=_float_env("QUOTE_MAX_AGE_SECONDS", 5.0, "ALGO_PULSE_MAX_ROUTE_AGE_SECONDS"),
        max_route_legs=_int_env("MAX_ROUTE_LENGTH", 3, "ALGO_PULSE_MAX_ROUTE_LEGS"),
        own_funds_only=_bool_env("ALGO_PULSE_OWN_FUNDS_ONLY", True),
        allowed_asset_ids=_int_tuple_env("ALGO_PULSE_ALLOWED_ASSET_IDS", ""),
        allowed_app_ids=_int_tuple_env("ALGO_PULSE_ALLOWED_APP_IDS", ""),
        require_app_id_allowlist=_bool_env("ALGO_PULSE_REQUIRE_APP_ID_ALLOWLIST", True),
        min_fee_buffer_multiplier=_float_env("ALGO_PULSE_MIN_FEE_BUFFER_MULTIPLIER", 2.0),
        min_net_profit_algos=min_net_profit_algos,
        min_net_profit_input_units=_float_env("ALGO_PULSE_MIN_NET_PROFIT_INPUT_UNITS", min_net_profit_algos),
        min_profit_bps=_float_env("MIN_PROFIT_BPS", 35.0, "ALGO_PULSE_MIN_PROFIT_BPS"),
        max_price_impact_bps=_float_env("MAX_PRICE_IMPACT_BPS", 50.0, "ALGO_PULSE_MAX_PRICE_IMPACT_BPS"),
        min_pool_reserve=_float_env("ALGO_PULSE_MIN_POOL_RESERVE", 1_000.0),
        estimated_network_fee_algos=_float_env("ALGO_PULSE_ESTIMATED_NETWORK_FEE_ALGOS", 0.006),
        safety_buffer_bps=_float_env("ALGO_PULSE_SAFETY_BUFFER_BPS", 15.0),
        max_daily_loss=_float_env("MAX_DAILY_LOSS_ALGO", 20.0, "ALGO_PULSE_MAX_DAILY_LOSS"),
        max_daily_trades=_int_env("MAX_DAILY_TRADES", 20, "ALGO_PULSE_MAX_DAILY_TRADES"),
        max_concurrent_execution=max(1, _int_env("ALGO_PULSE_MAX_CONCURRENT_EXECUTION", 1)),
        max_group_fee_algos=_float_env("ALGO_PULSE_MAX_GROUP_FEE_ALGOS", 0.05),
        algod_url=_env("ALGOD_URL", "https://mainnet-api.algonode.cloud", "ALGO_PULSE_ALGOD_URL"),
        indexer_url=_env("INDEXER_URL", "https://mainnet-idx.algonode.cloud", "ALGO_PULSE_INDEXER_URL"),
        algod_token=_env("ALGOD_TOKEN", "", "ALGO_PULSE_ALGOD_TOKEN"),
        indexer_token=_env("INDEXER_TOKEN", "", "ALGO_PULSE_INDEXER_TOKEN"),
        vestige_api_url=os.getenv("ALGO_PULSE_VESTIGE_API_URL", "https://api.vestigelabs.org").rstrip("/"),
        use_vestige_discovery=_bool_env("ALGO_PULSE_USE_VESTIGE_DISCOVERY", False),
        target_asset_id=_int_env("PNET_ASA_ID", 3169177585, "ALGO_PULSE_TARGET_ASSET_ID"),
        vestige_pinned_pair_asset_ids=_int_tuple_env("ALGO_PULSE_VESTIGE_PINNED_PAIR_ASSET_IDS", ""),
        vestige_include_fallback_pairs=_bool_env("ALGO_PULSE_VESTIGE_INCLUDE_FALLBACK_PAIRS", True),
        vestige_top_pool_count=_int_env("ALGO_PULSE_VESTIGE_TOP_POOL_COUNT", 8),
        vestige_min_target_reserve=_float_env("ALGO_PULSE_VESTIGE_MIN_TARGET_RESERVE", 500_000.0),
        vestige_protocol_ids=_int_tuple_env("ALGO_PULSE_VESTIGE_PROTOCOL_IDS", "2,3"),
        pnet_fee_receiver_address=_env(
            "PNET_FEE_RECEIVER_ADDRESS",
            "PLATFORM_FEE_WALLET_REVIEW",
            "ALGO_PULSE_PNET_FEE_RECEIVER_ADDRESS",
        ),
        pnet_fee_app_id=_env("PNET_FEE_APP_ID", "pending", "ALGO_PULSE_PNET_FEE_APP_ID"),
        admin_wallet_allowlist=_str_tuple_env("ADMIN_WALLET_ALLOWLIST", "", "ALGO_PULSE_ADMIN_WALLET_ALLOWLIST"),
        database_url=_env("DATABASE_URL", ""),
        redis_url=_env("REDIS_URL", ""),
        enable_scanner=_bool_env("ENABLE_SCANNER", True),
    )
