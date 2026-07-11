from __future__ import annotations

from types import SimpleNamespace

from algopulse.connectors.pact import PactConnector


def test_pact_non_json_api_response_has_explicit_degradation_reason():
    connector = object.__new__(PactConnector)
    connector.settings = SimpleNamespace(asset_pairs=((0, 10_458_941),))

    evidence = connector._build_health_evidence(
        pools=[],
        failures=["JSONDecodeError"],
        latency_ms=125.0,
    )

    assert evidence["status"] == "error"
    assert evidence["detail"] == "pact_api_non_json_response"
    assert evidence["metrics"]["failedPairCount"] == 1
    assert evidence["metrics"]["poolCount"] == 0


def test_pact_factory_fallback_success_is_degraded_not_false_healthy():
    connector = object.__new__(PactConnector)
    connector.settings = SimpleNamespace(asset_pairs=((0, 10_458_941),))
    evidence = connector._build_health_evidence(
        pools=[object()],
        failures=["JSONDecodeError"],
        latency_ms=80.0,
        discovery_mode="algod_factory",
    )
    assert evidence["status"] == "degraded"
    assert evidence["detail"] == "pact_api_fallback_to_algod_factory"
    assert evidence["metrics"]["discoveryMode"] == "algod_factory"
