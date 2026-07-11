from __future__ import annotations

import argparse
import json
import signal
import sys
import time
import uuid
from collections.abc import Callable
from pathlib import Path

from algopulse.config import Settings, get_settings
from algopulse.live_pool_scanner import run_live_scan_cycle
from algopulse.readonly_safety import ReadonlySafetyError, assert_mainnet_readonly_safe
from algopulse.store import MarketStore


LOCK_FILENAME = "mainnet_readonly_collector.lock"
DEFAULT_INTERVAL_SECONDS = 60
DEFAULT_DURATION_HOURS = 24


def lock_path_for(settings: Settings) -> Path:
    return Path(settings.data_dir) / LOCK_FILENAME


def _pid_is_alive(pid: int) -> bool:
    import os

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


def acquire_collector_lock(settings: Settings, *, run_id: str) -> Path:
    import os

    path = lock_path_for(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            existing_pid = int(existing.get("pid") or 0)
            if existing_pid and _pid_is_alive(existing_pid) and existing_pid != os.getpid():
                raise ReadonlySafetyError(
                    f"another_mainnet_readonly_collector_active:pid={existing_pid}:run_id={existing.get('runId')}"
                )
        except ReadonlySafetyError:
            raise
        except Exception:
            pass
    path.write_text(
        json.dumps({"pid": os.getpid(), "runId": run_id, "acquiredAt": time.time(), "mode": "mainnet-readonly"}, sort_keys=True),
        encoding="utf-8",
    )
    return path


def release_collector_lock(path: Path | None) -> None:
    import os

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


def run_mainnet_readonly_cycle(
    *,
    settings: Settings | None = None,
    store: MarketStore | None = None,
    perform_rechecks: bool = True,
    recheck_delays: tuple[float, float] = (5.5, 25.0),
    sleep_fn: Callable[[float], None] = time.sleep,
    now_fn: Callable[[], float] = time.time,
    scanner=None,
) -> dict:
    """One fail-closed MainNet read-only research cycle (no keys, no signing)."""
    active = settings or get_settings()
    assert_mainnet_readonly_safe(active)
    active_store = store or MarketStore(active.database_path)
    # Live pool scanner + liquidity-aware paper evaluation (verified registry).
    result = run_live_scan_cycle(
        settings=active,
        store=active_store,
        perform_rechecks=perform_rechecks,
        recheck_delays=recheck_delays,
        sleep_fn=sleep_fn,
        now_fn=now_fn,
        scanner=scanner,
    )
    result["mode"] = "mainnet-readonly"
    result["controlRoomHint"] = (
        "Open the dashboard as local-review admin and inspect Control Room: "
        "pipeline, connectors, paper scoreboard, rejections, environment (network=mainnet)."
    )
    return result


def run_mainnet_readonly_collector(
    *,
    settings: Settings | None = None,
    store: MarketStore | None = None,
    duration_hours: float = DEFAULT_DURATION_HOURS,
    interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
    perform_rechecks: bool = True,
    sleep_fn: Callable[[float], None] = time.sleep,
    now_fn: Callable[[], float] = time.time,
    should_stop: Callable[[], bool] | None = None,
) -> dict:
    """Continuous MainNet read-only paper collector for a bounded duration (default 24h)."""
    active = settings or get_settings()
    assert_mainnet_readonly_safe(active)
    if interval_seconds < 15:
        raise ReadonlySafetyError("interval_below_minimum_15")
    active_store = store or MarketStore(active.database_path)
    active_store.initialize(run_backfills=False)

    run_id = f"mainnet_ro_{uuid.uuid4().hex[:12]}"
    lock = acquire_collector_lock(active, run_id=run_id)

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
            last_result = run_mainnet_readonly_cycle(
                settings=active,
                store=active_store,
                perform_rechecks=perform_rechecks,
                sleep_fn=sleep_fn,
                now_fn=now_fn,
            )
            cycles += 1
            active_store.record_service_health(
                "mainnet_readonly_collector",
                "ok" if last_result.get("outcome") else "degraded",
                detail=str(last_result.get("outcome") or "cycle"),
                metrics={
                    "runId": run_id,
                    "cycle": cycles,
                    "outcome": last_result.get("outcome"),
                    "selectedPair": last_result.get("selectedPair"),
                    "opportunityCount": last_result.get("opportunityCount"),
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
        release_collector_lock(lock)
        if previous_sigint is not None:
            try:
                signal.signal(signal.SIGINT, previous_sigint)
            except Exception:
                pass

    return {
        "runId": run_id,
        "mode": "mainnet-readonly",
        "cyclesCompleted": cycles,
        "durationHours": float(duration_hours),
        "intervalSeconds": float(interval_seconds),
        "lastResult": last_result,
        "productionReady": False,
        "liveExecutionLocked": True,
        "status": "stopped",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AlgoPulse MainNet READ-ONLY staging (no keys, no signing, no submission)."
    )
    parser.add_argument("--once", action="store_true", help="Run a single MainNet read-only cycle.")
    parser.add_argument(
        "--duration-hours",
        type=float,
        default=DEFAULT_DURATION_HOURS,
        help="Collector duration in hours (default 24).",
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=DEFAULT_INTERVAL_SECONDS,
        help="Seconds between collector cycles (default 60).",
    )
    parser.add_argument(
        "--skip-rechecks",
        action="store_true",
        help="Skip T+5/T+30 waits inside each cycle.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.once or (args.duration_hours <= 0):
            result = run_mainnet_readonly_cycle(perform_rechecks=not args.skip_rechecks)
            print(json.dumps(result, indent=2, sort_keys=True, default=str))
            return 0
        result = run_mainnet_readonly_collector(
            duration_hours=args.duration_hours,
            interval_seconds=args.interval_seconds,
            perform_rechecks=not args.skip_rechecks,
        )
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        return 0
    except ReadonlySafetyError as exc:
        print(json.dumps({"ok": False, "error": "mainnet_readonly_safety", "detail": str(exc)}, indent=2))
        return 2
    except KeyboardInterrupt:
        print(json.dumps({"ok": False, "error": "interrupted", "detail": "graceful_stop"}, indent=2))
        return 130
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "detail": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
