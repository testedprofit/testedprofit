# Milestone: Phase 0A-0G Operator Ladder

Date: 2026-06-22

Screenshot:
`docs/milestones/screenshots/2026-06-22-phase-0a-0g-ladder.png`

## What Changed

- Added a top-level Phase 0A-0G operator ladder to `/api/ops/phase-gates`.
- Updated the admin Control Room to prefer the clean phase ladder while preserving detailed evidence gates in the API.
- Rendered Phase 0F Live Micro as `LOCKED` instead of a normal 0% progress state.
- Added source badges to the ladder cards and mobile-safe seven-phase rendering.

## What Is Mock

- Frontend fallback telemetry still provides a clearly labeled `mock` Phase 0A-0G ladder if the ops API is unavailable.
- Mock values are not presented as production evidence.

## What Is Live Or Stored

- The rendered Control Room screenshot uses stored ops data from the local backend.
- Scanner, quote, route, paper, and risk cards show stored/unavailable source labels.
- No new live scanner, signer, hot-wallet, or execution behavior was added.

## What Is Still Blocked

- Phase 0D Paper Trading still needs a full 7-day paper window.
- Phase 0E Risk Engine still needs more runtime rejection evidence.
- Phase 0F Live Micro remains locked.
- Signer, hot-wallet, mnemonic handling, and live transaction submission remain untouched.

## Production Gate Moved Forward

- Phase 0G Public Dash moved forward visually because the Control Room now shows a public-safe, source-labeled readiness ladder.
- Phase 0A Inventory is clearly marked complete at 100%.
- Phase 0B through 0E now show current progress without implying live-readiness.

## Verification

- `python -m pytest -q` passed: 130 tests.
- `python -m pytest tests\test_control_plane_api.py -q` passed: 14 tests.
- `node --check src\algopulse\static\app.js` passed.
- `git diff --check` passed.
- Browser QA passed for admin Control Room and guest gating.
- Mobile admin Control Room QA at 390px showed 7 ladder cards, `LOCKED` visible, and no horizontal overflow.
