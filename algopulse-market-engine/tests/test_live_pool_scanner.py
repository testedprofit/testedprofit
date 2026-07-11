from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import time

from algopulse.config import get_settings
from algopulse.live_pool_scanner import run_live_scan_cycle, run_live_scanner_loop
from algopulse.models import Pool
from algopulse.store import MarketStore


def _settings(tmp_path: Path, **overrides):
    get_settings.cache_clear()
    base = get_settings()
    values = {
        "env": "mainnet-readonly",
        "network": "mainnet",
        "data_dir": tmp_path / "data",
        "database_path": tmp_path / "data" / "live-scanner.db",
        "connector_mode": "tinyman,pact",
        "public_delay_seconds": 900,
        "enable_live_execution": False,
        "execute_approved": False,
        "allow_api_execution": False,
        "unsigned_executor_only": True,
        "signer_enabled": False,
        "signer_kill_switch": True,
        "trader_mnemonic": "",
        "asset_pairs": ((0, 31566704),),
        "allowed_asset_ids": (0, 31566704),
        "allowed_app_ids": (),
        "require_app_id_allowlist": True,
        "max_route_age_seconds": 30.0,
        "min_net_profit_algos": 0.000001,
        "min_profit_bps": 1.0,
        "max_price_impact_bps": 5000.0,
        "min_pool_reserve": 1.0,
        "max_live_trade_size": 10.0,
        "trade_sizes": (0.1, 1.0, 5.0, 10.0),
    }
    values.update(overrides)
    return replace(base, **values)


def _pool(venue: str, app_id: int, reserve_a: float, reserve_b: float) -> Pool:
    return Pool(
        pool_id=f"{venue}:{app_id}:0-31566704",
        venue_id=venue,
        app_id=app_id,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=reserve_a,
        reserve_b=reserve_b,
        fee_bps=30,
        block_round=100,
        captured_at=time.time(),
    )


class _FakeConnector:
    def __init__(self, name: str, pools: list[Pool]):
        self.name = name
        self._pools = pools

    def list_assets(self):
        return []

    def list_venues(self):
        return []

    def list_pools(self):
        return list(self._pools)

    def health_evidence(self):
        return {"status": "ok", "detail": None, "metrics": {"poolCount": len(self._pools)}}


class _FakeScanner:
    def __init__(self, settings, store, connectors):
        self.settings = settings
        self.store = store
        self.connectors = connectors

    def collect_pools(self):
        pools = []
        health = []
        for connector in self.connectors:
            connector_pools = connector.list_pools()
            pools.extend(connector_pools)
            self.store.record_service_health(
                f"connector:{connector.name}",
                "ok",
                metrics={"poolCount": len(connector_pools)},
            )
            health.append(
                {
                    "connectorName": connector.name,
                    "status": "ok",
                    "detail": None,
                    "latencyMs": 1.0,
                    "poolCount": len(connector_pools),
                }
            )
        self.store.record_pool_snapshots(pools)
        return {
            "status": "ok",
            "pools": len(pools),
            "connector_health": health,
            "pool_objects": pools,
            "paper_rechecks_5s": 0,
            "paper_rechecks_30s": 0,
            "paper_recheck_errors": 0,
        }


def test_live_scan_cycle_persists_snapshots_and_uses_registry(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)

    tinyman = _pool("tinyman", 111, 20_000, 18_000)
    pact = _pool("pact", 222, 19_000, 16_000)
    scanner = _FakeScanner(settings, store, [_FakeConnector("tinyman", [tinyman]), _FakeConnector("pact", [pact])])

    monkeypatch.setattr(
        "algopulse.paper_arb_loop.build_verified_pool_registry",
        lambda pools, **kwargs: {
            "acceptedCount": 2,
            "rejectedCount": 0,
            "acceptedAppIds": [111, 222],
            "rejectedAppIds": [],
            "accepted": [
                {"app_id": 111, "status": "accepted", "verification_source": "test"},
                {"app_id": 222, "status": "accepted", "verification_source": "test"},
            ],
            "rejected": [],
            "executionAllowlistUnchanged": True,
            "signerAllowlistUnchanged": True,
            "paperOnlyRegistry": True,
        },
    )

    result = run_live_scan_cycle(
        settings=settings,
        store=store,
        scanner=scanner,
        perform_rechecks=False,
        now_fn=lambda: 1_700_000_100.0,
        sleep_fn=lambda _s: None,
    )

    assert result["walletRequired"] is False
    assert result["signingEnabled"] is False
    assert result["mode"] == "live_pool_scanner"
    assert result["opportunityCount"] >= 1
    assert result["pairSelection"]["evaluatedPairCount"] >= 1
    assert result["selectedPair"] == [0, 31566704]

    latest = store.list_latest_pools(limit=10)
    assert len(latest) >= 2
    assert all(row.get("source") == "connector" for row in latest)
    assert all(row.get("capturedAt") is not None for row in latest)
    assert any(row.get("venue_id") == "tinyman" for row in latest)
    assert any(row.get("venue_id") == "pact" for row in latest)

    # Quotes/routes/paper consumed stored scan path.
    assert store.list_paper_trades(limit=5)
    assert result["rejectionDistribution"] or result["approvedCount"] >= 0
    # app allowlist should not dominate when registry accepts pools
    top = (result.get("rejectionDistribution") or [{}])[0]
    if result["opportunityCount"] > 0:
        assert top.get("reason") != "app_ids_allowlisted" or result["approvedCount"] > 0


def test_live_scanner_loop_two_cycles_advance_evidence(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)

    clock = {"t": 1_700_000_000.0}
    cycle = {"n": 0}

    def fake_cycle(**kwargs):
        cycle["n"] += 1
        clock["t"] += 10
        store.record_pool_snapshots(
            [
                Pool(
                    pool_id=f"tinyman:cycle{cycle['n']}",
                    venue_id="tinyman",
                    app_id=1000 + cycle["n"],
                    asset_a_id=0,
                    asset_b_id=31566704,
                    reserve_a=1000 + cycle["n"],
                    reserve_b=2000 + cycle["n"],
                    fee_bps=30,
                    block_round=100 + cycle["n"],
                    captured_at=clock["t"],
                )
            ]
        )
        store.record_service_health(
            "live_pool_scanner",
            "ok",
            detail="cycle",
            metrics={"cycle": cycle["n"], "capturedAt": clock["t"], "blockRound": 100 + cycle["n"]},
        )
        return {
            "outcome": "spread_below_profit_threshold",
            "scan": {"pools": cycle["n"]},
            "opportunityCount": 0,
            "approvedCount": 0,
            "selectedPair": [0, 31566704],
            "poolsInspected": [{"blockRound": 100 + cycle["n"]}],
        }

    monkeypatch.setattr("algopulse.live_pool_scanner.run_live_scan_cycle", fake_cycle)
    monkeypatch.setattr("algopulse.live_pool_scanner.acquire_scanner_lock", lambda settings, run_id: tmp_path / "lock")
    monkeypatch.setattr("algopulse.live_pool_scanner.release_scanner_lock", lambda path: None)

    def sleep(seconds: float):
        clock["t"] += float(seconds)

    result = run_live_scanner_loop(
        settings=settings,
        store=store,
        duration_hours=24,
        interval_seconds=15,
        sleep_fn=sleep,
        now_fn=lambda: clock["t"],
        should_stop=lambda: cycle["n"] >= 2,
    )

    assert result["cyclesCompleted"] >= 2
    assert cycle["n"] >= 2
    latest = store.list_latest_pools(limit=20)
    assert len(latest) >= 2
    rounds = sorted({int(row["block_round"]) for row in latest})
    assert max(rounds) > min(rounds)
