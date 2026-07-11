from __future__ import annotations

import base64

from algopulse.pact_discovery import discover_pool_app_ids_from_factory
from algopulse.pact_discovery import factory_ids_for_network


class _FakeAlgod:
    def __init__(self, boxes: list[tuple[bytes, bytes]]):
        self._boxes = boxes

    def application_boxes(self, app_id: int):
        return {"boxes": [{"name": base64.b64encode(name).decode()} for name, _ in self._boxes]}

    def application_box_by_name(self, app_id: int, name: bytes):
        for box_name, value in self._boxes:
            if box_name == name:
                return {"value": base64.b64encode(value).decode()}
        raise KeyError(name)


def test_factory_ids_for_testnet_and_mainnet():
    assert 166_540_424 in factory_ids_for_network("testnet")
    assert 1_072_843_805 in factory_ids_for_network("mainnet")


def test_discover_pool_app_ids_from_factory_decodes_matching_pair():
    name = (
        (0).to_bytes(8, "big")
        + (10_458_941).to_bytes(8, "big")
        + (30).to_bytes(8, "big")
        + (201).to_bytes(8, "big")
    )
    value = (765_604_788).to_bytes(8, "big")
    other = (
        (0).to_bytes(8, "big")
        + (1).to_bytes(8, "big")
        + (30).to_bytes(8, "big")
        + (201).to_bytes(8, "big")
    )
    algod = _FakeAlgod([(name, value), (other, (9).to_bytes(8, "big"))])
    found = discover_pool_app_ids_from_factory(
        algod,
        factory_app_id=166_540_424,
        asset_a=10_458_941,
        asset_b=0,
    )
    assert found == [765_604_788]
