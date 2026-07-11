# Step 6 QA Completion Report

Date: 2026-06-21

## Status

Step 6 is complete for the Phase 0 arb bot handoff. The app is still intentionally read-only for live execution, but it now behaves like a live-market watch agent for the initial PNET pools and records rolling paper-trade replays before any real funds can move.

Local dashboard:

```text
http://127.0.0.1:8766/
```

Local path:

```text
C:\Users\rober\OneDrive\Documents\Algorand_Phase0_Arb_Bot\phase0-market-engine
```

## Current Live-Market Result

Fresh PNET scan smoke:

```text
Target asset: PNET / ASA 3169177585
Connectors: tinyman,pact
Fresh scan pools: 29
Fresh route candidates: 984
Approved routes: 0
Paper candidates written: 984
Paper 5s replays updated on follow-up scan: 984
Paper 30s replays updated on follow-up scan: 65
Paper replay errors: 0
Best approved route: none
Execution enabled: false
API execution enabled: false
```

Current route gate behavior:

```text
Current scan approved 0 routes.
Rejected routes are still paper-recorded with skip reasons.
Paper replay rows store simulated final output, quote decay, and expected-vs-simulated profit.
```

This is the correct conservative behavior: the bot is watching live PNET markets, but it is not approving trades just for volume.

## QA Fixes Made

1. Stale approved routes can no longer leak into readiness.
   - Readiness now filters fresh scan opportunities.
   - Worker execution only selects opportunities from the current scan window.
   - Regression test added.

2. Stale route execution is blocked before wallet checks.
   - Executor rejects routes older than `ALGO_PULSE_MAX_ROUTE_AGE_SECONDS`.
   - Default is `5` seconds.
   - Regression test added.

3. Balance reconciliation is now visible.
   - Added `/api/reconciliations`.
   - Added dashboard panel for expected and actual balance deltas.
   - Submitted trades will create reconciliation receipts.

4. Dashboard/API profit guard is clearer.
   - Risk policy now exposes `max_route_age_seconds`.
   - Risk policy now exposes `requires_positive_net_after_fees`.
   - Dashboard now states `Positive net after fees only`.

5. PNET dashboard data is now target-scoped.
   - Old ALGO/USDC/mock data no longer pollutes PNET pool counts or best-route selection.
   - `/api/pools` now returns 16 PNET pools, and every returned pool includes ASA `3169177585`.
   - Regression test added.

6. UI labels now distinguish current pools from 24h cumulative route history.
   - Radar label changed to `Routes 24h`.
   - Metric label changed to `Opps 24h`.

7. Install/run docs were corrected.
   - The package must be installed with `python -m pip install -e .` or run with `PYTHONPATH=src`.
   - Editable install was verified locally.

8. Refund/failure handling is now visible and manual-only.
   - Added `/api/refund-cases` and `/api/refund-cases/{case_id}/status`.
   - Added dashboard queue for failure records, review cases, and manual resolution txids.
   - Refund cases never submit transactions.

9. Rolling paper trading now matches the Step 6 contract.
   - Every opportunity creates a paper-trade row.
   - Approved rows store `would_execute=true`; rejected rows keep the skip reason.
   - Later scanner cycles replay due routes at 5 seconds and 30 seconds from fresh pool state.
   - Replay rows store simulated final output, quote decay, and expected-vs-simulated profit.
   - The dashboard surfaces completed replay rows before newly pending rows.

## Verification Commands

```powershell
python -m pip install -e .
python -m pytest -q
python -m algopulse.cli demo-run
python -m algopulse.cli readiness --no-execution-plan
```

Latest test result:

```text
45 passed
```

Browser QA:

```text
Dashboard reload: pass
Scan now button: pass
Radar canvas: pass
PNET pool scoping: pass
Positive-profit wording: pass
Refund/failure queue: pass
Refund queue local smoke rows removed after QA: pass
Paper trading panel: pass
5s/30s replay visibility: pass
No NaN/undefined text: pass
Console errors/warnings: 0
```

## Local Read-Only Env Used

```powershell
$env:ALGO_PULSE_CONNECTORS='tinyman,pact'
$env:ALGO_PULSE_TARGET_ASSET_ID='3169177585'
$env:ALGO_PULSE_USE_VESTIGE_DISCOVERY='true'
$env:ALGO_PULSE_VESTIGE_PINNED_PAIR_ASSET_IDS='1290751153,3436365167,1893942045,31566704,1390638935,2644742542,3249403496,3427156477,1119722936,3410350791,846652486,3427041827,1674484158,3227174563'
$env:ALGO_PULSE_VESTIGE_INCLUDE_FALLBACK_PAIRS='false'
$env:ALGO_PULSE_ALLOW_NON_ALGO_STARTING_ROUTES='true'
$env:ALGO_PULSE_ENABLE_LIVE_EXECUTION='false'
$env:ALGO_PULSE_EXECUTE_APPROVED='false'
$env:ALGO_PULSE_ALLOW_API_EXECUTION='false'
$env:ALGO_PULSE_MAX_ROUTE_AGE_SECONDS='5'
python -m uvicorn algopulse.api:app --host 127.0.0.1 --port 8766
```

## Do Not Enable Live Until

1. A dedicated hot wallet is created, funded lightly, and asset-opted into the required PNET route assets.
2. Claude reviews the atomic transaction group builder against Tinyman and Pact SDK expectations.
3. A dry-run preflight builds the exact intended transaction group from a fresh route under 5 seconds old.
4. The balance reconciliation receipt is reviewed for at least one dry-run plan.
5. Non-ALGO live submission remains disabled until profit can be reconciled in ALGO-equivalent terms.
6. Live trade size is capped tiny first, then raised only after submitted balance deltas prove profit after fees.
