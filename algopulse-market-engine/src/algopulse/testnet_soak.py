from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
import uuid
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from algopulse.config import Settings, get_settings
from algopulse.store import MarketStore


SOAK_TARGET_SECONDS = 24 * 60 * 60
DEFAULT_INTERVAL_SECONDS = 60
MIN_INTERVAL_SECONDS = 5
MAX_OBSERVATION_LIMIT = 5000
ALGOD_STALE_NO_PROGRESS_SECONDS = 300
INDEXER_LAG_WAIT_ROUNDS = 50
LOCK_FILENAME = "testnet_soak.lock"

FORBIDDEN_EVIDENCE_TOKENS = (
    "mnemonic",
    "private_key",
    "seed_phrase",
    "seed",
    "signer_secret",
    "signer secret",
    "hot_wallet",
    "signed_txn",
    "submission_payload",
    "execution_queue",
    "raw_route_json",
    "api_key",
    "secret",
)


from algopulse.readonly_safety import ReadonlySafetyError
from algopulse.readonly_safety import assert_testnet_readonly_safe


class SoakSafetyError(ReadonlySafetyError):
    """Raised when the soak runner must refuse to start."""


class SoakLockError(RuntimeError):
    """Raised when another soak runner holds the local lock."""


@dataclass
class SoakProbeDeps:
    """Injectable probes so tests never need live network calls."""

    probe_algod: Callable[[], dict]
    probe_indexer: Callable[[], dict]
    run_scan: Callable[[], dict]
    quote_freshness: Callable[[], dict]


def assert_safe_to_run(settings: Settings) -> None:
    try:
        assert_testnet_readonly_safe(settings)
    except ReadonlySafetyError as exc:
        raise SoakSafetyError(str(exc)) from exc


def observation_source_for_settings(settings: Settings) -> str:
    modes = {part.strip().lower() for part in settings.connector_mode.split(",") if part.strip()}
    live_modes = modes.intersection({"tinyman", "pact"})
    if live_modes and "mock" not in modes:
        return "live"
    if live_modes and "mock" in modes:
        return "live"
    if "mock" in modes or not modes:
        return "mock"
    return "live"


def lock_path_for(settings: Settings) -> Path:
    return Path(settings.data_dir) / LOCK_FILENAME


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if os.name == "nt":
        import ctypes

        process_query_limited_information = 0x1000
        still_active = 259
        access_denied = 5
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return kernel32.GetLastError() == access_denied
        try:
            exit_code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return exit_code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def acquire_soak_lock(settings: Settings, *, run_id: str) -> Path:
    path = lock_path_for(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            existing_pid = int(existing.get("pid") or 0)
            if existing_pid and _pid_is_alive(existing_pid) and existing_pid != os.getpid():
                raise SoakLockError(
                    f"another_soak_runner_active:pid={existing_pid}:run_id={existing.get('runId')}"
                )
        except SoakLockError:
            raise
        except Exception:
            pass
    payload = {
        "pid": os.getpid(),
        "runId": run_id,
        "acquiredAt": time.time(),
        "network": settings.network,
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def release_soak_lock(path: Path | None) -> None:
    if path is None:
        return
    try:
        if not path.exists():
            return
        existing = json.loads(path.read_text(encoding="utf-8"))
        if int(existing.get("pid") or 0) not in {0, os.getpid()}:
            return
        path.unlink(missing_ok=True)
    except Exception:
        pass


def next_sequence_number(store: MarketStore, run_id: str) -> int:
    return store.next_testnet_soak_sequence(run_id)


def _status_from_exception(exc: Exception) -> str:
    name = type(exc).__name__.lower()
    if "timeout" in name:
        return "error"
    return "error"


def default_probe_algod(settings: Settings) -> dict:
    started = time.perf_counter()
    try:
        from algopulse.algorand import build_algod_client

        client = build_algod_client(settings)
        status = client.status()
        latest_round = int(status.get("last-round") or status.get("last_round") or 0)
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        if latest_round <= 0:
            return {
                "status": "error",
                "latencyMs": latency_ms,
                "latestRound": latest_round,
                "detail": "algod_round_unavailable",
            }
        return {
            "status": "ok",
            "latencyMs": latency_ms,
            "latestRound": latest_round,
            "detail": None,
        }
    except Exception as exc:
        return {
            "status": _status_from_exception(exc),
            "latencyMs": round((time.perf_counter() - started) * 1000, 3),
            "latestRound": None,
            "detail": type(exc).__name__,
        }


def default_probe_indexer(settings: Settings) -> dict:
    started = time.perf_counter()
    try:
        from algopulse.algorand import build_indexer_client

        client = build_indexer_client(settings)
        health = client.health()
        latest_round = int(
            health.get("round")
            or health.get("latest-round")
            or health.get("last-round")
            or 0
        )
        if latest_round <= 0:
            # Fallback: some Indexer deployments expose round via /v2/transactions limit 1
            try:
                tip = client.search_transactions(limit=1)
                latest_round = int((tip.get("current-round") or tip.get("current_round") or 0))
            except Exception:
                latest_round = 0
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        if latest_round <= 0:
            return {
                "status": "error",
                "latencyMs": latency_ms,
                "latestRound": None,
                "detail": "indexer_round_unavailable",
            }
        return {
            "status": "ok",
            "latencyMs": latency_ms,
            "latestRound": latest_round,
            "detail": None,
        }
    except Exception as exc:
        return {
            "status": _status_from_exception(exc),
            "latencyMs": round((time.perf_counter() - started) * 1000, 3),
            "latestRound": None,
            "detail": type(exc).__name__,
        }


def _connector_slice(scan: dict, name: str) -> dict:
    for item in scan.get("connector_health") or []:
        if str(item.get("connectorName") or "").lower() == name:
            return {
                "status": item.get("status") or "unavailable",
                "latencyMs": item.get("latencyMs"),
                "poolCount": int(item.get("poolCount") or 0),
                "detail": item.get("detail"),
            }
    return {"status": "unavailable", "latencyMs": None, "poolCount": 0, "detail": "not_in_scan"}


def _route_counts_from_scan_and_store(store: MarketStore, scan_started_at: float) -> dict:
    opportunities = store.list_opportunities(limit=200, public_delay_seconds=0, min_created_at=scan_started_at - 1)
    status_counts: Counter[str] = Counter()
    rejection_reasons: Counter[str] = Counter()
    for item in opportunities:
        status = str(item.get("status") or "unknown")
        status_counts[status] += 1
        if status not in {"approved"}:
            reason = str(item.get("skip_reason") or item.get("skipReason") or "unspecified")
            rejection_reasons[reason] += 1
    return {
        "routeCandidateCount": len(opportunities),
        "approvedRouteCount": int(status_counts.get("approved", 0)),
        "rejectedRouteCount": int(
            status_counts.get("rejected", 0)
            + status_counts.get("skipped", 0)
            + status_counts.get("blocked", 0)
        ),
        "waitRouteCount": int(status_counts.get("wait", 0) + status_counts.get("pending", 0)),
        "paperOnlyRouteCount": int(status_counts.get("paper", 0) + status_counts.get("paper_only", 0)),
        "rejectionReasons": [
            {"reason": reason, "count": count}
            for reason, count in sorted(rejection_reasons.items(), key=lambda pair: (-pair[1], pair[0]))
        ],
    }


def build_observation(
    *,
    settings: Settings,
    store: MarketStore,
    run_id: str,
    sequence_number: int,
    deps: SoakProbeDeps,
    now: float | None = None,
) -> dict:
    started_at = float(now if now is not None else time.time())
    source = observation_source_for_settings(settings)
    errors: list[str] = []
    degraded_reasons: list[str] = []

    try:
        algod = deps.probe_algod()
    except Exception as exc:
        algod = {
            "status": "error",
            "latencyMs": None,
            "latestRound": None,
            "detail": type(exc).__name__,
        }
        errors.append(f"algod:{type(exc).__name__}")

    try:
        indexer = deps.probe_indexer()
    except Exception as exc:
        indexer = {
            "status": "error",
            "latencyMs": None,
            "latestRound": None,
            "detail": type(exc).__name__,
        }
        errors.append(f"indexer:{type(exc).__name__}")

    scan: dict[str, Any] = {}
    try:
        scan = deps.run_scan() or {}
    except Exception as exc:
        errors.append(f"scanner:{type(exc).__name__}")
        scan = {
            "status": "error",
            "pools": 0,
            "opportunities": 0,
            "approved": 0,
            "paper_candidates": 0,
            "paper_rechecks_5s": 0,
            "paper_rechecks_30s": 0,
            "connector_health": [],
            "connector_error_count": 1,
            "connector_degraded_count": 0,
        }

    try:
        quotes = deps.quote_freshness() or {}
    except Exception as exc:
        errors.append(f"quotes:{type(exc).__name__}")
        quotes = {
            "quoteCount": 0,
            "freshCount": 0,
            "agingCount": 0,
            "staleCount": 0,
            "unavailableCount": 0,
            "source": "unavailable",
        }

    tinyman = _connector_slice(scan, "tinyman")
    pact = _connector_slice(scan, "pact")
    mock_slice = _connector_slice(scan, "mock")
    if source == "mock" and mock_slice["status"] != "unavailable":
        # Mock connector present — keep explicit mock labeling on DEX fields.
        tinyman = {
            "status": "mock",
            "latencyMs": mock_slice.get("latencyMs"),
            "poolCount": int(mock_slice.get("poolCount") or scan.get("pools") or 0),
            "detail": "mock_connector",
        }
        pact = {
            "status": "mock",
            "latencyMs": None,
            "poolCount": 0,
            "detail": "mock_connector",
        }

    scanner_status = str(scan.get("status") or "error")
    if scanner_status == "degraded":
        degraded_reasons.append("scanner_degraded")
    if tinyman.get("status") in {"error", "degraded"}:
        degraded_reasons.append(f"tinyman_{tinyman.get('status')}")
    if pact.get("status") in {"error", "degraded"}:
        degraded_reasons.append(f"pact_{pact.get('status')}")
    if algod.get("status") != "ok":
        errors.append(f"algod_{algod.get('detail') or algod.get('status')}")
    if indexer.get("status") != "ok":
        errors.append(f"indexer_{indexer.get('detail') or indexer.get('status')}")

    algod_round = algod.get("latestRound")
    indexer_round = indexer.get("latestRound")
    round_lag = None
    if isinstance(algod_round, int) and isinstance(indexer_round, int):
        round_lag = max(0, algod_round - indexer_round)
        if round_lag >= INDEXER_LAG_WAIT_ROUNDS and algod.get("status") == "ok":
            degraded_reasons.append("indexer_round_lag")

    route_counts = _route_counts_from_scan_and_store(store, started_at)
    if not route_counts["routeCandidateCount"] and scan.get("opportunities") is not None:
        route_counts["routeCandidateCount"] = int(scan.get("opportunities") or 0)
        route_counts["approvedRouteCount"] = int(scan.get("approved") or 0)

    component_statuses = [
        str(algod.get("status") or "unavailable"),
        str(indexer.get("status") or "unavailable"),
        str(tinyman.get("status") or "unavailable"),
        str(pact.get("status") or "unavailable"),
        scanner_status,
    ]
    if any(status == "error" for status in component_statuses) or degraded_reasons or errors:
        # Partial connector failure is degraded evidence, not fabricated success.
        if scanner_status == "error" and tinyman.get("status") == "error" and pact.get("status") == "error":
            observation_status = "error"
        elif any(status in {"error", "degraded"} for status in component_statuses) or degraded_reasons:
            observation_status = "degraded"
        else:
            observation_status = "error"
    else:
        observation_status = "ok"

    completed_at = time.time()
    observation_id = f"obs_{uuid.uuid4().hex[:16]}"
    observation = {
        "observationId": observation_id,
        "runId": run_id,
        "sequenceNumber": int(sequence_number),
        "startedAt": started_at,
        "completedAt": completed_at,
        "network": settings.network,
        "source": source,
        "status": observation_status,
        "algod": {
            "status": algod.get("status") or "unavailable",
            "latencyMs": algod.get("latencyMs"),
            "latestRound": algod_round,
            "detail": algod.get("detail"),
        },
        "indexer": {
            "status": indexer.get("status") or "unavailable",
            "latencyMs": indexer.get("latencyMs"),
            "latestRound": indexer_round,
            "roundLag": round_lag,
            "detail": indexer.get("detail"),
        },
        "tinyman": tinyman,
        "pact": pact,
        "scanner": {
            "status": scanner_status,
            "poolsObserved": int(scan.get("pools") or 0),
            "opportunities": int(scan.get("opportunities") or 0),
            "approved": int(scan.get("approved") or 0),
            "paperCandidates": int(scan.get("paper_candidates") or 0),
            "paperRechecks5s": int(scan.get("paper_rechecks_5s") or 0),
            "paperRechecks30s": int(scan.get("paper_rechecks_30s") or 0),
            "connectorErrorCount": int(scan.get("connector_error_count") or 0),
            "connectorDegradedCount": int(scan.get("connector_degraded_count") or 0),
        },
        "poolsObserved": int(scan.get("pools") or 0),
        "quotesObserved": int(quotes.get("quoteCount") or 0),
        "quoteFreshness": {
            "fresh": int(quotes.get("freshCount") or quotes.get("freshQuoteCount") or 0),
            "aging": int(quotes.get("agingCount") or quotes.get("agingQuoteCount") or 0),
            "stale": int(quotes.get("staleCount") or quotes.get("staleQuoteCount") or 0),
            "unavailable": int(quotes.get("unavailableCount") or quotes.get("unavailableQuoteCount") or 0),
            "source": quotes.get("source") or "unavailable",
        },
        "routes": route_counts,
        "paper": {
            "candidateCount": int(scan.get("paper_candidates") or 0),
            "recheckCompleted5s": int(scan.get("paper_rechecks_5s") or 0),
            "recheckCompleted30s": int(scan.get("paper_rechecks_30s") or 0),
        },
        "errors": sorted(set(errors)),
        "degradedReasons": sorted(set(degraded_reasons)),
        "productionReady": False,
        "liveExecutionLocked": True,
    }
    return observation


def persist_observation(store: MarketStore, observation: dict) -> dict:
    store.record_testnet_soak_observation(observation)
    return observation


def _live_observations(observations: list[dict]) -> list[dict]:
    return [item for item in observations if str(item.get("source") or "") == "live"]


def _longest_gap_seconds(observations: list[dict]) -> float:
    if len(observations) < 2:
        return 0.0
    ordered = sorted(float(item["completedAt"]) for item in observations)
    gaps = [ordered[index] - ordered[index - 1] for index in range(1, len(ordered))]
    return float(max(gaps) if gaps else 0.0)


def _algod_stale_blocker(live: list[dict], *, now: float) -> str | None:
    if not live:
        return None
    latest = live[-1]
    algod = latest.get("algod") or {}
    if algod.get("status") != "ok":
        return "stale_or_unhealthy_algod"
    rounds = [
        (item.get("algod") or {}).get("latestRound")
        for item in live
        if (item.get("algod") or {}).get("latestRound") is not None
    ]
    if len(rounds) < 2:
        return None
    # If the latest observation is older than the no-progress window and rounds never advanced.
    first_with_round = next((item for item in live if (item.get("algod") or {}).get("latestRound") is not None), None)
    last_with_round = next(
        (item for item in reversed(live) if (item.get("algod") or {}).get("latestRound") is not None),
        None,
    )
    if not first_with_round or not last_with_round:
        return None
    first_round = (first_with_round.get("algod") or {}).get("latestRound")
    last_round = (last_with_round.get("algod") or {}).get("latestRound")
    span = float(last_with_round["completedAt"]) - float(first_with_round["completedAt"])
    if span >= ALGOD_STALE_NO_PROGRESS_SECONDS and first_round == last_round:
        return "stale_algod_no_round_progress"
    # Also detect plateau ending at latest observation.
    recent = [item for item in live if now - float(item["completedAt"]) <= ALGOD_STALE_NO_PROGRESS_SECONDS]
    recent_rounds = [
        (item.get("algod") or {}).get("latestRound")
        for item in recent
        if (item.get("algod") or {}).get("latestRound") is not None
    ]
    if len(recent_rounds) >= 2 and len(set(recent_rounds)) == 1 and (now - float(recent[0]["completedAt"])) >= ALGOD_STALE_NO_PROGRESS_SECONDS:
        return "stale_algod_no_round_progress"
    return None


def _connector_status_counts(live: list[dict], key: str) -> dict[str, int]:
    """Roll connector statuses into ok / degraded / down (error maps to down)."""
    counts = {"ok": 0, "degraded": 0, "down": 0, "error": 0}
    for item in live:
        status = str((item.get(key) or {}).get("status") or "unavailable")
        if status == "ok":
            counts["ok"] += 1
        elif status == "degraded":
            counts["degraded"] += 1
        else:
            # error, down, unavailable, mock — remain visible as non-ok
            counts["down"] += 1
            counts["error"] += 1  # alias kept for existing consumers
    return counts


def build_soak_rollup(
    observations: list[dict],
    *,
    interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
    target_seconds: float = SOAK_TARGET_SECONDS,
    now: float | None = None,
    runner_state: str = "idle",
) -> dict:
    """Summarize stored soak observations into readiness rollup evidence.

    Live observations only count toward coverage. Mock never satisfies the 24h gate.
    productionReady is always false. Gate never passes before 24 real elapsed hours.
    """
    current_time = float(now if now is not None else time.time())
    ordered = sorted(observations, key=lambda item: float(item.get("completedAt") or 0.0))
    live = _live_observations(ordered)
    mock_count = sum(1 for item in ordered if item.get("source") == "mock")
    stored_count = sum(1 for item in ordered if item.get("source") == "stored")

    first_at = float(live[0]["completedAt"]) if live else None
    latest_at = float(live[-1]["completedAt"]) if live else None
    elapsed = 0.0 if first_at is None or latest_at is None else max(0.0, latest_at - first_at)
    expected = 0
    if live and interval_seconds > 0:
        expected = max(1, int(elapsed // interval_seconds) + 1)
    completed = len(live)
    coverage_percent = 0.0
    if target_seconds > 0:
        coverage_percent = min(100.0, (elapsed / target_seconds) * 100.0)

    scanner_ok = sum(1 for item in live if (item.get("scanner") or {}).get("status") == "ok")
    scanner_success_rate = 0.0 if completed <= 0 else scanner_ok / completed

    tinyman_counts = _connector_status_counts(live, "tinyman")
    pact_counts = _connector_status_counts(live, "pact")
    algod_counts = _connector_status_counts(live, "algod")
    indexer_counts = _connector_status_counts(live, "indexer")

    pools_observed = sum(int(item.get("poolsObserved") or 0) for item in live)
    quotes_observed = sum(int(item.get("quotesObserved") or 0) for item in live)
    fresh_quotes = sum(int((item.get("quoteFreshness") or {}).get("fresh") or 0) for item in live)
    aging_quotes = sum(int((item.get("quoteFreshness") or {}).get("aging") or 0) for item in live)
    stale_quotes = sum(int((item.get("quoteFreshness") or {}).get("stale") or 0) for item in live)
    fresh_quote_percent = 0.0 if quotes_observed <= 0 else (fresh_quotes / quotes_observed) * 100.0

    route_candidates = sum(int((item.get("routes") or {}).get("routeCandidateCount") or 0) for item in live)
    approved_routes = sum(int((item.get("routes") or {}).get("approvedRouteCount") or 0) for item in live)
    rejected_routes = sum(int((item.get("routes") or {}).get("rejectedRouteCount") or 0) for item in live)
    rejection_totals: Counter[str] = Counter()
    for item in live:
        for bucket in (item.get("routes") or {}).get("rejectionReasons") or []:
            rejection_totals[str(bucket.get("reason") or "unspecified")] += int(bucket.get("count") or 0)

    paper_candidates = sum(int((item.get("paper") or {}).get("candidateCount") or 0) for item in live)
    paper_5s = sum(int((item.get("paper") or {}).get("recheckCompleted5s") or 0) for item in live)
    paper_30s = sum(int((item.get("paper") or {}).get("recheckCompleted30s") or 0) for item in live)

    blockers: list[str] = []
    warnings: list[str] = []

    if completed <= 0:
        blockers.append("no_live_observations")
    if mock_count and completed <= 0:
        blockers.append("mock_observations_do_not_count_toward_live_coverage")
    if elapsed < target_seconds:
        blockers.append("elapsed_coverage_below_24h")
    # One-shot / single observation can never complete the 24h gate even if timestamps are equal.
    if completed == 1:
        if "elapsed_coverage_below_24h" not in blockers:
            blockers.append("elapsed_coverage_below_24h")
        warnings.append("one_shot_evidence_not_24h_completion")

    algod_blocker = _algod_stale_blocker(live, now=current_time)
    if algod_blocker:
        blockers.append(algod_blocker)
    if live and (live[-1].get("algod") or {}).get("status") != "ok":
        if "stale_or_unhealthy_algod" not in blockers:
            blockers.append("stale_or_unhealthy_algod")

    latest_indexer = (live[-1].get("indexer") if live else {}) or {}
    latest_algod = (live[-1].get("algod") if live else {}) or {}
    lag = latest_indexer.get("roundLag")
    if (
        live
        and latest_algod.get("status") == "ok"
        and latest_indexer.get("status") == "ok"
        and isinstance(lag, int)
        and lag >= INDEXER_LAG_WAIT_ROUNDS
    ):
        warnings.append("indexer_lag_while_algod_progresses")
    elif live and latest_algod.get("status") == "ok" and latest_indexer.get("status") != "ok":
        warnings.append("indexer_unhealthy_while_algod_ok")

    if paper_candidates <= 0 and paper_5s <= 0 and paper_30s <= 0:
        blockers.append("missing_paper_trading_evidence")
    if completed and (pact_counts["down"] + pact_counts["degraded"]) > 0:
        warnings.append("pact_degraded_or_down")
    if completed and tinyman_counts["down"] == completed:
        blockers.append("tinyman_unavailable_for_all_live_observations")
    if completed and (tinyman_counts["down"] + tinyman_counts["degraded"] + pact_counts["down"] + pact_counts["degraded"]) > 0:
        warnings.append("connector_failures_visible_in_rollup")

    longest_gap = _longest_gap_seconds(live)
    if interval_seconds > 0 and longest_gap > interval_seconds * 3:
        warnings.append("observation_gap_exceeds_3x_interval")

    # Gate cannot pass with any blocker, and never before 24 real hours.
    if blockers or elapsed < target_seconds:
        gate_status = "in_progress" if completed else "not_started"
        if "stale_or_unhealthy_algod" in blockers or "stale_algod_no_round_progress" in blockers:
            gate_status = "blocked"
        elif completed and elapsed < target_seconds:
            gate_status = "in_progress"
        elif completed and "missing_paper_trading_evidence" in blockers:
            gate_status = "in_progress"
    else:
        gate_status = "ready_for_review"

    # Hard rule: never complete before 24h regardless of other fields.
    if elapsed < target_seconds:
        if "elapsed_coverage_below_24h" not in blockers:
            blockers.append("elapsed_coverage_below_24h")
        if gate_status == "ready_for_review":
            gate_status = "in_progress"

    run_ids = sorted({str(item.get("runId")) for item in ordered if item.get("runId")})

    return {
        "phase": "Phase 3 - TestNet 24h Read-Only Soak",
        "runnerState": runner_state,
        "runIds": run_ids,
        "firstObservationAt": first_at,
        "latestObservationAt": latest_at,
        "elapsedCoverageSeconds": elapsed,
        "targetCoverageSeconds": float(target_seconds),
        "intervalSeconds": float(interval_seconds),
        "expectedObservationCount": expected,
        "completedObservationCount": completed,
        "totalStoredObservationCount": len(ordered),
        "mockObservationCount": mock_count,
        "storedObservationCount": stored_count,
        "coveragePercent": round(coverage_percent, 3),
        "longestGapSeconds": longest_gap,
        "scannerSuccessRate": round(scanner_success_rate, 4),
        "connectors": {
            "tinyman": tinyman_counts,
            "pact": pact_counts,
            "algod": algod_counts,
            "indexer": indexer_counts,
        },
        "poolsObserved": pools_observed,
        "quotesObserved": quotes_observed,
        "freshQuoteCount": fresh_quotes,
        "agingQuoteCount": aging_quotes,
        "staleQuoteCount": stale_quotes,
        "freshQuotePercent": round(fresh_quote_percent, 3),
        "routes": {
            "candidateCount": route_candidates,
            "approvedCount": approved_routes,
            "rejectedCount": rejected_routes,
            "rejectionReasons": [
                {"reason": reason, "count": count}
                for reason, count in sorted(rejection_totals.items(), key=lambda pair: (-pair[1], pair[0]))
            ],
        },
        "paper": {
            "candidateCount": paper_candidates,
            "recheckCompleted5s": paper_5s,
            "recheckCompleted30s": paper_30s,
            "coverage5s": 0.0 if paper_candidates <= 0 else min(1.0, paper_5s / paper_candidates),
            "coverage30s": 0.0 if paper_candidates <= 0 else min(1.0, paper_30s / paper_candidates),
        },
        "blockers": blockers,
        "warnings": warnings,
        "gateStatus": gate_status,
        "currentGateStatus": gate_status,
        "productionReady": False,
        "liveExecutionLocked": True,
        "source": "live" if completed else ("mock" if mock_count else "unavailable"),
        "evidenceSource": "stored_observations",
    }


def summarize_testnet_soak_readiness(
    store: MarketStore,
    *,
    interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
    target_seconds: float = SOAK_TARGET_SECONDS,
    now: float | None = None,
    runner_state: str = "idle",
) -> dict:
    """Service entrypoint: roll up observations already stored by the soak runner."""
    observations = store.list_testnet_soak_observations(limit=MAX_OBSERVATION_LIMIT)
    return build_soak_rollup(
        observations,
        interval_seconds=interval_seconds,
        target_seconds=target_seconds,
        now=now,
        runner_state=runner_state,
    )


def public_safe_observation(observation: dict) -> dict:
    """Return a copy with only operational public-safe fields."""
    return {
        "observationId": observation.get("observationId"),
        "runId": observation.get("runId"),
        "sequenceNumber": observation.get("sequenceNumber"),
        "startedAt": observation.get("startedAt"),
        "completedAt": observation.get("completedAt"),
        "network": observation.get("network"),
        "source": observation.get("source"),
        "status": observation.get("status"),
        "algod": observation.get("algod") or {},
        "indexer": observation.get("indexer") or {},
        "tinyman": observation.get("tinyman") or {},
        "pact": observation.get("pact") or {},
        "scanner": observation.get("scanner") or {},
        "poolsObserved": observation.get("poolsObserved"),
        "quotesObserved": observation.get("quotesObserved"),
        "quoteFreshness": observation.get("quoteFreshness") or {},
        "routes": {
            "routeCandidateCount": (observation.get("routes") or {}).get("routeCandidateCount"),
            "approvedRouteCount": (observation.get("routes") or {}).get("approvedRouteCount"),
            "rejectedRouteCount": (observation.get("routes") or {}).get("rejectedRouteCount"),
            "waitRouteCount": (observation.get("routes") or {}).get("waitRouteCount"),
            "paperOnlyRouteCount": (observation.get("routes") or {}).get("paperOnlyRouteCount"),
            "rejectionReasons": (observation.get("routes") or {}).get("rejectionReasons") or [],
        },
        "paper": observation.get("paper") or {},
        "errors": observation.get("errors") or [],
        "degradedReasons": observation.get("degradedReasons") or [],
        "productionReady": False,
        "liveExecutionLocked": True,
    }


def contains_forbidden_evidence(payload: Any) -> list[str]:
    """Flag dangerous key names or explicit secret-like values in API evidence."""
    hits: list[str] = []

    def walk(value: Any, key_path: str = "") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lower_key = str(key).lower()
                path = f"{key_path}.{lower_key}" if key_path else lower_key
                for token in FORBIDDEN_EVIDENCE_TOKENS:
                    if token == lower_key or token in lower_key.replace("-", "_"):
                        hits.append(path)
                        break
                walk(child, path)
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{key_path}[{index}]")
            return
        if isinstance(value, str):
            lowered = value.lower()
            for token in FORBIDDEN_EVIDENCE_TOKENS:
                if token in {"seed", "secret"}:
                    continue
                if token in lowered:
                    hits.append(f"{key_path}:{token}")

    walk(payload)
    return sorted(set(hits))


def build_default_deps(settings: Settings, store: MarketStore, scanner) -> SoakProbeDeps:
    return SoakProbeDeps(
        probe_algod=lambda: default_probe_algod(settings),
        probe_indexer=lambda: default_probe_indexer(settings),
        run_scan=scanner.run_once,
        quote_freshness=lambda: store.quote_freshness_evidence(
            max_age_seconds=settings.max_route_age_seconds,
            limit=50,
        ),
    )


def run_once(
    *,
    settings: Settings,
    store: MarketStore,
    run_id: str | None = None,
    deps: SoakProbeDeps | None = None,
    scanner=None,
    acquire_lock: bool = True,
) -> dict:
    assert_safe_to_run(settings)
    store.initialize(run_backfills=False)
    active_run_id = run_id or f"soak_{uuid.uuid4().hex[:12]}"
    lock: Path | None = None
    if acquire_lock:
        lock = acquire_soak_lock(settings, run_id=active_run_id)
    try:
        if deps is None:
            if scanner is None:
                from algopulse.scanner import MarketScanner

                scanner = MarketScanner(settings=settings, store=store)
            deps = build_default_deps(settings, store, scanner)
        sequence = next_sequence_number(store, active_run_id)
        observation = build_observation(
            settings=settings,
            store=store,
            run_id=active_run_id,
            sequence_number=sequence,
            deps=deps,
        )
        persist_observation(store, observation)
        return observation
    finally:
        if acquire_lock:
            release_soak_lock(lock)


def run_soak(
    *,
    settings: Settings,
    store: MarketStore,
    duration_hours: float,
    interval_seconds: float,
    run_id: str | None = None,
    deps: SoakProbeDeps | None = None,
    scanner=None,
    sleep_fn: Callable[[float], None] = time.sleep,
    should_stop: Callable[[], bool] | None = None,
) -> dict:
    assert_safe_to_run(settings)
    if interval_seconds < MIN_INTERVAL_SECONDS:
        raise SoakSafetyError(f"interval_below_minimum_{MIN_INTERVAL_SECONDS}")
    store.initialize(run_backfills=False)
    active_run_id = run_id or f"soak_{uuid.uuid4().hex[:12]}"
    lock = acquire_soak_lock(settings, run_id=active_run_id)
    stop_requested = {"value": False}

    def _handle_signal(_signum, _frame) -> None:
        stop_requested["value"] = True

    previous_sigint = signal.getsignal(signal.SIGINT)
    try:
        signal.signal(signal.SIGINT, _handle_signal)
    except Exception:
        previous_sigint = None

    if deps is None:
        if scanner is None:
            from algopulse.scanner import MarketScanner

            scanner = MarketScanner(settings=settings, store=store)
        deps = build_default_deps(settings, store, scanner)

    deadline = time.time() + max(0.0, float(duration_hours) * 3600.0)
    completed = 0
    last_observation: dict | None = None
    try:
        while True:
            if stop_requested["value"] or (should_stop and should_stop()):
                break
            sequence = next_sequence_number(store, active_run_id)
            last_observation = build_observation(
                settings=settings,
                store=store,
                run_id=active_run_id,
                sequence_number=sequence,
                deps=deps,
            )
            persist_observation(store, last_observation)
            completed += 1
            if time.time() >= deadline:
                break
            if stop_requested["value"] or (should_stop and should_stop()):
                break
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            sleep_fn(min(interval_seconds, remaining))
    finally:
        release_soak_lock(lock)
        if previous_sigint is not None:
            try:
                signal.signal(signal.SIGINT, previous_sigint)
            except Exception:
                pass

    observations = store.list_testnet_soak_observations(limit=MAX_OBSERVATION_LIMIT)
    rollup = build_soak_rollup(
        observations,
        interval_seconds=interval_seconds,
        runner_state="stopped",
    )
    return {
        "runId": active_run_id,
        "completedObservations": completed,
        "lastObservation": public_safe_observation(last_observation) if last_observation else None,
        "rollup": rollup,
        "productionReady": False,
        "liveExecutionLocked": True,
    }


def build_testnet_soak_summary(
    store: MarketStore,
    settings: Settings,
    *,
    interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
) -> dict:
    runner_state = "idle"
    lock = lock_path_for(settings)
    if lock.exists():
        try:
            payload = json.loads(lock.read_text(encoding="utf-8"))
            pid = int(payload.get("pid") or 0)
            runner_state = "running" if pid and _pid_is_alive(pid) else "stale_lock"
        except Exception:
            runner_state = "unknown"
    rollup = summarize_testnet_soak_readiness(
        store,
        interval_seconds=interval_seconds,
        runner_state=runner_state,
    )
    observations = store.list_testnet_soak_observations(limit=MAX_OBSERVATION_LIMIT, newest_first=True)
    latest = public_safe_observation(observations[0]) if observations else None
    return {
        **rollup,
        "latestObservation": latest,
        "network": settings.network,
        "productionReady": False,
        "liveExecutionLocked": True,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AlgoPulse Phase 3 TestNet read-only soak runner (no signing, no submission)."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single observation and exit.",
    )
    parser.add_argument(
        "--duration-hours",
        type=float,
        default=24.0,
        help="Bounded soak duration in hours (default 24).",
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=DEFAULT_INTERVAL_SECONDS,
        help=f"Seconds between observations (default {DEFAULT_INTERVAL_SECONDS}).",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Optional stable run id for restart continuity.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    store = MarketStore(settings.database_path)
    try:
        if args.once:
            observation = run_once(settings=settings, store=store, run_id=args.run_id)
            print(json.dumps(public_safe_observation(observation), indent=2, sort_keys=True))
            return 0
        result = run_soak(
            settings=settings,
            store=store,
            duration_hours=args.duration_hours,
            interval_seconds=args.interval_seconds,
            run_id=args.run_id,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except SoakSafetyError as exc:
        print(json.dumps({"ok": False, "error": "soak_safety", "detail": str(exc)}, indent=2))
        return 2
    except SoakLockError as exc:
        print(json.dumps({"ok": False, "error": "soak_lock", "detail": str(exc)}, indent=2))
        return 3
    except KeyboardInterrupt:
        print(json.dumps({"ok": False, "error": "interrupted", "detail": "graceful_stop"}, indent=2))
        return 130


if __name__ == "__main__":
    sys.exit(main())
