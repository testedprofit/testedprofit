# Phase 0 Test Matrix

## Unit Tests

- decimal conversion: `tests/test_phase0_units.py`
- quote normalization: `tests/test_phase0_units.py`
- gross/net profit calculation: `tests/test_phase0_units.py`, `tests/test_route_math.py`
- fee calculation: `tests/test_phase0_units.py`, `tests/test_route_math.py`
- price impact calculation: `tests/test_phase0_units.py`, `tests/test_route_math.py`
- route hash stability: `tests/test_phase0_units.py`, `tests/test_route_math.py`
- risk approval/rejection: `tests/test_risk_pure.py`, `tests/test_risk.py`, `tests/test_phase0_security.py`
- stale quote rejection: `tests/test_risk_pure.py`, `tests/test_risk.py`
- allowlist rejection: `tests/test_risk.py`, `tests/test_phase0_security.py`
- PNET fee quote validation: `tests/test_control_plane_api.py`, `tests/test_phase0_integration.py`
- mock/TestNet x402 report access gating: `tests/test_x402_market_intelligence_access.py`
- Vestige recent PNET swap normalization: `tests/test_recent_swaps.py`
- transparency proof ledger and audit snapshot contracts: `tests/test_transparency_system.py`
- production readiness pure guardrails: `tests/test_production_readiness.py`
- admin Control Room telemetry endpoints: `tests/test_control_plane_api.py`

## Integration Tests

- mock Tinyman connector: `tests/test_phase0_integration.py`
- mock Pact connector: `tests/test_phase0_integration.py`
- route generation from stored quotes: `tests/test_phase0_integration.py`
- paper-trade logging: `tests/test_phase0_integration.py`, `tests/test_store.py`
- admin preflight endpoint: `tests/test_control_plane_api.py`, `tests/test_phase0_integration.py`
- user PNET access endpoint: `tests/test_control_plane_api.py`, `tests/test_phase0_integration.py`
- delayed market report unlock through mock/TestNet x402 access layer: `tests/test_x402_market_intelligence_access.py`
- public transparency dashboard API surfaces: `tests/test_transparency_system.py`
- public recent PNET swap API shape: `tests/test_recent_swaps.py`

## Security Tests

- non-admin cannot call admin endpoints: `tests/test_phase0_security.py`, `tests/test_control_plane_api.py`
- frontend role does not grant backend role: `tests/test_phase0_security.py`
- unknown app ID rejected: `tests/test_phase0_security.py`, `tests/test_risk.py`
- unknown asset rejected: `tests/test_phase0_security.py`, `tests/test_risk.py`
- over-limit trade rejected: `tests/test_phase0_security.py`
- kill switch blocks execution requests: `tests/test_phase0_security.py`
- mock/TestNet x402 report endpoint does not expose signer, custody, submission, or fresh executable route data: `tests/test_x402_market_intelligence_access.py`
- transparency endpoints redact raw txids, wallet values, secrets, payment headers, and payment payloads: `tests/test_transparency_system.py`
- recent PNET swaps redact raw Vestige payload fields, wallet addresses, group IDs, signer, hot-wallet, and submission fields: `tests/test_recent_swaps.py`

Run all tests:

```powershell
python -m pytest -q
```
