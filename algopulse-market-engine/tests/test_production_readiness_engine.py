import time
from dataclasses import replace

from algopulse.config import get_settings
from algopulse.models import Pool
from algopulse.production_readiness import build_production_readiness_report
from algopulse.store import MarketStore


def _pool(captured_at: float) -> Pool:
    return Pool(
        pool_id="pact:ALGO-USDC",
        venue_id="pact",
        app_id=1,
        asset_a_id=0,
        asset_b_id=31566704,
        reserve_a=10_000,
        reserve_b=20_000,
        fee_bps=30,
        block_round=1,
        captured_at=captured_at,
    )


def _settings():
    return replace(
        get_settings(),
        enable_live_execution=False,
        signer_enabled=False,
        signer_kill_switch=True,
        trader_mnemonic="",
        public_delay_seconds=300,
        max_route_age_seconds=5,
    )


def test_production_readiness_score_is_derived_from_evidence(tmp_path):
    now = time.time()
    store = MarketStore(tmp_path / "market.db")
    store.initialize()

    empty_report = build_production_readiness_report(store=store, settings=_settings(), now=now)
    assert empty_report["overallPercent"] == round(
        (empty_report["passedEvidenceCount"] / empty_report["totalEvidenceCount"]) * 100
    )
    assert empty_report["gates"]
    scanner_gate = next(gate for gate in empty_report["gates"] if gate["key"] == "scanner_reliability")
    assert next(item for item in scanner_gate["evidence"] if item["evidenceKey"] == "scanner_uptime_24h")["status"] == "fail"

    store.record_pool_snapshots([_pool(now - 90_000), _pool(now)])
    scanner_report = build_production_readiness_report(store=store, settings=_settings(), now=now)
    scanner_gate = next(gate for gate in scanner_report["gates"] if gate["key"] == "scanner_reliability")
    assert next(item for item in scanner_gate["evidence"] if item["evidenceKey"] == "scanner_uptime_24h")["status"] == "pass"
    assert scanner_report["passedEvidenceCount"] > empty_report["passedEvidenceCount"]

    persisted = store.list_production_evidence()
    assert len(persisted) == scanner_report["totalEvidenceCount"]
    assert {item["status"] for item in persisted}.issubset({"pass", "fail"})
