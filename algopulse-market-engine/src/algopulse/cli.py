from __future__ import annotations

import argparse
import json
import time

from algopulse.config import get_settings
from algopulse.demo import run_five_to_ten_demo
from algopulse.readiness import build_live_readiness_report
from algopulse.scanner import MarketScanner
from algopulse.store import MarketStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AlgoPulse Phase 0 market engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Run scanner cycles")
    scan.add_argument("--cycles", type=int, default=1)
    scan.add_argument("--loop", action="store_true")
    scan.add_argument("--interval", type=float, default=None)

    worker = subparsers.add_parser("worker", help="Run the scanner worker")
    worker.add_argument("--loop", action="store_true")
    worker.add_argument("--execute-approved", action="store_true")
    worker.add_argument("--interval", type=float, default=None)

    subparsers.add_parser("pulse", help="Print current market pulse")
    subparsers.add_parser("execute-best", help="Build or execute the best approved route")
    subparsers.add_parser("demo-run", help="Print the synthetic 5 ALGO to 10 ALGO pipeline proof")

    readiness = subparsers.add_parser("readiness", help="Print live-market readiness preflight")
    readiness.add_argument("--scan", action="store_true", help="Run a fresh market scan before reporting")
    readiness.add_argument(
        "--no-execution-plan",
        action="store_true",
        help="Skip building the safe atomic dry-run plan",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = get_settings()
    store = MarketStore(settings.database_path)
    store.initialize()
    scanner = MarketScanner(settings=settings, store=store)

    if args.command == "pulse":
        print(json.dumps(store.get_pulse(settings.public_delay_seconds), indent=2))
        return

    if args.command == "execute-best":
        result = scanner.execute_best_once()
        print(json.dumps(result, indent=2))
        return

    if args.command == "demo-run":
        print(json.dumps(run_five_to_ten_demo(), indent=2))
        return

    if args.command == "readiness":
        result = build_live_readiness_report(
            settings=scanner.settings,
            store=store,
            scanner=scanner,
            run_scan=args.scan,
            build_execution_plan=not args.no_execution_plan,
        )
        print(json.dumps(result, indent=2))
        return

    if args.command == "scan":
        interval = args.interval if args.interval is not None else settings.scanner_interval_seconds
        cycles = 0
        while True:
            result = scanner.run_once()
            print(json.dumps(result, indent=2))
            cycles += 1
            if not args.loop and cycles >= args.cycles:
                return
            time.sleep(interval)

    if args.command == "worker":
        interval = args.interval if args.interval is not None else settings.scanner_interval_seconds
        while True:
            result = scanner.execute_best_once() if args.execute_approved else scanner.run_once()
            print(json.dumps(result, indent=2))
            if not args.loop:
                return
            time.sleep(interval)


if __name__ == "__main__":
    main()
