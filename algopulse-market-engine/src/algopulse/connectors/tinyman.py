from __future__ import annotations

import time

from algopulse.algorand import build_algod_client, current_algod_round, raw_to_display
from algopulse.config import Settings
from algopulse.connectors.base import MarketConnector
from algopulse.models import Asset, Pool, Venue


class TinymanConnector(MarketConnector):
    name = "tinyman"

    def __init__(self, settings: Settings) -> None:
        from tinyman.v2.client import TinymanV2MainnetClient, TinymanV2TestnetClient

        self.settings = settings
        self.algod = build_algod_client(settings)
        client_cls = TinymanV2TestnetClient if settings.network == "testnet" else TinymanV2MainnetClient
        self.client = client_cls(self.algod, client_name="algopulse-phase0")
        self._last_health = super().health_evidence()

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
        return [Venue(venue_id="tinyman", name="Tinyman", kind="amm")]

    def list_pools(self) -> list[Pool]:
        started_at = time.perf_counter()
        pools: list[Pool] = []
        failures: list[str] = []
        block_round = current_algod_round(self.algod)
        for left, right in self.settings.asset_pairs:
            try:
                live_pool = self.client.fetch_pool(left, right, fetch=True)
                if not getattr(live_pool, "exists", False) or not getattr(live_pool, "issued_pool_tokens", 0):
                    continue
                asset_1 = live_pool.asset_1
                asset_2 = live_pool.asset_2
                reserve_1 = raw_to_display(live_pool.asset_1_reserves, asset_1.decimals)
                reserve_2 = raw_to_display(live_pool.asset_2_reserves, asset_2.decimals)
                if reserve_1 <= 0 or reserve_2 <= 0:
                    continue
                pools.append(
                    Pool(
                        pool_id=f"tinyman:{live_pool.address}:{asset_1.id}-{asset_2.id}",
                        venue_id="tinyman",
                        app_id=int(live_pool.validator_app_id),
                        asset_a_id=int(asset_1.id),
                        asset_b_id=int(asset_2.id),
                        reserve_a=reserve_1,
                        reserve_b=reserve_2,
                        fee_bps=int(live_pool.total_fee_share),
                        block_round=block_round,
                    )
                )
            except Exception as exc:
                failures.append(type(exc).__name__)
                print(f"[tinyman] skipped pair {left}-{right}: {type(exc).__name__}")
        self._last_health = self._build_health_evidence(
            pools=pools,
            failures=failures,
            latency_ms=(time.perf_counter() - started_at) * 1000,
        )
        return pools

    def health_evidence(self) -> dict:
        return {**self._last_health, "metrics": dict(self._last_health["metrics"])}

    def _build_health_evidence(self, *, pools: list[Pool], failures: list[str], latency_ms: float) -> dict:
        attempted = len(self.settings.asset_pairs)
        failed = len(failures)
        status = "ok" if failed == 0 else "degraded" if pools else "error"
        detail = None if failed == 0 else "partial_pair_failure" if pools else "all_pairs_failed"
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
            },
        }

    def _fetch_asset(self, asset_id: int) -> Asset:
        try:
            live = self.client.fetch_asset(asset_id)
            return Asset(
                asset_id=int(live.id),
                symbol=live.unit_name or ("ALGO" if live.id == 0 else f"ASA{live.id}"),
                name=live.name or ("Algorand" if live.id == 0 else f"ASA {live.id}"),
                decimals=int(live.decimals if live.decimals is not None else 0),
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
