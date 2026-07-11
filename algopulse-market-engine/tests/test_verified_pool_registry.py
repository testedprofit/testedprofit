from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from algopulse.models import Opportunity, Pool
from algopulse.risk import RiskEngine, RiskPolicy, policy_from_settings
from algopulse.store import MarketStore
from algopulse.verified_pool_registry import (
    VerifiedPoolRecord,
    build_verified_pool_registry,
    load_paper_verified_app_ids,
    verify_pool_on_chain,
    write_registry_report,
)


def _pool(
    *,
    venue: str = "pact",
    app_id: int = 1001,
    asset_a: int = 0,
    asset_b: int = 31566704,
    reserve_a: float = 10_000.0,
    reserve_b: float = 25_000.0,
    fee_bps: int = 30,
) -> Pool:
    return Pool(
        pool_id=f"{venue}:{app_id}:{asset_a}-{asset_b}",
        venue_id=venue,
        app_id=app_id,
        asset_a_id=asset_a,
        asset_b_id=asset_b,
        reserve_a=reserve_a,
        reserve_b=reserve_b,
        fee_bps=fee_bps,
        block_round=50,
    )


def _opportunity(app_ids: list[int] | None = None) -> Opportunity:
    return Opportunity.from_route(
        route=[],
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=6.0,
        expected_net_profit=1.0,
        expected_profit_bps=2_000.0,
        max_price_impact_bps=10.0,
        involved_pool_ids=["pool"],
        involved_asset_ids=[0, 31566704],
    )


def test_verify_rejects_missing_app_id():
    record = verify_pool_on_chain(
        _pool(app_id=0),
        algod=MagicMock(),
        network="mainnet",
        now=1.0,
    )
    assert record.status == "rejected"
    assert record.reason == "missing_app_id"


def test_verify_rejects_unknown_venue():
    algod = MagicMock()
    algod.application_info.return_value = {"params": {"global-state": [{"key": "x"}]}}
    record = verify_pool_on_chain(
        _pool(venue="unknown-dex", app_id=42),
        algod=algod,
        network="mainnet",
        now=1.0,
    )
    assert record.status == "rejected"
    assert "unknown_venue" in record.reason
    assert record.verification_source == "algod_application_info"


def test_verify_tinyman_accepts_app_with_global_state_and_reserves():
    algod = MagicMock()
    algod.application_info.return_value = {"params": {"global-state": [{"key": "asset_1_id"}]}}
    record = verify_pool_on_chain(
        _pool(venue="tinyman", app_id=1002541853, reserve_a=5_000, reserve_b=12_000),
        algod=algod,
        network="mainnet",
        now=2.0,
    )
    assert record.status == "accepted"
    assert record.reason == "tinyman_app_on_chain_verified"
    assert "algod_application_info" in record.verification_source
    assert record.asset_a_id == 0
    assert record.asset_b_id == 31566704
    assert record.reserve_a == 5_000
    assert record.reserve_b == 12_000
    assert record.fee_bps == 30


def test_verify_tinyman_rejects_zero_reserves():
    algod = MagicMock()
    algod.application_info.return_value = {"params": {"global-state": [{"key": "x"}]}}
    record = verify_pool_on_chain(
        _pool(venue="tinyman", app_id=1002541853, reserve_a=0, reserve_b=10),
        algod=algod,
        network="mainnet",
        now=2.0,
    )
    assert record.status == "rejected"
    assert record.reason == "zero_or_negative_reserves"


def test_verify_rejects_when_algod_application_info_fails():
    algod = MagicMock()
    algod.application_info.side_effect = RuntimeError("not found")
    record = verify_pool_on_chain(
        _pool(app_id=999),
        algod=algod,
        network="mainnet",
        now=1.0,
    )
    assert record.status == "rejected"
    assert "algod_application_info_failed" in record.reason


def test_build_registry_persists_and_returns_report(tmp_path: Path, monkeypatch):
    accepted = VerifiedPoolRecord(
        app_id=111,
        venue_id="pact",
        asset_a_id=0,
        asset_b_id=31566704,
        fee_bps=30,
        reserve_a=1_000.0,
        reserve_b=2_000.0,
        latest_round=99,
        status="accepted",
        reason="pact_on_chain_verified",
        verification_source="pactsdk_fetch_pool_by_id",
        verified_at=10.0,
        pool_id="pact:111",
    )
    rejected = VerifiedPoolRecord(
        app_id=222,
        venue_id="pact",
        asset_a_id=0,
        asset_b_id=31566704,
        fee_bps=30,
        reserve_a=0.0,
        reserve_b=0.0,
        latest_round=99,
        status="rejected",
        reason="zero_or_negative_reserves",
        verification_source="pactsdk_fetch_pool_by_id",
        verified_at=10.0,
        pool_id="pact:222",
    )

    def fake_verify(pool, **kwargs):
        return accepted if pool.app_id == 111 else rejected

    monkeypatch.setattr("algopulse.verified_pool_registry.verify_pool_on_chain", fake_verify)
    monkeypatch.setattr("algopulse.verified_pool_registry.build_algod_client", lambda settings: MagicMock())

    store = MarketStore(tmp_path / "registry.db")
    store.initialize(run_backfills=False)
    settings = SimpleNamespace(network="mainnet", database_path=tmp_path / "registry.db")

    report = build_verified_pool_registry(
        [_pool(app_id=111), _pool(app_id=222)],
        settings=settings,
        store=store,
        now=10.0,
    )

    assert report["acceptedCount"] == 1
    assert report["rejectedCount"] == 1
    assert report["acceptedAppIds"] == [111]
    assert report["paperOnlyRegistry"] is True
    assert report["executionAllowlistUnchanged"] is True
    assert report["signerAllowlistUnchanged"] is True
    assert all(item.get("verification_source") for item in report["accepted"])

    rows = store.list_verified_pool_registry(network="mainnet")
    assert len(rows) == 2
    accepted_ids = load_paper_verified_app_ids(store, network="mainnet")
    assert accepted_ids == (111,)

    out = tmp_path / "report.json"
    write_registry_report(report, str(out))
    assert out.is_file()
    assert "acceptedAppIds" in out.read_text(encoding="utf-8")


def test_paper_verified_app_ids_allow_risk_without_execution_allowlist():
    """Paper path uses verified registry; execution allowed_app_ids stays empty."""
    pool = _pool(app_id=555)
    opportunity = _opportunity()

    # Execution-style policy: require allowlist, empty execution list → reject.
    exec_policy = RiskPolicy(
        require_app_id_allowlist=True,
        allowed_app_ids=(),
        paper_verified_app_ids=(),
        min_profit_absolute=0.01,
        min_profit_bps=1.0,
        max_price_impact_bps=500.0,
    )
    exec_decision = RiskEngine(exec_policy).assess(opportunity, [pool])
    assert not exec_decision.approved
    assert exec_decision.reason == "app_ids_allowlisted"

    # Paper policy: same empty execution allowlist, but verified registry set.
    paper_policy = RiskPolicy(
        require_app_id_allowlist=True,
        allowed_app_ids=(),  # execution/signer unchanged
        paper_verified_app_ids=(555,),
        min_profit_absolute=0.01,
        min_profit_bps=1.0,
        max_price_impact_bps=500.0,
    )
    paper_decision = RiskEngine(paper_policy).assess(opportunity, [pool])
    assert paper_decision.approved
    assert paper_decision.rules["app_ids_allowlisted"] is True


def test_paper_verified_rejects_unknown_app_still():
    pool = _pool(app_id=999)
    opportunity = _opportunity()
    policy = RiskPolicy(
        require_app_id_allowlist=True,
        allowed_app_ids=(),
        paper_verified_app_ids=(555,),
        min_profit_absolute=0.01,
        min_profit_bps=1.0,
        max_price_impact_bps=500.0,
    )
    decision = RiskEngine(policy).assess(opportunity, [pool])
    assert not decision.approved
    assert decision.reason == "app_ids_allowlisted"


def test_policy_from_settings_keeps_execution_allowlist_separate():
    settings = SimpleNamespace(
        asset_pairs=((0, 31566704),),
        max_live_trade_size=10.0,
        min_net_profit_algos=0.25,
        min_net_profit_input_units=0.25,
        min_profit_bps=35.0,
        max_price_impact_bps=50.0,
        min_pool_reserve=1_000.0,
        estimated_network_fee_algos=0.006,
        safety_buffer_bps=15.0,
        max_route_age_seconds=5.0,
        max_route_legs=3,
        own_funds_only=True,
        allowed_asset_ids=(0, 31566704),
        allowed_app_ids=(),  # execution empty
        require_app_id_allowlist=True,
        min_fee_buffer_multiplier=2.0,
    )
    policy = policy_from_settings(settings, paper_verified_app_ids=(1001, 2002))
    assert policy.allowed_app_ids == ()
    assert policy.require_app_id_allowlist is True
    assert policy.paper_verified_app_ids == (1001, 2002)
    public = policy.to_public_dict()
    assert public["allowed_app_ids"] == []
    assert public["paper_verified_app_ids"] == [1001, 2002]


def test_policy_from_settings_without_paper_ids_does_not_invent_allowlist():
    settings = SimpleNamespace(
        asset_pairs=((0, 31566704),),
        max_live_trade_size=10.0,
        min_net_profit_algos=0.25,
        min_net_profit_input_units=0.25,
        min_profit_bps=35.0,
        max_price_impact_bps=50.0,
        min_pool_reserve=1_000.0,
        estimated_network_fee_algos=0.006,
        safety_buffer_bps=15.0,
        max_route_age_seconds=5.0,
        max_route_legs=3,
        own_funds_only=True,
        allowed_asset_ids=(0, 31566704),
        allowed_app_ids=(),
        require_app_id_allowlist=True,
        min_fee_buffer_multiplier=2.0,
    )
    policy = policy_from_settings(settings)
    assert policy.allowed_app_ids == ()
    assert policy.paper_verified_app_ids == ()
