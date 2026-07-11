from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from algopulse.risk import ALGORAND_TX_GROUP_LIMIT


FORBIDDEN_PAYLOAD_KEYS = {
    "mnemonic": "secret_material_present",
    "private_key": "secret_material_present",
    "privatekey": "secret_material_present",
    "seed": "secret_material_present",
    "seed_phrase": "secret_material_present",
    "seedphrase": "secret_material_present",
    "signed_payload": "signed_payload_present",
    "signedpayload": "signed_payload_present",
    "signed_txn": "signed_payload_present",
    "signedtxn": "signed_payload_present",
    "signed_transactions": "signed_payload_present",
    "submission_payload": "submission_payload_present",
    "submissionpayload": "submission_payload_present",
}


@dataclass(frozen=True)
class UnsignedGroupValidationPolicy:
    approved_route_hashes: tuple[str, ...]
    allowed_app_ids: tuple[int, ...]
    allowed_asset_ids: tuple[int, ...]
    supported_transaction_types: tuple[str, ...] = ("pay", "axfer", "appl")
    max_group_size: int = ALGORAND_TX_GROUP_LIMIT
    max_total_fee_microalgos: int = 50_000


def validate_unsigned_group_summary(group: dict[str, Any], policy: UnsignedGroupValidationPolicy) -> dict[str, Any]:
    transactions = _transactions(group)
    route_hash = str(_pick(group, "routeHash", "route_hash") or "")
    approved_route_hash = _pick(group, "approvedRouteHash", "approved_route_hash")
    tx_count = len(transactions)
    app_ids = _collect_app_ids(group, transactions)
    asset_ids = _collect_asset_ids(group, transactions)
    txn_types = _collect_transaction_types(transactions)
    total_fee = _total_fee_microalgos(group, transactions)
    forbidden_fields = _find_forbidden_fields(group)
    references_check = _references_check(group)
    rules = {
        "no_secret_material": not any(reason == "secret_material_present" for _, reason in forbidden_fields),
        "no_signed_payload": not any(reason == "signed_payload_present" for _, reason in forbidden_fields),
        "no_submission_payload": not any(reason == "submission_payload_present" for _, reason in forbidden_fields),
        "unsigned_only": bool(group.get("unsigned", group.get("unsignedGroup", True))) and not bool(group.get("signed", False)),
        "route_hash_matches": bool(route_hash)
        and route_hash in set(policy.approved_route_hashes)
        and (approved_route_hash is None or str(approved_route_hash) == route_hash),
        "group_size_ok": 0 < tx_count <= min(policy.max_group_size, ALGORAND_TX_GROUP_LIMIT),
        "transaction_types_supported": bool(txn_types)
        and all(txn_type in set(policy.supported_transaction_types) for txn_type in txn_types),
        "app_ids_allowlisted": all(app_id in set(policy.allowed_app_ids) for app_id in app_ids),
        "asset_ids_allowlisted": all(asset_id in set(policy.allowed_asset_ids) for asset_id in asset_ids),
        "fee_cap_ok": total_fee <= int(policy.max_total_fee_microalgos),
        "validity_window_present": _validity_window_present(group, transactions),
        "lease_or_replay_plan_declared": _lease_or_replay_plan_declared(group, transactions),
        "required_references_declared": references_check["ok"],
    }
    reason = _first_failure_reason(rules, forbidden_fields)
    warnings = []
    if references_check["explicitlyMissing"]:
        warnings.append("required_references_explicitly_missing")
    return {
        "ok": reason is None,
        "reason": reason,
        "rules": rules,
        "warnings": warnings,
        "routeHash": route_hash,
        "txCount": tx_count,
        "maxGroupSize": min(policy.max_group_size, ALGORAND_TX_GROUP_LIMIT),
        "totalFeeMicroAlgos": total_fee,
        "maxTotalFeeMicroAlgos": int(policy.max_total_fee_microalgos),
        "appIds": app_ids,
        "assetIds": asset_ids,
        "transactionTypes": txn_types,
        "forbiddenFields": [field for field, _ in forbidden_fields],
        "requiredReferences": references_check["required"],
        "missingReferences": references_check["missing"],
        "policy": {
            **asdict(policy),
            "approved_route_hashes": list(policy.approved_route_hashes),
            "allowed_app_ids": list(policy.allowed_app_ids),
            "allowed_asset_ids": list(policy.allowed_asset_ids),
            "supported_transaction_types": list(policy.supported_transaction_types),
        },
        "submitted": False,
        "signed": False,
        "dryRunOnly": True,
        "liveExecutionTouched": False,
        "signerCodeTouched": False,
    }


def _first_failure_reason(rules: dict[str, bool], forbidden_fields: list[tuple[str, str]]) -> str | None:
    for _, reason in forbidden_fields:
        if reason in {"secret_material_present", "signed_payload_present", "submission_payload_present"}:
            return reason
    for name, passed in rules.items():
        if not passed:
            return name
    return None


def _transactions(group: dict[str, Any]) -> list[dict[str, Any]]:
    txns = _pick(group, "transactions", "txns", "unsignedTransactions", "unsigned_transactions")
    return txns if isinstance(txns, list) else []


def _collect_transaction_types(transactions: list[dict[str, Any]]) -> list[str]:
    return [str(_pick(txn, "type", "txnType", "transactionType", "txn_type") or "") for txn in transactions]


def _collect_app_ids(group: dict[str, Any], transactions: list[dict[str, Any]]) -> list[int]:
    app_ids: set[int] = set(_int_values(_pick(group, "appIds", "app_ids", "expectedAppIds", "expected_app_ids")))
    for txn in transactions:
        app_ids.update(_int_values(_pick(txn, "appId", "app_id", "apid", "applicationId")))
        app_ids.update(_int_values(_pick(txn, "appIds", "app_ids", "foreignApps", "foreign_apps")))
    return sorted(app_ids)


def _collect_asset_ids(group: dict[str, Any], transactions: list[dict[str, Any]]) -> list[int]:
    asset_ids: set[int] = set(_int_values(_pick(group, "assetIds", "asset_ids", "expectedAssetIds", "expected_asset_ids")))
    for txn in transactions:
        asset_ids.update(_int_values(_pick(txn, "assetId", "asset_id", "xaid")))
        asset_ids.update(_int_values(_pick(txn, "assetIds", "asset_ids", "foreignAssets", "foreign_assets")))
    return sorted(asset_ids)


def _total_fee_microalgos(group: dict[str, Any], transactions: list[dict[str, Any]]) -> int:
    explicit = _pick(group, "totalFeeMicroAlgos", "total_fee_microalgos", "feeMicroAlgos", "fee_microalgos")
    if explicit is not None:
        return int(float(explicit))
    return sum(int(float(_pick(txn, "feeMicroAlgos", "fee_microalgos", "fee") or 0)) for txn in transactions)


def _validity_window_present(group: dict[str, Any], transactions: list[dict[str, Any]]) -> bool:
    validity = _pick(group, "validityWindow", "validity_window")
    if isinstance(validity, dict) and _pick(validity, "firstValid", "first_valid") and _pick(validity, "lastValid", "last_valid"):
        return True
    return bool(transactions) and all(
        _pick(txn, "firstValid", "first_valid") is not None and _pick(txn, "lastValid", "last_valid") is not None
        for txn in transactions
    )


def _lease_or_replay_plan_declared(group: dict[str, Any], transactions: list[dict[str, Any]]) -> bool:
    replay = _pick(group, "replayProtection", "replay_protection")
    if _replay_declared(replay) or _pick(group, "lease", "leasePlan", "lease_plan") is not None:
        return True
    return any(_pick(txn, "lease", "leasePlan", "lease_plan") is not None for txn in transactions)


def _replay_declared(value: Any) -> bool:
    if isinstance(value, str):
        return value in {"lease_planned", "planned", "explicitly_missing", "missing_explicit"}
    if isinstance(value, dict):
        status = str(_pick(value, "status", "state") or "")
        return status in {"lease_planned", "planned", "explicitly_missing", "missing_explicit"}
    return False


def _references_check(group: dict[str, Any]) -> dict[str, Any]:
    required = _normalize_references(_pick(group, "requiredReferences", "required_references"))
    references = _normalize_references(_pick(group, "references", "availableReferences", "available_references"))
    explicit_missing = bool(_pick(group, "referencesExplicitlyMissing", "references_explicitly_missing"))
    missing = {
        key: sorted(set(required[key]) - set(references[key]))
        for key in required
    }
    missing = {key: values for key, values in missing.items() if values}
    return {
        "ok": not missing or explicit_missing,
        "required": required,
        "missing": missing,
        "explicitlyMissing": bool(missing and explicit_missing),
    }


def _normalize_references(value: Any) -> dict[str, list]:
    value = value if isinstance(value, dict) else {}
    return {
        "apps": sorted(_int_values(_pick(value, "apps", "appIds", "app_ids"))),
        "assets": sorted(_int_values(_pick(value, "assets", "assetIds", "asset_ids"))),
        "accounts": sorted(str(item) for item in _list_value(_pick(value, "accounts", "addresses"))),
    }


def _find_forbidden_fields(value: Any, path: str = "") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = _normalize_key(str(key))
            child_path = f"{path}.{key}" if path else str(key)
            if normalized in FORBIDDEN_PAYLOAD_KEYS:
                found.append((child_path, FORBIDDEN_PAYLOAD_KEYS[normalized]))
            found.extend(_find_forbidden_fields(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_find_forbidden_fields(child, f"{path}[{index}]"))
    return found


def _pick(mapping: Any, *keys: str) -> Any:
    if not isinstance(mapping, dict):
        return None
    for key in keys:
        if key in mapping:
            return mapping[key]
    normalized = {_normalize_key(str(key)): value for key, value in mapping.items()}
    for key in keys:
        value = normalized.get(_normalize_key(key))
        if value is not None:
            return value
    return None


def _int_values(value: Any) -> list[int]:
    return [int(item) for item in _list_value(value) if item is not None and str(item) != ""]


def _list_value(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _normalize_key(key: str) -> str:
    return key.replace("-", "_").replace(" ", "_").lower()
