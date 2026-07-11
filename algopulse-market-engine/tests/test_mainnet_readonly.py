from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from algopulse.config import get_settings
from algopulse.mainnet_readonly import run_mainnet_readonly_collector, run_mainnet_readonly_cycle
from algopulse.readonly_safety import ReadonlySafetyError, assert_mainnet_readonly_safe
from algopulse.store import MarketStore


def _settings(tmp_path: Path, **overrides):
    get_settings.cache_clear()
    base = get_settings()
    values = {
        "env": "mainnet-readonly",
        "network": "mainnet",
        "data_dir": tmp_path / "data",
        "database_path": tmp_path / "data" / "mainnet-ro.db",
        "connector_mode": "tinyman,pact",
        "public_delay_seconds": 900,
        "enable_live_execution": False,
        "execute_approved": False,
        "allow_api_execution": False,
        "unsigned_executor_only": True,
        "signer_enabled": False,
        "signer_kill_switch": True,
        "trader_mnemonic": "",
        "asset_pairs": ((0, 3_169_177_585), (0, 31_566_704)),
        "allowed_asset_ids": (0, 3_169_177_585, 31_566_704),
        "target_asset_id": 3_169_177_585,
    }
    values.update(overrides)
    return replace(base, **values)


def test_mainnet_readonly_profile_accepts_safe_config(tmp_path):
    assert_mainnet_readonly_safe(_settings(tmp_path))


def test_mainnet_readonly_refuses_execution_and_signer(tmp_path):
    with pytest.raises(ReadonlySafetyError, match="refused_live_execution_enabled"):
        assert_mainnet_readonly_safe(_settings(tmp_path, enable_live_execution=True))
    with pytest.raises(ReadonlySafetyError, match="refused_signer_enabled"):
        assert_mainnet_readonly_safe(_settings(tmp_path, signer_enabled=True))
    with pytest.raises(ReadonlySafetyError, match="refused_api_execution_enabled"):
        assert_mainnet_readonly_safe(_settings(tmp_path, allow_api_execution=True))
    with pytest.raises(ReadonlySafetyError, match="refused_signer_secret_loaded"):
        assert_mainnet_readonly_safe(_settings(tmp_path, trader_mnemonic="abandon " * 12 + "about"))


def test_mainnet_readonly_refuses_wrong_network_or_env(tmp_path):
    with pytest.raises(ReadonlySafetyError, match="refused_non_mainnet"):
        assert_mainnet_readonly_safe(_settings(tmp_path, network="testnet"))
    with pytest.raises(ReadonlySafetyError, match="refused_mainnet_without_readonly_profile"):
        assert_mainnet_readonly_safe(_settings(tmp_path, env="local"))


def test_mainnet_readonly_refuses_short_public_delay(tmp_path):
    with pytest.raises(ReadonlySafetyError, match="refused_public_delay_below_900"):
        assert_mainnet_readonly_safe(_settings(tmp_path, public_delay_seconds=60))


def test_collector_runs_bounded_cycles_with_injected_clock(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)

    # Avoid live network: stub cycle.
    calls = {"n": 0}

    def fake_cycle(**kwargs):
        calls["n"] += 1
        return {
            "outcome": "spread_below_profit_threshold",
            "selectedPair": [0, 31_566_704],
            "opportunityCount": 1,
            "productionReady": False,
        }

    monkeypatch.setattr("algopulse.mainnet_readonly.run_mainnet_readonly_cycle", fake_cycle)
    clock = {"t": 0.0}

    def now():
        return clock["t"]

    def sleep(seconds: float):
        clock["t"] += float(seconds)

    result = run_mainnet_readonly_collector(
        settings=settings,
        store=store,
        duration_hours=0.01,  # 36 seconds of virtual time
        interval_seconds=15.0,
        perform_rechecks=False,
        sleep_fn=sleep,
        now_fn=now,
    )
    assert result["mode"] == "mainnet-readonly"
    assert result["cyclesCompleted"] >= 1
    assert result["productionReady"] is False
    assert result["liveExecutionLocked"] is True
    assert calls["n"] >= 1
