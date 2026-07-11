from __future__ import annotations

from collections.abc import Mapping
from typing import Any

PublicSchema = dict[str, Any]


REPORT_RECORD_TYPES = {
    "paper_trade_report",
    "market_daily_report",
    "market_archive_report",
}

BLOCKED_PENDING_HUMAN_REVIEW_RECORD_TYPES = {
    "live_trade_receipt",
    "reconciliation_record",
    "pnet_fee_payment",
    "refund_case",
    "failed_trade",
    "execution_queue_item",
    "route_detail",
    "dry_run_summary",
    "admin_audit_event",
}

PUBLIC_RECORD_REDACTION_CONTRACT: dict[str, dict[str, str]] = {
    **{
        record_type: {
            "status": "phase0_report_surface_implemented",
            "default": "never_expose_unlisted_fields",
        }
        for record_type in REPORT_RECORD_TYPES
    },
    **{
        record_type: {
            "status": "blocked_pending_human_review",
            "default": "never_expose_unlisted_fields",
        }
        for record_type in BLOCKED_PENDING_HUMAN_REVIEW_RECORD_TYPES
    },
}

LIQUIDITY_CHANGE_KEYS: PublicSchema = {
    "poolId": None,
    "venue": None,
    "appId": None,
    "pairLabel": None,
    "startLiquidity": None,
    "endLiquidity": None,
    "change": None,
    "changePct": None,
    "snapshotCount": None,
    "firstSeenAt": None,
    "lastSeenAt": None,
}

PNET_LIQUIDITY_WATCHLIST_KEYS: PublicSchema = {
    "assetId": None,
    "symbol": None,
    "poolCount": None,
    "totalPnetReserve": None,
    "source": None,
    "listedWithoutOpportunity": None,
    "publicSafe": None,
    "notice": None,
    "lpRiskNotice": None,
    "pools": {
        "poolId": None,
        "venue": None,
        "appId": None,
        "pairLabel": None,
        "pnetAssetId": None,
        "otherAssetId": None,
        "otherSymbol": None,
        "pnetReserve": None,
        "otherReserve": None,
        "liquidityEstimate": None,
        "liquidityChangePct": None,
        "feeBps": None,
        "snapshotCount": None,
        "firstSeenAt": None,
        "lastSeenAt": None,
        "opportunityRequired": None,
        "lpVisibilityNote": None,
    },
}

MARKET_CONTEXT_RIBBON_KEYS: PublicSchema = {
    "title": None,
    "symbol": None,
    "change24hPct": None,
    "contextLabel": None,
    "snapshotAgeSeconds": None,
    "snapshotAgeLabel": None,
    "sourceLabel": None,
    "availability": None,
    "cached": None,
    "external": None,
    "scope": None,
    "notice": None,
}

PUBLIC_SAFE_ALLOWED_KEYS: dict[str, PublicSchema] = {
    "paper_trade_report": {
        "windowSeconds": None,
        "candidates": None,
        "wouldExecute": None,
        "skipped": None,
        "checked5s": None,
        "checked30s": None,
        "completionRate30s": None,
        "daysCollected": None,
        "expectedNetProfit": None,
        "simulatedProfit30s": None,
        "averageQuoteDecay30s": None,
        "averageProfitDelta30s": None,
        "skipReasons": {"reason": None, "count": None},
        "bestRoute": {
            "route_hash": None,
            "input_asset_id": None,
            "input_amount": None,
            "expected_net_profit": None,
            "simulated_profit_30s": None,
            "checked_30s_at": None,
            "skip_reason": None,
            "would_execute": None,
        },
    },
    "market_daily_report": {
        "reportDate": None,
        "windowStart": None,
        "windowEnd": None,
        "generatedAt": None,
        "source": None,
        "reportTier": None,
        "preview": None,
        "premium": None,
        "access": None,
        "delayed": None,
        "paymentUpgradeAvailable": None,
        "upgradeResource": None,
        "paymentUnlocks": None,
        "excludedDetailSections": None,
        "premiumSections": None,
        "exportMetadata": {
            "resource": None,
            "format": None,
            "redacted": None,
            "paymentGated": None,
            "reportDate": None,
            "generatedAt": None,
        },
        "redactionPolicy": {
            "rawRoutes": None,
            "custodyFields": None,
            "paymentMaterial": None,
            "freshExecutableRoutes": None,
        },
        "publicSafe": None,
        "liveExecutionTouched": None,
        "signerCodeTouched": None,
        "marketSummary": {
            "headline": None,
            "narrative": None,
            "opportunityCount": None,
            "pairCount": None,
            "venueCount": None,
            "topPair": None,
            "positiveSpreadCount": None,
            "largestLiquidityMove": LIQUIDITY_CHANGE_KEYS,
            "scannerStatus": None,
            "paperWinRate30s": None,
        },
        "marketContextRibbon": MARKET_CONTEXT_RIBBON_KEYS,
        "summary": {
            "headline": None,
            "topPair": None,
            "opportunityCount": None,
            "paperWinRate30s": None,
            "scannerStatus": None,
        },
        "topPairs": {
            "pairKey": None,
            "pairLabel": None,
            "opportunityCount": None,
            "averageSpreadBps": None,
            "bestSpreadBps": None,
            "expectedNetProfit": None,
            "approvedCount": None,
            "rejectedCount": None,
            "paperCount": None,
            "paperWinRate30s": None,
        },
        "pnetLiquidityWatchlist": PNET_LIQUIDITY_WATCHLIST_KEYS,
        "topSpreads": {
            "pairLabel": None,
            "venues": None,
            "expectedProfitBps": None,
            "expectedNetProfit": None,
            "grossProfit": None,
            "priceImpactBps": None,
            "status": None,
            "skipReason": None,
            "confidenceScore": None,
            "createdAt": None,
        },
        "liquidityChanges": LIQUIDITY_CHANGE_KEYS,
        "opportunityCounts": {
            "total": None,
            "approved": None,
            "rejected": None,
            "positiveSpreadCount": None,
            "byStatus": {"status": None, "count": None},
            "bySkipReason": {"reason": None, "count": None},
            "byHour": {"hour": None, "startAt": None, "count": None},
        },
        "routePerformance": {
            "routeCount": None,
            "approvedCount": None,
            "rejectedCount": None,
            "averageRouteLength": None,
            "averageConfidence": None,
            "averageExpectedProfitBps": None,
            "totalExpectedNetProfit": None,
            "topRejectionReasons": {"reason": None, "count": None},
        },
        "paperTradePerformance": {
            "candidates": None,
            "wouldExecute": None,
            "skipped": None,
            "checked5s": None,
            "checked30s": None,
            "winRate5s": None,
            "winRate30s": None,
            "expectedNetProfit": None,
            "simulatedProfit5s": None,
            "simulatedProfit30s": None,
            "averageQuoteDecay5s": None,
            "averageQuoteDecay30s": None,
            "averageProfitDelta30s": None,
        },
        "scannerHealth": {
            "status": None,
            "latestDetail": None,
            "lastRunAt": None,
            "okCount": None,
            "errorCount": None,
            "checks": None,
            "snapshotCount": None,
            "poolsScanned": None,
            "latestSnapshotAt": None,
        },
        "riskEvents": {"reason": None, "count": None, "approved": None, "latestAt": None},
        "exports": {"json": None, "markdown": None},
    },
    "market_archive_report": {
        "reports": "market_daily_report",
        "count": None,
        "source": None,
        "publicSafe": None,
        "liveExecutionTouched": None,
        "signerCodeTouched": None,
    },
}

NEVER_EXPOSE_KEYS = {
    "adminkey",
    "adminpolicy",
    "apikey",
    "executionqueue",
    "hotwallet",
    "mnemonic",
    "privatekey",
    "rawroutejson",
    "routejson",
    "secret",
    "seed",
    "seedphrase",
    "signer",
    "signedtxn",
    "submissionpayload",
    "unsignedtxngroup",
}

NEVER_EXPOSE_KEY_FRAGMENTS = {
    "apikey",
    "executionqueue",
    "hotwallet",
    "mnemonic",
    "privatekey",
    "rawroutejson",
    "routejson",
    "secret",
    "seedphrase",
    "signedtxn",
    "signedgroup",
    "submissionpayload",
    "submittedtxid",
    "submittedtransaction",
    "signerresponse",
    "signersecret",
    "signerstate",
    "unsignedtxngroup",
}

NEVER_EXPOSE_VALUE_FRAGMENTS = {
    "api_key",
    "execution_queue",
    "hot_wallet",
    "mnemonic",
    "private_key",
    "seed_phrase",
    "signed_txn",
    "submission_payload",
    "signersecret",
    "signer_secret",
}


def redact_public_record(record: Mapping[str, Any], record_type: str) -> dict[str, Any]:
    """Return the public-safe shape for a record covered by the redaction contract."""
    if record_type not in PUBLIC_RECORD_REDACTION_CONTRACT:
        raise ValueError(f"unknown public record type: {record_type}")

    data = dict(record)
    if not data:
        return {}

    status = PUBLIC_RECORD_REDACTION_CONTRACT[record_type]["status"]
    if status == "blocked_pending_human_review":
        return {
            "recordType": record_type,
            "publicSafe": False,
            "redactionStatus": "blocked_pending_human_review",
        }

    schema = PUBLIC_SAFE_ALLOWED_KEYS.get(record_type, {})
    return _redact_mapping(data, schema=schema)


def assert_public_safe(record: Mapping[str, Any], record_type: str) -> None:
    """Raise AssertionError when a public record would be changed by redaction."""
    redacted = redact_public_record(record, record_type)
    if redacted != dict(record):
        raise AssertionError(f"{record_type} contains non-public fields")


def _redact_mapping(value: Mapping[str, Any], *, schema: PublicSchema) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, child in value.items():
        normalized = _normalize_key(key)
        if _is_never_expose_key(normalized) or key not in schema:
            continue
        redacted[key] = _redact_value(child, schema=schema[key])
    return redacted


def _redact_value(value: Any, *, schema: Any) -> Any:
    if isinstance(schema, str):
        if schema not in PUBLIC_SAFE_ALLOWED_KEYS:
            return None
        if isinstance(value, list):
            return [
                redact_public_record(item, schema) if isinstance(item, Mapping) else _redact_value(item, schema=None)
                for item in value
            ]
        return redact_public_record(value, schema) if isinstance(value, Mapping) else None
    if isinstance(schema, Mapping):
        if isinstance(value, Mapping):
            return _redact_mapping(value, schema=dict(schema))
        if isinstance(value, list):
            return [_redact_value(item, schema=schema) for item in value]
        return None
    if isinstance(value, list):
        return [_redact_value(item, schema=None) for item in value]
    if isinstance(value, str) and _has_forbidden_value(value):
        return "[redacted]"
    return value


def _normalize_key(key: str) -> str:
    return "".join(character for character in str(key).lower() if character.isalnum())


def _is_never_expose_key(normalized_key: str) -> bool:
    return normalized_key in NEVER_EXPOSE_KEYS or any(
        fragment in normalized_key for fragment in NEVER_EXPOSE_KEY_FRAGMENTS
    )


def _has_forbidden_value(value: str) -> bool:
    lowered = value.lower()
    normalized = _normalize_key(value)
    return any(fragment in lowered for fragment in NEVER_EXPOSE_VALUE_FRAGMENTS) or _is_never_expose_key(normalized)
