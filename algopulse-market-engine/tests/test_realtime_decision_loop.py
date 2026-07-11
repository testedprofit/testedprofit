from __future__ import annotations

import time
import threading
from types import SimpleNamespace

from algopulse.models import Opportunity, Pool
from algopulse.realtime_decision_loop import (
    PoolStateCache,
    SKIP_STALE_QUOTE,
    _is_strictly_consecutive,
    _should_continue_run,
    dedupe_routes_for_round,
    enforce_freshness,
    wait_for_next_round,
)


def _opp(
    *,
    pools: list[str],
    net: float,
    round_n: int,
    captured_at: float,
    input_amount: float = 1.0,
) -> Opportunity:
    route = [
        {
            "pool_id": pid,
            "venue": "pact",
            "input_asset_id": 0,
            "output_asset_id": 31566704 if i == 0 else 0,
            "input_amount": input_amount,
            "expected_output": input_amount,
            "fee_amount": 0.001,
            "fee_asset_id": 0,
            "fee_amount_in_input_asset": 0.001,
            "price_impact_bps": 1.0,
            "block_round": round_n,
            "captured_at": captured_at,
            "expires_at": captured_at + 5,
        }
        for i, pid in enumerate(pools)
    ]
    return Opportunity.from_route(
        route=route,
        input_asset_id=0,
        input_amount=input_amount,
        expected_final_amount=input_amount + net + 0.07,
        expected_net_profit=net,
        expected_profit_bps=net * 10_000,
        max_price_impact_bps=1.0,
        involved_pool_ids=list(pools),
        involved_asset_ids=[0, 31566704],
        gross_profit=net + 0.07,
        estimated_network_fee=0.006,
        total_dex_fees=0.002,
        slippage_buffer=0.0625,
    )


def test_enforce_skips_stale_source_capture_times():
    now = time.time()
    fresh = _opp(pools=["a", "b"], net=-0.05, round_n=100, captured_at=now - 1.0)
    stale = _opp(pools=["c", "d"], net=-0.04, round_n=100, captured_at=now - 10.0)
    kept, skips = enforce_freshness([fresh, stale], now=now, max_age_seconds=5.0)
    assert len(kept) == 1
    assert skips.get(SKIP_STALE_QUOTE, 0) == 1


def test_enforce_uses_pool_source_capture_not_decision_time():
    now = time.time()
    # Source capture is old even if "decision" is now.
    opp = _opp(pools=["a", "b"], net=-0.01, round_n=50, captured_at=now - 30.0)
    kept, skips = enforce_freshness([opp], now=now, max_age_seconds=5.0)
    assert kept == []
    assert skips[SKIP_STALE_QUOTE] == 1


def test_dedupe_per_round_keeps_best_net():
    now = time.time()
    worse = _opp(pools=["a", "b"], net=-0.10, round_n=7, captured_at=now, input_amount=1.0)
    better = _opp(pools=["a", "b"], net=-0.05, round_n=7, captured_at=now, input_amount=0.5)
    other = _opp(pools=["a", "c"], net=-0.06, round_n=7, captured_at=now)
    out = dedupe_routes_for_round([worse, better, other], decision_round=7)
    assert len(out) == 2
    assert any(o.expected_net_profit == -0.05 for o in out)


def test_wait_for_next_round_advances():
    class FakeAlgod:
        def __init__(self):
            self.round = 10

        def status_after_block(self, r):
            self.round = max(self.round, int(r) + 1)
            return {"last-round": self.round}

        def status(self):
            return {"last-round": self.round}

    clock = {"t": 0.0}

    def now():
        return clock["t"]

    def sleep(dt):
        clock["t"] += float(dt)

    nxt, timed_out = wait_for_next_round(
        FakeAlgod(), last_round=10, timeout_seconds=2, sleep_fn=sleep, now_fn=now
    )
    assert nxt > 10
    assert timed_out is False


def test_strict_consecutive_detection():
    assert _is_strictly_consecutive([1, 2, 3]) is True
    assert _is_strictly_consecutive([1, 3, 4]) is False
    assert _is_strictly_consecutive([10]) is True


def test_realtime_data_ready_requires_twenty_rounds():
    from algopulse.realtime_decision_loop import MIN_ROUNDS_FOR_DATA_READY, USABLE_ROUND_TARGET

    assert MIN_ROUNDS_FOR_DATA_READY == 20
    assert USABLE_ROUND_TARGET == 0.95


def test_paper_target_keeps_scanning_after_minimum_rounds_until_complete_or_deadline():
    assert _should_continue_run(
        rounds_seen=20,
        minimum_rounds=20,
        paper_target=10,
        paper_completed=4,
        deadline_reached=False,
    )
    assert not _should_continue_run(
        rounds_seen=25,
        minimum_rounds=20,
        paper_target=10,
        paper_completed=10,
        deadline_reached=False,
    )
    assert not _should_continue_run(
        rounds_seen=25,
        minimum_rounds=20,
        paper_target=10,
        paper_completed=4,
        deadline_reached=True,
    )
    assert not _should_continue_run(
        rounds_seen=20,
        minimum_rounds=20,
        paper_target=0,
        paper_completed=0,
        deadline_reached=False,
    )


def test_registry_refresh_uses_full_accumulated_cache_snapshot(monkeypatch):
    captured: list[list[str]] = []
    completed = threading.Event()

    monkeypatch.setattr(
        "algopulse.realtime_decision_loop.load_paper_verified_app_ids",
        lambda *_args, **_kwargs: (),
    )

    def fake_build(pools, **_kwargs):
        captured.append([pool.pool_id for pool in pools])
        completed.set()
        return {"acceptedAppIds": [pool.app_id for pool in pools]}

    monkeypatch.setattr(
        "algopulse.realtime_decision_loop.build_verified_pool_registry",
        fake_build,
    )
    cache = PoolStateCache(
        SimpleNamespace(network="mainnet"),
        object(),
        pairs=[(0, 31566704)],
    )
    tinyman = Pool("t", "tinyman", 1, 0, 31566704, 1000, 200, 30, 1, time.time())
    pact = Pool("p", "pact", 2, 0, 31566704, 1000, 201, 30, 1, time.time())
    cache._venue_pools = {"tinyman": {"t": tinyman}, "pact": {"p": pact}}
    cache._registry_queue.start()
    try:
        cache._maybe_refresh_registry([tinyman])
        assert completed.wait(2.0)
    finally:
        cache._registry_queue.stop()
    assert captured == [["t", "p"]]
    assert set(cache._verified_ids) == {1, 2}
