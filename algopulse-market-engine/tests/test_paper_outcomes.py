from __future__ import annotations

import time
from dataclasses import replace

import pytest

from algopulse.models import Opportunity, Pool
from algopulse.paper_outcomes import PaperOutcomeWorker
from algopulse.store import MarketStore, _paper_route_class


USDC = 31_566_704


def _pool(
    pool_id: str,
    venue: str,
    *,
    reserve_algo: float,
    reserve_usdc: float,
    captured_at: float,
) -> Pool:
    return Pool(
        pool_id=pool_id,
        venue_id=venue,
        app_id=abs(hash(pool_id)) % 1_000_000 + 1,
        asset_a_id=0,
        asset_b_id=USDC,
        reserve_a=reserve_algo,
        reserve_b=reserve_usdc,
        fee_bps=30,
        block_round=100,
        captured_at=captured_at,
    )


def _opportunity(first: Pool, second: Pool, *, captured_at: float) -> Opportunity:
    input_amount = 1.0
    first_quote = first.quote(0, input_amount)
    assert first_quote is not None
    second_quote = second.quote(USDC, first_quote.output_amount)
    assert second_quote is not None
    route = [
        {
            "route_kind": "two_leg_venue_arb",
            "venue": first.venue_id,
            "pool_id": first.pool_id,
            "input_asset_id": 0,
            "output_asset_id": USDC,
            "input_amount": input_amount,
            "expected_output": first_quote.output_amount,
            "captured_at": captured_at,
            "block_round": 100,
        },
        {
            "route_kind": "two_leg_venue_arb",
            "venue": second.venue_id,
            "pool_id": second.pool_id,
            "input_asset_id": USDC,
            "output_asset_id": 0,
            "input_amount": first_quote.output_amount,
            "expected_output": second_quote.output_amount,
            "captured_at": captured_at,
            "block_round": 100,
        },
    ]
    gross = second_quote.output_amount - input_amount
    return Opportunity.from_route(
        route=route,
        input_asset_id=0,
        input_amount=input_amount,
        expected_final_amount=second_quote.output_amount,
        expected_net_profit=gross - 0.006,
        expected_profit_bps=(gross - 0.006) * 10_000,
        max_price_impact_bps=max(first_quote.price_impact_bps, second_quote.price_impact_bps),
        involved_pool_ids=[first.pool_id, second.pool_id],
        involved_asset_ids=[0, USDC],
        gross_profit=gross,
        estimated_network_fee=0.006,
        total_dex_fees=0.0,
        slippage_buffer=0.0,
    )


def _worker(store: MarketStore, run_id: str, started_at: float, pools_ref: list[list[Pool]]) -> PaperOutcomeWorker:
    return PaperOutcomeWorker(
        store=store,
        snapshot_fn=lambda: (list(pools_ref[0]), (), {}, started_at),
        run_id=run_id,
        started_at=started_at,
        max_quote_age_seconds=5.0,
        poll_interval_seconds=0.1,
    )


def test_exact_stored_route_is_rechecked_at_t5_and_t30(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    started_at = time.time() - 1
    run_id = "paper_exact_route"
    initial_a = _pool("tinyman-a", "tinyman", reserve_algo=1_000, reserve_usdc=200, captured_at=time.time())
    initial_b = _pool("pact-b", "pact", reserve_algo=1_000, reserve_usdc=205, captured_at=time.time())
    opportunity = _opportunity(initial_a, initial_b, captured_at=time.time())
    assert store.record_paper_trade(
        opportunity,
        would_execute=False,
        notes=f"runId={run_id}; round=100; near_miss",
        decision_round=100,
    )
    assert not store.record_paper_trade(
        opportunity,
        would_execute=False,
        notes=f"runId={run_id}; round=100; duplicate",
        decision_round=100,
    )
    created_at = store.list_paper_trades_since(started_at)[0]["created_at"]

    exact_a = replace(initial_a, reserve_b=210, captured_at=created_at + 5)
    exact_b = replace(initial_b, reserve_b=204, captured_at=created_at + 5)
    unrelated_better = _pool(
        "unrelated-better",
        "pact",
        reserve_algo=1_000,
        reserve_usdc=400,
        captured_at=created_at + 5,
    )
    pools_ref = [[exact_a, exact_b, unrelated_better]]
    worker = _worker(store, run_id, started_at, pools_ref)
    worker.run_once(now=created_at + 6)

    expected_first = exact_a.quote(0, 1.0)
    assert expected_first is not None
    expected_second = exact_b.quote(USDC, expected_first.output_amount)
    assert expected_second is not None
    row = store.list_paper_trades_since(started_at)[0]
    assert row["simulated_final_amount_5s"] == pytest.approx(expected_second.output_amount)
    assert row["route_class"] == "cross_venue_tinyman_pact"

    pools_ref[0] = [
        replace(exact_a, reserve_b=211, captured_at=created_at + 30),
        replace(exact_b, reserve_b=203, captured_at=created_at + 30),
        replace(unrelated_better, captured_at=created_at + 30),
    ]
    worker.run_once(now=created_at + 31)
    summary = worker.summary()
    row = store.list_paper_trades_since(started_at)[0]
    assert row["checked_5s_at"] is not None
    assert row["checked_30s_at"] is not None
    assert row["quote_decay_5s"] is not None
    assert row["quote_decay_30s"] is not None
    assert summary["completedBothCount"] == 1
    assert summary["exactStoredRouteReplay"] is True
    assert summary["routeClassCounts"] == {"cross_venue_tinyman_pact": 1}

    assert store.record_paper_trade(
        opportunity,
        would_execute=False,
        notes=f"runId={run_id}; round=101; newer pending",
        decision_round=101,
    )
    prioritized = worker.summary(limit=1)
    assert prioritized["candidateCount"] == 2
    assert prioritized["samples"][0]["t30"]["status"] != "pending"


def test_missing_route_pool_records_checkpoint_failure_without_substitution(tmp_path):
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    started_at = time.time() - 1
    run_id = "paper_failure"
    first = _pool("first", "tinyman", reserve_algo=1_000, reserve_usdc=200, captured_at=time.time())
    second = _pool("second", "pact", reserve_algo=1_000, reserve_usdc=205, captured_at=time.time())
    opportunity = _opportunity(first, second, captured_at=time.time())
    assert store.record_paper_trade(
        opportunity,
        would_execute=False,
        notes=f"runId={run_id}; round=200; near_miss",
        decision_round=200,
    )
    created_at = store.list_paper_trades_since(started_at)[0]["created_at"]
    pools_ref = [[replace(first, captured_at=created_at + 5)]]
    worker = _worker(store, run_id, started_at, pools_ref)
    worker.run_once(now=created_at + 6)

    row = store.list_paper_trades_since(started_at)[0]
    assert row["checked_5s_at"] is not None
    assert row["failure_reason_5s"] == "missing pool for paper route: second"
    assert row["simulated_final_amount_5s"] is None

    pools_ref[0] = [
        replace(first, captured_at=created_at + 30),
        replace(second, captured_at=created_at + 30),
    ]
    worker.run_once(now=created_at + 31)
    row = store.list_paper_trades_since(started_at)[0]
    assert row["checked_30s_at"] is not None
    assert row["failure_reason_30s"] is None
    assert row["failure_reason_5s"] == "missing pool for paper route: second"
    assert worker.summary()["completedBothCount"] == 1


def test_route_classes_distinguish_same_cross_venue_and_triangle():
    same = [{"venue": "pact"}, {"venue": "pact"}]
    cross = [{"venue": "tinyman"}, {"venue": "pact"}]
    triangle = [{"venue": "pact"}, {"venue": "tinyman"}, {"venue": "pact"}]
    assert _paper_route_class(same) == "same_venue"
    assert _paper_route_class(cross) == "cross_venue_tinyman_pact"
    assert _paper_route_class(triangle) == "triangle"
