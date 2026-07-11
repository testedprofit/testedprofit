from __future__ import annotations

import algopulse.api as api_module
from algopulse.store import MarketStore


def test_initial_scan_failure_is_recorded_without_raising(monkeypatch):
    recorded: dict = {}

    def fail_scan() -> dict:
        raise TimeoutError("connector timed out")

    def record_health(service_name: str, status: str, *, detail=None, metrics=None) -> None:
        recorded.update(
            serviceName=service_name,
            status=status,
            detail=detail,
            metrics=metrics,
        )

    monkeypatch.setattr(api_module.scanner, "run_once", fail_scan)
    monkeypatch.setattr(api_module.store, "record_service_health", record_health)

    api_module._run_initial_scan_safely()

    assert recorded == {
        "serviceName": "market_scanner",
        "status": "error",
        "detail": "initial_scan_failed",
        "metrics": {"errorType": "TimeoutError"},
    }


def test_api_store_initialization_can_skip_historical_backfills(tmp_path, monkeypatch):
    store = MarketStore(tmp_path / "market.db")

    def fail_backfill(_connection) -> None:
        raise AssertionError("historical backfill must not run on the API startup path")

    monkeypatch.setattr(store, "_backfill_opportunity_breakdowns", fail_backfill)
    monkeypatch.setattr(store, "_backfill_paper_calibration", fail_backfill)
    monkeypatch.setattr(store, "_backfill_opportunity_decay", fail_backfill)
    monkeypatch.setattr(store, "_backfill_route_forensics", fail_backfill)

    store.initialize(run_backfills=False)

    assert store.has_market_data() is False
