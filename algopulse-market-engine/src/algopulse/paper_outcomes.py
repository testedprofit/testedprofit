from __future__ import annotations

import json
import threading
import time
from collections import Counter
from collections.abc import Callable
from typing import Any

from algopulse.models import Pool
from algopulse.store import MarketStore


class PaperOutcomeWorker:
    """Recheck stored paper candidates against fresh snapshots of their exact route."""

    def __init__(
        self,
        *,
        store: MarketStore,
        snapshot_fn: Callable[[], tuple[list[Pool], tuple[int, ...], dict[str, Any], float]],
        run_id: str,
        started_at: float,
        max_quote_age_seconds: float,
        poll_interval_seconds: float = 0.5,
        now_fn: Callable[[], float] = time.time,
    ) -> None:
        self.store = store
        self.snapshot_fn = snapshot_fn
        self.run_id = run_id
        self.started_at = float(started_at)
        self.max_quote_age_seconds = float(max_quote_age_seconds)
        self.poll_interval_seconds = max(0.1, float(poll_interval_seconds))
        self.now_fn = now_fn
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._cycle_totals = {"checked_5s": 0, "checked_30s": 0, "checked_60s": 0, "errors": 0}
        self._last_cycle: dict[str, Any] | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="paper-outcome-worker",
            daemon=True,
        )
        self._thread.start()

    def stop(self, *, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        self._thread = None

    def run_once(self, *, now: float | None = None) -> dict[str, Any]:
        checked_at = float(self.now_fn() if now is None else now)
        pools, _, _, _ = self.snapshot_fn()
        fresh_pools = [
            pool
            for pool in pools
            if _pool_is_fresh(pool, now=checked_at, max_age_seconds=self.max_quote_age_seconds)
        ]
        updates = self.store.update_due_paper_trades(
            fresh_pools,
            now=checked_at,
            created_at_min=self.started_at,
            run_id=self.run_id,
        )
        cycle = {
            **updates,
            "checkedAt": checked_at,
            "availablePoolCount": len(pools),
            "freshPoolCount": len(fresh_pools),
        }
        with self._lock:
            for key in self._cycle_totals:
                self._cycle_totals[key] += int(updates.get(key) or 0)
            self._last_cycle = cycle
        return cycle

    def summary(self, *, limit: int = 10) -> dict[str, Any]:
        rows = [
            row
            for row in self.store.list_paper_trades_since(self.started_at, limit=10_000)
            if f"runId={self.run_id}" in str(row.get("notes") or "")
        ]
        completed_5s = sum(row.get("checked_5s_at") is not None for row in rows)
        completed_30s = sum(row.get("checked_30s_at") is not None for row in rows)
        completed_both = sum(
            row.get("checked_5s_at") is not None and row.get("checked_30s_at") is not None
            for row in rows
        )
        route_classes = Counter(str(row.get("route_class") or "unknown") for row in rows)
        failures_5s = sum(bool(row.get("failure_reason_5s")) for row in rows)
        failures_30s = sum(bool(row.get("failure_reason_30s")) for row in rows)
        sample_rows = sorted(
            rows,
            key=lambda row: (
                row.get("checked_5s_at") is not None and row.get("checked_30s_at") is not None,
                float(row.get("checked_30s_at") or 0.0),
                float(row.get("created_at") or 0.0),
            ),
            reverse=True,
        )
        samples = [_paper_evidence_row(row) for row in sample_rows[: max(1, int(limit))]]
        with self._lock:
            totals = dict(self._cycle_totals)
            last_cycle = dict(self._last_cycle) if self._last_cycle else None
        return {
            "runId": self.run_id,
            "candidateCount": len(rows),
            "completed5sCount": completed_5s,
            "completed30sCount": completed_30s,
            "completedBothCount": completed_both,
            "pendingBothCount": max(0, len(rows) - completed_both),
            "failure5sCount": failures_5s,
            "failure30sCount": failures_30s,
            "routeClassCounts": dict(sorted(route_classes.items())),
            "workerTotals": totals,
            "lastCycle": last_cycle,
            "exactStoredRouteReplay": True,
            "samples": samples,
        }

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.run_once()
            except Exception as exc:
                with self._lock:
                    self._cycle_totals["errors"] += 1
                    self._last_cycle = {
                        "checkedAt": self.now_fn(),
                        "error": type(exc).__name__,
                    }
            self._stop.wait(self.poll_interval_seconds)


def _pool_is_fresh(pool: Pool, *, now: float, max_age_seconds: float) -> bool:
    try:
        captured_at = float(pool.captured_at)
    except (TypeError, ValueError):
        return False
    if captured_at <= 0 or captured_at > now + 1.0:
        return False
    return now - captured_at <= max_age_seconds


def _paper_evidence_row(row: dict[str, Any]) -> dict[str, Any]:
    try:
        route = json.loads(row.get("route_json") or "[]")
    except (TypeError, json.JSONDecodeError):
        route = []
    return {
        "routeHash": row.get("route_hash"),
        "routeClass": row.get("route_class") or "unknown",
        "poolIds": [leg.get("pool_id") for leg in route],
        "venues": [leg.get("venue") for leg in route],
        "sourceCaptureTimes": [leg.get("captured_at") for leg in route],
        "sourceRounds": [leg.get("block_round") for leg in route],
        "inputAmount": row.get("input_amount"),
        "expectedOutput": row.get("expected_final_amount"),
        "expectedProfit": row.get("expected_net_profit"),
        "t5": _checkpoint_evidence(row, "5s"),
        "t30": _checkpoint_evidence(row, "30s"),
        "wouldExecute": bool(row.get("would_execute")),
        "skipReason": row.get("skip_reason"),
    }


def _checkpoint_evidence(row: dict[str, Any], suffix: str) -> dict[str, Any]:
    checked_at = row.get(f"checked_{suffix}_at")
    failure = row.get(f"failure_reason_{suffix}")
    survived = row.get(f"survived_{suffix}")
    if checked_at is None:
        status = "pending"
    elif failure:
        status = "failed"
    elif bool(survived):
        status = "survived"
    else:
        status = "faded"
    return {
        "status": status,
        "checkedAt": checked_at,
        "simulatedOutput": row.get(f"simulated_final_amount_{suffix}") if checked_at is not None else None,
        "simulatedProfit": row.get(f"simulated_profit_{suffix}") if checked_at is not None and not failure else None,
        "quoteDecay": row.get(f"quote_decay_{suffix}") if checked_at is not None and not failure else None,
        "profitDelta": row.get(f"expected_vs_simulated_profit_{suffix}") if checked_at is not None and not failure else None,
        "survived": None if checked_at is None else bool(survived),
        "failureReason": failure,
    }
