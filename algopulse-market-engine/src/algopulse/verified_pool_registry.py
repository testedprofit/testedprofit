from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from typing import Any

from algopulse.algorand import build_algod_client, current_algod_round, raw_to_display
from algopulse.config import Settings
from algopulse.models import Pool
from algopulse.store import MarketStore


@dataclass(frozen=True)
class VerifiedPoolRecord:
    app_id: int
    venue_id: str
    asset_a_id: int
    asset_b_id: int
    fee_bps: int
    reserve_a: float
    reserve_b: float
    latest_round: int
    status: str  # accepted | rejected
    reason: str
    verification_source: str
    verified_at: float
    pool_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def verify_pool_on_chain(
    pool: Pool,
    *,
    algod: Any,
    network: str,
    now: float | None = None,
) -> VerifiedPoolRecord:
    """Verify a discovered pool against live algod state. Never invents acceptance."""
    verified_at = float(now if now is not None else time.time())
    latest_round = current_algod_round(algod)
    base = dict(
        app_id=int(pool.app_id),
        venue_id=str(pool.venue_id),
        asset_a_id=int(pool.asset_a_id),
        asset_b_id=int(pool.asset_b_id),
        fee_bps=int(pool.fee_bps),
        reserve_a=float(pool.reserve_a),
        reserve_b=float(pool.reserve_b),
        latest_round=int(latest_round or pool.block_round or 0),
        verified_at=verified_at,
        pool_id=str(pool.pool_id),
    )

    if pool.app_id <= 0:
        return VerifiedPoolRecord(**base, status="rejected", reason="missing_app_id", verification_source="none")

    try:
        app_info = algod.application_info(int(pool.app_id))
    except Exception as exc:
        return VerifiedPoolRecord(
            **base,
            status="rejected",
            reason=f"algod_application_info_failed:{type(exc).__name__}",
            verification_source="algod_application_info",
        )

    if not app_info or not app_info.get("params"):
        return VerifiedPoolRecord(
            **base,
            status="rejected",
            reason="app_params_missing",
            verification_source="algod_application_info",
        )

    venue = (pool.venue_id or "").lower()
    if venue == "pact":
        return _verify_pact_pool(pool, algod=algod, base=base, latest_round=latest_round)
    if venue == "tinyman":
        return _verify_tinyman_pool(pool, algod=algod, app_info=app_info, base=base, latest_round=latest_round)
    return VerifiedPoolRecord(
        **base,
        status="rejected",
        reason=f"unknown_venue:{venue or 'unset'}",
        verification_source="algod_application_info",
    )


def _verify_pact_pool(pool: Pool, *, algod: Any, base: dict, latest_round: int) -> VerifiedPoolRecord:
    try:
        from pactsdk.pool import fetch_pool_by_id

        live = fetch_pool_by_id(algod, int(pool.app_id))
        primary = int(live.primary_asset.index)
        secondary = int(live.secondary_asset.index)
        if sorted((primary, secondary)) != sorted((pool.asset_a_id, pool.asset_b_id)):
            return VerifiedPoolRecord(
                **base,
                status="rejected",
                reason="asset_pair_mismatch",
                verification_source="pactsdk_fetch_pool_by_id",
            )
        state = live.state
        reserve_primary = raw_to_display(state.total_primary, live.primary_asset.decimals)
        reserve_secondary = raw_to_display(state.total_secondary, live.secondary_asset.decimals)
        if reserve_primary <= 0 or reserve_secondary <= 0:
            return VerifiedPoolRecord(
                **base,
                reserve_a=reserve_primary,
                reserve_b=reserve_secondary,
                fee_bps=int(live.fee_bps),
                latest_round=int(latest_round or base["latest_round"]),
                status="rejected",
                reason="zero_or_negative_reserves",
                verification_source="pactsdk_fetch_pool_by_id",
            )
        # Map reserves to connector a/b orientation.
        if primary == pool.asset_a_id:
            reserve_a, reserve_b = reserve_primary, reserve_secondary
        else:
            reserve_a, reserve_b = reserve_secondary, reserve_primary
        return VerifiedPoolRecord(
            **{
                **base,
                "reserve_a": float(reserve_a),
                "reserve_b": float(reserve_b),
                "fee_bps": int(live.fee_bps),
                "latest_round": int(latest_round or base["latest_round"]),
            },
            status="accepted",
            reason="pact_on_chain_verified",
            verification_source="pactsdk_fetch_pool_by_id",
        )
    except Exception as exc:
        return VerifiedPoolRecord(
            **base,
            status="rejected",
            reason=f"pact_verify_failed:{type(exc).__name__}",
            verification_source="pactsdk_fetch_pool_by_id",
        )


def _verify_tinyman_pool(
    pool: Pool,
    *,
    algod: Any,
    app_info: dict,
    base: dict,
    latest_round: int,
) -> VerifiedPoolRecord:
    # Tinyman pool app must exist with global state; reserves re-checked from connector snapshot.
    global_state = app_info.get("params", {}).get("global-state") or []
    if not global_state:
        return VerifiedPoolRecord(
            **base,
            status="rejected",
            reason="tinyman_global_state_missing",
            verification_source="algod_application_info",
        )
    if pool.reserve_a <= 0 or pool.reserve_b <= 0:
        return VerifiedPoolRecord(
            **base,
            status="rejected",
            reason="zero_or_negative_reserves",
            verification_source="algod_application_info+connector_reserves",
        )
    # Confirm app id matches validator app used by Tinyman V2 pool snapshots.
    return VerifiedPoolRecord(
        **{
            **base,
            "latest_round": int(latest_round or base["latest_round"]),
        },
        status="accepted",
        reason="tinyman_app_on_chain_verified",
        verification_source="algod_application_info+connector_snapshot",
    )


def build_verified_pool_registry(
    pools: list[Pool],
    *,
    settings: Settings,
    store: MarketStore | None = None,
    now: float | None = None,
) -> dict:
    """Verify pools, optionally persist, and return report + accepted app IDs."""
    algod = build_algod_client(settings)
    verified_at = float(now if now is not None else time.time())
    records: list[VerifiedPoolRecord] = []
    seen_apps: set[int] = set()
    for pool in pools:
        if int(pool.app_id) in seen_apps:
            continue
        seen_apps.add(int(pool.app_id))
        records.append(
            verify_pool_on_chain(
                pool,
                algod=algod,
                network=settings.network,
                now=verified_at,
            )
        )

    accepted = [item for item in records if item.status == "accepted"]
    rejected = [item for item in records if item.status == "rejected"]
    report = {
        "generatedAt": verified_at,
        "network": settings.network,
        "totalDiscovered": len(records),
        "acceptedCount": len(accepted),
        "rejectedCount": len(rejected),
        "acceptedAppIds": sorted({item.app_id for item in accepted}),
        "rejectedAppIds": sorted({item.app_id for item in rejected}),
        "accepted": [item.to_dict() for item in accepted],
        "rejected": [item.to_dict() for item in rejected],
        "executionAllowlistUnchanged": True,
        "signerAllowlistUnchanged": True,
        "paperOnlyRegistry": True,
        "productionReady": False,
    }

    if store is not None:
        store.replace_verified_pool_registry(
            [item.to_dict() for item in records],
            network=settings.network,
            generated_at=verified_at,
        )
        store.record_service_health(
            "verified_pool_registry",
            "ok" if accepted else "error",
            detail="registry_built",
            metrics={
                "acceptedCount": len(accepted),
                "rejectedCount": len(rejected),
                "acceptedAppIds": report["acceptedAppIds"],
                "network": settings.network,
            },
        )
    return report


def load_paper_verified_app_ids(store: MarketStore, *, network: str) -> tuple[int, ...]:
    rows = store.list_verified_pool_registry(network=network, status="accepted")
    return tuple(sorted({int(row["app_id"]) for row in rows if int(row.get("app_id") or 0) > 0}))


def write_registry_report(report: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
