# Opportunity Replay Lab Milestone

Date: 2026-06-22

Screenshot: `docs/milestones/screenshots/2026-06-22-opportunity-replay-lab.png`

## What Changed

- Added admin-only Replay Lab tab for historical opportunity review.
- Added `/api/ops/replay-lab` to rebuild replay records from stored paper-trade history.
- Added T0, T+5s, and T+30s timeline checkpoints with expected profit, simulated profit, quote decay, price impact change, liquidity change, confidence, and verdict reason.
- Added playback controls, timeline scrub, selected replay inspector, and side-by-side comparison mode.
- Added tests for admin role-gating and stored replay reconstruction.

## What Is Mock

- Frontend has mock-labeled fallback replay data only when the backend endpoint is unavailable.
- No mock value is displayed as production data; fallback values show `mock` source badges.

## What Is Live Or Stored

- Local QA on `http://127.0.0.1:8766/` showed `stored` source badges from `/api/ops/replay-lab`.
- Replay Lab loaded 30 stored paper-trade replay cards.
- Timeline checkpoints and compare cards rendered from stored paper-trade rows.

## What Is Still Blocked

- Live execution remains `LOCKED / DISARMED`.
- No signer, mnemonic, hot-wallet, or transaction submission code was changed.
- Production remains blocked by 24h scanner uptime proof, 7-day paper trading proof, dry-run validation, signer isolation proof, and reconciled manual micro-trade proof.

## Production Gate Movement

- Phase 0D Paper Trading moved forward visually: historical paper-trade evidence is now replayable and explainable.
- Phase 0E Risk Engine also gained evidence visibility because unsafe/stale/would-skip verdicts now show route-level reasons.

## QA

- `python -m pytest -q`: 131 passed.
- `node --check src/algopulse/static/app.js`: passed.
- Browser QA: admin Replay Lab rendered stored data, 30 replay cards, 3 timeline checkpoints, 3 comparison cards, locked live execution, no console errors, and no horizontal overflow at desktop or 390px mobile width.
