from __future__ import annotations

import time

from algopulse.algorand import build_algod_client, current_algod_round, raw_to_display
from algopulse.config import Settings
from algopulse.connectors.base import MarketConnector
from algopulse.models import Asset, Pool, Venue
from algopulse.pact_discovery import discover_pool_app_ids_for_pair


class PactConnector(MarketConnector):
    name = "pact"

    def __init__(self, settings: Settings) -> None:
        from pactsdk import PactClient

        self.settings = settings
        self.algod = build_algod_client(settings)
        network = "testnet" if settings.network == "testnet" else "mainnet"
        self.network = network
        self.client = PactClient(self.algod, network=network)
        self._last_health = super().health_evidence()
        self._discovery_mode: str | None = None

    def list_assets(self) -> list[Asset]:
        seen: set[int] = set()
        assets: list[Asset] = []
        for left, right in self.settings.asset_pairs:
            for asset_id in (left, right):
                if asset_id in seen:
                    continue
                seen.add(asset_id)
                assets.append(self._fetch_asset(asset_id))
        return assets

    def list_venues(self) -> list[Venue]:
        return [Venue(venue_id="pact", name="Pact", kind="amm")]

    def list_pools(self) -> list[Pool]:
        started_at = time.perf_counter()
        pools: list[Pool] = []
        failures: list[str] = []
        discovery_modes: list[str] = []
        block_round = current_algod_round(self.algod)
        for left, right in self.settings.asset_pairs:
            pair_pools, pair_failures, mode = self._fetch_pair_pools(left, right, block_round=block_round)
            pools.extend(pair_pools)
            failures.extend(pair_failures)
            if mode:
                discovery_modes.append(mode)
            if pair_failures and not pair_pools:
                print(f"[pact] skipped pair {left}-{right}: {','.join(sorted(set(pair_failures)))}")
        self._discovery_mode = ",".join(sorted(set(discovery_modes))) if discovery_modes else None
        self._last_health = self._build_health_evidence(
            pools=pools,
            failures=failures,
            latency_ms=(time.perf_counter() - started_at) * 1000,
            discovery_mode=self._discovery_mode,
        )
        return pools

    def health_evidence(self) -> dict:
        return {**self._last_health, "metrics": dict(self._last_health["metrics"])}

    def _fetch_pair_pools(
        self,
        left: int,
        right: int,
        *,
        block_round: int,
    ) -> tuple[list[Pool], list[str], str | None]:
        failures: list[str] = []
        # 1) Official Pact API path (preferred when healthy).
        try:
            live_pools = list(self.client.fetch_pools_by_assets(left, right))
            return self._normalize_live_pools(live_pools, block_round=block_round), [], "api"
        except Exception as exc:
            failures.append(type(exc).__name__)

        # 2) Algod factory-box discovery fallback (no Pact REST dependency).
        try:
            app_ids = discover_pool_app_ids_for_pair(
                self.algod,
                network=self.network,
                asset_a=left,
                asset_b=right,
            )
            if not app_ids:
                failures.append("factory_no_pool_for_pair")
                return [], failures, "factory_empty"
            from pactsdk.pool import fetch_pool_by_id

            live_pools = []
            for app_id in app_ids:
                try:
                    live_pools.append(fetch_pool_by_id(self.algod, app_id))
                except Exception as exc:
                    failures.append(type(exc).__name__)
            if live_pools:
                return (
                    self._normalize_live_pools(live_pools, block_round=block_round),
                    failures,
                    "algod_factory",
                )
        except Exception as exc:
            failures.append(type(exc).__name__)
        return [], failures, "failed"

    def _normalize_live_pools(self, live_pools, *, block_round: int) -> list[Pool]:
        pools: list[Pool] = []
        for live_pool in live_pools:
            primary = live_pool.primary_asset
            secondary = live_pool.secondary_asset
            state = live_pool.state
            reserve_primary = raw_to_display(state.total_primary, primary.decimals)
            reserve_secondary = raw_to_display(state.total_secondary, secondary.decimals)
            if reserve_primary <= 0 or reserve_secondary <= 0:
                continue
            pools.append(
                Pool(
                    pool_id=f"pact:{live_pool.app_id}:{primary.index}-{secondary.index}",
                    venue_id="pact",
                    app_id=int(live_pool.app_id),
                    asset_a_id=int(primary.index),
                    asset_b_id=int(secondary.index),
                    reserve_a=reserve_primary,
                    reserve_b=reserve_secondary,
                    fee_bps=int(live_pool.fee_bps),
                    block_round=block_round,
                )
            )
        return pools

    def _build_health_evidence(
        self,
        *,
        pools: list[Pool],
        failures: list[str],
        latency_ms: float,
        discovery_mode: str | None = None,
    ) -> dict:
        attempted = len(self.settings.asset_pairs)
        failed = len(failures)
        # Factory fallback success still counts as healthy connector evidence.
        if pools and discovery_mode == "algod_factory" and failed:
            status = "degraded"
            detail = "pact_api_fallback_to_algod_factory"
        elif failed == 0:
            status, detail = "ok", None
        elif pools:
            status, detail = "degraded", "partial_pair_failure"
        else:
            status = "error"
            if set(failures) <= {"JSONDecodeError", "factory_no_pool_for_pair"} and "JSONDecodeError" in failures:
                detail = "pact_api_non_json_response"
            else:
                detail = "all_pairs_failed"
        return {
            "status": status,
            "detail": detail,
            "metrics": {
                "connector": self.name,
                "connectorType": "dex",
                "latencyMs": round(latency_ms, 3),
                "attemptedPairCount": attempted,
                "failedPairCount": failed,
                "poolCount": len(pools),
                "errorTypes": sorted(set(failures)),
                "discoveryMode": discovery_mode,
            },
        }

    def _fetch_asset(self, asset_id: int) -> Asset:
        try:
            live = self.client.fetch_asset(asset_id)
            return Asset(
                asset_id=int(live.index),
                symbol=live.unit_name or ("ALGO" if live.index == 0 else f"ASA{live.index}"),
                name=live.name or ("Algorand" if live.index == 0 else f"ASA {live.index}"),
                decimals=int(live.decimals),
                is_verified=True,
                is_allowlisted=True,
            )
        except Exception:
            return Asset(
                asset_id=asset_id,
                symbol="ALGO" if asset_id == 0 else f"ASA{asset_id}",
                name="Algorand" if asset_id == 0 else f"ASA {asset_id}",
                decimals=6,
                is_verified=asset_id == 0,
                is_allowlisted=True,
            )
