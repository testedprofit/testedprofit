# Step 10 Tiny Live Execution Runbook

Date: 2026-06-21

## Purpose

Step 10 is the first tiny live execution phase. It is not broad live trading.

The goal is to prove one reviewed ALGO/USDC route with a tiny hot wallet, then record Lora verification and balance reconciliation before any tiny automation is allowed.

## Preconditions

Do not begin Step 10 until all of these are true:

- scanner has run without signer secret material
- paper trading is recording candidates and 5s/30s quote decay
- risk engine rejects weak routes
- unsigned executor builds atomic dry-run groups only
- isolated signer tests pass
- app ID allowlist is reviewed
- asset universe is ALGO/USDC only
- the hot wallet is new and disposable

## Capital Policy

Use a new hot wallet funded with only money the project can lose:

- 100-250 ALGO total wallet balance
- small USDC only if needed for opt-in or route testing
- no treasury wallet
- no personal main wallet
- no user funds

## Required Env Shape

Start from `.env.tiny-live.example`.

Important locked defaults:

```text
ALGO_PULSE_ASSET_PAIRS=0-31566704
ALGO_PULSE_ALLOWED_ASSET_IDS=0,31566704
ALGO_PULSE_TARGET_ASSET_ID=31566704
ALGO_PULSE_USE_VESTIGE_DISCOVERY=false

ALGO_PULSE_MAX_LIVE_TRADE_SIZE=10
ALGO_PULSE_MAX_DAILY_LOSS=20
ALGO_PULSE_MAX_DAILY_TRADES=20
ALGO_PULSE_MAX_ROUTE_LEGS=3
ALGO_PULSE_MAX_CONCURRENT_EXECUTION=1

ALGO_PULSE_TINY_LIVE_MODE=true
ALGO_PULSE_TINY_LIVE_ALLOW_AUTOMATION=false
ALGO_PULSE_TINY_LIVE_MANUAL_ROUTE_HASH=
ALGO_PULSE_TINY_LIVE_LORA_TXID=
ALGO_PULSE_TINY_LIVE_RECONCILIATION_CONFIRMED=false

ALGO_PULSE_UNSIGNED_EXECUTOR_ONLY=true
ALGO_PULSE_SIGNER_ENABLED=false
ALGO_PULSE_SIGNER_KILL_SWITCH=true
```

## Operator Sequence

1. Create a fresh hot wallet.
2. Fund it with 100-250 ALGO.
3. Opt into USDC only if needed.
4. Run live read-only scan on Tinyman/Pact.
5. Confirm readiness shows `Tiny Live` mode enabled but blocked.
6. Wait for a risk-approved ALGO/USDC route.
7. Build an unsigned dry-run group.
8. Copy the approved route hash into `ALGO_PULSE_TINY_LIVE_MANUAL_ROUTE_HASH`.
9. Review app IDs, asset IDs, input amount, tx count, group id, fee ceiling, and expected profit.
10. Enable the isolated signer only for the reviewed route hash.
11. Manually submit the first signed group through the reviewed signer flow.
12. Verify the transaction in Lora.
13. Record the Lora transaction id in `ALGO_PULSE_TINY_LIVE_LORA_TXID`.
14. Reconcile expected vs actual output and balance deltas.
15. Set `ALGO_PULSE_TINY_LIVE_RECONCILIATION_CONFIRMED=true` only after reconciliation passes.
16. Keep automation disabled until the first live trade is reviewed.
17. After review, set `ALGO_PULSE_TINY_LIVE_ALLOW_AUTOMATION=true` for tiny ALGO/USDC only.

## Readiness Gates Added

`/api/live-readiness` now reports `tiny_live` with:

- ALGO/USDC-only scope
- 10 ALGO max trade
- 20 ALGO max daily loss
- 20 max daily submitted trades
- max route length 3
- max concurrent execution 1
- hot wallet funding range 100-250 ALGO
- manual route hash approval
- Lora txid recorded
- expected-vs-actual reconciliation confirmed
- automation blocked until manual/Lora/reconciliation gates pass

The dashboard has a `Tiny Live` readiness card that shows mode, scope, limits, manual route approval, and Lora/reconciliation state.

## Stop Conditions

Stop immediately if any of these happen:

- transaction output is below the conservative expected floor
- balance reconciliation fails
- Lora transaction details do not match the reviewed group
- wallet balance falls outside the tiny hot-wallet range
- signer rejects a group
- app ID or asset ID does not match route intent
- route is stale
- daily loss or trade count limit is reached

## Current Status

Step 10 gates are implemented and locked by default.

This repo still does not contain a production submitter. The combined FastAPI/scanner app remains read-only plus unsigned execution. Meaningful mainnet capital still requires separate isolated signer deployment, key provisioning, and first-trade operator review.
