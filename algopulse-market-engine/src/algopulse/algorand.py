from __future__ import annotations

from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from algopulse.config import Settings


def build_algod_client(settings: Settings) -> AlgodClient:
    headers = {}
    token = settings.algod_token
    return AlgodClient(token, settings.algod_url, headers=headers)


def build_indexer_client(settings: Settings) -> IndexerClient:
    headers = {}
    token = settings.indexer_token
    return IndexerClient(token, settings.indexer_url, headers=headers)


def current_algod_round(algod: AlgodClient) -> int:
    try:
        status = algod.status()
    except Exception:
        return 0
    return int(status.get("last-round") or status.get("last_round") or 0)


def raw_to_display(amount: int | float, decimals: int) -> float:
    return float(amount) / float(10**decimals)


def display_to_raw(amount: float, decimals: int) -> int:
    return int(round(amount * (10**decimals)))
