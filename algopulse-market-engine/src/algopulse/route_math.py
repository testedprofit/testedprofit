from __future__ import annotations

import hashlib
import json
from collections import deque
from dataclasses import asdict, dataclass
from typing import Any


BPS_DENOMINATOR = 10_000


@dataclass(frozen=True)
class ConstantProductQuote:
    input_amount: float
    output_amount: float
    fee_amount: float
    price_impact_bps: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class DexFeeEvidence:
    """One DEX fee leg with native asset and value normalized to route input asset."""

    amount: float
    asset_id: int
    amount_in_input_asset: float | None
    input_asset_id: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RouteProfitBreakdown:
    gross_profit: float
    estimated_network_fee: float
    total_dex_fees: float
    total_price_impact_bps: float
    max_price_impact_bps: float
    slippage_buffer: float
    expected_net_profit: float
    expected_profit_bps: float
    fee_unit_asset_id: int = 0
    dex_fee_evidence: tuple[dict, ...] = ()
    # AMM outputs already embed DEX fees; net does not re-subtract them.
    dex_fees_embedded_in_output: bool = True
    fee_conversion_ok: bool = True
    fee_unit_consistent: bool = True
    network_fee_conversion_ok: bool = True

    def to_dict(self) -> dict:
        data = asdict(self)
        data["dex_fee_evidence"] = list(self.dex_fee_evidence)
        return data


def canonical_route_hash(route: list[dict], length: int = 16) -> str:
    payload = json.dumps(route, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


def constant_product_quote(
    *,
    reserve_in: float,
    reserve_out: float,
    input_amount: float,
    fee_bps: float,
) -> ConstantProductQuote | None:
    if reserve_in <= 0 or reserve_out <= 0 or input_amount <= 0:
        return None
    fee_rate = fee_bps / BPS_DENOMINATOR
    fee_amount = input_amount * fee_rate
    amount_after_fee = input_amount - fee_amount
    output_amount = (reserve_out * amount_after_fee) / (reserve_in + amount_after_fee)
    mid_price_output = input_amount * (reserve_out / reserve_in)
    price_impact_bps = 0.0
    if mid_price_output > 0:
        price_impact_bps = max(0.0, (1 - (output_amount / mid_price_output)) * BPS_DENOMINATOR)
    return ConstantProductQuote(
        input_amount=input_amount,
        output_amount=output_amount,
        fee_amount=fee_amount,
        price_impact_bps=price_impact_bps,
    )


def mid_rate(pool: Any, from_asset_id: int, to_asset_id: int) -> float | None:
    """Return mid-price units of to_asset per 1 from_asset from pool reserves."""
    from_id = int(from_asset_id)
    to_id = int(to_asset_id)
    if from_id == to_id:
        return 1.0
    a_id = int(getattr(pool, "asset_a_id", -1))
    b_id = int(getattr(pool, "asset_b_id", -1))
    ra = float(getattr(pool, "reserve_a", 0.0) or 0.0)
    rb = float(getattr(pool, "reserve_b", 0.0) or 0.0)
    if ra <= 0 or rb <= 0:
        return None
    if from_id == a_id and to_id == b_id:
        return rb / ra
    if from_id == b_id and to_id == a_id:
        return ra / rb
    return None


def convert_amount_to_asset(
    amount: float,
    from_asset_id: int,
    to_asset_id: int,
    pools: list[Any],
) -> float | None:
    """Convert amount via pool mid prices (BFS). Returns None if unconvertible."""
    amount = float(amount)
    if amount == 0:
        return 0.0
    from_id = int(from_asset_id)
    to_id = int(to_asset_id)
    if from_id == to_id:
        return amount
    graph: dict[int, list[tuple[int, Any]]] = {}
    for pool in pools:
        a = int(getattr(pool, "asset_a_id", -1))
        b = int(getattr(pool, "asset_b_id", -1))
        if a < 0 or b < 0:
            continue
        graph.setdefault(a, []).append((b, pool))
        graph.setdefault(b, []).append((a, pool))

    queue: deque[tuple[int, float]] = deque([(from_id, amount)])
    seen = {from_id}
    while queue:
        asset_id, value = queue.popleft()
        if asset_id == to_id:
            return value
        for neighbor, pool in graph.get(asset_id, []):
            if neighbor in seen:
                continue
            rate = mid_rate(pool, asset_id, neighbor)
            if rate is None or rate <= 0:
                continue
            seen.add(neighbor)
            queue.append((neighbor, value * rate))
    # Fail closed: never invent a zero conversion for unknown fees.
    return None


def normalize_dex_fees_to_input_asset(
    *,
    fee_legs: list[tuple[float, int]] | tuple[tuple[float, int], ...],
    input_asset_id: int,
    pools: list[Any],
    route_input_amount: float | None = None,
    leg_input_amounts: list[float] | tuple[float, ...] | None = None,
) -> tuple[float | None, list[dict], bool]:
    """Normalize DEX fee legs into route input-asset units.

    Prefer route-path quote conversion. Never treats unconvertible fees as zero.
    Returns (total_or_none, evidence, conversion_ok).
    """
    input_id = int(input_asset_id)
    evidence: list[dict] = []
    total = 0.0
    conversion_ok = True
    path_inputs = list(leg_input_amounts) if leg_input_amounts is not None else None
    route_in = float(route_input_amount) if route_input_amount is not None else None

    for idx, (raw_amount, fee_asset_id) in enumerate(fee_legs):
        amount = max(0.0, float(raw_amount))
        fee_asset = int(fee_asset_id)
        method = "identity"
        normalized: float | None
        if amount == 0:
            normalized = 0.0
            method = "zero_fee"
        elif fee_asset == input_id:
            normalized = amount
            method = "identity"
        elif (
            route_in is not None
            and route_in > 0
            and path_inputs is not None
            and idx < len(path_inputs)
            and float(path_inputs[idx]) > 0
        ):
            normalized = amount * (route_in / float(path_inputs[idx]))
            method = "route_path_quote"
        else:
            normalized = convert_amount_to_asset(amount, fee_asset, input_id, pools)
            method = "pool_mid_fallback" if normalized is not None else "unavailable"

        if normalized is None:
            conversion_ok = False
            row = DexFeeEvidence(
                amount=amount,
                asset_id=fee_asset,
                amount_in_input_asset=None,  # never zero-fill unknown conversions
                input_asset_id=input_id,
            ).to_dict()
            row["conversionMethod"] = "unavailable"
            row["conversionOk"] = False
            evidence.append(row)
            continue

        row = DexFeeEvidence(
            amount=amount,
            asset_id=fee_asset,
            amount_in_input_asset=float(normalized),
            input_asset_id=input_id,
        ).to_dict()
        row["conversionMethod"] = method
        row["conversionOk"] = True
        evidence.append(row)
        total += float(normalized)

    if not conversion_ok:
        return None, evidence, False
    return total, evidence, True


def route_profit_breakdown(
    *,
    input_amount: float,
    final_amount: float,
    dex_fee_amounts: list[float] | tuple[float, ...] | None = None,
    price_impact_bps: list[float] | tuple[float, ...],
    estimated_network_fee: float,
    safety_buffer_bps: float,
    minimum_safety_buffer: float,
    # Preferred: per-leg fees with asset ids + pools for normalization.
    dex_fee_legs: list[tuple[float, int]] | tuple[tuple[float, int], ...] | None = None,
    fee_pools: list[Any] | None = None,
    leg_input_amounts: list[float] | tuple[float, ...] | None = None,
    input_asset_id: int = 0,
    network_fee_asset_id: int = 0,
) -> RouteProfitBreakdown:
    """Compute route P&L in a single unit (route input asset).

    AMM quote outputs already include DEX fee drag, so net profit is:
      gross - network_fee(normalized) - slippage_buffer
    without re-subtracting DEX fees. ``total_dex_fees`` is evidence only, in
    input-asset units, for fee-buffer comparisons.
    """
    if input_amount <= 0:
        raise ValueError("input_amount must be positive")
    if final_amount < 0:
        raise ValueError("final_amount cannot be negative")
    if estimated_network_fee < 0 or safety_buffer_bps < 0 or minimum_safety_buffer < 0:
        raise ValueError("fees and buffers cannot be negative")

    pools = list(fee_pools or [])
    input_id = int(input_asset_id)
    if dex_fee_legs is not None:
        total_dex_fees_opt, fee_evidence, dex_ok = normalize_dex_fees_to_input_asset(
            fee_legs=dex_fee_legs,
            input_asset_id=input_id,
            pools=pools,
            route_input_amount=input_amount,
            leg_input_amounts=leg_input_amounts,
        )
        total_dex_fees = float(total_dex_fees_opt or 0.0)
    else:
        # Backward compatible: amounts assumed already in input-asset units.
        raw = [max(0.0, float(v)) for v in (dex_fee_amounts or [])]
        total_dex_fees = sum(raw)
        dex_ok = True
        fee_evidence = [
            {
                **DexFeeEvidence(
                    amount=amount,
                    asset_id=input_id,
                    amount_in_input_asset=amount,
                    input_asset_id=input_id,
                ).to_dict(),
                "conversionMethod": "identity",
                "conversionOk": True,
            }
            for amount in raw
        ]

    network_native = max(0.0, float(estimated_network_fee))
    network_ok = True
    if int(network_fee_asset_id) == input_id or network_native == 0:
        network_in_input: float | None = network_native
    else:
        network_in_input = convert_amount_to_asset(
            network_native,
            int(network_fee_asset_id),
            input_id,
            pools,
        )
        if network_in_input is None:
            network_ok = False
            network_in_input = 0.0

    fee_conversion_ok = bool(dex_ok and network_ok)
    fee_unit_consistent = bool(
        fee_conversion_ok
        and all(bool(item.get("conversionOk", False)) for item in fee_evidence)
    )

    gross_profit = final_amount - input_amount
    slippage_buffer = max(minimum_safety_buffer, input_amount * safety_buffer_bps / BPS_DENOMINATOR)
    # Do not re-subtract DEX fees: already embedded in AMM final_amount.
    if fee_conversion_ok:
        expected_net_profit = gross_profit - float(network_in_input) - slippage_buffer
    else:
        # Fail closed: do not publish a ready net when units are unknown.
        expected_net_profit = gross_profit - slippage_buffer
    expected_profit_bps = (expected_net_profit / input_amount) * BPS_DENOMINATOR
    impact_values = [max(0.0, float(value)) for value in price_impact_bps]
    return RouteProfitBreakdown(
        gross_profit=gross_profit,
        estimated_network_fee=float(network_in_input or 0.0),
        total_dex_fees=float(total_dex_fees),
        total_price_impact_bps=sum(impact_values),
        max_price_impact_bps=max(impact_values, default=0.0),
        slippage_buffer=slippage_buffer,
        expected_net_profit=expected_net_profit,
        expected_profit_bps=expected_profit_bps,
        fee_unit_asset_id=input_id,
        dex_fee_evidence=tuple(fee_evidence),
        dex_fees_embedded_in_output=True,
        fee_conversion_ok=fee_conversion_ok,
        fee_unit_consistent=fee_unit_consistent,
        network_fee_conversion_ok=network_ok,
    )
