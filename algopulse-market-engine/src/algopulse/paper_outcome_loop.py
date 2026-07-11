"""Compatibility CLI for the sustained read-only T+5/T+30 outcome loop."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Callable

from algopulse.config import Settings, get_settings
from algopulse.models import Pool
from algopulse.readonly_safety import assert_readonly_profile_safe
from algopulse.realtime_decision_loop import RealtimeDecisionLoop
from algopulse.store import MarketStore


DEFAULT_MIN_COMPLETED = 10
DEFAULT_MAX_SECONDS = 15 * 60


def _simulate_exact_route(route: list[dict], pools: list[Pool], input_amount: float) -> dict:
    """Pure fixed-pool replay helper used by deterministic contract tests."""
    pool_by_id = {pool.pool_id: pool for pool in pools}
    amount = float(input_amount)
    leg_quotes: list[dict] = []
    for leg in route:
        pool_id = str(leg.get("pool_id") or "")
        pool = pool_by_id.get(pool_id)
        if pool is None:
            return {"ok": False, "reason": f"missing_pool:{pool_id}", "final_amount": None}
        quote = pool.quote(input_asset_id=int(leg["input_asset_id"]), input_amount=amount)
        if quote is None:
            return {
                "ok": False,
                "reason": f"quote_failed:{pool_id}:{leg.get('input_asset_id')}",
                "final_amount": None,
            }
        expected_output_asset = int(leg.get("output_asset_id") or quote.output_asset_id)
        if int(quote.output_asset_id) != expected_output_asset:
            return {"ok": False, "reason": f"output_asset_mismatch:{pool_id}", "final_amount": None}
        leg_quotes.append(
            {
                "poolId": pool_id,
                "venue": pool.venue_id,
                "inputAssetId": quote.input_asset_id,
                "outputAssetId": quote.output_asset_id,
                "inputAmount": quote.input_amount,
                "outputAmount": quote.output_amount,
                "blockRound": pool.block_round,
                "capturedAt": pool.captured_at,
            }
        )
        amount = quote.output_amount
    return {"ok": True, "final_amount": amount, "legs": leg_quotes}


class PaperOutcomeLoop:
    """Thin compatibility wrapper around the canonical realtime paper scheduler."""

    def __init__(
        self,
        settings: Settings,
        store: MarketStore,
        *,
        cache_interval_seconds: float = 0.5,
    ) -> None:
        self.settings = settings
        self.store = store
        self.decision_loop = RealtimeDecisionLoop(
            settings,
            store,
            cache_interval_seconds=cache_interval_seconds,
        )

    def run(
        self,
        *,
        min_completed_both: int = DEFAULT_MIN_COMPLETED,
        max_seconds: float = DEFAULT_MAX_SECONDS,
        sleep_fn: Callable[[float], None] = time.sleep,
        now_fn: Callable[[], float] = time.time,
    ) -> dict:
        assert_readonly_profile_safe(self.settings)
        started_at = now_fn()
        result = self.decision_loop.run(
            max_rounds=20,
            sleep_fn=sleep_fn,
            now_fn=now_fn,
            paper_target_completed=max(1, int(min_completed_both)),
            paper_max_wait_seconds=max(0.0, float(max_seconds)),
            paper_poll_interval_seconds=0.5,
        )
        paper = result.get("paperOutcome") or {}
        failures = int(paper.get("failure5sCount") or 0) + int(paper.get("failure30sCount") or 0)
        decisions = result.get("decisions") or []
        return {
            "mode": "paper_outcome_t5_t30",
            "runId": result.get("runId"),
            "elapsedSeconds": round(now_fn() - started_at, 3),
            "maxSeconds": max_seconds,
            "decisionCycles": result.get("roundsAttempted", 0),
            "candidatesEnqueued": paper.get("candidateCount", 0),
            "paperDuplicatesSkipped": sum(int(row.get("paperDuplicatesSkipped") or 0) for row in decisions),
            "completedT5": paper.get("completed5sCount", 0),
            "completedT30": paper.get("completed30sCount", 0),
            "completedBothT5AndT30": paper.get("completedBothCount", 0),
            "targetCompletedBoth": paper.get("targetCompletedBoth", min_completed_both),
            "targetMet": bool(paper.get("targetMet")),
            "recheckErrors": failures,
            "outcomesByRouteClass": paper.get("routeClassCounts") or {},
            "sampleEvidence": paper.get("samples") or [],
            "lastDecisionMeta": decisions[-1] if decisions else {},
            "exactStoredRouteReplay": True,
            "productionReady": False,
            "signingEnabled": False,
            "submissionEnabled": False,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="T+5/T+30 paper outcome loop (read-only).")
    parser.add_argument("--data-dir", type=str, default="data/mainnet-live-scanner")
    parser.add_argument("--min-completed", type=int, default=DEFAULT_MIN_COMPLETED)
    parser.add_argument("--max-seconds", type=float, default=DEFAULT_MAX_SECONDS)
    parser.add_argument("--cache-interval", type=float, default=0.5)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    if args.data_dir:
        data_dir = Path(args.data_dir).resolve()
        settings = replace(settings, data_dir=data_dir, database_path=data_dir / "market.db")
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)
    loop = PaperOutcomeLoop(settings, store, cache_interval_seconds=args.cache_interval)
    result = loop.run(min_completed_both=args.min_completed, max_seconds=args.max_seconds)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
