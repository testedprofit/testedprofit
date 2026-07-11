# Step 7 Risk Engine Report

Date: 2026-06-21

## Status

Step 7 is implemented as enforced policy, not just documentation. The scanner can still discover routes and paper-trade every candidate, but approval is now deliberately hard.

## Enforced Gates

- own funds only
- asset allowlist only
- reviewed app ID allowlist required by default
- quote freshness under 5 seconds
- profit buffer at least 2x expected total fees
- max price impact default 50 bps
- minimum profit must clear 0.25 starting-asset units and 35 bps
- max live trade size default 25 ALGO, live example set to 10 ALGO
- max daily submitted loss 20 ALGO
- max daily submitted trades 20
- max route length 3 swaps
- max concurrent execution 1

## Important Behavior

If `ALGO_PULSE_REQUIRE_APP_ID_ALLOWLIST=true` and `ALGO_PULSE_ALLOWED_APP_IDS` is empty, routes can still be scanned, stored, and paper-traded, but they should not be approved. This is intentional until Tinyman/Pact app IDs are reviewed.

## Code Touchpoints

- `src/algopulse/risk.py`: route approval rules
- `src/algopulse/config.py`: env-backed defaults
- `src/algopulse/scanner.py`: daily trade and concurrent execution caps
- `src/algopulse/readiness.py`: readiness checks and dashboard risk data
- `src/algopulse/static/app.js`: dashboard risk-limit display

## QA

Full test suite passed:

```text
52 passed
```

Live-style local smoke:

```text
Risk policy: 50 bps impact, 2x fee buffer, 5s quote age, 3 max swaps
App-ID allowlist: required, 0 app IDs configured
Fresh scan: 984 candidates, 0 approved
Latest rejection sample: app_ids_allowlisted and trade_size_ok
Execution enabled: false
```

Browser QA:

```text
Dashboard verdict: Not live-market ready
Risk Limits card: visible
0 allowed app IDs: visible
2x fee buffer: visible
1 concurrent execution: visible
Console warnings/errors: 0
```
