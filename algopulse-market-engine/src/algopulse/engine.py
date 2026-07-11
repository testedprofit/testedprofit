from __future__ import annotations

import time
from collections import defaultdict
from itertools import permutations, product

from algopulse.config import STANDARD_QUOTE_SIZES
from algopulse.models import Opportunity, Pool, Quote
from algopulse.risk import RiskEngine
from algopulse.route_math import route_profit_breakdown


ALGO_ASSET_ID = 0
USDC_ASSET_ID = 31566704


class RouteEngine:
    def __init__(self, risk_engine: RiskEngine, trade_sizes: list[float] | None = None) -> None:
        self.risk_engine = risk_engine
        self.trade_sizes = trade_sizes or list(STANDARD_QUOTE_SIZES)

    def find_opportunities(self, pools: list[Pool]) -> list[Opportunity]:
        grouped: dict[tuple[int, int], list[Pool]] = defaultdict(list)
        for pool in pools:
            grouped[pool.asset_pair].append(pool)

        opportunities: list[Opportunity] = []
        opportunities.extend(self._find_two_leg_opportunities(grouped))
        opportunities.extend(self._find_triangular_opportunities(grouped))

        opportunities.sort(key=lambda item: item.expected_net_profit, reverse=True)
        return opportunities

    def _find_two_leg_opportunities(self, grouped: dict[tuple[int, int], list[Pool]]) -> list[Opportunity]:
        opportunities: list[Opportunity] = []
        for pair_pools in grouped.values():
            if len(pair_pools) < 2:
                continue
            input_assets = self._input_assets_for_pair(pair_pools[0])
            for input_asset_id in input_assets:
                for trade_size in self.trade_sizes:
                    for first, second in permutations(pair_pools, 2):
                        first_quote = first.quote(input_asset_id=input_asset_id, input_amount=trade_size)
                        if first_quote is None:
                            continue
                        second_quote = second.quote(
                            input_asset_id=first_quote.output_asset_id,
                            input_amount=first_quote.output_amount,
                        )
                        if second_quote is None:
                            continue
                        opportunities.append(
                            self._build_opportunity(
                                pools=[first, second],
                                quotes=[first_quote, second_quote],
                                input_asset_id=input_asset_id,
                                input_amount=trade_size,
                                route_kind="two_leg_venue_arb",
                            )
                        )
        return opportunities

    def _find_triangular_opportunities(self, grouped: dict[tuple[int, int], list[Pool]]) -> list[Opportunity]:
        middle_assets = self._triangle_middle_assets(grouped)
        opportunities: list[Opportunity] = []
        for middle_asset_id in middle_assets:
            for asset_path in (
                (ALGO_ASSET_ID, middle_asset_id, USDC_ASSET_ID, ALGO_ASSET_ID),
                (ALGO_ASSET_ID, USDC_ASSET_ID, middle_asset_id, ALGO_ASSET_ID),
            ):
                opportunities.extend(
                    self._find_asset_path_opportunities(
                        grouped=grouped,
                        asset_path=asset_path,
                        route_kind="three_leg_triangle",
                    )
                )
        return opportunities

    def _find_asset_path_opportunities(
        self,
        *,
        grouped: dict[tuple[int, int], list[Pool]],
        asset_path: tuple[int, ...],
        route_kind: str,
    ) -> list[Opportunity]:
        leg_pool_sets = [grouped.get(_asset_pair(left, right), []) for left, right in zip(asset_path, asset_path[1:])]
        if any(not pool_set for pool_set in leg_pool_sets):
            return []

        opportunities: list[Opportunity] = []
        for trade_size in self.trade_sizes:
            for route_pools in product(*leg_pool_sets):
                quotes: list[Quote] = []
                amount = trade_size
                for pool, input_asset_id, expected_output_asset_id in zip(route_pools, asset_path, asset_path[1:]):
                    quote = pool.quote(input_asset_id=input_asset_id, input_amount=amount)
                    if quote is None or quote.output_asset_id != expected_output_asset_id:
                        quotes = []
                        break
                    quotes.append(quote)
                    amount = quote.output_amount
                if not quotes:
                    continue
                opportunities.append(
                    self._build_opportunity(
                        pools=list(route_pools),
                        quotes=quotes,
                        input_asset_id=asset_path[0],
                        input_amount=trade_size,
                        route_kind=route_kind,
                    )
                )
        return opportunities

    def _build_opportunity(
        self,
        *,
        pools: list[Pool],
        quotes: list[Quote],
        input_asset_id: int,
        input_amount: float,
        route_kind: str,
    ) -> Opportunity:
        # Inherit source/pool capture times — never invent wall-clock freshness.
        max_age = float(self.risk_engine.policy.max_route_age_seconds)
        capture_times: list[float] = []
        for pool in pools:
            raw = getattr(pool, "captured_at", None)
            try:
                captured = float(raw) if raw is not None else 0.0
            except (TypeError, ValueError):
                captured = 0.0
            if captured <= 0:
                return self._unavailable_opportunity(
                    pools=pools,
                    quotes=quotes,
                    input_asset_id=input_asset_id,
                    input_amount=input_amount,
                    route_kind=route_kind,
                    reason="quote_unavailable",
                    detail="missing_pool_captured_at",
                )
            capture_times.append(captured)

        fee_legs = [(float(quote.fee_amount), int(quote.input_asset_id)) for quote in quotes]
        leg_inputs = [float(quote.input_amount) for quote in quotes]
        expected_final_amount = quotes[-1].output_amount
        breakdown = self._profit_breakdown(
            input_amount=input_amount,
            final_amount=expected_final_amount,
            quotes=quotes,
            pools=pools,
            input_asset_id=input_asset_id,
            leg_count=len(quotes),
            fee_legs=fee_legs,
            leg_input_amounts=leg_inputs,
        )
        if not breakdown.get("fee_conversion_ok", False):
            return self._unavailable_opportunity(
                pools=pools,
                quotes=quotes,
                input_asset_id=input_asset_id,
                input_amount=input_amount,
                route_kind=route_kind,
                reason="fee_conversion_unavailable",
                detail="unconvertible_dex_or_network_fee",
                capture_times=capture_times,
                breakdown=breakdown,
            )

        fee_evidence = list(breakdown.get("dex_fee_evidence") or [])
        route = [
            self._route_leg(
                pool=pool,
                quote=quote,
                route_kind=route_kind,
                captured_at=capture_times[idx],
                expires_at=capture_times[idx] + max_age,
                fee_evidence=fee_evidence[idx] if idx < len(fee_evidence) else None,
            )
            for idx, (pool, quote) in enumerate(zip(pools, quotes))
        ]
        expected_net = breakdown["expected_net_profit"]
        max_price_impact_bps = max(quote.price_impact_bps for quote in quotes)
        involved_asset_ids = sorted(
            {
                asset_id
                for quote in quotes
                for asset_id in (quote.input_asset_id, quote.output_asset_id)
            }
        )
        opportunity = Opportunity.from_route(
            route=route,
            input_asset_id=input_asset_id,
            input_amount=input_amount,
            expected_final_amount=expected_final_amount,
            expected_net_profit=expected_net,
            expected_profit_bps=(expected_net / input_amount) * 10_000,
            max_price_impact_bps=max_price_impact_bps,
            involved_pool_ids=[pool.pool_id for pool in pools],
            involved_asset_ids=involved_asset_ids,
            gross_profit=breakdown["gross_profit"],
            estimated_network_fee=breakdown["estimated_network_fee"],
            total_dex_fees=breakdown["total_dex_fees"],
            total_price_impact_bps=breakdown["total_price_impact_bps"],
            slippage_buffer=breakdown["slippage_buffer"],
        )
        decision = self.risk_engine.assess(opportunity, pools)
        opportunity.status = "approved" if decision.approved else "rejected"
        opportunity.skip_reason = None if decision.approved else decision.reason
        opportunity.risk_rules = {
            **decision.rules,
            "fee_unit_asset_id": breakdown.get("fee_unit_asset_id", input_asset_id),
            "dex_fees_embedded_in_output": breakdown.get("dex_fees_embedded_in_output", True),
            "fee_conversion_ok": True,
            "fee_unit_consistent": bool(breakdown.get("fee_unit_consistent", False)),
        }
        return opportunity

    def _unavailable_opportunity(
        self,
        *,
        pools: list[Pool],
        quotes: list[Quote],
        input_asset_id: int,
        input_amount: float,
        route_kind: str,
        reason: str,
        detail: str,
        capture_times: list[float] | None = None,
        breakdown: dict | None = None,
    ) -> Opportunity:
        """Fail-closed rejected opportunity without inventing capture times or fee units."""
        max_age = float(self.risk_engine.policy.max_route_age_seconds)
        route: list[dict] = []
        for idx, (pool, quote) in enumerate(zip(pools, quotes)):
            if capture_times is not None and idx < len(capture_times):
                captured_at = capture_times[idx]
                expires_at = captured_at + max_age
            else:
                # Missing capture: leave explicit nulls — never time.time().
                captured_at = None
                expires_at = None
            route.append(
                {
                    "route_kind": route_kind,
                    "venue": pool.venue_id,
                    "pool_id": pool.pool_id,
                    "input_asset_id": quote.input_asset_id,
                    "output_asset_id": quote.output_asset_id,
                    "input_amount": quote.input_amount,
                    "expected_output": quote.output_amount,
                    "fee_amount": quote.fee_amount,
                    "fee_asset_id": int(quote.input_asset_id),
                    "fee_amount_in_input_asset": None,
                    "price_impact_bps": quote.price_impact_bps,
                    "block_round": pool.block_round,
                    "captured_at": captured_at,
                    "expires_at": expires_at,
                    "unavailable_detail": detail,
                }
            )
        expected_final = quotes[-1].output_amount if quotes else 0.0
        opportunity = Opportunity.from_route(
            route=route,
            input_asset_id=input_asset_id,
            input_amount=input_amount,
            expected_final_amount=expected_final,
            expected_net_profit=(breakdown or {}).get("expected_net_profit", expected_final - input_amount),
            expected_profit_bps=0.0,
            max_price_impact_bps=max((q.price_impact_bps for q in quotes), default=0.0),
            involved_pool_ids=[pool.pool_id for pool in pools],
            involved_asset_ids=sorted(
                {a for q in quotes for a in (q.input_asset_id, q.output_asset_id)}
            ),
            gross_profit=expected_final - input_amount,
            estimated_network_fee=(breakdown or {}).get("estimated_network_fee", 0.0),
            total_dex_fees=(breakdown or {}).get("total_dex_fees", 0.0),
            slippage_buffer=(breakdown or {}).get("slippage_buffer", 0.0),
        )
        opportunity.status = "rejected"
        opportunity.skip_reason = reason
        opportunity.risk_rules = {
            "fee_conversion_ok": False if reason == "fee_conversion_unavailable" else None,
            "fee_unit_consistent": False,
            "quote_capture_ok": reason != "quote_unavailable",
            "unavailable_detail": detail,
        }
        return opportunity

    def _route_leg(
        self,
        *,
        pool: Pool,
        quote: Quote,
        route_kind: str,
        captured_at: float,
        expires_at: float,
        fee_evidence: dict | None = None,
    ) -> dict:
        evidence = fee_evidence or {}
        return {
            "route_kind": route_kind,
            "venue": pool.venue_id,
            "pool_id": pool.pool_id,
            "input_asset_id": quote.input_asset_id,
            "output_asset_id": quote.output_asset_id,
            "input_amount": quote.input_amount,
            "expected_output": quote.output_amount,
            # Native DEX fee (in leg input asset). Not summable across assets.
            "fee_amount": quote.fee_amount,
            "fee_asset_id": int(quote.input_asset_id),
            # Same fee in route input asset; None when conversion unavailable (never fake zero).
            "fee_amount_in_input_asset": evidence.get("amount_in_input_asset") if evidence else None,
            "price_impact_bps": quote.price_impact_bps,
            "block_round": pool.block_round,
            "captured_at": captured_at,
            "expires_at": expires_at,
        }

    def _profit_breakdown(
        self,
        *,
        input_amount: float,
        final_amount: float,
        quotes: list[Quote],
        pools: list[Pool],
        input_asset_id: int,
        leg_count: int,
        fee_legs: list[tuple[float, int]],
        leg_input_amounts: list[float] | None = None,
    ) -> dict:
        return route_profit_breakdown(
            input_amount=input_amount,
            final_amount=final_amount,
            price_impact_bps=[quote.price_impact_bps for quote in quotes],
            estimated_network_fee=self._estimated_network_fee(leg_count),
            safety_buffer_bps=self.risk_engine.policy.safety_buffer_bps,
            minimum_safety_buffer=max(0.0, self.risk_engine.policy.min_profit_absolute * 0.25),
            dex_fee_legs=fee_legs,
            fee_pools=pools,
            leg_input_amounts=leg_input_amounts or [float(q.input_amount) for q in quotes],
            input_asset_id=int(input_asset_id),
            network_fee_asset_id=0,  # network fees paid in ALGO
        ).to_dict()

    def _estimated_network_fee(self, leg_count: int) -> float:
        two_leg_fee = self.risk_engine.policy.estimated_network_fee
        return two_leg_fee * max(1.0, leg_count / 2)

    def _triangle_middle_assets(self, grouped: dict[tuple[int, int], list[Pool]]) -> list[int]:
        algo_assets = {
            pair[1] if pair[0] == ALGO_ASSET_ID else pair[0]
            for pair in grouped
            if ALGO_ASSET_ID in pair and USDC_ASSET_ID not in pair
        }
        usdc_assets = {
            pair[1] if pair[0] == USDC_ASSET_ID else pair[0]
            for pair in grouped
            if USDC_ASSET_ID in pair and ALGO_ASSET_ID not in pair
        }
        return sorted(asset_id for asset_id in algo_assets & usdc_assets if asset_id not in {ALGO_ASSET_ID, USDC_ASSET_ID})

    def _input_assets_for_pair(self, pool: Pool) -> list[int]:
        if ALGO_ASSET_ID in pool.asset_pair:
            return [ALGO_ASSET_ID]
        return [pool.asset_a_id, pool.asset_b_id]


def _asset_pair(left: int, right: int) -> tuple[int, int]:
    return tuple(sorted((left, right)))
