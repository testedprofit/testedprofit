# Release Checklist

Use this before tagging, deploying, or handing the repo to another developer.

## Pre-Release

- Confirm working tree is clean except intentional release changes.
- Confirm version target and changelog entry.
- Confirm `.env`, signer secrets, wallet exports, databases, and logs are not staged.
- Confirm no adopted dependency, copied repo, or deployment helper asks for repo-local signer secrets, frontend wallet keys, unlimited routing, missing app ID allowlists, missing daily loss caps, missing kill switches, or execution without paper-trading history.
- Run `python -m pip install -e .`.
- Run `python -m pytest -q`.
- Confirm minimum database tables initialize: `assets`, `venues`, `pools`, `pool_snapshots`, `quotes`, `opportunities`, `paper_trades`, `risk_decisions`, `live_trades`, `service_health`, `alerts`.
- Confirm scanner-only mode has no signer secret material configured and can collect pool/app IDs, reserves, liquidity estimate, block round, timestamp, and freshness.
- Confirm quote probes are `1,5,10,25,50,100` and live execution cap is reviewed separately.
- Confirm stored quote rows include venue, pool, input/output assets, input amount, expected output, price impact, fee estimate, block round, `captured_at`, and `expires_at`.
- Confirm stored opportunity rows include gross profit, network fees, DEX fees, price impact, slippage buffer, net expected profit, confidence score, and skip reason.
- Confirm paper trading records every opportunity, preserves `would_execute` versus skip reason, and updates 5s/30s quote decay plus expected-vs-simulated profit from fresh pool state.
- Confirm risk policy rejects stale quotes, missing app-ID allowlist, weak fee buffers, oversized routes, oversized trades, high price impact, daily trade limit breaches, and concurrent execution.
- Confirm execution dry-run receipts are unsigned, unsubmitted, and include group size plus SDK `TX_GROUP_LIMIT`.
- Confirm the main executor cannot directly sign or submit and returns signer handoff metadata only.
- Confirm the executor requires `status=approved` and a passing `risk_rules` receipt before building a group.
- Confirm isolated signer tests cover kill switch, route hash, app IDs, asset IDs, input cap, fee cap, transaction types, wallet reserve, atomic group, arbitrary instruction rejection, and audit logging.
- Confirm isolated signer tests cover mismatched route intent: app IDs, asset IDs, input amount, tx count, and group id.
- Confirm tiny-live readiness gates are disabled by default and enforce ALGO/USDC-only scope, 10 ALGO max trade, 20 ALGO daily loss, 20 daily trades, route length <=3, one concurrent route, manual route hash, Lora txid, and reconciliation when enabled.
- Confirm route tests cover two-leg venue arb and three-leg ALGO/ASA/USDC triangle discovery, and confirm live execution still rejects non-two-leg routes.
- Run `python -m algopulse.cli demo-run`.
- Run live readiness in read-only mode:

```powershell
$env:ALGO_PULSE_CONNECTORS='tinyman,pact'
$env:ALGO_PULSE_TARGET_ASSET_ID='3169177585'
$env:ALGO_PULSE_USE_VESTIGE_DISCOVERY='true'
$env:ALGO_PULSE_ENABLE_LIVE_EXECUTION='false'
$env:ALGO_PULSE_EXECUTE_APPROVED='false'
$env:ALGO_PULSE_ALLOW_API_EXECUTION='false'
python -m algopulse.cli readiness --scan --no-execution-plan
```

## Dashboard QA

- Dashboard loads locally.
- Browser console has no warnings or errors.
- Pool count is scoped to the target asset.
- Synthetic demo is clearly labeled synthetic.
- Profit gate says positive net after fees only.
- Live execution state is visible.
- Public dashboard data is delayed/redacted and does not expose fresh executable routes.
- Balance reconciliation panel is visible.
- Payment verification panel is visible.
- Payment verification rejects wrong receiver, wrong amount, unconfirmed tx, rekey, and close-out fields.
- Refund/failure queue is visible.
- Refund cases require manual resolution and do not submit transactions.
- Refund-ready cases require a payment verification receipt with sender, amount, and confirmed round.
- Signer boundary is visible in live readiness and shows disabled/kill-switch/route-hash state.
- Tiny Live card is visible and shows mode, scope, limits, manual route, and Lora/reconciliation state.
- Route and opportunity labels distinguish live scan from 24h cumulative counts.

## Execution Safety Gate

Do not enable submitted live trades unless every item below is true:

- Scanner-only mode has run for 24 hours with no crashes, no key material, and no submitted transactions.
- Dedicated tiny hot wallet exists.
- Wallet is not a treasury or personal main wallet.
- AI agents do not have signer secrets or wallet keys.
- Frontend code does not have wallet keys.
- No unknown repo, unreviewed service, or unpinned dependency signs transactions.
- Bot asset universe is allowlisted; it does not trade every asset it sees.
- Bot does not accept user funds.
- Bot does not implement sandwich attacks or predatory MEV behavior.
- Wallet is opted into every required non-ALGO ASA.
- Route is fresh under `ALGO_PULSE_MAX_ROUTE_AGE_SECONDS`.
- `ALGO_PULSE_ALLOWED_APP_IDS` contains only reviewed app IDs and `ALGO_PULSE_REQUIRE_APP_ID_ALLOWLIST=true`.
- Atomic group dry-run builds from the exact fresh route.
- `ALGO_PULSE_UNSIGNED_EXECUTOR_ONLY=true` unless the isolated signer phase has been reviewed.
- `ALGO_PULSE_SIGNER_ENABLED=false` and `ALGO_PULSE_SIGNER_KILL_SWITCH=true` unless the signer process has been reviewed separately.
- `ALGO_PULSE_SIGNER_ALLOWED_ROUTE_HASHES` contains only reviewed route hashes.
- Isolated signer logs every approval/rejection and does not log signed transaction blobs.
- Transaction group size is at most 16.
- Transaction group validation checks expected app IDs and asset IDs.
- Transaction group validation rejects rekey and close-out fields.
- Fee ceiling is below `ALGO_PULSE_MAX_GROUP_FEE_ALGOS`.
- Net profit after fees exceeds minimum absolute and bps thresholds.
- Expected net profit is at least 2x expected total fees.
- Daily submitted trade count is below `ALGO_PULSE_MAX_DAILY_TRADES`.
- Max concurrent execution remains `1`.
- Balance reconciliation receipt is reviewed.
- Any payment-gated operator flow verifies the txid with `/api/verify-payment` and stores a receipt.
- Any refund flow records a refund case and manual resolution txid/note before being treated as closed.
- Meaningful mainnet capital requires an isolated signer separate from unsigned execution planning.
- Automated signing, if enabled, runs only inside the isolated signer and cannot be triggered directly by the scanner/API process.
- Any new major ASA, goBTC, or goETH route has passed liquidity, price-impact, wallet opt-in, app ID, and reconciliation review.
- API execution remains disabled unless the API is private and authenticated.

## Release

```powershell
git status --short
git add .
git commit -m "chore: prepare v0.1.0 release"
git tag -a v0.1.0 -m "Phase 0 read-only PNET market engine"
git push origin main --tags
```

Adjust the version/tag if this is not `v0.1.0`.

## Post-Release

- Record deployment URL or local-only status in `TEAM_HANDOFF.md`.
- Record any known issues in `CHANGELOG.md`.
- Keep live execution disabled until the execution safety gate passes.
