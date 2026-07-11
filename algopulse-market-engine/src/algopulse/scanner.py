from __future__ import annotations

from dataclasses import replace
import threading
import time

from algopulse.config import Settings
from algopulse.connectors import MockMarketConnector, PactConnector, TinymanConnector
from algopulse.connectors.base import MarketConnector
from algopulse.engine import RouteEngine
from algopulse.risk import RiskEngine, policy_from_settings
from algopulse.store import MarketStore
from algopulse.vestige import VestigeDiscovery


ROUTING_ANCHOR_PAIRS = ((0, 31566704),)


class MarketScanner:
    def __init__(self, settings: Settings, store: MarketStore) -> None:
        self.discovery_report: dict | None = None
        self.settings = self._settings_with_discovered_pairs(settings)
        self.store = store
        self.connectors = self._build_connectors()
        self.risk_engine = RiskEngine(policy_from_settings(self.settings))
        self.route_engine = RouteEngine(risk_engine=self.risk_engine, trade_sizes=list(self.settings.trade_sizes))
        self._live_executor = None
        self._execution_slots = threading.BoundedSemaphore(max(1, self.settings.max_concurrent_execution))

    def collect_pools(self) -> dict:
        """Discover and persist real connector pools only (no fabricated routes).

        Continues with degraded status when one connector fails.
        """
        self.store.initialize(run_backfills=False)
        assets = []
        venues = []
        pools = []
        connector_health = []
        for connector in self.connectors:
            started_at = time.perf_counter()
            connector_assets = []
            connector_venues = []
            connector_pools = []
            try:
                connector_assets = connector.list_assets()
                connector_venues = connector.list_venues()
                connector_pools = connector.list_pools()
                evidence_builder = getattr(connector, "health_evidence", None)
                evidence = evidence_builder() if callable(evidence_builder) else {}
                status = str(evidence.get("status") or "ok")
                detail = evidence.get("detail")
                metrics = dict(evidence.get("metrics") or {})
            except Exception as exc:
                status = "error"
                detail = "connector_call_failed"
                metrics = {"errorTypes": [type(exc).__name__]}

            if status not in {"ok", "degraded", "error"}:
                status = "error"
                detail = "connector_health_status_invalid"
            metrics.update(
                {
                    "connector": connector.name,
                    "connectorType": "dex",
                    "latencyMs": float(metrics.get("latencyMs") or (time.perf_counter() - started_at) * 1000),
                    "assetCount": len(connector_assets),
                    "venueCount": len(connector_venues),
                    "poolCount": len(connector_pools),
                }
            )
            self.store.record_service_health(
                f"connector:{connector.name}",
                status,
                detail=detail,
                metrics=metrics,
            )
            connector_health.append(
                {
                    "connectorName": connector.name,
                    "status": status,
                    "detail": detail,
                    "latencyMs": round(float(metrics["latencyMs"]), 3),
                    "poolCount": len(connector_pools),
                }
            )
            assets.extend(connector_assets)
            venues.extend(connector_venues)
            pools.extend(connector_pools)

        self.store.upsert_assets(assets)
        self.store.upsert_venues(venues)
        self.store.record_pool_snapshots(pools)
        paper_updates = self.store.update_due_paper_trades(pools)

        connector_error_count = sum(1 for item in connector_health if item["status"] == "error")
        connector_degraded_count = sum(1 for item in connector_health if item["status"] == "degraded")
        if connector_health and connector_error_count == len(connector_health):
            scanner_status = "error"
        elif connector_error_count or connector_degraded_count:
            scanner_status = "degraded"
        else:
            scanner_status = "ok"

        return {
            "captured_at": time.time(),
            "connectors": [connector.name for connector in self.connectors],
            "connector_health": connector_health,
            "connector_error_count": connector_error_count,
            "connector_degraded_count": connector_degraded_count,
            "status": scanner_status,
            "target_asset_id": self.settings.target_asset_id,
            "asset_pairs": [list(pair) for pair in self.settings.asset_pairs],
            "discovery": self.discovery_report,
            "assets": len({asset.asset_id for asset in assets}),
            "venues": len({venue.venue_id for venue in venues}),
            "pools": len(pools),
            "pool_objects": pools,
            "paper_rechecks_5s": paper_updates["checked_5s"],
            "paper_rechecks_30s": paper_updates["checked_30s"],
            "paper_recheck_errors": paper_updates["errors"],
        }

    def run_once(self) -> dict:
        collected = self.collect_pools()
        pools = list(collected.pop("pool_objects", []) or [])

        # Paper-only verified registry for readonly profiles — never mutates execution allowlists.
        paper_verified_app_ids: tuple[int, ...] = ()
        env = str(getattr(self.settings, "env", "") or "").strip().lower()
        if env in {"mainnet-readonly", "mainnet_readonly", "staging", "testnet"} and pools:
            try:
                from algopulse.verified_pool_registry import build_verified_pool_registry

                registry = build_verified_pool_registry(
                    pools,
                    settings=self.settings,
                    store=self.store,
                )
                paper_verified_app_ids = tuple(
                    int(app_id) for app_id in (registry.get("acceptedAppIds") or []) if int(app_id) > 0
                )
                if paper_verified_app_ids:
                    self.risk_engine = RiskEngine(
                        policy_from_settings(self.settings, paper_verified_app_ids=paper_verified_app_ids)
                    )
                    self.route_engine = RouteEngine(
                        risk_engine=self.risk_engine,
                        trade_sizes=list(self.settings.trade_sizes),
                    )
            except Exception:
                paper_verified_app_ids = ()

        opportunities = self.route_engine.find_opportunities(pools)
        self.store.record_opportunities(opportunities)

        approved = [item for item in opportunities if item.status == "approved"]
        for opportunity in opportunities:
            would_execute = opportunity.status == "approved"
            notes = (
                "would_execute: risk approved; paper tracking before real funds"
                if would_execute
                else f"skip: {opportunity.skip_reason or 'unknown'}"
            )
            self.store.record_paper_trade(
                opportunity=opportunity,
                would_execute=would_execute,
                notes=notes,
            )

        scanner_status = str(collected.get("status") or "ok")
        result = {
            **collected,
            "opportunities": len(opportunities),
            "approved": len(approved),
            "paper_candidates": len(opportunities),
            "best_expected_net_profit": approved[0].expected_net_profit if approved else 0.0,
            "paper_verified_app_ids": list(paper_verified_app_ids),
            "paper_only_registry": bool(paper_verified_app_ids),
        }
        scanner_metrics = {**result, "connector_names": result["connectors"]}
        scanner_metrics.pop("connectors", None)
        scanner_metrics["source"] = "live"
        scanner_metrics["liveConnectorSnapshots"] = True
        self.store.record_service_health(
            "market_scanner",
            scanner_status,
            detail=None if scanner_status == "ok" else "connector_degradation_detected",
            metrics=scanner_metrics,
        )
        return result

    def execute_best_once(self) -> dict:
        if not self._execution_slots.acquire(blocking=False):
            return {
                "executed": False,
                "reason": "max concurrent execution reached",
                "max_concurrent_execution": self.settings.max_concurrent_execution,
            }
        try:
            return self._execute_best_once_locked()
        finally:
            self._execution_slots.release()

    def _execute_best_once_locked(self) -> dict:
        scan_started_at = time.time()
        scan = self.run_once()
        required_asset_id = self.settings.target_asset_id if self.settings.use_vestige_discovery else None
        opportunity = self.store.get_best_approved_opportunity(
            max_input_amount=self.settings.max_live_trade_size,
            min_created_at=scan_started_at - 1,
            required_asset_id=required_asset_id,
        )
        if not opportunity:
            return {"executed": False, "reason": "no approved opportunity", "scan": scan}
        daily_profit = self.store.get_submitted_live_profit_24h()
        if daily_profit <= -abs(self.settings.max_daily_loss):
            return {
                "executed": False,
                "reason": "daily loss limit reached",
                "daily_profit_24h": daily_profit,
                "scan": scan,
            }
        daily_trade_count = self.store.get_submitted_live_trade_count_24h()
        if daily_trade_count >= self.settings.max_daily_trades:
            return {
                "executed": False,
                "reason": "daily trade limit reached",
                "daily_submitted_trades_24h": daily_trade_count,
                "max_daily_trades": self.settings.max_daily_trades,
                "scan": scan,
            }
        result = self.live_executor.execute(opportunity)
        self.store.record_live_trade(opportunity, result)
        return {"executed": result.get("submitted", False), "result": result, "scan": scan}

    @property
    def live_executor(self):
        if self._live_executor is None:
            from algopulse.executor import ArbitrageExecutor

            self._live_executor = ArbitrageExecutor(settings=self.settings)
        return self._live_executor

    def _build_connectors(self) -> list[MarketConnector]:
        modes = {part.strip().lower() for part in self.settings.connector_mode.split(",")}
        connectors: list[MarketConnector] = []
        if "mock" in modes:
            connectors.append(MockMarketConnector())
        if "tinyman" in modes:
            connectors.append(TinymanConnector(self.settings))
        if "pact" in modes:
            connectors.append(PactConnector(self.settings))
        if not connectors:
            connectors.append(MockMarketConnector())
        return connectors

    def _settings_with_discovered_pairs(self, settings: Settings) -> Settings:
        modes = {part.strip().lower() for part in settings.connector_mode.split(",")}
        live_mode = bool({"tinyman", "pact"} & modes)
        if not settings.use_vestige_discovery or not live_mode:
            return settings

        discovery = VestigeDiscovery(settings).discover_pairs()
        self.discovery_report = discovery.to_dict()
        if not discovery.pairs:
            return settings
        asset_pairs = _merge_asset_pairs(
            (
                *discovery.asset_pairs,
                *settings.asset_pairs,
                *ROUTING_ANCHOR_PAIRS,
            )
        )
        return replace(settings, asset_pairs=asset_pairs)


def _merge_asset_pairs(pairs: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    seen: set[tuple[int, int]] = set()
    ordered: list[tuple[int, int]] = []
    for left, right in pairs:
        pair = tuple(sorted((int(left), int(right))))
        if pair in seen:
            continue
        seen.add(pair)
        ordered.append(pair)
    return tuple(ordered)
