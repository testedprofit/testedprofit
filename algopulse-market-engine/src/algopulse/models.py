from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field

from algopulse.route_math import canonical_route_hash
from algopulse.route_math import constant_product_quote


@dataclass(frozen=True)
class Asset:
    asset_id: int
    symbol: str
    name: str
    decimals: int
    is_verified: bool = False
    is_allowlisted: bool = False
    has_freeze: bool = False
    has_clawback: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Venue:
    venue_id: str
    name: str
    kind: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Quote:
    pool_id: str
    venue_id: str
    input_asset_id: int
    output_asset_id: int
    input_amount: float
    output_amount: float
    fee_amount: float
    price_impact_bps: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Pool:
    pool_id: str
    venue_id: str
    app_id: int
    asset_a_id: int
    asset_b_id: int
    reserve_a: float
    reserve_b: float
    fee_bps: int
    block_round: int
    captured_at: float = field(default_factory=time.time)

    @property
    def asset_pair(self) -> tuple[int, int]:
        return tuple(sorted((self.asset_a_id, self.asset_b_id)))

    def to_dict(self) -> dict:
        data = asdict(self)
        data["price_a_in_b"] = self.reserve_b / self.reserve_a if self.reserve_a else 0.0
        data["price_b_in_a"] = self.reserve_a / self.reserve_b if self.reserve_b else 0.0
        return data

    def quote(self, input_asset_id: int, input_amount: float) -> Quote | None:
        if input_amount <= 0:
            return None
        if input_asset_id == self.asset_a_id:
            reserve_in = self.reserve_a
            reserve_out = self.reserve_b
            output_asset_id = self.asset_b_id
        elif input_asset_id == self.asset_b_id:
            reserve_in = self.reserve_b
            reserve_out = self.reserve_a
            output_asset_id = self.asset_a_id
        else:
            return None

        if reserve_in <= 0 or reserve_out <= 0:
            return None

        quote = constant_product_quote(
            reserve_in=reserve_in,
            reserve_out=reserve_out,
            input_amount=input_amount,
            fee_bps=self.fee_bps,
        )
        if quote is None:
            return None

        return Quote(
            pool_id=self.pool_id,
            venue_id=self.venue_id,
            input_asset_id=input_asset_id,
            output_asset_id=output_asset_id,
            input_amount=input_amount,
            output_amount=quote.output_amount,
            fee_amount=quote.fee_amount,
            price_impact_bps=quote.price_impact_bps,
        )


@dataclass
class Opportunity:
    route_hash: str
    route: list[dict]
    input_asset_id: int
    input_amount: float
    expected_final_amount: float
    expected_net_profit: float
    expected_profit_bps: float
    max_price_impact_bps: float
    involved_pool_ids: list[str]
    involved_asset_ids: list[int]
    gross_profit: float = 0.0
    estimated_network_fee: float = 0.0
    total_dex_fees: float = 0.0
    total_price_impact_bps: float = 0.0
    slippage_buffer: float = 0.0
    status: str = "new"
    skip_reason: str | None = None
    confidence_score: float = 0.0
    risk_rules: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    @classmethod
    def from_route(
        cls,
        route: list[dict],
        input_asset_id: int,
        input_amount: float,
        expected_final_amount: float,
        expected_net_profit: float,
        expected_profit_bps: float,
        max_price_impact_bps: float,
        involved_pool_ids: list[str],
        involved_asset_ids: list[int],
        gross_profit: float | None = None,
        estimated_network_fee: float = 0.0,
        total_dex_fees: float = 0.0,
        total_price_impact_bps: float | None = None,
        slippage_buffer: float | None = None,
    ) -> "Opportunity":
        route_hash = canonical_route_hash(route)
        gross_profit = expected_final_amount - input_amount if gross_profit is None else gross_profit
        total_price_impact_bps = max_price_impact_bps if total_price_impact_bps is None else total_price_impact_bps
        if slippage_buffer is None:
            slippage_buffer = max(0.0, gross_profit - estimated_network_fee - expected_net_profit)
        confidence = max(0.0, min(100.0, 100.0 - max_price_impact_bps))
        return cls(
            route_hash=route_hash,
            route=route,
            input_asset_id=input_asset_id,
            input_amount=input_amount,
            expected_final_amount=expected_final_amount,
            expected_net_profit=expected_net_profit,
            expected_profit_bps=expected_profit_bps,
            max_price_impact_bps=max_price_impact_bps,
            involved_pool_ids=involved_pool_ids,
            involved_asset_ids=sorted(set(involved_asset_ids)),
            gross_profit=gross_profit,
            estimated_network_fee=estimated_network_fee,
            total_dex_fees=total_dex_fees,
            total_price_impact_bps=total_price_impact_bps,
            slippage_buffer=slippage_buffer,
            confidence_score=confidence,
        )

    def to_dict(self) -> dict:
        return asdict(self)
