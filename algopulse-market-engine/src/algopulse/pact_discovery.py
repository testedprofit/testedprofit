from __future__ import annotations

import base64
from typing import Any


# Official Pact TestNet constant-product factory IDs from pactsdk.config.
TESTNET_FACTORY_CONSTANT_PRODUCT_ID = 166_540_424
TESTNET_FACTORY_NFT_CONSTANT_PRODUCT_ID = 190_269_485
MAINNET_FACTORY_CONSTANT_PRODUCT_ID = 1_072_843_805
MAINNET_FACTORY_NFT_CONSTANT_PRODUCT_ID = 1_076_423_760


def factory_ids_for_network(network: str) -> tuple[int, ...]:
    if (network or "").strip().lower() == "testnet":
        return (
            TESTNET_FACTORY_CONSTANT_PRODUCT_ID,
            TESTNET_FACTORY_NFT_CONSTANT_PRODUCT_ID,
        )
    return (
        MAINNET_FACTORY_CONSTANT_PRODUCT_ID,
        MAINNET_FACTORY_NFT_CONSTANT_PRODUCT_ID,
    )


def discover_pool_app_ids_from_factory(
    algod: Any,
    *,
    factory_app_id: int,
    asset_a: int,
    asset_b: int,
) -> list[int]:
    """Discover Pact pool app IDs for an asset pair from factory box storage.

    Box name layout (observed on TestNet factory): primary(8) + secondary(8) + fee_bps(8) + marker(8).
    Box value: pool app id as big-endian uint64.
    """
    primary, secondary = sorted((int(asset_a), int(asset_b)))
    try:
        boxes = algod.application_boxes(int(factory_app_id)).get("boxes") or []
    except Exception:
        return []

    app_ids: list[int] = []
    for item in boxes:
        try:
            name_b64 = item.get("name") or ""
            raw_name = base64.b64decode(name_b64)
            if len(raw_name) < 16:
                continue
            left = int.from_bytes(raw_name[0:8], "big")
            right = int.from_bytes(raw_name[8:16], "big")
            if sorted((left, right)) != [primary, secondary]:
                continue
            value_payload = algod.application_box_by_name(int(factory_app_id), raw_name)
            raw_value = base64.b64decode(value_payload.get("value") or "")
            if len(raw_value) < 8:
                continue
            app_id = int.from_bytes(raw_value[0:8], "big")
            if app_id > 0:
                app_ids.append(app_id)
        except Exception:
            continue
    # Preserve order, unique.
    seen: set[int] = set()
    ordered: list[int] = []
    for app_id in app_ids:
        if app_id in seen:
            continue
        seen.add(app_id)
        ordered.append(app_id)
    return ordered


def discover_pool_app_ids_for_pair(
    algod: Any,
    *,
    network: str,
    asset_a: int,
    asset_b: int,
) -> list[int]:
    found: list[int] = []
    for factory_id in factory_ids_for_network(network):
        found.extend(
            discover_pool_app_ids_from_factory(
                algod,
                factory_app_id=factory_id,
                asset_a=asset_a,
                asset_b=asset_b,
            )
        )
    seen: set[int] = set()
    ordered: list[int] = []
    for app_id in found:
        if app_id in seen:
            continue
        seen.add(app_id)
        ordered.append(app_id)
    return ordered
