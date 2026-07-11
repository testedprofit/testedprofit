# Opportunity Decay Analytics

## Screenshot

![Opportunity Decay Analytics](screenshots/2026-06-22-opportunity-decay-analytics.png)

## What Changed

- Added stored opportunity-decay analytics through admin-only `GET /api/ops/opportunity-decay`.
- Added `opportunity_decay` persistence with detected profit plus 5s, 30s, and 60s expected-profit checkpoints.
- Extended paper-trading rechecks with a 60s checkpoint so future samples can measure longer opportunity decay.
- Added pure half-life aggregation for average, median, fastest, slowest, pair, venue, route-type, timeline, and recent-record summaries.
- Added admin `Half-Life` dashboard with 1h, 24h, and 7d views, source badges, empty states, safety copy, and guest lockout.

## What Is Mock

- The frontend includes a visibly labeled `mock` fallback only if `/api/ops/opportunity-decay` is unavailable.
- Browser QA used stored endpoint data for 24h and 7d views.
- The 1h view honestly rendered `unavailable` because no records existed in that local time window.

## What Is Live Or Stored

- Local FastAPI returned `stored` decay analytics from persisted opportunities and paper-trade rows.
- API QA observed 2,952 stored opportunity-decay rows in the 24h view, 24 timeline buckets, 25 recent records, 3 breakdown groups, and 60 actionable candidates.
- The endpoint reported `liveExecutionTouched=false` and `signerCodeTouched=false`.

## Still Blocked

- Live execution remains disarmed.
- Signer, mnemonic, hot-wallet, and transaction submission code remain untouched.
- Existing migrated data has no completed 60s samples yet; new paper-trading runs will populate that checkpoint after candidates mature.
- Production still needs scanner uptime, 7-day paper-trading edge, dry-run validation, signer isolation proof, and manual micro-trade reconciliation before any live micro-execution.

## Production Gate Movement

- Strengthens Phase 0C Route Engine evidence by quantifying how quickly route opportunities decay.
- Strengthens Phase 0D Paper Trading evidence by adding a 60s observation point and half-life reporting.
- Does not advance the live-execution gate.

## QA

- `python -m pytest tests\test_opportunity_decay.py tests\test_store.py tests\test_phase0_integration.py tests\test_control_plane_api.py -q`
- `node --check src\algopulse\static\app.js`
- API QA on `http://127.0.0.1:8766/api/ops/opportunity-decay?view=24h`: stored source, 2,952 rows, 24 timeline buckets, 25 recent records, admin-only 403 for guest.
- Browser QA on `http://127.0.0.1:8766/#decay`: stored badges, 1h/24h/7d controls, guest lock, no console errors, no desktop or 390px mobile overflow.
