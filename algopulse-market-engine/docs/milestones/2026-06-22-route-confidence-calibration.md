# Route Confidence Calibration

## What Changed

- Added stored paper-trade confidence calibration through `/api/ops/confidence-calibration`.
- Paper trades now preserve `confidence_score` and resolved `success` state for 5s/30s paper checks.
- Added admin `Confidence` tab with bucketed success-rate analysis, average quote decay, average simulated profit, calibration gap, sample trade evidence, and safety flags.

## What Is Mock

- The frontend has a visibly labeled `mock` fallback if the confidence endpoint is unavailable.
- Browser QA used stored endpoint data; the Confidence panel did not display mock badges.

## What Is Live Or Stored

- Local FastAPI served `stored` confidence analytics from the local SQLite paper-trade history.
- QA observed 6 confidence buckets and 12 sample paper-trade evidence rows.
- The endpoint reported `liveExecutionTouched=false` and `signerCodeTouched=false`.

## Still Blocked

- Live execution remains disarmed.
- Signer, mnemonic, hot-wallet, and transaction submission code remain untouched.
- Production still needs scanner uptime, 7-day paper-trading edge, dry-run validation, signer isolation proof, and manual micro-trade reconciliation before any live micro-execution.

## Production Gate Movement

- Strengthens Phase 0D Paper Trading evidence and Route Engine analytics by showing whether confidence scores predict paper-trade success.
- No live-execution gate was advanced.

## Screenshot

![Route Confidence Calibration](screenshots/2026-06-22-route-confidence-calibration.png)

## QA

- `python -m pytest tests\test_confidence_calibration.py tests\test_store.py tests\test_phase0_integration.py tests\test_control_plane_api.py -q`
- `node --check src\algopulse\static\app.js`
- Browser QA on `http://127.0.0.1:8766/#confidence`: stored badges, 6 buckets, 12 sample rows, guest lock, no console errors, no desktop or 390px mobile overflow.
