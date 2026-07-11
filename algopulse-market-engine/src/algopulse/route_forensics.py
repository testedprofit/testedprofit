from __future__ import annotations

import time
from typing import Any


RISK_RULE_LABELS = {
    "own_funds_only": "Own funds only",
    "assets_allowlisted": "Asset allowlist",
    "app_ids_allowlisted": "App ID allowlist",
    "quote_freshness_ok": "Quote freshness",
    "trade_size_ok": "Trade size",
    "route_leg_count_ok": "Route length",
    "net_profit_after_fees_ok": "Net profit after fees",
    "profit_bps_ok": "Profit bps floor",
    "fee_buffer_ok": "Fee buffer",
    "price_impact_ok": "Price impact",
    "pool_reserves_ok": "Pool reserves",
    "daily_loss_ok": "Daily loss",
    "daily_trade_count_ok": "Daily trade count",
    "concurrent_execution_ok": "Concurrent execution",
}


def build_route_forensics(
    opportunity: dict[str, Any],
    *,
    opportunity_id: int | None = None,
    liquidity: dict[str, Any] | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    observed_at = float(now or time.time())
    route = _normal_route(opportunity.get("route") or [])
    input_amount = _number(opportunity.get("input_amount"))
    expected_final_amount = _number(opportunity.get("expected_final_amount"))
    expected_net_profit = _number(opportunity.get("expected_net_profit"))
    expected_profit_bps = _number(opportunity.get("expected_profit_bps"))
    gross_profit = _number(opportunity.get("gross_profit"), expected_final_amount - input_amount)
    estimated_network_fee = _number(opportunity.get("estimated_network_fee"))
    total_dex_fees = _number(opportunity.get("total_dex_fees"))
    slippage_buffer = _number(opportunity.get("slippage_buffer"))
    total_price_impact_bps = _number(opportunity.get("total_price_impact_bps"))
    if not total_price_impact_bps:
        total_price_impact_bps = sum(_number(leg.get("priceImpactBps")) for leg in route)
    max_price_impact_bps = _number(opportunity.get("max_price_impact_bps"))
    if not max_price_impact_bps:
        max_price_impact_bps = max((_number(leg.get("priceImpactBps")) for leg in route), default=0.0)

    quote_freshness = _quote_freshness(route, observed_at)
    profitability = {
        "inputAmount": input_amount,
        "expectedFinalAmount": expected_final_amount,
        "grossProfit": gross_profit,
        "estimatedNetworkFee": estimated_network_fee,
        "totalDexFees": total_dex_fees,
        "slippageBuffer": slippage_buffer,
        "expectedNetProfit": expected_net_profit,
        "expectedProfitBps": expected_profit_bps,
        "profitableAfterFees": expected_net_profit > 0,
    }
    price_impact = {
        "totalBps": total_price_impact_bps,
        "maxBps": max_price_impact_bps,
        "perLeg": [
            {
                "index": leg["index"],
                "poolId": leg["poolId"],
                "venue": leg["venue"],
                "priceImpactBps": leg["priceImpactBps"],
            }
            for leg in route
        ],
    }
    liquidity_score = _liquidity_score(liquidity or {}, input_amount=input_amount)
    risk_rules = dict(opportunity.get("risk_rules") or {})
    risk_result = _risk_result(opportunity, risk_rules)
    confidence = _confidence_calculation(
        opportunity=opportunity,
        quote_freshness=quote_freshness,
        profitability=profitability,
        price_impact=price_impact,
        liquidity_score=liquidity_score,
        risk_result=risk_result,
    )
    approval_decision = _approval_decision(opportunity, risk_result)
    rejection_reason = _rejection_reason(opportunity, risk_result, approval_decision)
    decision_tree = _decision_tree(
        route=route,
        quote_freshness=quote_freshness,
        profitability=profitability,
        price_impact=price_impact,
        liquidity_score=liquidity_score,
        risk_result=risk_result,
        approval_decision=approval_decision,
        rejection_reason=rejection_reason,
    )
    missing = _missing_required_fields(
        {
            "routeHash": opportunity.get("route_hash"),
            "routePath": route,
            "profitability": profitability,
            "quoteFreshness": quote_freshness,
            "priceImpact": price_impact,
            "liquidityScore": liquidity_score,
            "riskResult": risk_result,
            "approvalDecision": approval_decision,
            "rejectionReason": rejection_reason,
            "confidenceCalculation": confidence,
            "decisionTree": decision_tree,
        }
    )
    completeness = {
        "complete": not missing,
        "missingFields": missing,
        "requiredFields": [
            "routeHash",
            "routePath",
            "profitability",
            "quoteFreshness",
            "priceImpact",
            "liquidityScore",
            "riskResult",
            "approvalDecision",
            "rejectionReason",
            "confidenceCalculation",
            "decisionTree",
        ],
    }

    return {
        "routeHash": str(opportunity.get("route_hash") or ""),
        "opportunityId": opportunity_id,
        "routePath": route,
        "routePathLabel": _route_path_label(route, opportunity),
        "profitability": profitability,
        "quoteFreshness": quote_freshness,
        "priceImpact": price_impact,
        "liquidityScore": liquidity_score,
        "riskResult": risk_result,
        "approvalDecision": approval_decision,
        "rejectionReason": rejection_reason,
        "confidenceCalculation": confidence,
        "decisionTree": decision_tree,
        "completeness": completeness,
        "source": "stored",
        "createdAt": float(opportunity.get("created_at") or observed_at),
    }


def _normal_route(route: list[dict[str, Any]]) -> list[dict[str, Any]]:
    legs = []
    for index, leg in enumerate(route):
        legs.append(
            {
                "index": index,
                "routeKind": leg.get("route_kind") or "route",
                "venue": leg.get("venue") or leg.get("venue_id") or "unknown",
                "poolId": leg.get("pool_id") or "",
                "appId": leg.get("app_id"),
                "inputAssetId": _int_or_none(leg.get("input_asset_id")),
                "outputAssetId": _int_or_none(leg.get("output_asset_id")),
                "inputAmount": _number(leg.get("input_amount")),
                "expectedOutput": _number(leg.get("expected_output") or leg.get("output_amount")),
                "feeAmount": _number(leg.get("fee_amount")),
                "priceImpactBps": _number(leg.get("price_impact_bps")),
                "blockRound": _int_or_none(leg.get("block_round")),
                "capturedAt": _number(leg.get("captured_at")) or None,
                "expiresAt": _number(leg.get("expires_at")) or None,
            }
        )
    return legs


def _quote_freshness(route: list[dict[str, Any]], observed_at: float) -> dict[str, Any]:
    captured = [float(leg["capturedAt"]) for leg in route if leg.get("capturedAt")]
    expires = [float(leg["expiresAt"]) for leg in route if leg.get("expiresAt")]
    if not route:
        return {
            "status": "unavailable",
            "maxAgeSeconds": None,
            "oldestCapturedAt": None,
            "newestExpiresAt": None,
            "secondsToExpiry": None,
            "fresh": False,
            "detail": "No route legs were stored, so quote freshness cannot be proven.",
        }
    if not captured:
        return {
            "status": "unavailable",
            "maxAgeSeconds": None,
            "oldestCapturedAt": None,
            "newestExpiresAt": max(expires) if expires else None,
            "secondsToExpiry": None,
            "fresh": False,
            "detail": "Route exists, but quote capture timestamps are missing.",
        }
    oldest = min(captured)
    newest_expiry = max(expires) if expires else None
    max_age = max(0.0, observed_at - oldest)
    seconds_to_expiry = None if newest_expiry is None else newest_expiry - observed_at
    fresh = seconds_to_expiry is None or seconds_to_expiry >= 0
    return {
        "status": "fresh" if fresh else "stale",
        "maxAgeSeconds": max_age,
        "oldestCapturedAt": oldest,
        "newestExpiresAt": newest_expiry,
        "secondsToExpiry": seconds_to_expiry,
        "fresh": fresh,
        "detail": "Quote timestamps and expiry metadata are present." if fresh else "At least one quote expired before review.",
    }


def _liquidity_score(liquidity: dict[str, Any], *, input_amount: float) -> dict[str, Any]:
    total = liquidity.get("totalLiquidity")
    min_liquidity = liquidity.get("minLiquidity")
    pool_count = int(liquidity.get("poolCount") or 0)
    missing_pool_ids = list(liquidity.get("missingPoolIds") or [])
    if total is None:
        return {
            "score": 0.0,
            "status": "unavailable",
            "totalLiquidity": None,
            "minLegLiquidity": None,
            "poolCount": pool_count,
            "missingPoolIds": missing_pool_ids,
            "detail": "No pool liquidity snapshots were available for this route.",
        }
    ratio = float(total) / max(input_amount, 1e-9)
    score = max(0.0, min(100.0, ratio))
    if missing_pool_ids:
        score = min(score, 60.0)
    status = "ok" if score >= 75 else "watch" if score >= 35 else "thin"
    return {
        "score": score,
        "status": status,
        "totalLiquidity": float(total),
        "minLegLiquidity": None if min_liquidity is None else float(min_liquidity),
        "poolCount": pool_count,
        "missingPoolIds": missing_pool_ids,
        "detail": (
            "Liquidity was estimated from stored pool snapshots."
            if not missing_pool_ids
            else "Some route pools were missing liquidity snapshots."
        ),
    }


def _risk_result(opportunity: dict[str, Any], risk_rules: dict[str, Any]) -> dict[str, Any]:
    failed_rules = [key for key, value in risk_rules.items() if value is False]
    passed_rules = [key for key, value in risk_rules.items() if value is True]
    approved = str(opportunity.get("status") or "").lower() == "approved" and not failed_rules
    reason = opportunity.get("skip_reason") or (failed_rules[0] if failed_rules else None)
    return {
        "approved": bool(approved),
        "status": "approved" if approved else "rejected",
        "reason": reason,
        "rules": risk_rules,
        "passedRules": passed_rules,
        "failedRules": failed_rules,
        "ruleLabels": {key: RISK_RULE_LABELS.get(key, key.replace("_", " ")) for key in risk_rules},
    }


def _confidence_calculation(
    *,
    opportunity: dict[str, Any],
    quote_freshness: dict[str, Any],
    profitability: dict[str, Any],
    price_impact: dict[str, Any],
    liquidity_score: dict[str, Any],
    risk_result: dict[str, Any],
) -> dict[str, Any]:
    stored_score = _number(opportunity.get("confidence_score"))
    if 0 <= stored_score <= 1:
        stored_score *= 100.0
    impact_component = max(0.0, 100.0 - _number(price_impact.get("maxBps")))
    freshness_component = 100.0 if quote_freshness.get("fresh") else 0.0
    profit_component = max(0.0, min(100.0, _number(profitability.get("expectedProfitBps"))))
    liquidity_component = _number(liquidity_score.get("score"))
    risk_component = 100.0 if risk_result.get("approved") else max(0.0, 100.0 - len(risk_result.get("failedRules") or []) * 15.0)
    computed = (
        impact_component * 0.25
        + freshness_component * 0.20
        + profit_component * 0.20
        + liquidity_component * 0.15
        + risk_component * 0.20
    )
    final_score = stored_score if stored_score else computed
    return {
        "score": max(0.0, min(100.0, final_score)),
        "storedScore": stored_score,
        "computedScore": max(0.0, min(100.0, computed)),
        "components": [
            {"key": "price_impact", "label": "Price impact", "weight": 0.25, "score": impact_component},
            {"key": "quote_freshness", "label": "Quote freshness", "weight": 0.20, "score": freshness_component},
            {"key": "profitability", "label": "Profitability", "weight": 0.20, "score": profit_component},
            {"key": "liquidity", "label": "Liquidity", "weight": 0.15, "score": liquidity_component},
            {"key": "risk_policy", "label": "Risk policy", "weight": 0.20, "score": risk_component},
        ],
    }


def _approval_decision(opportunity: dict[str, Any], risk_result: dict[str, Any]) -> dict[str, Any]:
    status = str(opportunity.get("status") or "unknown").lower()
    approved = status == "approved" and bool(risk_result.get("approved"))
    return {
        "decision": "approved" if approved else "rejected",
        "approved": approved,
        "status": status,
        "detail": (
            "Risk policy approved this route for paper/dry-run review only."
            if approved
            else "Route was rejected or is not eligible for dry-run review."
        ),
    }


def _rejection_reason(
    opportunity: dict[str, Any],
    risk_result: dict[str, Any],
    approval_decision: dict[str, Any],
) -> str:
    if approval_decision.get("approved"):
        return "none"
    return str(opportunity.get("skip_reason") or risk_result.get("reason") or "decision_not_approved")


def _decision_tree(
    *,
    route: list[dict[str, Any]],
    quote_freshness: dict[str, Any],
    profitability: dict[str, Any],
    price_impact: dict[str, Any],
    liquidity_score: dict[str, Any],
    risk_result: dict[str, Any],
    approval_decision: dict[str, Any],
    rejection_reason: str,
) -> list[dict[str, Any]]:
    return [
        {
            "key": "route_path",
            "label": "Route path stored",
            "status": "pass" if route else "fail",
            "detail": f"{len(route)} legs recorded." if route else "No route legs were recorded.",
        },
        {
            "key": "quote_freshness",
            "label": "Quote freshness checked",
            "status": "pass" if quote_freshness.get("fresh") else "fail",
            "detail": quote_freshness.get("detail") or "",
        },
        {
            "key": "profitability",
            "label": "Profitability calculated",
            "status": "pass" if profitability.get("profitableAfterFees") else "fail",
            "detail": f"Expected net profit {profitability.get('expectedNetProfit', 0):.6f}.",
        },
        {
            "key": "price_impact",
            "label": "Price impact calculated",
            "status": "pass" if price_impact.get("maxBps") is not None else "fail",
            "detail": f"Max impact {price_impact.get('maxBps', 0):.4f} bps.",
        },
        {
            "key": "liquidity_score",
            "label": "Liquidity scored",
            "status": "pass" if liquidity_score.get("status") in {"ok", "watch", "thin"} else "fail",
            "detail": liquidity_score.get("detail") or "",
        },
        {
            "key": "risk_result",
            "label": "Risk policy evaluated",
            "status": "pass" if risk_result.get("approved") else "fail",
            "detail": (
                "Risk approved the route."
                if risk_result.get("approved")
                else f"Risk rejected the route: {rejection_reason}."
            ),
        },
        {
            "key": "approval_decision",
            "label": "Final route decision",
            "status": "pass" if approval_decision.get("approved") else "fail",
            "detail": approval_decision.get("detail") or "",
        },
    ]


def _missing_required_fields(payload: dict[str, Any]) -> list[str]:
    missing = []
    for key, value in payload.items():
        if value is None:
            missing.append(key)
        elif isinstance(value, str) and not value:
            missing.append(key)
        elif isinstance(value, dict) and not value:
            missing.append(key)
    return missing


def _route_path_label(route: list[dict[str, Any]], opportunity: dict[str, Any]) -> str:
    if not route:
        asset_id = opportunity.get("input_asset_id", "unknown")
        return f"{asset_id}"
    assets = [route[0].get("inputAssetId")]
    assets.extend(leg.get("outputAssetId") for leg in route)
    return " -> ".join(str(asset) for asset in assets if asset is not None)


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _int_or_none(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
