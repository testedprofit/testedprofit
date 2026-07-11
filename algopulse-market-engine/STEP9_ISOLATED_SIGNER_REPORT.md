# Step 9 Isolated Signer Report

Date: 2026-06-21

## What Changed

- Added `src/algopulse/signer.py` as a tiny isolated signer policy module.
- Added locked signer env controls to `.env.example` and `.env.live.example`.
- Removed the main executor's direct sign/send path. The executor now stops at `signer_handoff` metadata with `signing_blocked=true`.
- Added signer state to `/api/live-readiness` and the dashboard readiness panel.
- Added tests for signer approval, rejection, audit logging, and the executor handoff boundary.
- Tightened executor input so it requires a risk-approved opportunity with a passing `risk_rules` receipt before building a group.

## Signer Validates

- signer enabled flag
- kill switch
- hot-wallet signer secret resolves to the reviewed wallet address
- route hash allowlist
- route intent match for actual app IDs, asset IDs, input amount, transaction count, and group id
- group size and atomic group id
- transaction types
- sender wallet
- rekey and close-out fields
- app ID allowlist
- asset ID allowlist
- input asset allowlist
- max input amount
- max group fee
- wallet reserve after fees

`SignerRequest.from_payload` rejects arbitrary executor instruction fields including `instructions`, `command`, `prompt`, `tool`, and `action`.

## Audit Behavior

Every signer approval or rejection can be written to JSONL through `JsonlSignerAuditLog`.

Audit rows include route hash, request id, rules, tx count, fee, signed transaction count, and reason. They do not include signer secrets or signed transaction blobs.

## Defaults

```text
ALGO_PULSE_SIGNER_ENABLED=false
ALGO_PULSE_SIGNER_KILL_SWITCH=true
ALGO_PULSE_SIGNER_ALLOWED_ROUTE_HASHES=
ALGO_PULSE_SIGNER_AUDIT_LOG=./data/signer-audit.jsonl
ALGO_PULSE_SIGNER_MIN_WALLET_RESERVE_ALGOS=0.2
```

## QA

```text
python -m pytest
67 passed
```

## Still Not Live

This step does not make the bot live-trade-ready. The signer can validate and sign transaction groups, but the production process split, route-hash approval registry, signer deployment isolation, key provisioning, and network submission workflow still need separate review.

The combined FastAPI/scanner app remains an unsigned executor and dashboard. It should not hold signer key material in production.
