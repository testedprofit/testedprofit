from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from typing import Any


PROTOCOL_LABELS = {
    2: "Tinyman",
    3: "Pact",
}


def fetch_recent_pnet_swaps(
    *,
    vestige_api_url: str,
    asset_id: int,
    limit: int = 5,
    network_id: int = 0,
    now: float | None = None,
) -> dict[str, Any]:
    safe_limit = max(1, min(25, int(limit)))
    url = _vestige_swaps_url(
        vestige_api_url=vestige_api_url,
        asset_id=asset_id,
        limit=safe_limit,
        network_id=network_id,
    )
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "AlgoPulse Phase0 read-only market intelligence",
        },
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return normalize_vestige_swaps(payload, target_asset_id=asset_id, limit=safe_limit, now=now)


def normalize_vestige_swaps(
    payload: dict[str, Any],
    *,
    target_asset_id: int,
    limit: int = 5,
    now: float | None = None,
) -> dict[str, Any]:
    observed_at = float(now or time.time())
    extra = payload.get("extra") if isinstance(payload.get("extra"), dict) else {}
    rows = []
    for row in (payload.get("results") or [])[: max(1, min(25, int(limit)))]:
        if not isinstance(row, dict):
            continue
        normalized = _normalize_swap_row(row, extra=extra, observed_at=observed_at)
        if normalized:
            rows.append(normalized)
    return {
        "assetId": int(target_asset_id),
        "source": "live" if rows else "unavailable",
        "sourceLabel": "Vestige swaps API",
        "dataPolicy": "public_read_only_historical_swaps",
        "publicSafe": True,
        "freshExecutableRoutes": False,
        "liveExecutionTouched": False,
        "signerCodeTouched": False,
        "count": len(rows),
        "swaps": rows,
    }


def _vestige_swaps_url(*, vestige_api_url: str, asset_id: int, limit: int, network_id: int) -> str:
    base = vestige_api_url.rstrip("/")
    query = urllib.parse.urlencode(
        {
            "network_id": int(network_id),
            "asset_id": int(asset_id),
            "limit": max(1, min(25, int(limit))),
            "order_by": "offset",
            "order_dir": "desc",
        }
    )
    return f"{base}/swaps?{query}"


def _normalize_swap_row(row: dict[str, Any], *, extra: dict[str, Any], observed_at: float) -> dict[str, Any] | None:
    asset_1_id = int(row.get("asset_1_id") or 0)
    asset_2_id = int(row.get("asset_2_id") or 0)
    asset_1_delta = float(row.get("asset_1_delta") or 0.0)
    asset_2_delta = float(row.get("asset_2_delta") or 0.0)
    if not asset_1_id and not asset_2_id:
        return None

    from_asset_id, to_asset_id, input_amount, output_amount = _swap_direction(
        asset_1_id=asset_1_id,
        asset_2_id=asset_2_id,
        asset_1_delta=asset_1_delta,
        asset_2_delta=asset_2_delta,
    )
    timestamp = float(row.get("timestamp") or 0.0)
    notional_value = max(float(row.get("asset_1_delta_value") or 0.0), float(row.get("asset_2_delta_value") or 0.0))
    protocol_id = int(row.get("protocol_id") or 0)
    offset = row.get("offset")
    return {
        "id": f"vestige-{offset or int(timestamp)}",
        "routeHash": f"vestige-swap-{offset or int(timestamp)}",
        "pair": f"{_asset_ticker(asset_1_id, extra)}/{_asset_ticker(asset_2_id, extra)}",
        "fromAsset": _asset_ticker(from_asset_id, extra),
        "toAsset": _asset_ticker(to_asset_id, extra),
        "fromAssetId": from_asset_id,
        "toAssetId": to_asset_id,
        "inputAmount": abs(input_amount),
        "expectedOutput": abs(output_amount),
        "notionalUsd": notional_value,
        "notionalLabel": f"${notional_value:.4f}",
        "timestamp": timestamp or None,
        "ageSeconds": max(0.0, observed_at - timestamp) if timestamp else None,
        "ageLabel": _age_label(observed_at, timestamp),
        "block": int(row.get("block") or 0) or None,
        "protocolId": protocol_id,
        "protocolLabel": PROTOCOL_LABELS.get(protocol_id, f"Protocol {protocol_id}" if protocol_id else "Vestige"),
        "source": "live",
        "sourceLabel": "Vestige swaps API",
        "sample": False,
        "publicSafe": True,
    }


def _swap_direction(
    *,
    asset_1_id: int,
    asset_2_id: int,
    asset_1_delta: float,
    asset_2_delta: float,
) -> tuple[int, int, float, float]:
    if asset_1_delta < 0 <= asset_2_delta:
        return asset_1_id, asset_2_id, asset_1_delta, asset_2_delta
    if asset_2_delta < 0 <= asset_1_delta:
        return asset_2_id, asset_1_id, asset_2_delta, asset_1_delta
    return asset_1_id, asset_2_id, asset_1_delta, asset_2_delta


def _asset_ticker(asset_id: int, extra: dict[str, Any]) -> str:
    if asset_id == 0:
        return "ALGO"
    meta = extra.get(str(asset_id)) if isinstance(extra, dict) else None
    ticker = meta.get("ticker") if isinstance(meta, dict) else None
    return str(ticker or f"ASA {asset_id}")


def _age_label(observed_at: float, timestamp: float) -> str:
    if not timestamp:
        return "live"
    age = max(0.0, observed_at - timestamp)
    if age < 60:
        return f"{int(age)}s ago"
    if age < 3600:
        return f"{int(age // 60)}m ago"
    if age < 86_400:
        return f"{int(age // 3600)}h ago"
    return f"{int(age // 86_400)}d ago"
