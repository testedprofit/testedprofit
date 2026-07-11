from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass

from algopulse.config import Settings


PROTOCOL_NAMES = {
    0: "tinyman-v1",
    1: "tinyman-v1.1",
    2: "tinyman-v2",
    3: "pact",
    4: "pact-stableswap",
}


@dataclass(frozen=True)
class DiscoveredPair:
    target_asset_id: int
    other_asset_id: int
    target_reserve: float
    protocols: list[str]
    protocol_ids: list[int]
    other_symbol: str | None = None

    @property
    def asset_pair(self) -> tuple[int, int]:
        return tuple(sorted((self.target_asset_id, self.other_asset_id)))

    def to_dict(self) -> dict:
        return {
            "target_asset_id": self.target_asset_id,
            "other_asset_id": self.other_asset_id,
            "other_symbol": self.other_symbol,
            "asset_pair": list(self.asset_pair),
            "target_reserve": self.target_reserve,
            "protocols": self.protocols,
            "protocol_ids": self.protocol_ids,
        }


@dataclass(frozen=True)
class VestigeDiscoveryResult:
    target_asset: dict
    pairs: list[DiscoveredPair]
    fallback_asset_pairs: tuple[tuple[int, int], ...]
    min_target_reserve: float
    pinned_pair_asset_ids: tuple[int, ...] = ()
    include_fallback_asset_pairs: bool = True
    error: str | None = None

    @property
    def asset_pairs(self) -> tuple[tuple[int, int], ...]:
        discovered = [pair.asset_pair for pair in self.pairs]
        include_fallback = self.include_fallback_asset_pairs or not discovered
        seen: set[tuple[int, int]] = set()
        ordered: list[tuple[int, int]] = []
        candidate_pairs = discovered + (list(self.fallback_asset_pairs) if include_fallback else [])
        for pair in candidate_pairs:
            if pair in seen:
                continue
            seen.add(pair)
            ordered.append(pair)
        return tuple(ordered)

    def to_dict(self) -> dict:
        return {
            "source": "vestige",
            "target_asset": self.target_asset,
            "min_target_reserve": self.min_target_reserve,
            "pinned_pair_asset_ids": list(self.pinned_pair_asset_ids),
            "include_fallback_asset_pairs": self.include_fallback_asset_pairs,
            "pairs": [pair.to_dict() for pair in self.pairs],
            "asset_pairs": [list(pair) for pair in self.asset_pairs],
            "error": self.error,
        }


class VestigeDiscovery:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.vestige_api_url.rstrip("/")

    def discover_pairs(self) -> VestigeDiscoveryResult:
        try:
            target_asset = self._asset_map([self.settings.target_asset_id]).get(self.settings.target_asset_id, {})
            composition = self._get_json(f"/assets/{self.settings.target_asset_id}/composition", {"network_id": 0})
            candidates = self._pairs_from_composition(composition)
            other_assets = self._asset_map([pair.other_asset_id for pair in candidates])
            pair_limit = None if self.settings.vestige_pinned_pair_asset_ids else self.settings.vestige_top_pool_count
            selected_candidates = candidates if pair_limit is None else candidates[:pair_limit]
            pairs = [
                DiscoveredPair(
                    target_asset_id=pair.target_asset_id,
                    other_asset_id=pair.other_asset_id,
                    target_reserve=pair.target_reserve,
                    protocols=pair.protocols,
                    protocol_ids=pair.protocol_ids,
                    other_symbol=other_assets.get(pair.other_asset_id, {}).get("ticker"),
                )
                for pair in selected_candidates
            ]
            return VestigeDiscoveryResult(
                target_asset=_asset_public_dict(target_asset),
                pairs=pairs,
                fallback_asset_pairs=self.settings.asset_pairs,
                min_target_reserve=self.settings.vestige_min_target_reserve,
                pinned_pair_asset_ids=self.settings.vestige_pinned_pair_asset_ids,
                include_fallback_asset_pairs=self.settings.vestige_include_fallback_pairs,
            )
        except Exception as exc:
            return VestigeDiscoveryResult(
                target_asset={"id": self.settings.target_asset_id},
                pairs=[],
                fallback_asset_pairs=self.settings.asset_pairs,
                min_target_reserve=self.settings.vestige_min_target_reserve,
                pinned_pair_asset_ids=self.settings.vestige_pinned_pair_asset_ids,
                include_fallback_asset_pairs=self.settings.vestige_include_fallback_pairs,
                error=str(exc),
            )

    def _pairs_from_composition(self, composition: dict) -> list[DiscoveredPair]:
        if self.settings.vestige_pinned_pair_asset_ids:
            return self._pinned_pairs_from_composition(composition)

        by_other_asset: dict[int, dict] = {}
        protocol_filter = set(self.settings.vestige_protocol_ids)
        for protocol_id_text, assets in composition.items():
            protocol_id = int(protocol_id_text)
            if protocol_filter and protocol_id not in protocol_filter:
                continue
            for other_asset_id_text, target_reserve in assets.items():
                target_reserve = float(target_reserve)
                other_asset_id = int(other_asset_id_text)
                entry = by_other_asset.setdefault(
                    other_asset_id,
                    {
                        "target_reserve": 0.0,
                        "protocol_ids": set(),
                    },
                )
                entry["target_reserve"] += target_reserve
                entry["protocol_ids"].add(protocol_id)

        pairs = [
            DiscoveredPair(
                target_asset_id=self.settings.target_asset_id,
                other_asset_id=other_asset_id,
                target_reserve=data["target_reserve"],
                protocols=[PROTOCOL_NAMES.get(protocol_id, f"protocol-{protocol_id}") for protocol_id in sorted(data["protocol_ids"])],
                protocol_ids=sorted(data["protocol_ids"]),
            )
            for other_asset_id, data in by_other_asset.items()
            if data["target_reserve"] >= self.settings.vestige_min_target_reserve
        ]
        pairs.sort(key=lambda pair: _pair_sort_key(pair), reverse=True)
        return pairs

    def _pinned_pairs_from_composition(self, composition: dict) -> list[DiscoveredPair]:
        pairs: list[DiscoveredPair] = []
        protocol_filter = set(self.settings.vestige_protocol_ids)
        for other_asset_id in self.settings.vestige_pinned_pair_asset_ids:
            target_reserve = 0.0
            protocol_ids: set[int] = set()
            for protocol_id_text, assets in composition.items():
                protocol_id = int(protocol_id_text)
                if protocol_filter and protocol_id not in protocol_filter:
                    continue
                reserve = assets.get(str(other_asset_id))
                if reserve is None:
                    continue
                target_reserve += float(reserve)
                protocol_ids.add(protocol_id)
            if not protocol_ids:
                continue
            pairs.append(
                DiscoveredPair(
                    target_asset_id=self.settings.target_asset_id,
                    other_asset_id=int(other_asset_id),
                    target_reserve=target_reserve,
                    protocols=[PROTOCOL_NAMES.get(protocol_id, f"protocol-{protocol_id}") for protocol_id in sorted(protocol_ids)],
                    protocol_ids=sorted(protocol_ids),
                )
            )
        return pairs

    def _asset_map(self, asset_ids: list[int]) -> dict[int, dict]:
        unique_ids = sorted(set(int(asset_id) for asset_id in asset_ids if asset_id is not None))
        if not unique_ids:
            return {}
        data = self._get_json(
            "/assets",
            {
                "network_id": 0,
                "asset_ids": ",".join(str(asset_id) for asset_id in unique_ids),
            },
        )
        if isinstance(data, dict) and "id" in data:
            return {int(data["id"]): data}
        return {int(item["id"]): item for item in data}

    def _get_json(self, path: str, query: dict) -> dict | list:
        url = f"{self.base_url}{path}?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(url, headers={"accept": "application/json", "user-agent": "algopulse-phase0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))


def _pair_sort_key(pair: DiscoveredPair) -> tuple[int, float]:
    includes_algo = 1 if pair.other_asset_id == 0 else 0
    includes_usdc = 1 if pair.other_asset_id == 31566704 else 0
    return (includes_algo + includes_usdc, pair.target_reserve)


def _asset_public_dict(asset: dict) -> dict:
    return {
        "id": asset.get("id"),
        "name": asset.get("name"),
        "ticker": asset.get("ticker"),
        "decimals": asset.get("decimals"),
        "total_supply": asset.get("total_supply"),
        "url": asset.get("url"),
        "manager": asset.get("manager"),
        "reserve": asset.get("reserve"),
        "freeze": asset.get("freeze"),
        "clawback": asset.get("clawback"),
    }
