"""Liquidity-aware pair selection and adaptive trade sizing for paper evaluation.

Does not change execution/signer allowlists or risk limit floors.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from algopulse.models import Opportunity, Pool


SKIP_LOW_CROSS_VENUE_LIQUIDITY = "pair_skipped_low_cross_venue_liquidity"

# Bounded probe ladder for adaptive sizing (ALGO-in). Risk max_trade_size still binds.
PROBE_TRADE_SIZES = (0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0)


def pool_liquidity_estimate(pool: Pool | dict) -> float:
    if isinstance(pool, Pool):
        reserve_a = float(pool.reserve_a)
        reserve_b = float(pool.reserve_b)
    else:
        reserve_a = float(pool.get("reserveA") or pool.get("reserve_a") or 0.0)
        reserve_b = float(pool.get("reserveB") or pool.get("reserve_b") or 0.0)
    if reserve_a <= 0 or reserve_b <= 0:
        return 0.0
    return math.sqrt(reserve_a * reserve_b)


def min_reserve(pool: Pool | dict) -> float:
    if isinstance(pool, Pool):
        return min(float(pool.reserve_a), float(pool.reserve_b))
    return min(
        float(pool.get("reserveA") or pool.get("reserve_a") or 0.0),
        float(pool.get("reserveB") or pool.get("reserve_b") or 0.0),
    )


def cross_venue_liquidity(tinyman_pools: list, pact_pools: list) -> float:
    """Usable depth is limited by the weaker venue's best pool liquidity."""
    tiny = max((pool_liquidity_estimate(p) for p in tinyman_pools), default=0.0)
    pact = max((pool_liquidity_estimate(p) for p in pact_pools), default=0.0)
    return min(tiny, pact)


def venue_min_usable_reserve(pools: list) -> float:
    return max((min_reserve(p) for p in pools), default=0.0)


def pair_is_usable(
    tinyman_pools: list,
    pact_pools: list,
    *,
    min_cross_venue_liquidity: float,
    min_venue_reserve: float,
) -> tuple[bool, str | None]:
    if not tinyman_pools or not pact_pools:
        return False, SKIP_LOW_CROSS_VENUE_LIQUIDITY
    if venue_min_usable_reserve(tinyman_pools) < min_venue_reserve:
        return False, SKIP_LOW_CROSS_VENUE_LIQUIDITY
    if venue_min_usable_reserve(pact_pools) < min_venue_reserve:
        return False, SKIP_LOW_CROSS_VENUE_LIQUIDITY
    if cross_venue_liquidity(tinyman_pools, pact_pools) < min_cross_venue_liquidity:
        return False, SKIP_LOW_CROSS_VENUE_LIQUIDITY
    return True, None


def rank_shared_pairs(
    pools: list[Pool],
    *,
    network: str = "mainnet",
    preferred_pairs: tuple[tuple[int, int], ...] = (),
    min_cross_venue_liquidity: float = 50.0,
    min_venue_reserve: float = 1.0,
) -> dict[str, Any]:
    """Rank every dual-venue shared pair; skip unusable dust with an explicit reason.

    Liquidity (cross-venue depth) is primary. Preferred pair labels are secondary
    only among equally liquid candidates — never elevates empty PNET-style venues.
    """
    by_pair: dict[tuple[int, int], dict[str, list[Pool]]] = defaultdict(lambda: defaultdict(list))
    for pool in pools:
        if pool.reserve_a <= 0 or pool.reserve_b <= 0:
            continue
        if pool.venue_id not in {"tinyman", "pact"}:
            continue
        by_pair[pool.asset_pair][pool.venue_id].append(pool)

    accepted: list[dict] = []
    skipped: list[dict] = []

    for pair, venues in by_pair.items():
        tinyman = venues.get("tinyman") or []
        pact = venues.get("pact") or []
        if not tinyman or not pact:
            continue
        row = {
            "pair": list(pair),
            "tinymanPools": [_pool_summary(p) for p in tinyman],
            "pactPools": [_pool_summary(p) for p in pact],
            "crossVenueLiquidity": cross_venue_liquidity(tinyman, pact),
            "tinymanBestMinReserve": venue_min_usable_reserve(tinyman),
            "pactBestMinReserve": venue_min_usable_reserve(pact),
        }
        usable, reason = pair_is_usable(
            tinyman,
            pact,
            min_cross_venue_liquidity=min_cross_venue_liquidity,
            min_venue_reserve=min_venue_reserve,
        )
        if not usable:
            row["status"] = "skipped"
            row["skipReason"] = reason
            skipped.append(row)
            continue
        row["status"] = "accepted"
        row["skipReason"] = None
        accepted.append(row)

    preferred_index = {tuple(p): i for i, p in enumerate(preferred_pairs)}

    def sort_key(item: dict) -> tuple:
        pair = tuple(item["pair"])
        pref = preferred_index.get(pair, len(preferred_index) + 1)
        # Primary: deeper cross-venue liquidity first. Preferred is tie-breaker only.
        return (-float(item["crossVenueLiquidity"]), pref, pair[0], pair[1])

    accepted.sort(key=sort_key)
    skipped.sort(key=lambda item: (-float(item["crossVenueLiquidity"]), item["pair"][0], item["pair"][1]))
    return {
        "accepted": accepted,
        "skipped": skipped,
        "selected": accepted[0] if accepted else None,
        "minCrossVenueLiquidity": min_cross_venue_liquidity,
        "minVenueReserve": min_venue_reserve,
    }


def _pool_summary(pool: Pool) -> dict:
    return {
        "poolId": pool.pool_id,
        "appId": pool.app_id,
        "reserveA": pool.reserve_a,
        "reserveB": pool.reserve_b,
        "feeBps": pool.fee_bps,
        "liquidity": pool_liquidity_estimate(pool),
        "blockRound": pool.block_round,
    }


def adaptive_trade_sizes(
    *,
    max_size: float = 10.0,
    min_size: float = 0.1,
    opportunities: list[Opportunity] | None = None,
) -> tuple[float, ...]:
    """Bounded size ladder 0.1–10; refine around best observed opportunity when present."""
    ceiling = max(min_size, min(float(max_size), 10.0))
    floor = max(0.1, float(min_size))
    probes = tuple(size for size in PROBE_TRADE_SIZES if floor - 1e-12 <= size <= ceiling + 1e-12)
    if not probes:
        probes = (floor, ceiling) if floor != ceiling else (floor,)

    if not opportunities:
        return probes

    best = max(opportunities, key=lambda item: float(item.expected_net_profit))
    best_size = float(best.input_amount)
    refined = {round(size, 6) for size in probes}
    for candidate in (
        best_size,
        max(floor, best_size * 0.5),
        min(ceiling, best_size * 1.5),
        max(floor, best_size - 0.25),
        min(ceiling, best_size + 0.25),
        max(floor, best_size * 0.75),
        min(ceiling, best_size * 1.25),
    ):
        if floor - 1e-12 <= candidate <= ceiling + 1e-12:
            refined.add(round(candidate, 6))
    return tuple(sorted(refined))


def pools_for_pairs(pools: list[Pool], pairs: list[tuple[int, int] | list[int]]) -> list[Pool]:
    wanted = {tuple(sorted((int(a), int(b)))) for a, b in pairs}
    return [pool for pool in pools if pool.asset_pair in wanted and pool.venue_id in {"tinyman", "pact"}]
