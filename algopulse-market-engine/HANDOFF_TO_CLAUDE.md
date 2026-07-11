# Handoff To Claude

This repo is a deployable Phase 0 Algorand market intelligence and micro-arb engine.

Before deployment work, read `TEAM_HANDOFF.md`, `VERSION_CONTROL.md`, `CHANGELOG.md`, and `docs/RELEASE_CHECKLIST.md`. Those files define the team handoff, repo split, version-control policy, and release gate.

It supports live Tinyman/Pact read-only scanning now. Live submission is intentionally disabled unless the operator explicitly enables it with env flags and a tiny hot wallet.

The initial live market target is ProfitNet / PNET, asset `3169177585`. The bot can use Vestige to discover the larger PNET pools, then Tinyman/Pact SDKs to fetch executable reserves.

Connector priority is intentional: Tinyman and Pact are the first executable venues. Vestige is data/discovery only for now. Folks routes and other AMMs are later expansion after connector math, transaction construction, quote freshness, app IDs, and reconciliation are reviewed.

Route-pair priority is also intentional: start with ALGO/USDC, then ALGO/major ASAs and USDC/major ASAs. Add goBTC/goETH routes only after liquidity verification, route-size testing, and balance reconciliation prove they are not thin-pool traps.

The initial testing universe is pinned from the user-provided Vestige pool screenshot. See `INITIAL_TEST_POOLS.md` and `.env.live.example`.

Route generation now includes two-leg venue arb and three-leg ALGO/ASA/USDC triangles:

- `ALGO -> USDC on Tinyman -> ALGO on Pact`
- `ALGO -> ASA on Pact -> ALGO on Tinyman`
- `ALGO -> ASA -> USDC -> ALGO`
- `ALGO -> USDC -> ASA -> ALGO`

Three-leg routes are scanner/risk/paper-trade candidates only. `src/algopulse/executor.py` still rejects live execution for non-two-leg routes until a separate 3-leg atomic group implementation is reviewed.

Production should move toward this service chain:

```text
Pool Scanner -> Quote Engine -> Route Engine -> Simulator / Paper Trader -> Risk Engine -> Unsigned Executor -> Isolated Signer -> Algorand Network
```

Every service should write structured state/events to Postgres, logs, alerts, and a delayed/redacted public dashboard projection. The current repo is still a Phase 0 local app with SQLite and a combined backend.

Automation policy: scanning, quote comparison, paper trading, risk rejection, and unsigned transaction construction can be automated. Signing can be automated only inside a tiny isolated signer that keeps signer secrets outside the scanner/API repo path, revalidates policy, and refuses out-of-policy transaction groups.

Security red lines: AI agents must not hold wallet keys, the frontend must not hold wallet keys, a main wallet must not sign trades, unknown repos must not sign transactions, the bot must not trade every asset it sees, the bot must not accept user funds, and the bot must not perform sandwich attacks or predatory MEV.

Minimum database tables are `assets`, `venues`, `pools`, `pool_snapshots`, `quotes`, `opportunities`, `paper_trades`, `risk_decisions`, `live_trades`, `service_health`, and `alerts`. SQLite now initializes this shape for Phase 0; production should migrate it to Postgres.

Scanner contract: scanner mode is read-only and must run without signer secret material. It records venue, pool/app IDs, asset pair, reserves, fee bps, liquidity estimate, spot price, block round, timestamp, and data freshness. Phase 0A exit gate is 24 hours of scanner uptime with no crashes and no key material configured.

Quote engine standard probe sizes are 1, 5, 10, 25, 50, and 100 ALGO. These are quote/paper-trade sizes only; live execution remains capped separately by `ALGO_PULSE_MAX_LIVE_TRADE_SIZE`.

Every quote row must preserve venue, pool, input asset, output asset, input amount, expected output, price impact, fee estimate, block round, `captured_at`, and `expires_at`. Missing quote metadata should be treated as a handoff blocker for live execution work.

Every opportunity row must preserve gross profit, estimated network fees, DEX fee estimate, price impact, slippage/safety buffer, net expected profit, confidence score, and skip reason. DEX fees are already included in quote outputs and should not be subtracted twice.

Every opportunity also gets a paper-trade replay row before real funds are considered. Approved routes store `would_execute=true`; rejected routes store `would_execute=false` plus the skip reason. Later scanner cycles recheck due routes at 5 seconds and 30 seconds using fresh pool state, then store simulated final output, quote decay, and expected-vs-simulated profit. This paper loop must remain keyless and transaction-free.

Risk engine policy is deliberately harsh. Routes should be rejected unless they use own funds only, allowed assets, reviewed app IDs, quotes fresher than 5 seconds, no more than 3 swaps, max trade size 10-25 ALGO, max price impact about 50 bps, net profit above both 0.25 starting-asset units and 35 bps, and expected net profit at least 2x expected total fees. Execution is also capped at 20 submitted trades/day, 20 ALGO daily loss, and one concurrent execution. If `ALGO_PULSE_ALLOWED_APP_IDS` is empty while app-ID allowlisting is required, scanner/paper mode still runs but routes should not approve.

Execution dry-run policy is unsigned-only before live trading. `src/algopulse/executor.py` builds SDK transaction groups and assigns a group id for review, but `ALGO_PULSE_UNSIGNED_EXECUTOR_ONLY=true` blocks signing even if live flags are accidentally enabled. Group size is enforced with the installed Algorand SDK `TX_GROUP_LIMIT`, currently 16. Any route that would exceed 16 transactions must be rejected before signing.

Step 9 signer policy now exists in `src/algopulse/signer.py`. The main executor requires `status=approved` plus a passing `risk_rules` receipt before it builds a dry-run group. It no longer signs or submits directly; if live flags are armed after dry-run review, it returns `signer_handoff` metadata and `signing_blocked=true`. The isolated signer validates route hash, route-intent app IDs/assets/input/tx count/group id, app and asset allowlists, max input, max fees, transaction types, wallet reserve, kill switch, sender wallet, atomic group size, and no rekey/close-out before signing. It rejects arbitrary executor fields such as `instructions`, `command`, `prompt`, or `tool`, and logs every approval/rejection to JSONL without writing signed blobs.

Step 10 tiny-live gates now exist in readiness and `.env.tiny-live.example`. Tiny live mode is ALGO/USDC only, max trade size 10 ALGO, 20 ALGO max daily loss, 20 max daily submitted trades, route length up to 3, one concurrent route, new 100-250 ALGO hot wallet, manual route-hash approval, Lora txid recording, and expected-vs-actual reconciliation before `ALGO_PULSE_TINY_LIVE_ALLOW_AUTOMATION=true`.

Before changing live execution behavior, read:

- `FOUNDER_AUTOMATION_PLAYBOOK.md`
- `ALGORAND_ARB_AGENT_RULES.md`
- `REAL_ARB_BOT_ARCHITECTURE.md`
- `STEP10_TINY_LIVE_EXECUTION_RUNBOOK.md`

## What Works Now

- FastAPI backend
- SQLite persistence
- deterministic mock market connector
- live Tinyman connector
- live Pact connector
- Vestige larger-pool discovery for PNET
- pinned initial PNET test-pool discovery
- pool scanner
- 2-leg arbitrage route engine
- 3-leg ALGO/ASA/USDC triangle discovery for paper review
- risk policy engine
- Step 7 risk gates for quote freshness, fee buffer, app IDs, daily trade cap, and single execution slot
- candidate-wide rolling paper trading with 5s/30s quote-decay replay
- guarded atomic execution builder
- unsigned execution dry-run receipts with `TX_GROUP_LIMIT` group-size enforcement
- isolated signer policy module with kill switch, route-hash allowlist, app/asset allowlists, fee/input/reserve checks, and JSONL audit logging
- main executor signer handoff stub; direct sign/send path removed from the combined app
- tiny-live readiness gates and `.env.tiny-live.example` for ALGO/USDC-only first execution
- configurable no-volume profit guard
- opportunity-level profit breakdown and skip-reason audit fields
- configurable probe trade sizes
- stale-route rejection before execution
- PNET/non-ALGO starting route dry-run guard
- wallet input-inventory and ALGO fee-budget checks
- balance reconciliation receipts for dry-runs and submitted trades
- Algorand payment verification receipts through `/api/verify-payment` and `/api/payment-verifications`
- refund/failure queue through `/api/refund-cases`, with manual resolution txid recording
- live-market readiness preflight
- worker command for continuous scanning/execution
- public dashboard
- synthetic 5 ALGO to 10 ALGO demo proof
- scan-now API endpoint
- tests for route and risk behavior

## Review Before Live Funds

1. Review Tinyman/Pact connector math against SDK examples.
2. Review two-leg execution construction in `src/algopulse/executor.py`; three-leg routes are discovery/paper-only until executor support is deliberately added.
3. Keep `ALGO_PULSE_ENABLE_LIVE_EXECUTION=false` until manual go-live.
4. Keep `ALGO_PULSE_ALLOW_API_EXECUTION=false` unless the API is private/authenticated.
5. Set `ALGO_PULSE_PUBLIC_DELAY_SECONDS=120` or higher before publishing live route data.
6. Keep `ALGO_PULSE_MIN_NET_PROFIT_INPUT_UNITS` and `ALGO_PULSE_MIN_PROFIT_BPS` positive.
7. Keep `ALGO_PULSE_MIN_FEE_BUFFER_MULTIPLIER=2` or higher.
8. Keep `ALGO_PULSE_REQUIRE_APP_ID_ALLOWLIST=true` and populate `ALGO_PULSE_ALLOWED_APP_IDS` only after app review.
9. Keep `ALGO_PULSE_UNSIGNED_EXECUTOR_ONLY=true` until isolated signer review.
10. Keep `ALGO_PULSE_SIGNER_ENABLED=false` and `ALGO_PULSE_SIGNER_KILL_SWITCH=true` until the signer process is deployed and reviewed separately.
11. Allowlist route hashes in `ALGO_PULSE_SIGNER_ALLOWED_ROUTE_HASHES` only after risk approval and unsigned group review.
12. Use a fresh tiny hot wallet only.
13. Confirm the hot wallet is opted into every intermediate ASA and holds the starting asset for the route.
14. Keep `ALGO_PULSE_ALLOW_NON_ALGO_LIVE_SUBMISSION=false` until ALGO-equivalent PNET profit accounting is reviewed.

## Local Run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
python -m algopulse.cli scan --cycles 5
uvicorn algopulse.api:app --host 127.0.0.1 --port 8765
```

For a blank Python-first setup, the core package path is:

```bash
pip install py-algorand-sdk fastapi uvicorn pydantic sqlalchemy psycopg2-binary redis python-dotenv
pip install git+https://github.com/tinymanorg/tinyman-py-sdk.git
pip install pactsdk
```

This repo pins Tinyman from GitHub in `requirements.txt`/`pyproject.toml` and uses Pact's `pactsdk` package. Postgres/Redis packages are present for the target service split; local Phase 0 still uses SQLite.

## Live Read-Only Scan

```bash
ALGO_PULSE_CONNECTORS=tinyman,pact ALGO_PULSE_TARGET_ASSET_ID=3169177585 ALGO_PULSE_USE_VESTIGE_DISCOVERY=true python -m algopulse.cli scan --cycles 1
```

## Live Readiness Preflight

```bash
ALGO_PULSE_CONNECTORS=tinyman,pact ALGO_PULSE_TARGET_ASSET_ID=3169177585 ALGO_PULSE_USE_VESTIGE_DISCOVERY=true python -m algopulse.cli readiness --scan
```

This reports whether the bot is live-market ready across connector health, pool data, scan freshness, wallet funding, ASA opt-ins, daily loss room, approved route availability, and safe atomic dry-run construction. The preflight never submits transactions.

Profit guard behavior is intentional: the scanner only approves routes that clear the configured starting-asset net floor and bps floor after quote fees, estimated network fees, and buffer. The executor rejects stale routes, separates starting-asset profit from ALGO fee budget, then rechecks final minimum output after SDK transaction construction before any signing can happen.

Balance reconciliation behavior is intentional: dry-run execution records expected deltas, and submitted execution captures post-confirmation balances and compares actual deltas against the conservative expected floor. The dashboard exposes these receipts through `/api/reconciliations`.

Payment verification behavior is read-only: the verifier checks an indexer txid against expected receiver, amount, confirmations, optional sender/note, and rejects rekey or close-out fields. It records a local receipt but does not submit or custody funds.

Refund/failure behavior is also manual-only: cases can be created from payment verification receipts, then classified as `refund_ready`, `needs_review`, or `not_refundable`. The app records the queue and final resolution txid/note, but it does not send refund transactions.

ALGO-starting routes can submit only when live flags are armed. PNET/non-ALGO starting routes can build atomic dry-runs when `ALGO_PULSE_ALLOW_NON_ALGO_STARTING_ROUTES=true`, but live signing should remain blocked with `ALGO_PULSE_ALLOW_NON_ALGO_LIVE_SUBMISSION=false` until a reviewed ALGO-equivalent valuation/reconciliation layer exists.

Vestige discovery should be reviewed in `src/algopulse/vestige.py`. It uses Vestige composition data to pick larger PNET pairs, with Tinyman v2 and Pact as the initial protocol set.

## Synthetic Demo Proof

```bash
python -m algopulse.cli demo-run
```

This returns a clearly labeled synthetic route that shows 5 ALGO in and 10 ALGO out. It is for demo/proof only and must not be represented as live market profit.

## Worker Dry-Run

```bash
ALGO_PULSE_CONNECTORS=tinyman,pact \
ALGO_PULSE_TRADER_ADDRESS=YOUR_HOT_WALLET \
ALGO_PULSE_ALLOW_NON_ALGO_STARTING_ROUTES=true \
ALGO_PULSE_ALLOW_NON_ALGO_LIVE_SUBMISSION=false \
ALGO_PULSE_ENABLE_LIVE_EXECUTION=false \
ALGO_PULSE_EXECUTE_APPROVED=false \
python -m algopulse.cli worker --execute-approved
```

## Docker

```bash
docker build -t algopulse-phase0 .
docker run --rm -p 8765:8765 -v "%cd%/data:/app/data" algopulse-phase0
```

Worker profile:

```bash
docker compose --profile worker up --build worker
```

## Production Safety Notes

- Do not commit signer secrets or wallet exports.
- Do not run with a treasury wallet.
- Do not give AI agents wallet keys.
- Do not put wallet keys in frontend code.
- Do not use unknown or unreviewed repos/services to sign transactions.
- Do not accept user funds.
- Do not build sandwich or predatory MEV behavior.
- Keep dashboard/API behind auth if deployed publicly.
- Leave `ALGO_PULSE_ALLOW_API_EXECUTION=false`.
- Start with scanner-only, then dry-run, then tiny live execution.
- Signer should be split into its own process before trade sizes increase.
- Public dashboard data should be delayed/redacted and should not expose fresh executable routes.

## Good Next Tasks

- Add exact quote refresh immediately before signing.
- Add per-asset valuation before any non-ALGO live submission.
- Add fixture tests comparing known pool quotes against SDK examples.
- Add a testnet route test with a funded test wallet.
- Add authenticated operator-only execution API if dashboard control is desired.
- Migrate SQLite to Postgres if running multiple workers.
- Split unsigned executor from isolated signer before meaningful mainnet capital.
- Add structured logs and alert routing for scanner, quote, route, risk, signer, reconciliation, and refund events.
