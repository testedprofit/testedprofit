from __future__ import annotations

from abc import ABC, abstractmethod

from algopulse.models import Asset, Pool, Venue


class MarketConnector(ABC):
    name: str

    def health_evidence(self) -> dict:
        return {
            "status": "ok",
            "detail": None,
            "metrics": {"connector": self.name, "connectorType": "dex"},
        }

    @abstractmethod
    def list_assets(self) -> list[Asset]:
        raise NotImplementedError

    @abstractmethod
    def list_venues(self) -> list[Venue]:
        raise NotImplementedError

    @abstractmethod
    def list_pools(self) -> list[Pool]:
        raise NotImplementedError
