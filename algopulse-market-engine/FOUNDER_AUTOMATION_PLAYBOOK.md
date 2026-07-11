# Founder Automation Playbook

This is the operator playbook for turning AlgoPulse from a Phase 0 PNET arb scanner into a real, trusted market agent.

The mindset: build the machine in layers. Every phase should produce a useful artifact, a visible dashboard improvement, and a measurable readiness signal. Do not jump from "it sees spreads" to "it should trade money."

## North Star

Create the most trusted Algorand micro-arb and liquidity intelligence agent for PNET first, then expand into a daily-use Algorand market tool.

The bot should:

- find real market inefficiencies
- avoid trading for volume
- prove profit after fees and slippage
- show clear route-gate reasons
- attract LPs by showing missing depth
- build public credibility before scaling live execution

## Product Thesis

Use public repos as references, especially Arbitron-style projects and simple educational scanners, but build the real system around official Tinyman, Pact, and Algorand SDKs.

The product is AlgoPulse Market Engine, not a generic arb bot. It should produce market scanning, routing intelligence, historical quotes, paper-trade performance, tiny own-funds execution only if safe, public receipts, and a delayed public dashboard.

Founder rule: Phase 0 wins when it creates evidence and trust. A live trade is only useful after scanner data, quote history, paper-trading decay, risk rejection, unsigned execution review, signer isolation, and reconciliation are already boring.

## Automation Boundary

Codex can automate:

- code changes
- tests
- dashboard improvements
- scanner runs
- dry-run readiness reports
- documentation
- route analysis
- wallet-readiness checks using public address
- deployment handoff prep

Codex must not automate without explicit human approval:

- storing or entering signer secrets
- enabling live submission
- changing wallet permissions
- exposing execution APIs publicly
- increasing trade caps
- enabling non-ALGO live signing
- deploying a smart contract with custody behavior

## Version Ladder

This is the first version path to actually build. Do not start with live execution.

1. v0.1: read-only scanner
2. v0.2: Tinyman + Pact quote comparison
3. v0.3: ALGO/USDC route engine
4. v0.4: paper trading with 5s/30s recheck
5. v0.5: dashboard showing delayed spreads
6. v0.6: risk engine
7. v0.7: unsigned transaction builder
8. v0.8: signer service
9. v0.9: one manual tiny trade
10. v1.0: fully automated tiny own-funds micro-arb

Founder rule: v0.1 through v0.8 can be impressive without moving funds. v0.9 is the first submitted trade, and it must be manually approved, tiny, ALGO/USDC-only, Lora-verified, and reconciled before v1.0 automation is considered.

## Phase 0: Make The Agent Real Without Risking Funds

### Step 0.1 - Lock The Operating Rules

Goal: prevent future AI work from accidentally making the bot unsafe.

Automated actions:

1. Keep `ALGORAND_ARB_AGENT_RULES.md` in the repo.
2. Keep `REAL_ARB_BOT_ARCHITECTURE.md` in the repo.
3. Make Claude/Codex read both before changing execution behavior.
4. Keep README and handoff docs linked to both files.

Done when:

- Any new agent knows the trading safety boundaries.
- The repo clearly says PyTeal is not required for basic two-leg arb.
- Non-ALGO live signing remains blocked unless reviewed.

Current status: done.

### Step 0.2 - Run Live Market Watch Mode

Goal: prove the scanner can observe the pinned PNET universe reliably.

Automated actions:

1. Start scanner with Tinyman/Pact connectors.
2. Use Vestige pinned PNET pool list.
3. Use small route sizes: `1,2,5,10`.
4. Save scan data into SQLite.
5. Display market state on the dashboard.
6. Record all route rejection reasons.

Command:

```powershell
$env:PYTHONPATH='src'
$env:ALGO_PULSE_CONNECTORS='tinyman,pact'
$env:ALGO_PULSE_NETWORK='mainnet'
$env:ALGO_PULSE_TARGET_ASSET_ID='3169177585'
$env:ALGO_PULSE_USE_VESTIGE_DISCOVERY='true'
$env:ALGO_PULSE_VESTIGE_PINNED_PAIR_ASSET_IDS='1290751153,3436365167,1893942045,31566704,1390638935,2644742542,3249403496,3427156477,1119722936,3410350791,846652486,3427041827,1674484158,3227174563'
$env:ALGO_PULSE_VESTIGE_INCLUDE_FALLBACK_PAIRS='false'
$env:ALGO_PULSE_TRADE_SIZES='1,2,5,10'
$env:ALGO_PULSE_ENABLE_LIVE_EXECUTION='false'
$env:ALGO_PULSE_EXECUTE_APPROVED='false'
python -m algopulse.cli readiness --scan
```

Done when:

- live connectors are configured
- pools are observed on both Tinyman and Pact when available
- scanner runs without crashing
- dashboard shows "watch-ready" or better
- route gate explains why there is no trade

### Step 0.3 - Improve Route-Gate Intelligence

Goal: make the bot tell us why it is not trading.

Automated actions:

1. Count rejection reasons per scan.
2. Surface best rejected route.
3. Show whether the blocker is profit floor, bps floor, price impact, pool reserves, trade size, or wallet readiness.
4. Add trend tracking: which blocker dominates over time?

Product reason:

This makes the dashboard useful even when there is no trade. A founder can say: "The bot is not asleep. It is waiting because the current spread does not pay."

Done when:

- every no-trade state has a reason
- no vague "no opportunity" state remains
- route-gate data is visible on dashboard and API

Current status: partially done.

### Step 0.4 - Add Balance Reconciliation

Goal: move from "route looked profitable" to "wallet balances prove the outcome."

Automated actions:

1. Before dry-run or live submit, snapshot wallet balances for all route assets.
2. After confirmation, snapshot balances again.
3. Compute actual delta per asset.
4. Compare actual delta against expected output and minimum output.
5. Store reconciliation result in SQLite.
6. Show reconciliation in dashboard.

Human gate:

- Public address is okay.
- Signer secrets are not needed for scanner-only reconciliation planning.
- Do not sign anything yet.

Done when:

- the bot can explain expected vs actual balances for every route
- non-ALGO profit is tracked in starting-asset units
- ALGO fees are tracked separately

Priority: next engineering task.

### Step 0.5 - Add Fresh Quote Refresh

Goal: prevent stale-route execution.

Automated actions:

1. When an approved route appears, fetch exact fresh SDK quotes again.
2. Rebuild transaction group from fresh quotes.
3. Reject if route age exceeds cutoff.
4. Reject if fresh expected profit falls below floor.
5. Reject if final minimum output fails.

Suggested setting:

```text
ALGO_PULSE_MAX_ROUTE_AGE_SECONDS=5
```

Done when:

- routes cannot execute using stale scan data
- dry-run receipt includes route age and quote refresh timestamp

### Step 0.6 - Dry-Run With A Public Hot Wallet Address

Goal: prove transaction groups can build without signing.

Human input required:

- reviewed hot wallet public address
- no signer secret
- wallet opted into required ASAs
- tiny balances only

Automated actions:

1. Configure `ALGO_PULSE_TRADER_ADDRESS`.
2. Keep live execution disabled.
3. Run worker with `--execute-approved`.
4. Build atomic dry-run groups only when approved route exists.
5. Store dry-run receipts.
6. Verify group fields and fees.

Required flags:

```text
ALGO_PULSE_ENABLE_LIVE_EXECUTION=false
ALGO_PULSE_EXECUTE_APPROVED=false
ALGO_PULSE_ALLOW_NON_ALGO_STARTING_ROUTES=true
ALGO_PULSE_ALLOW_NON_ALGO_LIVE_SUBMISSION=false
```

Done when:

- wallet lookup passes
- opt-ins pass
- inventory checks pass
- approved route builds atomic group
- no signing occurs

### Step 0.7 - Tiny ALGO-Start Live Trade

Goal: perform the first real trade only after scanner, dry-run, and reconciliation are proven.

Human approval required:

- explicit go-live approval
- tiny hot-wallet signer secrets provisioned only on the isolated signer host
- operator watching the first run

Required settings:

```text
ALGO_PULSE_ENABLE_LIVE_EXECUTION=true
ALGO_PULSE_EXECUTE_APPROVED=true
ALGO_PULSE_ALLOW_API_EXECUTION=false
ALGO_PULSE_ALLOW_NON_ALGO_LIVE_SUBMISSION=false
ALGO_PULSE_MAX_LIVE_TRADE_SIZE=1
ALGO_PULSE_TRADE_SIZES=1
```

Automated actions:

1. Run readiness preflight.
2. Confirm wallet and opt-ins.
3. Confirm fresh approved route.
4. Build group.
5. Validate group.
6. Sign.
7. Submit.
8. Wait for confirmation.
9. Reconcile balances.
10. Write live receipt.

Done when:

- transaction confirms
- balance reconciliation is within expected range
- no unexpected transaction fields appear
- daily loss and max fee gates remain active

## Phase 1: Productize The Public Dashboard

Goal: make AlgoPulse useful every day even when it is not trading.

Automated actions:

1. Improve dashboard states:
   - watching
   - wallet needed
   - route blocked
   - dry-run ready
   - submission armed
2. Add route-gate history.
3. Add LP opportunity board:
   - pair
   - current venues
   - missing second venue
   - estimated depth need
4. Add public delay for route data.
5. Add SEO landing copy that does not overclaim.
6. Keep synthetic demo clearly labeled.

Founder outcome:

The bot becomes a marketing surface for PNET liquidity. People can see where LPs are needed.

Done when:

- dashboard is useful without live trading
- no state feels broken or empty
- LP CTAs are clean and not cluttered

## Phase 2: Operator-Grade Automation

Goal: make the bot boring, monitored, and recoverable.

Automated actions:

1. Add structured logs.
2. Add error counters.
3. Add alert hooks.
4. Add daily summary report:
   - pools scanned
   - routes found
   - approved routes
   - dry-runs built
   - rejected route reasons
   - wallet readiness
   - profit/loss if live
5. Add config sanity checker.
6. Add backup/export for SQLite.

Done when:

- operator can trust the system state within one minute
- failures produce clear messages
- config mistakes are caught before runtime

## Phase 3: Non-ALGO Profit Accounting

Goal: decide whether PNET-starting routes are truly valuable.

Automated actions:

1. Add per-asset valuation source.
2. Track PNET, ALGO, USDC, and USD-equivalent deltas.
3. Separate realized profit from inventory mark-to-market.
4. Add rebalancing rules.
5. Add "do not trade if profit cannot be valued" guard.

Human decision:

Choose the primary profit unit:

- PNET accumulation
- ALGO accumulation
- USDC value
- USD-equivalent reporting

Done when:

- non-ALGO live signing can be reviewed with real accounting
- the operator can explain why a PNET profit is worth taking

## Phase 4: Smart Contract Evaluation

Goal: decide whether on-chain strategy logic is actually needed.

Do not start here.

Smart contract becomes useful only if we need:

- pooled user capital
- strategy vault
- permissioned executors
- profit splitting
- contract-held inventory
- flash-liquidity callback logic
- on-chain circuit breakers

Preferred path:

1. Write contract spec first.
2. Use AlgoKit / Algorand Python unless a specific PyTeal reason exists.
3. Test on LocalNet.
4. Test on TestNet.
5. Audit dangerous paths.
6. Deploy with tiny caps.

Done when:

- contract reduces risk or unlocks a required product feature
- it is not just complexity for its own sake

## Phase 5: Expansion

Goal: expand beyond PNET only after the engine is trusted.

Expansion order:

1. More PNET pairs.
2. More Algorand DEX venues.
3. More target assets.
4. Triangular routes.
5. Cross-chain monitoring, not execution.

Do not expand before:

- reconciliation works
- stale-route guard works
- dry-run receipts are stable
- dashboard explains failures
- live execution has proven tiny profitable runs

## Weekly Founder Operating Loop

Every week:

1. Run scanner for pinned PNET pools.
2. Review route rejection summary.
3. Identify whether liquidity, spread, or route size is the blocker.
4. Improve one dashboard decision surface.
5. Improve one execution safety check.
6. Update Claude handoff.
7. Decide whether the next phase gate is ready.

## Daily Automation Loop

Every day:

1. Fresh live scan.
2. Readiness report.
3. Route-gate summary.
4. LP opportunity summary.
5. Error log review.
6. Dashboard visual check.
7. No-go if wallet, quote freshness, or reconciliation fails.

## Founder Red-Team Rule

Before saying "ready," answer:

- What could lose money?
- What could mislead users?
- What could leak a key?
- What could trade for volume instead of profit?
- What could be stale?
- What could fail silently?
- Who notices first?
- What automatically stops it?

If any answer is weak, the next task is risk reduction, not growth.

## Immediate Next Build Queue

1. Add balance reconciliation tables and API.
2. Add pre/post balance snapshot functions.
3. Add route age cutoff.
4. Add fresh quote refresh before execution.
5. Add dashboard reconciliation card.
6. Add daily readiness summary command.
7. Add first-live-run checklist command.

This is the path from impressive demo to credible trading agent.
