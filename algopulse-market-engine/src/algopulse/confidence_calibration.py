from __future__ import annotations

from typing import Any


CONFIDENCE_BUCKETS = (
    (0.90, 1.00, "0.90-1.00"),
    (0.80, 0.899999, "0.80-0.89"),
    (0.70, 0.799999, "0.70-0.79"),
    (0.60, 0.699999, "0.60-0.69"),
    (0.50, 0.599999, "0.50-0.59"),
    (0.00, 0.499999, "0.00-0.49"),
)


def build_confidence_calibration_report(paper_trades: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [_calibration_row(row) for row in paper_trades]
    resolved = [row for row in rows if row["resolved"]]
    buckets = [_bucket_report(label, low, high, resolved) for low, high, label in CONFIDENCE_BUCKETS]
    overall_success_rate = _rate(sum(1 for row in resolved if row["success"]), len(resolved))
    average_confidence = _average([row["confidence"] for row in resolved])
    calibration_error = _weighted_average(
        [abs(bucket["successRate"] - bucket["averageConfidence"]) for bucket in buckets if bucket["count"]],
        [bucket["count"] for bucket in buckets if bucket["count"]],
    )
    verdict = _verdict(len(resolved), calibration_error)
    return {
        "buckets": buckets,
        "summary": {
            "paperTradeCount": len(rows),
            "resolvedCount": len(resolved),
            "successCount": sum(1 for row in resolved if row["success"]),
            "failureCount": sum(1 for row in resolved if not row["success"]),
            "overallSuccessRate": overall_success_rate,
            "averageConfidence": average_confidence,
            "calibrationError": calibration_error,
            "verdict": verdict,
            "verdictDetail": _verdict_detail(verdict, len(resolved), calibration_error),
        },
        "sampleTrades": rows[:12],
        "source": "stored" if rows else "unavailable",
        "liveExecutionTouched": False,
        "signerCodeTouched": False,
    }


def _calibration_row(row: dict[str, Any]) -> dict[str, Any]:
    confidence = _confidence(row.get("confidence_score"))
    expected_profit = _number(row.get("expected_net_profit") if row.get("expected_net_profit") is not None else row.get("expected_profit"))
    simulated_profit = _resolved_value(row, "simulated_profit_30s", "checked_30s_at")
    quote_decay = _resolved_value(row, "quote_decay_30s", "checked_30s_at")
    checkpoint = "30s"
    if simulated_profit is None:
        simulated_profit = _resolved_value(row, "simulated_profit_5s", "checked_5s_at")
        quote_decay = _resolved_value(row, "quote_decay_5s", "checked_5s_at")
        checkpoint = "5s"
    resolved = simulated_profit is not None
    success = bool(row.get("success")) if row.get("success") is not None else bool(resolved and simulated_profit > 0)
    return {
        "paperTradeId": row.get("id"),
        "routeHash": row.get("route_hash"),
        "confidence": confidence,
        "confidenceScore": round(confidence, 4),
        "expectedProfit": expected_profit,
        "simulatedProfit": simulated_profit,
        "quoteDecay": quote_decay,
        "success": success,
        "resolved": resolved,
        "checkpoint": checkpoint if resolved else "pending",
        "createdAt": row.get("created_at"),
    }


def _bucket_report(label: str, low: float, high: float, rows: list[dict[str, Any]]) -> dict[str, Any]:
    bucket_rows = [row for row in rows if low <= row["confidence"] <= high]
    count = len(bucket_rows)
    success_count = sum(1 for row in bucket_rows if row["success"])
    success_rate = _rate(success_count, count)
    average_confidence = _average([row["confidence"] for row in bucket_rows])
    return {
        "label": label,
        "minConfidence": low,
        "maxConfidence": 1.0 if high > 0.999 else high,
        "count": count,
        "successCount": success_count,
        "failureCount": count - success_count,
        "successRate": success_rate,
        "averageConfidence": average_confidence,
        "calibrationError": abs(success_rate - average_confidence) if count else 0.0,
        "averageQuoteDecay": _average([row["quoteDecay"] for row in bucket_rows if row["quoteDecay"] is not None]),
        "averageExpectedProfit": _average([row["expectedProfit"] for row in bucket_rows]),
        "averageSimulatedProfit": _average([row["simulatedProfit"] for row in bucket_rows if row["simulatedProfit"] is not None]),
    }


def _confidence(value: Any) -> float:
    numeric = _number(value)
    if numeric > 1:
        numeric = numeric / 100
    return max(0.0, min(1.0, numeric))


def _resolved_value(row: dict[str, Any], value_key: str, checked_key: str) -> float | None:
    if row.get(checked_key) is None:
        return None
    return _number(row.get(value_key))


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _weighted_average(values: list[float], weights: list[int]) -> float:
    total_weight = sum(weights)
    if not values or total_weight <= 0:
        return 0.0
    return sum(value * weight for value, weight in zip(values, weights, strict=True)) / total_weight


def _rate(numerator: int, denominator: int) -> float:
    return (numerator / denominator) if denominator else 0.0


def _verdict(resolved_count: int, calibration_error: float) -> str:
    if resolved_count < 20:
        return "under_sampled"
    if calibration_error > 0.25:
        return "needs_adjustment"
    if calibration_error > 0.12:
        return "watch"
    return "calibrated"


def _verdict_detail(verdict: str, resolved_count: int, calibration_error: float) -> str:
    if verdict == "under_sampled":
        return f"Only {resolved_count} resolved paper trades. Collect more samples before changing confidence math."
    if verdict == "needs_adjustment":
        return f"Observed success differs from predicted confidence by {calibration_error * 100:.1f} percentage points."
    if verdict == "watch":
        return f"Calibration gap is {calibration_error * 100:.1f} percentage points; watch more paper data before changing weights."
    return f"Calibration gap is {calibration_error * 100:.1f} percentage points; confidence scores are currently useful."
