"""Round-driven read-only arb decision loop (truthful latency + timestamps).

Pool cache updates continuously in the background. Decisions read the cache only
and never rewrite connector source rounds or capture times.
"""

from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import time
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

from algopulse.algorand import build_algod_client, current_algod_round
from algopulse.config import Settings, get_settings
from algopulse.models import Opportunity, Pool
from algopulse.paper_outcomes import PaperOutcomeWorker
from algopulse.readonly_safety import ReadonlySafetyError, assert_readonly_profile_safe
from algopulse.risk import RiskEngine, policy_from_settings
from algopulse.route_optimizer import ProfitSeekingRouteOptimizer, pools_from_store_rows
from algopulse.store import MarketStore
from algopulse.triangle_engine import TriangleOpportunityEngine, CANDIDATE_MAJOR_ASAS, ALGO, USDC
from algopulse.verified_pool_registry import build_verified_pool_registry, load_paper_verified_app_ids


MAX_QUOTE_AGE_SECONDS = 5.0
HEALTH_INTERVAL_SECONDS = 60.0
CACHE_REFRESH_INTERVAL_SECONDS = 1.0  # target cadence; workers independent
VENUE_MAX_RETRIES = 3
VENUE_BASE_BACKOFF_SECONDS = 0.35
MIN_ROUNDS_FOR_DATA_READY = 20
USABLE_ROUND_TARGET = 0.95
SKIP_STALE_QUOTE = "stale_quote_over_max_age"
SKIP_ROUND_MISMATCH = "pool_round_mismatch"
SKIP_NO_POOLS = "no_qualified_pools"
SKIP_NO_FRESH_ROUTE = "no_route_with_fresh_snapshot"
SKIP_WAIT_TIMEOUT = "round_wait_timeout"
SKIP_GAP = "non_consecutive_round_gap"


def wait_for_next_round(
    algod: Any,
    *,
    last_round: int,
    timeout_seconds: float = 30.0,
    sleep_fn: Callable[[float], None] = time.sleep,
    now_fn: Callable[[], float] = time.time,
) -> tuple[int, bool]:
    """Block until algod advances past last_round. Returns (round, timed_out)."""
    deadline = now_fn() + max(1.0, float(timeout_seconds))
    target = int(last_round)
    while now_fn() < deadline:
        try:
            if hasattr(algod, "status_after_block") and target > 0:
                status = algod.status_after_block(target)
                current = int(status.get("last-round") or status.get("last_round") or 0)
                if current > target:
                    return current, False
            current = current_algod_round(algod)
            if current > target:
                return current, False
        except Exception:
            current = current_algod_round(algod)
            if current > target:
                return current, False
        sleep_fn(0.15)
    return max(target, current_algod_round(algod)), True


def refresh_venue_pair(
    settings: Settings,
    *,
    venue: str,
    pair: tuple[int, int],
    max_retries: int = VENUE_MAX_RETRIES,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> tuple[list[Pool], dict[str, Any]]:
    """Refresh one venue for one asset pair with bounded retries.

    Preserves connector block_round/captured_at. Single-pair pulls keep per-update
    latency low so the continuous cache can stay under the 5s freshness window.
    """
    from algopulse.connectors.tinyman import TinymanConnector
    from algopulse.connectors.pact import PactConnector

    connector_cls = TinymanConnector if venue == "tinyman" else PactConnector
    started = time.perf_counter()
    last_error: str | None = None
    local: list[Pool] = []
    attempts = 0
    for attempt in range(max(1, int(max_retries))):
        attempts = attempt + 1
        try:
            scoped = replace(settings, asset_pairs=(tuple(sorted(pair)),))
            connector = connector_cls(scoped)
            local = list(connector.list_pools())
            last_error = None
            break
        except Exception as exc:
            last_error = type(exc).__name__
            local = []
            if attempt + 1 < max_retries:
                sleep_fn(VENUE_BASE_BACKOFF_SECONDS * (2**attempt))
    latency_ms = (time.perf_counter() - started) * 1000.0
    status = "ok" if last_error is None else "error"
    return local, {
        "venue": venue,
        "pair": list(pair),
        "status": status,
        "detail": last_error,
        "poolCount": len(local),
        "latencyMs": round(latency_ms, 3),
        "attempts": attempts,
        "completedAt": time.time(),
    }


def _route_rounds(opportunity: Opportunity) -> list[int]:
    rounds = []
    for leg in opportunity.route:
        try:
            rounds.append(int(leg.get("block_round") or 0))
        except (TypeError, ValueError):
            rounds.append(0)
    return rounds


def _route_capture_times(opportunity: Opportunity) -> list[float]:
    times = []
    for leg in opportunity.route:
        try:
            times.append(float(leg.get("captured_at") or 0.0))
        except (TypeError, ValueError):
            times.append(0.0)
    return times


def enforce_freshness(
    opportunities: list[Opportunity],
    *,
    now: float,
    max_age_seconds: float = MAX_QUOTE_AGE_SECONDS,
) -> tuple[list[Opportunity], dict[str, int]]:
    """Keep routes whose source capture times are all within max_age_seconds."""
    skips: dict[str, int] = {}
    kept: list[Opportunity] = []
    for opp in opportunities:
        rounds = _route_rounds(opp)
        captures = _route_capture_times(opp)
        if not captures or any(c <= 0 for c in captures):
            skips[SKIP_STALE_QUOTE] = skips.get(SKIP_STALE_QUOTE, 0) + 1
            continue
        ages = [max(0.0, now - c) for c in captures]
        if max(ages) > float(max_age_seconds):
            skips[SKIP_STALE_QUOTE] = skips.get(SKIP_STALE_QUOTE, 0) + 1
            continue
        if not rounds or any(r <= 0 for r in rounds):
            skips[SKIP_ROUND_MISMATCH] = skips.get(SKIP_ROUND_MISMATCH, 0) + 1
            continue
        kept.append(opp)
    return kept, skips


def dedupe_routes_for_round(
    opportunities: list[Opportunity],
    *,
    decision_round: int,
) -> list[Opportunity]:
    """One best net route per pool sequence + direction within the decision attempt."""
    best: dict[tuple, Opportunity] = {}
    for opp in opportunities:
        key = (
            int(decision_round),
            tuple(opp.involved_pool_ids),
            int(opp.input_asset_id),
            tuple(sorted(opp.involved_asset_ids)),
        )
        existing = best.get(key)
        if existing is None or opp.expected_net_profit > existing.expected_net_profit:
            best[key] = opp
    return sorted(best.values(), key=lambda item: item.expected_net_profit, reverse=True)


def select_paper_rows(opportunities: list[Opportunity]) -> tuple[list[Opportunity], list[Opportunity]]:
    approved = [o for o in opportunities if o.status == "approved"]
    near: dict[tuple, Opportunity] = {}
    for opp in opportunities:
        if opp.status == "approved":
            continue
        if opp.gross_profit <= 0:
            continue
        key = (tuple(sorted(opp.involved_asset_ids)), int(opp.input_asset_id))
        cur = near.get(key)
        if cur is None or opp.expected_net_profit > cur.expected_net_profit:
            near[key] = opp
    near_list = sorted(near.values(), key=lambda o: o.expected_net_profit, reverse=True)
    return approved, near_list


class BoundedWorkerQueue:
    """Single-worker queue for background jobs; drains and joins on stop."""

    def __init__(self, name: str, *, maxsize: int = 64) -> None:
        self.name = name
        self._queue: queue.Queue = queue.Queue(maxsize=max(1, int(maxsize)))
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._dropped = 0

    def start(self) -> None:
        if not self._thread.is_alive():
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, name=self.name, daemon=True)
            self._thread.start()

    def submit(self, fn: Callable[..., Any], *args: Any) -> bool:
        if self._stop.is_set():
            return False
        try:
            self._queue.put_nowait((fn, args))
            return True
        except queue.Full:
            # Drop oldest then enqueue to bound memory under load.
            try:
                self._queue.get_nowait()
                self._dropped += 1
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait((fn, args))
                return True
            except queue.Full:
                self._dropped += 1
                return False

    def stop(self, *, timeout: float = 5.0) -> None:
        self._stop.set()
        # Unblock worker
        try:
            self._queue.put_nowait((None, ()))
        except queue.Full:
            pass
        self._thread.join(timeout=timeout)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                item = self._queue.get(timeout=0.25)
            except queue.Empty:
                continue
            fn, args = item
            if fn is None:
                break
            try:
                fn(*args)
            except Exception:
                pass
        # Drain remaining work so shutdown does not abandon in-flight writes.
        while True:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break
            fn, args = item
            if fn is None:
                continue
            try:
                fn(*args)
            except Exception:
                pass


class PoolStateCache:
    """Continuous freshness cache v2: independent Tinyman/Pact workers, atomic per-venue updates."""

    def __init__(
        self,
        settings: Settings,
        store: MarketStore,
        *,
        pairs: list[tuple[int, int]],
        interval_seconds: float = CACHE_REFRESH_INTERVAL_SECONDS,
        max_quote_age_seconds: float = MAX_QUOTE_AGE_SECONDS,
    ) -> None:
        self.settings = settings
        self.store = store
        self.pairs = pairs
        self.interval_seconds = max(0.25, float(interval_seconds))
        self.max_quote_age_seconds = float(max_quote_age_seconds)
        self._lock = threading.RLock()
        # Per-venue atomic slots — one slow venue never blocks publishing the other.
        self._venue_pools: dict[str, dict[str, Pool]] = {"tinyman": {}, "pact": {}}
        self._venue_metrics: dict[str, dict[str, Any]] = {}
        self._venue_updated_at: dict[str, float] = {}
        self._verified_ids: tuple[int, ...] = ()
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []
        self._pair_cursors: dict[str, int] = {"tinyman": 0, "pact": 0}
        self._persist_queue = BoundedWorkerQueue("pool-cache-persist", maxsize=32)
        self._registry_queue = BoundedWorkerQueue("pool-cache-registry", maxsize=8)
        self._registry_refresh_pending = False

    def start(self) -> None:
        if self._threads:
            return
        self._stop.clear()
        self._persist_queue.start()
        self._registry_queue.start()
        # Initial parallel warm without blocking one on the other.
        for venue in ("tinyman", "pact"):
            thread = threading.Thread(
                target=self._venue_loop,
                args=(venue,),
                name=f"pool-cache-{venue}",
                daemon=True,
            )
            self._threads.append(thread)
            thread.start()
        # Warm both venues through at least one pair cycle before first decision.
        time.sleep(max(2.0, self.interval_seconds * 3))

    def stop(self) -> None:
        self._stop.set()
        for thread in self._threads:
            thread.join(timeout=3.0)
        self._threads = []
        self._persist_queue.stop(timeout=5.0)
        self._registry_queue.stop(timeout=5.0)

    def snapshot(self) -> tuple[list[Pool], tuple[int, ...], dict[str, Any], float]:
        with self._lock:
            by_id: dict[str, Pool] = {}
            for venue_map in self._venue_pools.values():
                by_id.update(venue_map)
            updated_times = [t for t in self._venue_updated_at.values() if t > 0]
            last_refresh = max(updated_times) if updated_times else 0.0
            metrics = {
                "venues": {k: dict(v) for k, v in self._venue_metrics.items()},
                "poolCount": len(by_id),
                "venueUpdatedAt": dict(self._venue_updated_at),
            }
            return list(by_id.values()), tuple(self._verified_ids), metrics, float(last_refresh)

    def coverage(self, *, now: float | None = None) -> dict[str, Any]:
        """Fresh-pool coverage by venue using original source capture ages."""
        now_ts = float(now if now is not None else time.time())
        with self._lock:
            report: dict[str, Any] = {"venues": {}, "totalPools": 0, "freshPools": 0}
            for venue, pool_map in self._venue_pools.items():
                pools = list(pool_map.values())
                fresh = 0
                ages: list[float] = []
                for pool in pools:
                    age = max(0.0, now_ts - float(pool.captured_at or 0.0))
                    ages.append(age)
                    if float(pool.captured_at or 0.0) > 0 and age <= self.max_quote_age_seconds:
                        fresh += 1
                report["venues"][venue] = {
                    "poolCount": len(pools),
                    "freshPoolCount": fresh,
                    "freshCoverage": (fresh / len(pools)) if pools else 0.0,
                    "maxAgeSeconds": max(ages) if ages else None,
                    "minAgeSeconds": min(ages) if ages else None,
                    "lastRefreshLatencyMs": (self._venue_metrics.get(venue) or {}).get("latencyMs"),
                    "lastStatus": (self._venue_metrics.get(venue) or {}).get("status"),
                    "updatedAt": self._venue_updated_at.get(venue),
                }
                report["totalPools"] += len(pools)
                report["freshPools"] += fresh
            report["freshCoverage"] = (
                report["freshPools"] / report["totalPools"] if report["totalPools"] else 0.0
            )
            return report

    def _venue_loop(self, venue: str) -> None:
        """Independent persistent worker; rotates pairs for low-latency incremental updates."""
        while not self._stop.is_set():
            cycle_start = time.perf_counter()
            try:
                if not self.pairs:
                    self._stop.wait(self.interval_seconds)
                    continue
                cursor = self._pair_cursors.get(venue, 0) % len(self.pairs)
                pair = self.pairs[cursor]
                self._pair_cursors[venue] = cursor + 1
                pools, metrics = refresh_venue_pair(
                    self.settings,
                    venue=venue,
                    pair=pair,
                    max_retries=VENUE_MAX_RETRIES,
                )
                if metrics.get("status") == "ok":
                    # Merge pair results into venue map; other pairs retain prior aging timestamps.
                    self._publish_venue_pair(venue, pools, metrics)
                    self._persist_async(pools)
                    self._maybe_refresh_registry(pools)
                else:
                    with self._lock:
                        prior_n = len(self._venue_pools.get(venue, {}))
                        metrics = {
                            **metrics,
                            "retainedPriorSnapshots": prior_n,
                            "retainPolicy": "original_aging_timestamps",
                        }
                        self._venue_metrics[venue] = metrics
                    self.store.record_service_health(
                        f"pool_cache:{venue}",
                        "error",
                        detail=str(metrics.get("detail") or "refresh_failed"),
                        metrics=metrics,
                    )
            except Exception as exc:
                self.store.record_service_health(
                    f"pool_cache:{venue}",
                    "error",
                    detail=type(exc).__name__,
                    metrics={},
                )
            elapsed = time.perf_counter() - cycle_start
            wait_s = max(0.02, self.interval_seconds - elapsed)
            self._stop.wait(wait_s)

    def _publish_venue_pair(self, venue: str, pools: list[Pool], metrics: dict[str, Any]) -> None:
        """Atomic merge of one pair's pools into the venue cache (no cross-venue wait)."""
        published_at = time.time()
        with self._lock:
            slot = dict(self._venue_pools.get(venue, {}))
            # Drop prior entries for same pair key so replaced fee tiers refresh cleanly.
            if pools:
                pair_key = pools[0].asset_pair
                slot = {
                    pid: pool
                    for pid, pool in slot.items()
                    if pool.asset_pair != pair_key
                }
            for pool in pools:
                slot[pool.pool_id] = pool
            self._venue_pools[venue] = slot
            self._venue_metrics[venue] = dict(metrics)
            self._venue_updated_at[venue] = published_at
        self.store.record_service_health(
            f"pool_cache:{venue}",
            "ok",
            detail="venue_pair_refresh",
            metrics={
                "poolCount": len(pools),
                "latencyMs": metrics.get("latencyMs"),
                "attempts": metrics.get("attempts"),
                "pair": metrics.get("pair"),
            },
        )

    def _persist_async(self, pools: list[Pool]) -> None:
        if not pools:
            return

        def _write(snapshot: list[Pool]) -> None:
            try:
                self.store.record_pool_snapshots(snapshot)
            except Exception:
                pass

        self._persist_queue.submit(_write, list(pools))

    def _maybe_refresh_registry(self, _pools: list[Pool]) -> None:
        """Debounced full-cache registry refresh; pair updates must never replace the full set."""

        with self._lock:
            if self._registry_refresh_pending:
                return
            full_snapshot = [
                pool
                for venue_pools in self._venue_pools.values()
                for pool in venue_pools.values()
            ]
            if not full_snapshot:
                return
            known = set(self._verified_ids)
            if known and all(int(pool.app_id) in known for pool in full_snapshot):
                return
            self._registry_refresh_pending = True

        def _reg(snapshot: list[Pool]) -> None:
            try:
                existing = load_paper_verified_app_ids(self.store, network=self.settings.network)
                known = set(existing)
                unknown = [p for p in snapshot if int(p.app_id) not in known]
                if unknown or not existing:
                    report = build_verified_pool_registry(
                        snapshot,
                        settings=self.settings,
                        store=self.store,
                    )
                    verified = tuple(int(a) for a in (report.get("acceptedAppIds") or []))
                else:
                    verified = existing
                if verified:
                    with self._lock:
                        self._verified_ids = verified
            except Exception:
                pass
            finally:
                with self._lock:
                    self._registry_refresh_pending = False

        if not self._registry_queue.submit(_reg, full_snapshot):
            with self._lock:
                self._registry_refresh_pending = False


class RealtimeDecisionLoop:
    def __init__(
        self,
        settings: Settings,
        store: MarketStore,
        *,
        max_quote_age_seconds: float = MAX_QUOTE_AGE_SECONDS,
        cache_interval_seconds: float = CACHE_REFRESH_INTERVAL_SECONDS,
    ) -> None:
        self.settings = settings
        self.store = store
        self.max_quote_age_seconds = float(max_quote_age_seconds)
        self.algod = build_algod_client(settings)
        self._graph_pairs = self._build_pair_universe()
        self._stop = threading.Event()
        self.cache = PoolStateCache(
            settings,
            store,
            pairs=self._graph_pairs,
            interval_seconds=cache_interval_seconds,
            max_quote_age_seconds=max_quote_age_seconds,
        )
        # Lightweight risk/optimizer rebuilt per decision from cached pools only.

    def _build_pair_universe(self) -> list[tuple[int, int]]:
        pairs = {tuple(sorted(p)) for p in self.settings.asset_pairs}
        pairs.add((ALGO, USDC))
        for asa, _ in CANDIDATE_MAJOR_ASAS:
            pairs.add(tuple(sorted((ALGO, asa))))
            pairs.add(tuple(sorted((USDC, asa))))
        # Keep canary path focused for latency: prefer configured pairs + USDC.
        focused = {tuple(sorted(p)) for p in self.settings.asset_pairs}
        focused.add((ALGO, USDC))
        if focused:
            return sorted(focused)
        return sorted(pairs)

    def decide_one_round(
        self,
        *,
        observed_round: int,
        now_fn: Callable[[], float] = time.time,
        pools_override: list[Pool] | None = None,
        run_id: str | None = None,
    ) -> dict:
        """Decide using cached pool state only — no synchronous full reload."""
        t0 = time.perf_counter()
        decision_started = now_fn()
        decision_round = int(observed_round)

        if pools_override is not None:
            pools = list(pools_override)
            verified_ids = load_paper_verified_app_ids(self.store, network=self.settings.network)
            refresh_metrics: dict[str, Any] = {}
            cache_age_ms = 0.0
            coverage = {"freshCoverage": None, "venues": {}}
        else:
            pools, verified_ids, refresh_metrics, last_refresh_at = self.cache.snapshot()
            cache_age_ms = max(0.0, (now_fn() - last_refresh_at) * 1000.0) if last_refresh_at else None
            coverage = self.cache.coverage(now=now_fn())

        # Never rewrite connector rounds or capture timestamps.
        if verified_ids:
            pools = [p for p in pools if int(p.app_id) in set(verified_ids)]

        if not pools:
            total_ms = (time.perf_counter() - t0) * 1000.0
            result = {
                "observedRound": decision_round,
                "decisionRound": decision_round,
                "skipReason": SKIP_NO_POOLS,
                "skipped": True,
                "decisions": 0,
                "paperRows": 0,
                "endToEndLatencyMs": round(total_ms, 3),
                "decisionComputeLatencyMs": round(total_ms, 3),
                "cacheAgeMs": cache_age_ms,
                "usable": False,
                "freshRouteCount": 0,
            }
            self._record_decision_health(result)
            return result

        asset_ids = sorted({a for p in pools for a in (p.asset_a_id, p.asset_b_id)} | {0})
        risk_settings = replace(
            self.settings,
            allowed_asset_ids=tuple(sorted(set(self.settings.allowed_asset_ids) | set(asset_ids))),
        )
        risk_engine = RiskEngine(
            policy_from_settings(risk_settings, paper_verified_app_ids=verified_ids)
        )

        two_leg = ProfitSeekingRouteOptimizer(risk_engine).optimize(pools)
        min_floor = max(1.0, min(float(self.settings.min_pool_reserve or 1000.0) * 0.001, 50.0))
        # Triangle only when enough distinct pairs exist in cache.
        pairs_present = {p.asset_pair for p in pools}
        unique_ops = [r.opportunity for r in two_leg.optimized_routes]
        triangles = None
        if len(pairs_present) >= 2:
            triangles = TriangleOpportunityEngine(
                risk_engine,
                min_venue_reserve=min_floor,
                verified_app_ids=verified_ids if verified_ids else None,
            ).search(pools)
            unique_ops.extend(r.opportunity for r in triangles.results)

        # Drop fail-closed unavailable routes before freshness.
        evidence_skips: dict[str, int] = {}
        ready_ops: list[Opportunity] = []
        for opp in unique_ops:
            skip = str(opp.skip_reason or "")
            if skip in {"quote_unavailable", "fee_conversion_unavailable"}:
                evidence_skips[skip] = evidence_skips.get(skip, 0) + 1
                continue
            rules = opp.risk_rules or {}
            if rules.get("fee_conversion_ok") is False:
                evidence_skips["fee_conversion_unavailable"] = (
                    evidence_skips.get("fee_conversion_unavailable", 0) + 1
                )
                continue
            ready_ops.append(opp)

        now = now_fn()
        fresh_ops, freshness_skips = enforce_freshness(
            ready_ops,
            now=now,
            max_age_seconds=self.max_quote_age_seconds,
        )
        # Merge evidence skips into freshness report surface.
        for key, count in evidence_skips.items():
            freshness_skips[key] = freshness_skips.get(key, 0) + count

        deduped = dedupe_routes_for_round(fresh_ops, decision_round=decision_round)
        approved, near_misses = select_paper_rows(deduped)
        paper_rows = approved + near_misses

        # Usable only if at least one route uses snapshots under max age.
        fresh_route_count = len(fresh_ops)
        usable = fresh_route_count > 0
        fee_unit_consistent = _derive_fee_unit_consistent(fresh_ops)
        # Derive fabrication: any non-unavailable route/leg missing source capture.
        fabricated_timestamps = _derive_fabricated_timestamps(unique_ops)

        paper_inserted = 0
        paper_duplicates_skipped = 0
        paper_candidates: list[dict] = []
        if paper_rows and usable:
            self.store.record_opportunities(paper_rows)
            for opportunity in paper_rows:
                would_execute = opportunity.status == "approved"
                route_class = classify_route_venues(opportunity.route)
                run_note = f"runId={run_id}; " if run_id else ""
                notes = (
                    f"{run_note}round={decision_round}; routeClass={route_class}; would_execute"
                    if would_execute
                    else f"{run_note}round={decision_round}; routeClass={route_class}; near_miss:{opportunity.skip_reason or 'risk'}"
                )
                inserted = self.store.record_paper_trade(
                    opportunity=opportunity,
                    would_execute=would_execute,
                    notes=notes,
                    decision_round=decision_round,
                )
                if inserted:
                    paper_inserted += 1
                    paper_candidates.append(
                        {
                            "routeHash": opportunity.route_hash,
                            "runId": run_id,
                            "decisionRound": decision_round,
                            "routeClass": route_class,
                            "venues": [leg.get("venue") for leg in opportunity.route],
                            "poolIds": list(opportunity.involved_pool_ids),
                            "sourceCaptures": [
                                leg.get("captured_at") for leg in opportunity.route
                            ],
                            "sourceRounds": [
                                leg.get("block_round") for leg in opportunity.route
                            ],
                            "inputAmount": opportunity.input_amount,
                            "expectedFinalAmount": opportunity.expected_final_amount,
                            "expectedNetProfit": opportunity.expected_net_profit,
                            "status": opportunity.status,
                            "skipReason": opportunity.skip_reason,
                        }
                    )
                else:
                    paper_duplicates_skipped += 1

        total_ms = (time.perf_counter() - t0) * 1000.0
        best = deduped[0] if deduped else None
        source_rounds = sorted({r for o in fresh_ops for r in _route_rounds(o) if r > 0})
        source_captures = [c for o in fresh_ops for c in _route_capture_times(o) if c > 0]
        cross_venue_fresh = sum(
            1
            for o in fresh_ops
            if classify_route_venues(o.route) == "cross_venue_tinyman_pact"
        )
        result = {
            "observedRound": decision_round,
            "decisionRound": decision_round,
            "usable": usable,
            "skipped": not usable,
            "skipReason": None
            if usable
            else (
                next(iter(freshness_skips.keys()), None)
                or (SKIP_NO_FRESH_ROUTE if unique_ops else SKIP_NO_POOLS)
            ),
            "poolCount": len(pools),
            "decisions": len(deduped),
            "freshRouteCount": fresh_route_count,
            "crossVenueFreshRouteCount": cross_venue_fresh,
            "routeVenueEvidence": _route_venue_evidence(fresh_ops),
            "approvedCount": len(approved),
            "nearMissCount": len(near_misses),
            "paperRows": paper_inserted if usable else 0,
            "paperDuplicatesSkipped": paper_duplicates_skipped,
            "paperCandidates": paper_candidates,
            "freshnessSkips": freshness_skips,
            "sourcePoolRounds": source_rounds,
            "sourceCaptureMin": min(source_captures) if source_captures else None,
            "sourceCaptureMax": max(source_captures) if source_captures else None,
            "aggregateRejections": {
                **(two_leg.aggregate_rejections or {}),
                **((triangles.aggregate_rejections if triangles else {}) or {}),
            },
            "cacheAgeMs": cache_age_ms,
            "venueRefresh": (refresh_metrics or {}).get("venues") or refresh_metrics,
            "freshPoolCoverage": coverage,
            "endToEndLatencyMs": round(total_ms, 3),
            "decisionComputeLatencyMs": round(total_ms, 3),
            "bestNet": best.expected_net_profit if best else None,
            "bestGross": best.gross_profit if best else None,
            "bestSize": best.input_amount if best else None,
            "bestStatus": best.status if best else None,
            "bestSkipReason": best.skip_reason if best else None,
            "feeUnitConsistent": fee_unit_consistent,
            "feeConversion": "route_path_quote",
            "fabricatedTimestamps": fabricated_timestamps,
            "maxQuoteAgeSeconds": self.max_quote_age_seconds,
            "startedAt": decision_started,
            "completedAt": now_fn(),
            "connectorStamped": False,
        }
        self._record_decision_health(result)
        return result

    def _record_decision_health(self, result: dict) -> None:
        self.store.record_service_health(
            "realtime_decision_loop",
            "ok" if result.get("usable") else "degraded",
            detail=str(result.get("skipReason") or result.get("bestSkipReason") or "round_decision"),
            metrics={
                "observedRound": result.get("observedRound"),
                "decisionRound": result.get("decisionRound"),
                "usable": result.get("usable"),
                "skipped": result.get("skipped"),
                "decisions": result.get("decisions"),
                "freshRouteCount": result.get("freshRouteCount"),
                "paperRows": result.get("paperRows"),
                "endToEndLatencyMs": result.get("endToEndLatencyMs"),
                "cacheAgeMs": result.get("cacheAgeMs"),
                "freshnessSkips": result.get("freshnessSkips"),
            },
        )

    def run(
        self,
        *,
        max_rounds: int = 20,
        health_interval_seconds: float = HEALTH_INTERVAL_SECONDS,
        sleep_fn: Callable[[float], None] = time.sleep,
        now_fn: Callable[[], float] = time.time,
        should_stop: Callable[[], bool] | None = None,
        paper_target_completed: int = 0,
        paper_max_wait_seconds: float = 900.0,
        paper_poll_interval_seconds: float = 0.5,
    ) -> dict:
        assert_readonly_profile_safe(self.settings)
        run_id = f"rt_loop_{uuid.uuid4().hex[:10]}"
        run_started_at = now_fn()
        self.cache.start()
        paper_worker: PaperOutcomeWorker | None = None
        paper_outcome: dict[str, Any] = {
            "runId": run_id,
            "candidateCount": 0,
            "completed5sCount": 0,
            "completed30sCount": 0,
            "completedBothCount": 0,
            "pendingBothCount": 0,
            "targetCompletedBoth": max(0, int(paper_target_completed)),
            "targetMet": False,
            "waitedSeconds": 0.0,
            "exactStoredRouteReplay": True,
            "samples": [],
        }
        if paper_target_completed > 0:
            paper_worker = PaperOutcomeWorker(
                store=self.store,
                snapshot_fn=self.cache.snapshot,
                run_id=run_id,
                started_at=run_started_at,
                max_quote_age_seconds=self.max_quote_age_seconds,
                poll_interval_seconds=paper_poll_interval_seconds,
                now_fn=now_fn,
            )
            paper_worker.start()
        paper_target = max(0, int(paper_target_completed))
        paper_wait_started = time.monotonic()
        paper_deadline = paper_wait_started + max(0.0, float(paper_max_wait_seconds))

        decisions: list[dict] = []
        skipped_rounds: list[dict] = []
        e2e_latencies: list[float] = []
        last_health = now_fn()
        last_round = current_algod_round(self.algod)
        rounds_seen = 0

        try:
            while True:
                if paper_worker is not None:
                    paper_outcome = paper_worker.summary(limit=10)
                deadline_reached = paper_worker is not None and time.monotonic() >= paper_deadline
                if not _should_continue_run(
                    rounds_seen=rounds_seen,
                    minimum_rounds=max_rounds,
                    paper_target=paper_target if paper_worker is not None else 0,
                    paper_completed=int(paper_outcome.get("completedBothCount") or 0),
                    deadline_reached=deadline_reached,
                ):
                    break
                if self._stop.is_set() or (should_stop and should_stop()):
                    break
                observed, timed_out = wait_for_next_round(
                    self.algod,
                    last_round=last_round,
                    sleep_fn=sleep_fn,
                    now_fn=now_fn,
                )
                if timed_out and observed <= last_round:
                    skipped_rounds.append(
                        {
                            "afterRound": last_round,
                            "observedRound": observed,
                            "reason": SKIP_WAIT_TIMEOUT,
                        }
                    )
                    sleep_fn(0.25)
                    continue
                if observed <= last_round:
                    sleep_fn(0.15)
                    continue

                gap = observed - last_round
                if last_round > 0 and gap > 1:
                    # Report every skipped intermediate round — do not claim consecutive.
                    for missing in range(last_round + 1, observed):
                        skipped_rounds.append(
                            {
                                "observedRound": missing,
                                "reason": SKIP_GAP,
                                "nextObservedRound": observed,
                            }
                        )

                last_round = observed
                rounds_seen += 1
                decision = self.decide_one_round(
                    observed_round=observed,
                    now_fn=now_fn,
                    run_id=run_id,
                )
                decisions.append(decision)
                if decision.get("endToEndLatencyMs") is not None:
                    e2e_latencies.append(float(decision["endToEndLatencyMs"]))
                if decision.get("skipped"):
                    skipped_rounds.append(
                        {
                            "observedRound": observed,
                            "reason": decision.get("skipReason") or "decision_skipped",
                            "freshnessSkips": decision.get("freshnessSkips"),
                        }
                    )

                if now_fn() - last_health >= health_interval_seconds:
                    self.store.record_service_health(
                        "realtime_decision_loop_health",
                        "ok",
                        detail="backup_telemetry_60s",
                        metrics={
                            "runId": run_id,
                            "decisionsCompleted": len(decisions),
                            "lastRound": last_round,
                            "p50EndToEndMs": _percentile(e2e_latencies, 50),
                            "p95EndToEndMs": _percentile(e2e_latencies, 95),
                            "skippedRoundCount": len(skipped_rounds),
                            "intervalSeconds": health_interval_seconds,
                        },
                    )
                    last_health = now_fn()

            if paper_worker is not None:
                paper_outcome = paper_worker.summary(limit=10)
                paper_outcome["targetCompletedBoth"] = paper_target
                paper_outcome["targetMet"] = int(paper_outcome.get("completedBothCount") or 0) >= paper_target
                paper_outcome["waitedSeconds"] = round(time.monotonic() - paper_wait_started, 3)
        finally:
            if paper_worker is not None:
                paper_worker.stop(timeout=5.0)
            self.cache.stop()

        if paper_worker is not None:
            paper_outcome = paper_worker.summary(limit=10)
            paper_outcome["targetCompletedBoth"] = paper_target
            paper_outcome["targetMet"] = int(paper_outcome.get("completedBothCount") or 0) >= paper_target
            paper_outcome["waitedSeconds"] = round(time.monotonic() - paper_wait_started, 3)

        usable = [r for r in decisions if r.get("usable")]
        decision_rounds = [int(r["decisionRound"]) for r in decisions if r.get("decisionRound") is not None]
        consecutive = _is_strictly_consecutive(decision_rounds) and not any(
            s.get("reason") == SKIP_GAP for s in skipped_rounds
        )
        p95 = _percentile(e2e_latencies, 95)
        decision_compute_ready = bool(p95 is not None and p95 < 5000.0)
        no_fabricated = all(not bool(r.get("fabricatedTimestamps")) for r in decisions) if decisions else True
        fee_ok = all(bool(r.get("feeUnitConsistent")) for r in usable) if usable else False
        usable_ratio = (len(usable) / rounds_seen) if rounds_seen else 0.0
        # RealtimeDataReady requires a full 20-round attempt window.
        realtime_data_ready = bool(
            rounds_seen >= MIN_ROUNDS_FOR_DATA_READY
            and decision_compute_ready
            and no_fabricated
            and fee_ok
            and usable_ratio >= USABLE_ROUND_TARGET
        )
        coverage_tail = (decisions[-1].get("freshPoolCoverage") if decisions else {}) or {}
        venue_latency = {
            venue: (meta or {}).get("lastRefreshLatencyMs")
            for venue, meta in ((coverage_tail.get("venues") or {}).items())
        }

        bottleneck = None
        if not realtime_data_ready:
            if rounds_seen < MIN_ROUNDS_FOR_DATA_READY:
                bottleneck = f"insufficient_rounds:{rounds_seen}<{MIN_ROUNDS_FOR_DATA_READY}"
            elif not decision_compute_ready:
                bottleneck = f"decision_compute_p95:{p95}"
            elif not no_fabricated:
                bottleneck = "fabricated_timestamps_detected"
            elif not fee_ok:
                bottleneck = "fee_unit_inconsistent_on_usable_rounds"
            elif usable_ratio < USABLE_ROUND_TARGET:
                bottleneck = f"usable_round_ratio:{usable_ratio:.4f}<{USABLE_ROUND_TARGET}"

        return {
            "runId": run_id,
            "mode": "continuous_freshness_cache_v2",
            "roundsAttempted": rounds_seen,
            "decisionsRecorded": len(decisions),
            "usableRounds": len(usable),
            "usableRoundRatio": round(usable_ratio, 4),
            "skippedRounds": skipped_rounds,
            "skippedRoundCount": len(skipped_rounds),
            "roundsAreStrictlyConsecutive": consecutive,
            "consecutiveClaimAllowed": False if skipped_rounds or not consecutive else True,
            "automaticDecisionEveryAttemptedRound": len(decisions) == rounds_seen,
            "p50EndToEndLatencyMs": _percentile(e2e_latencies, 50),
            "p95EndToEndLatencyMs": p95,
            "decisionComputeReady": decision_compute_ready,
            "decisionComputeReadyVerdict": (
                "DECISION_COMPUTE_READY" if decision_compute_ready else "DECISION_COMPUTE_NOT_READY"
            ),
            "realtimeDataReady": realtime_data_ready,
            "realtimeDataReadyVerdict": (
                "REALTIME_DATA_READY" if realtime_data_ready else "NOT REALTIME_DATA_READY"
            ),
            "realtimeReady": realtime_data_ready,
            "realtimeReadyVerdict": (
                "REAL-TIME READY" if realtime_data_ready else "NOT REAL-TIME READY"
            ),
            "p95TargetMs": 5000.0,
            "usableRoundTarget": USABLE_ROUND_TARGET,
            "minRoundsForDataReady": MIN_ROUNDS_FOR_DATA_READY,
            "decisions": decisions,
            "paperOutcome": paper_outcome,
            "feeUnitConsistent": fee_ok,
            "feeConversion": "route_path_quote",
            "fabricatedTimestamps": (not no_fabricated),
            "freshPoolCoverage": coverage_tail,
            "venueRefreshLatencyMs": venue_latency,
            "bottleneck": bottleneck,
            "maxQuoteAgeSeconds": self.max_quote_age_seconds,
            "healthIntervalSeconds": health_interval_seconds,
            "connectorTimestampsPreserved": True,
            "productionReady": False,
            "signingEnabled": False,
            "submissionEnabled": False,
        }


def _is_strictly_consecutive(rounds: list[int]) -> bool:
    if len(rounds) < 2:
        return True
    ordered = list(rounds)
    return all(ordered[i] == ordered[i - 1] + 1 for i in range(1, len(ordered)))


def _should_continue_run(
    *,
    rounds_seen: int,
    minimum_rounds: int,
    paper_target: int,
    paper_completed: int,
    deadline_reached: bool,
) -> bool:
    if paper_target > 0 and deadline_reached:
        return False
    if rounds_seen < minimum_rounds:
        return True
    return paper_target > 0 and paper_completed < paper_target


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 3)
    k = max(0, min(len(ordered) - 1, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return round(ordered[k], 3)


def _derive_fee_unit_consistent(opportunities: list[Opportunity]) -> bool:
    """True only when every opportunity reports successful fee conversion evidence."""
    if not opportunities:
        return False
    for opp in opportunities:
        rules = opp.risk_rules or {}
        if rules.get("fee_conversion_ok") is False:
            return False
        if rules.get("fee_unit_consistent") is False:
            return False
        if "fee_unit_consistent" in rules and not bool(rules.get("fee_unit_consistent")):
            return False
        if "fee_conversion_ok" in rules and rules.get("fee_conversion_ok") is not True:
            return False
        for leg in opp.route:
            if leg.get("fee_amount_in_input_asset") is None and float(leg.get("fee_amount") or 0) > 0:
                return False
    return True


def _derive_fabricated_timestamps(opportunities: list[Opportunity]) -> bool:
    """True if any non-unavailable route claims a decision without source capture."""
    for opp in opportunities:
        skip = str(opp.skip_reason or "")
        if skip == "quote_unavailable":
            # Explicit missing capture rejection is not fabrication.
            continue
        for leg in opp.route:
            raw = leg.get("captured_at")
            if raw is None:
                return True
            try:
                if float(raw) <= 0:
                    return True
            except (TypeError, ValueError):
                return True
    return False


def classify_route_venues(route: list[dict]) -> str:
    venues = [str(leg.get("venue") or "") for leg in route]
    unique = {v for v in venues if v}
    if len(route) >= 3 or any(leg.get("route_kind") == "three_leg_triangle" for leg in route):
        return "triangle"
    if unique == {"tinyman", "pact"}:
        return "cross_venue_tinyman_pact"
    if len(unique) == 1 and unique:
        return f"same_venue_{next(iter(unique))}"
    return "mixed_or_unknown"


def _route_venue_evidence(opportunities: list[Opportunity]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    samples: list[dict] = []
    for opp in opportunities:
        kind = classify_route_venues(opp.route)
        counts[kind] = counts.get(kind, 0) + 1
        if len(samples) < 5:
            samples.append(
                {
                    "routeHash": opp.route_hash,
                    "routeClass": kind,
                    "venues": [leg.get("venue") for leg in opp.route],
                    "poolIds": list(opp.involved_pool_ids),
                    "sourceCaptures": [leg.get("captured_at") for leg in opp.route],
                    "sourceRounds": [leg.get("block_round") for leg in opp.route],
                }
            )
    return {"counts": counts, "samples": samples}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Round-driven read-only arb decision loop.")
    parser.add_argument("--data-dir", type=str, default="data/mainnet-live-scanner")
    parser.add_argument("--max-rounds", type=int, default=20)
    parser.add_argument("--max-quote-age", type=float, default=MAX_QUOTE_AGE_SECONDS)
    parser.add_argument("--cache-interval", type=float, default=CACHE_REFRESH_INTERVAL_SECONDS)
    parser.add_argument("--paper-target-completed", type=int, default=10)
    parser.add_argument("--paper-max-wait-seconds", type=float, default=900.0)
    parser.add_argument("--paper-poll-interval", type=float, default=0.5)
    parser.add_argument(
        "--skip-paper-outcomes",
        action="store_true",
        help="Do not wait for sustained T+5/T+30 paper outcomes.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    if args.data_dir:
        data_dir = Path(args.data_dir).resolve()
        settings = replace(settings, data_dir=data_dir, database_path=data_dir / "market.db")
    store = MarketStore(settings.database_path)
    store.initialize(run_backfills=False)
    loop = RealtimeDecisionLoop(
        settings,
        store,
        max_quote_age_seconds=args.max_quote_age,
        cache_interval_seconds=args.cache_interval,
    )
    result = loop.run(
        max_rounds=args.max_rounds,
        paper_target_completed=0 if args.skip_paper_outcomes else args.paper_target_completed,
        paper_max_wait_seconds=args.paper_max_wait_seconds,
        paper_poll_interval_seconds=args.paper_poll_interval,
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
