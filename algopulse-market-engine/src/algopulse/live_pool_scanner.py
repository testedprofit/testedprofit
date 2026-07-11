"""Continuous MainNet/TestNet read-only live pool scanner.

Independent of the browser. Polls Tinyman/Pact, persists real pool snapshots,
drives liquidity-aware paper evaluation, and never fabricates pools.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import threading
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from algopulse.config import Settings, get_settings
from algopulse.paper_arb_loop import run_paper_arb_loop
from algopulse.readonly_safety import ReadonlySafetyError, assert_readonly_profile_safe
from algopulse.scanner import MarketScanner
from algopulse.store import MarketStore


LOCK_FILENAME = "live_pool_scanner.lock"
DEFAULT_INTERVAL_SECONDS = 60
DEFAULT_DURATION_HOURS = 24


def lock_path_for(settings: Settings) -> Path:
    return Path(settings.data_dir) / LOCK_FILENAME


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def acquire_scanner_lock(settings: Settings, *, run_id: str) -> Path:
    path = lock_path_for(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            existing_pid = int(existing.get("pid") or 0)
            if existing_pid and _pid_is_alive(existing_pid) and existing_pid != os.getpid():
                raise ReadonlySafetyError(
                    f"another_live_pool_scanner_active:pid={existing_pid}:run_id={existing.get('runId')}"
                )
        except ReadonlySafetyError:
            raise
        except Exception:
            pass
    path.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "runId": run_id,
                "acquiredAt": time.time(),
                "mode": "live_pool_scanner",
                "intervalSeconds": DEFAULT_INTERVAL_SECONDS,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def release_scanner_lock(path: Path | None) -> None:
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


def run_live_scan_cycle(
    *,
    settings: Settings | None = None,
    store: MarketStore | None = None,
    perform_rechecks: bool = False,
    recheck_delays: tuple[float, float] = (5.5, 25.0),
    sleep_fn: Callable[[float], None] = time.sleep,
    now_fn: Callable[[], float] = time.time,
    scanner: MarketScanner | None = None,
) -> dict:
    """One live pool scan + liquidity-aware paper evaluation cycle (no signing)."""
    active = settings or get_settings()
    assert_readonly_profile_safe(active)
    active_store = store or MarketStore(active.database_path)
    active_store.initialize(run_backfills=False)

    result = run_paper_arb_loop(
        settings=active,
        store=active_store,
        perform_rechecks=perform_rechecks,
        recheck_delays=recheck_delays,
        sleep_fn=sleep_fn,
        now_fn=now_fn,
        scanner=scanner,
    )
    result["mode"] = "live_pool_scanner"
    result["scannerIndependentOfBrowser"] = True
    result["walletRequired"] = False
    result["signingEnabled"] = False
    result["submissionEnabled"] = False
    result["productionReady"] = False

    # Explicit live-scanner health for Control Room / radar recovery after restarts.
    pools = int((result.get("scan") or {}).get("pools") or 0)
    active_store.record_service_health(
        "live_pool_scanner",
        "ok" if pools > 0 else "degraded",
        detail=str(result.get("outcome") or "cycle"),
        metrics={
            "pools": pools,
            "opportunityCount": result.get("opportunityCount"),
            "approvedCount": result.get("approvedCount"),
            "selectedPair": result.get("selectedPair"),
            "snapshotCountHint": pools,
            "blockRounds": sorted(
                {
                    int(p.get("blockRound") or 0)
                    for p in (result.get("poolsInspected") or [])
                    if int(p.get("blockRound") or 0) > 0
                }
            ),
            "outcome": result.get("outcome"),
            "productionReady": False,
        },
    )
    return result


def run_live_scanner_loop(
    *,
    settings: Settings | None = None,
    store: MarketStore | None = None,
    duration_hours: float = DEFAULT_DURATION_HOURS,
    interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
    perform_rechecks: bool = False,
    sleep_fn: Callable[[float], None] = time.sleep,
    now_fn: Callable[[], float] = time.time,
    should_stop: Callable[[], bool] | None = None,
) -> dict:
    """Continuous live pool scanner (default 60s interval, browser-independent)."""
    active = settings or get_settings()
    assert_readonly_profile_safe(active)
    if interval_seconds < 15:
        raise ReadonlySafetyError("interval_below_minimum_15")
    active_store = store or MarketStore(active.database_path)
    active_store.initialize(run_backfills=False)

    run_id = f"live_scan_{uuid.uuid4().hex[:12]}"
    lock = acquire_scanner_lock(active, run_id=run_id)
    stop_requested = {"value": False}

    def _handle_signal(_signum, _frame) -> None:
        stop_requested["value"] = True

    previous_sigint = signal.getsignal(signal.SIGINT)
    try:
        signal.signal(signal.SIGINT, _handle_signal)
    except Exception:
        previous_sigint = None

    deadline = now_fn() + max(0.0, float(duration_hours) * 3600.0)
    cycles = 0
    last_result: dict | None = None
    try:
        while True:
            if stop_requested["value"] or (should_stop and should_stop()):
                break
            last_result = run_live_scan_cycle(
                settings=active,
                store=active_store,
                perform_rechecks=perform_rechecks,
                sleep_fn=sleep_fn,
                now_fn=now_fn,
            )
            cycles += 1
            active_store.record_service_health(
                "live_pool_scanner_loop",
                "ok",
                detail=str((last_result or {}).get("outcome") or "cycle"),
                metrics={
                    "runId": run_id,
                    "cycle": cycles,
                    "outcome": (last_result or {}).get("outcome"),
                    "pools": (last_result or {}).get("scan", {}).get("pools"),
                    "selectedPair": (last_result or {}).get("selectedPair"),
                    "opportunityCount": (last_result or {}).get("opportunityCount"),
                    "intervalSeconds": interval_seconds,
                    "productionReady": False,
                },
            )
            if now_fn() >= deadline:
                break
            remaining = deadline - now_fn()
            if remaining <= 0:
                break
            sleep_fn(min(interval_seconds, remaining))
            if stop_requested["value"] or (should_stop and should_stop()):
                break
    finally:
        release_scanner_lock(lock)
        if previous_sigint is not None:
            try:
                signal.signal(signal.SIGINT, previous_sigint)
            except Exception:
                pass

    return {
        "runId": run_id,
        "mode": "live_pool_scanner",
        "cyclesCompleted": cycles,
        "durationHours": float(duration_hours),
        "intervalSeconds": float(interval_seconds),
        "lastResult": last_result,
        "productionReady": False,
        "liveExecutionLocked": True,
        "walletRequired": False,
        "status": "stopped",
    }


class BackgroundLiveScanner:
    """Daemon-thread scanner for API process recovery (optional, lock-aware)."""

    def __init__(
        self,
        settings: Settings,
        store: MarketStore,
        *,
        interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
    ) -> None:
        self.settings = settings
        self.store = store
        self.interval_seconds = max(15.0, float(interval_seconds))
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock_path: Path | None = None

    def start(self) -> bool:
        if self._thread and self._thread.is_alive():
            return False
        try:
            assert_readonly_profile_safe(self.settings)
        except ReadonlySafetyError:
            # Non-readonly profiles: still allow pool-only scans via MarketScanner.
            pass
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="algopulse-live-pool-scanner", daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop.set()
        release_scanner_lock(self._lock_path)
        self._lock_path = None

    def _run(self) -> None:
        run_id = f"bg_scan_{uuid.uuid4().hex[:10]}"
        try:
            self._lock_path = acquire_scanner_lock(self.settings, run_id=run_id)
        except ReadonlySafetyError as exc:
            self.store.record_service_health(
                "live_pool_scanner",
                "degraded",
                detail=str(exc),
                metrics={"background": True},
            )
            return
        while not self._stop.is_set():
            try:
                try:
                    assert_readonly_profile_safe(self.settings)
                    run_live_scan_cycle(
                        settings=self.settings,
                        store=self.store,
                        perform_rechecks=False,
                    )
                except ReadonlySafetyError:
                    scanner = MarketScanner(settings=self.settings, store=self.store)
                    scanner.run_once()
            except Exception as exc:
                self.store.record_service_health(
                    "live_pool_scanner",
                    "error",
                    detail=type(exc).__name__,
                    metrics={"background": True},
                )
            self._stop.wait(self.interval_seconds)
        release_scanner_lock(self._lock_path)
        self._lock_path = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AlgoPulse live pool scanner (read-only, browser-independent, no signing)."
    )
    parser.add_argument("--once", action="store_true", help="Run a single scan cycle.")
    parser.add_argument("--duration-hours", type=float, default=DEFAULT_DURATION_HOURS)
    parser.add_argument("--interval-seconds", type=float, default=DEFAULT_INTERVAL_SECONDS)
    parser.add_argument(
        "--perform-rechecks",
        action="store_true",
        help="Perform T+5/T+30 waits inside each cycle (slow).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.once or args.duration_hours <= 0:
            result = run_live_scan_cycle(perform_rechecks=bool(args.perform_rechecks))
            print(json.dumps(result, indent=2, sort_keys=True, default=str))
            return 0
        result = run_live_scanner_loop(
            duration_hours=args.duration_hours,
            interval_seconds=args.interval_seconds,
            perform_rechecks=bool(args.perform_rechecks),
        )
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        return 0
    except ReadonlySafetyError as exc:
        print(json.dumps({"ok": False, "error": "readonly_safety", "detail": str(exc)}, indent=2))
        return 2
    except KeyboardInterrupt:
        print(json.dumps({"ok": False, "error": "interrupted"}, indent=2))
        return 130
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "detail": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
