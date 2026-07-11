from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from algopulse.config import get_settings
from algopulse.models import Opportunity, Pool
from algopulse.paper_arb_loop import (
    OUTCOME_CONNECTOR_UNAVAILABLE,
    OUTCOME_NO_SHARED_PAIR,
    OUTCOME_PAPER_CANDIDATE,
    OUTCOME_ROUTE_REJECTED,
    OUTCOME_SPREAD_BELOW,
    classify_outcome,
    comparable_quotes_for_sizes,
    run_paper_arb_loop,
    shared_liquid_pairs,
)
from algopulse.store import MarketStore


def _settings(tmp_path: Path, **overrides):
    get_settings.cache_clear()
    base = get_settings()
    values = {
        "env": "testnet",
        "network": "testnet",
        "data_dir": tmp_path / "data",
        "database_path": tmp_path / "data" / "paper-arb.db",
        "connector_mode": "tinyman,pact",
        "public_delay_seconds": 900,
        "enable_live_execution": False,
        "execute_approved": False,
        "allow_api_execution": False,
        "unsigned_executor_only": True,
        "signer_enabled": False,
        "signer_kill_switch": True,
        "trader_mnemonic": "",
        "asset_pairs": ((0, 10_458_941),),
        "allowed_asset_ids": (0, 10_458_941),
        "allowed_app_ids": (),
        "require_app_id_allowlist": True,
        "max_route_age_seconds": 30.0,
        "min_net_profit_algos": 0.000001,
        "min_profit_bps": 1.0,
        "max_price_impact_bps": 5000.0,
        "trade_sizes": (1.0, 5.0, 10.0),
    }
    values.update(overrides)
    return replace(base, **values)


def _pool(venue: str, app_id: int, reserve_a: float, reserve_b: float) -> Pool:
    return Pool(
        pool_id=f"{venue}:{app_id}:0-10458941",
        venue_id=venue,
        app_id=app_id,
        asset_a_id=0,
        asset_b_id=10_458_941,
        reserve_a=reserve_a,
        reserve_b=reserve_b,
        fee_bps=30,
        block_round=100,
    )


def test_shared_liquid_pairs_requires_both_venues():
    pools = [
        _pool("tinyman", 1, 1000, 2000),
        _pool("pact", 2, 900, 2100),
        _pool("tinyman", 3, 50, 50),  # no pact counterpart for different fee only same pair
    ]
    shared = shared_liquid_pairs(pools)
    assert len(shared) == 1
    assert shared[0]["pair"] == [0, 10_458_941]
    assert len(shared[0]["tinymanPools"]) == 2
    assert len(shared[0]["pactPools"]) == 1


def test_comparable_quotes_for_1_5_10_algo():
    pool = _pool("tinyman", 1, 10_000, 25_000)
    quotes = comparable_quotes_for_sizes([pool], (1.0, 5.0, 10.0))
    assert {round(q["inputAmount"], 4) for q in quotes} == {1.0, 5.0, 10.0}
    assert all(q["venueId"] == "tinyman" for q in quotes)
    assert all(q["outputAmount"] > 0 for q in quotes)


def test_classify_connector_unavailable_and_no_shared_pair():
    outcome, _ = classify_outcome(
        tinyman_status="error",
        pact_status="error",
        tinyman_pools=0,
        pact_pools=0,
        shared_pairs=[],
        opportunities=[],
    )
    assert outcome == OUTCOME_CONNECTOR_UNAVAILABLE

    outcome, _ = classify_outcome(
        tinyman_status="ok",
        pact_status="error",
        tinyman_pools=1,
        pact_pools=0,
        shared_pairs=[],
        opportunities=[],
    )
    assert outcome == OUTCOME_CONNECTOR_UNAVAILABLE

    outcome, _ = classify_outcome(
        tinyman_status="ok",
        pact_status="ok",
        tinyman_pools=1,
        pact_pools=1,
        shared_pairs=[],
        opportunities=[],
    )
    assert outcome == OUTCOME_NO_SHARED_PAIR


def test_classify_spread_and_risk_and_paper():
    approved = Opportunity.from_route(
        route=[{"venue": "tinyman"}, {"venue": "pact"}],
        input_asset_id=0,
        input_amount=1.0,
        expected_final_amount=1.1,
        expected_net_profit=0.05,
        expected_profit_bps=500,
        max_price_impact_bps=10,
        involved_pool_ids=["a", "b"],
        involved_asset_ids=[0, 1],
    )
    approved.status = "approved"
    outcome, _ = classify_outcome(
        tinyman_status="ok",
        pact_status="ok",
        tinyman_pools=1,
        pact_pools=1,
        shared_pairs=[{"pair": [0, 1]}],
        opportunities=[approved],
    )
    assert outcome == OUTCOME_PAPER_CANDIDATE

    rejected_profit = Opportunity.from_route(
        route=[{"venue": "tinyman"}, {"venue": "pact"}],
        input_asset_id=0,
        input_amount=1.0,
        expected_final_amount=0.99,
        expected_net_profit=-0.02,
        expected_profit_bps=-200,
        max_price_impact_bps=10,
        involved_pool_ids=["a", "b"],
        involved_asset_ids=[0, 1],
    )
    rejected_profit.status = "rejected"
    rejected_profit.skip_reason = "net_profit_after_fees_ok"
    outcome, _ = classify_outcome(
        tinyman_status="ok",
        pact_status="ok",
        tinyman_pools=1,
        pact_pools=1,
        shared_pairs=[{"pair": [0, 1]}],
        opportunities=[rejected_profit],
    )
    assert outcome == OUTCOME_SPREAD_BELOW

    rejected_risk = replace_opportunity_skip(rejected_profit, "app_ids_allowlisted")
    outcome, _ = classify_outcome(
        tinyman_status="ok",
        pact_status="ok",
        tinyman_pools=1,
        pact_pools=1,
        shared_pairs=[{"pair": [0, 1]}],
        opportunities=[rejected_risk],
    )
    assert outcome == OUTCOME_ROUTE_REJECTED


def replace_opportunity_skip(opportunity: Opportunity, reason: str) -> Opportunity:
    opportunity.skip_reason = reason
    opportunity.status = "rejected"
    return opportunity


class _FakeConnector:
    def __init__(self, name: str, pools: list[Pool], status: str = "ok"):
        self.name = name
        self._pools = pools
        self._status = status

    def list_assets(self):
        return []

    def list_venues(self):
        return []

    def list_pools(self):
        if self._status == "error":
            raise TimeoutError("forced")
        return list(self._pools)

    def health_evidence(self):
        return {
            "status": self._status,
            "detail": None if self._status == "ok" else "forced",
            "metrics": {"poolCount": 0 if self._status == "error" else len(self._pools)},
        }


class _FakeScanner:
    def __init__(self, settings, store, connectors):
        self.settings = settings
        self.store = store
        self.connectors = connectors

    def run_once(self):
        assets = []
        venues = []
        pools = []
        connector_health = []
        for connector in self.connectors:
            try:
                assets.extend(connector.list_assets())
                venues.extend(connector.list_venues())
                connector_pools = connector.list_pools()
                pools.extend(connector_pools)
                evidence = connector.health_evidence()
                status = evidence["status"]
            except Exception as exc:
                connector_pools = []
                status = "error"
                evidence = {"status": "error", "detail": type(exc).__name__, "metrics": {}}
            self.store.record_service_health(
                f"connector:{connector.name}",
                status,
                detail=evidence.get("detail"),
                metrics=evidence.get("metrics") or {},
            )
            connector_health.append(
                {
                    "connectorName": connector.name,
                    "status": status,
                    "detail": evidence.get("detail"),
                    "latencyMs": 1.0,
                    "poolCount": len(connector_pools),
                }
            )
        self.store.upsert_assets(assets)
        self.store.upsert_venues(venues)
        self.store.record_pool_snapshots(pools)
        return {
            "status": "degraded" if any(item["status"] != "ok" for item in connector_health) else "ok",
            "pools": len(pools),
            "opportunities": 0,
            "connector_health": connector_health,
        }


def test_end_to_end_paper_loop_with_mocked_connectors_creates_route_and_rechecks(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)

    # Price skew so tinyman buy / pact sell can produce a candidate or at least risk-evaluated routes.
    tinyman = _pool("tinyman", 111, reserve_a=10_000.0, reserve_b=30_000.0)
    pact = _pool("pact", 222, reserve_a=12_000.0, reserve_b=24_000.0)
    scanner = _FakeScanner(
        settings,
        store,
        [
            _FakeConnector("tinyman", [tinyman]),
            _FakeConnector("pact", [pact]),
        ],
    )

    def fake_registry(pools, **kwargs):
        app_ids = sorted({int(p.app_id) for p in pools if int(p.app_id) > 0})
        return {
            "acceptedCount": len(app_ids),
            "rejectedCount": 0,
            "acceptedAppIds": app_ids,
            "rejectedAppIds": [],
            "accepted": [{"app_id": app_id, "status": "accepted", "verification_source": "test"} for app_id in app_ids],
            "rejected": [],
            "executionAllowlistUnchanged": True,
            "signerAllowlistUnchanged": True,
            "paperOnlyRegistry": True,
        }

    monkeypatch.setattr("algopulse.paper_arb_loop.build_verified_pool_registry", fake_registry)

    import time as time_module

    # Recheck timestamps are stored from wall-clock create time; use a future clock for due checks.
    clock = {"t": time_module.time() + 120.0}

    def now():
        return clock["t"]

    def sleep(seconds: float):
        clock["t"] += float(seconds)

    result = run_paper_arb_loop(
        settings=settings,
        store=store,
        scanner=scanner,
        sleep_fn=sleep,
        now_fn=now,
        perform_rechecks=True,
        recheck_delays=(5.5, 25.0),
    )

    assert result["productionReady"] is False
    assert result["liveExecutionLocked"] is True
    assert result["selectedPair"] == [0, 10_458_941]
    assert result["opportunityCount"] >= 1
    assert result["outcome"] in {
        OUTCOME_PAPER_CANDIDATE,
        OUTCOME_SPREAD_BELOW,
        OUTCOME_ROUTE_REJECTED,
    }
    assert result["route"] is not None
    assert "grossProfit" in result["route"]
    assert "slippageBuffer" in result["route"]
    assert result["comparableQuotes"]
    assert {round(q["inputAmount"], 1) for q in result["comparableQuotes"]} >= {1.0, 5.0, 10.0}

    paper = store.list_paper_trades(limit=50)
    assert paper
    # Rechecks should have completed for created paper rows.
    assert result["paper"]["recheck"]["checked_5s"] >= 1
    assert result["paper"]["recheck"]["checked_30s"] >= 1
    assert any(item.get("checked5sAt") or item.get("checked_5s_at") for item in paper) or result["paper"]["recheck"]["checked_5s"] >= 1


def test_end_to_end_no_shared_pair_outcome(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)
    tinyman = _pool("tinyman", 111, 1000, 2000)
    scanner = _FakeScanner(settings, store, [_FakeConnector("tinyman", [tinyman]), _FakeConnector("pact", [], status="error")])

    monkeypatch.setattr(
        "algopulse.paper_arb_loop.build_verified_pool_registry",
        lambda pools, **kwargs: {
            "acceptedCount": 1,
            "rejectedCount": 0,
            "acceptedAppIds": [111],
            "rejectedAppIds": [],
            "accepted": [{"app_id": 111, "status": "accepted"}],
            "rejected": [],
            "executionAllowlistUnchanged": True,
            "signerAllowlistUnchanged": True,
            "paperOnlyRegistry": True,
        },
    )

    result = run_paper_arb_loop(
        settings=settings,
        store=store,
        scanner=scanner,
        sleep_fn=lambda _s: None,
        now_fn=lambda: 1_700_000_000.0,
        perform_rechecks=False,
    )
    assert result["outcome"] in {OUTCOME_CONNECTOR_UNAVAILABLE, OUTCOME_NO_SHARED_PAIR}
    assert result["selectedPair"] is None


def test_mainnet_without_readonly_profile_refused(tmp_path):
    from algopulse.readonly_safety import ReadonlySafetyError

    settings = _settings(tmp_path, network="mainnet", env="local")
    store = MarketStore(settings.database_path)
    with pytest.raises(ReadonlySafetyError):
        run_paper_arb_loop(
            settings=settings,
            store=store,
            perform_rechecks=False,
            scanner=_FakeScanner(settings, store, []),
        )
