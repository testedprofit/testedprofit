from __future__ import annotations

import math
import time

from algopulse.connectors.base import MarketConnector
from algopulse.models import Asset, Pool, Venue


class MockMarketConnector(MarketConnector):
    name = "mock"

    def list_assets(self) -> list[Asset]:
        return [
            Asset(asset_id=0, symbol="ALGO", name="Algorand", decimals=6, is_verified=True, is_allowlisted=True),
            Asset(asset_id=31566704, symbol="USDC", name="USDC on Algorand", decimals=6, is_verified=True, is_allowlisted=True),
            Asset(asset_id=388592191, symbol="CHIPS", name="Chips", decimals=6, is_verified=True, is_allowlisted=True),
            Asset(asset_id=793124631, symbol="gALGO", name="Governance Algo", decimals=6, is_verified=True, is_allowlisted=True),
        ]

    def list_venues(self) -> list[Venue]:
        return [
            Venue(venue_id="tinyman", name="Tinyman", kind="amm"),
            Venue(venue_id="pact", name="Pact", kind="amm"),
        ]

    def list_pools(self) -> list[Pool]:
        now = time.time()
        slow = math.sin(now / 33.0)
        medium = math.sin(now / 19.0)
        fast = math.sin(now / 11.0)

        # Display-unit reserves. Live connectors should use raw units internally.
        tinyman_algo_usdc_price = 0.1900 + (slow * 0.0009)
        pact_algo_usdc_price = 0.1990 + (medium * 0.0010)
        chips_algo_price = 0.0022 + (fast * 0.00004)
        galgo_algo_price = 0.985 + (slow * 0.002)

        return [
            Pool(
                pool_id="tinyman:ALGO-USDC",
                venue_id="tinyman",
                app_id=1001001,
                asset_a_id=0,
                asset_b_id=31566704,
                reserve_a=125_000.0,
                reserve_b=125_000.0 * tinyman_algo_usdc_price,
                fee_bps=30,
                block_round=int(now),
            ),
            Pool(
                pool_id="pact:ALGO-USDC",
                venue_id="pact",
                app_id=2001001,
                asset_a_id=0,
                asset_b_id=31566704,
                reserve_a=96_000.0,
                reserve_b=96_000.0 * pact_algo_usdc_price,
                fee_bps=30,
                block_round=int(now),
            ),
            Pool(
                pool_id="tinyman:ALGO-CHIPS",
                venue_id="tinyman",
                app_id=1002001,
                asset_a_id=0,
                asset_b_id=388592191,
                reserve_a=45_000.0,
                reserve_b=45_000.0 / chips_algo_price,
                fee_bps=30,
                block_round=int(now),
            ),
            Pool(
                pool_id="pact:ALGO-CHIPS",
                venue_id="pact",
                app_id=2002001,
                asset_a_id=0,
                asset_b_id=388592191,
                reserve_a=28_500.0,
                reserve_b=28_500.0 / (chips_algo_price * 1.018),
                fee_bps=30,
                block_round=int(now),
            ),
            Pool(
                pool_id="tinyman:ALGO-gALGO",
                venue_id="tinyman",
                app_id=1003001,
                asset_a_id=0,
                asset_b_id=793124631,
                reserve_a=35_000.0,
                reserve_b=35_000.0 / galgo_algo_price,
                fee_bps=30,
                block_round=int(now),
            ),
            Pool(
                pool_id="pact:ALGO-gALGO",
                venue_id="pact",
                app_id=2003001,
                asset_a_id=0,
                asset_b_id=793124631,
                reserve_a=31_000.0,
                reserve_b=31_000.0 / (galgo_algo_price * 0.985),
                fee_bps=30,
                block_round=int(now),
            ),
        ]
