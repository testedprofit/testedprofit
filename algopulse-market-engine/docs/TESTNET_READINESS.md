# TestNet Readiness

AlgoPulse Phase 3 prepares the read-only market-intelligence stack for Algorand TestNet. It does not authorize signing, transaction submission, hot-wallet use, user deposits, or live trading.

## Implemented Boundary

- `src/algopulse/testnet_readiness.py` evaluates runtime configuration without returning endpoint URLs, tokens, or secrets.
- `GET /api/testnet/readiness` exposes a public-safe readiness summary for the dashboard.
- `.env.testnet.example` provides a fail-closed TestNet profile with execution and signing disabled.
- The dashboard shows network, delay, asset, connector, and wallet-boundary evidence under Phase 3.
- Public routes default to a 900-second delay even when no environment override is present.

## Read-Only TestNet Setup

```powershell
Copy-Item .env.testnet.example .env
```

Before starting staging, a human must:

1. Create or select a TestNet-only PNET test ASA.
2. Set `PNET_ASA_ID` to that TestNet asset ID.
3. Add the TestNet PNET pairs to `ALGO_PULSE_ASSET_PAIRS`.
4. Verify every TestNet asset and app ID against the selected Tinyman and Pact deployments.
5. Keep `ENABLE_EXECUTION=false`, `ENABLE_SIGNER=false`, `ALGO_PULSE_ALLOW_API_EXECUTION=false`, and `KILL_SWITCH=true`.

Start the local API and inspect the gate:

```powershell
uvicorn algopulse.api:app --host 127.0.0.1 --port 8769
Invoke-RestMethod http://127.0.0.1:8769/api/testnet/readiness
```

The profile is ready for wallet review only when `testnetReadOnlyReady` is `true`. `walletConnectionReady` and `productionReady` intentionally remain `false`.

## Read-Only TestNet Probe - 2026-07-09

The isolated profile was exercised against separate local storage with all signer, execution, and submission flags forced off.

- TestNet algod responded at round `65171995`.
- TestNet Indexer resolved ASA `10458941` as `USDC` with 6 decimals.
- Tinyman returned one ALGO/USDC TestNet pool.
- Pact's configured TestNet API returned HTTP 502 for the same pair. The SDK surfaced that non-JSON response as `JSONDecodeError`; connector evidence records it as `error / pact_api_non_json_response`.
- The scanner correctly rolled the run up as `degraded`, with 1 pool, 0 opportunities, and 0 paper candidates.
- No signer, wallet, hot-wallet, transaction construction, or submission path was used.

This proves read-only TestNet connectivity and safe partial-failure reporting. It does not prove PNET TestNet liquidity or cross-venue quote comparability.

## 24-Hour Read-Only Soak Runner

The soak runner is the operator process that builds sustained TestNet evidence before any wallet integration review. It is local-only, read-only, and never starts from the API.

### MainNet Read-Only Staging

Fail-closed MainNet research profile (no keys, no signing, no submission):

```powershell
# Use .env.mainnet-readonly.example as the local profile basis
python -m algopulse.mainnet_readonly --once
python -m algopulse.mainnet_readonly --duration-hours 24 --interval-seconds 60
```

Requires `APP_ENV=mainnet-readonly` and `ALGORAND_NETWORK=mainnet`. Refuses execution, signer, API execution, and mnemonic configuration. Monitors allowlisted pairs (ALGO/PNET, ALGO/USDC by default). Control Room environment matrix shows `network=mainnet`.

### First real paper-arbitrage loop

Run a single read-only TestNet paper loop (Tinyman + Pact, quotes 1/5/10 ALGO, route/risk, optional T+5/T+30 rechecks):

```powershell
python -m algopulse.paper_arb_loop
```

Fast local/dev path without waiting for rechecks:

```powershell
python -m algopulse.paper_arb_loop --skip-rechecks
```

Pact TestNet REST (`api.testnet.pact.fi`) may return HTTP 502. The Pact connector then falls back to algod factory-box discovery and still stores degraded connector evidence. Outcomes are explicit (`paper_candidate_created`, `spread_below_profit_threshold`, `route_rejected_by_risk`, `no_shared_liquid_pair`, `connector_unavailable`) and feed the same Control Room store tables.

### Commands

One-shot observation (local verification):

```powershell
python -m algopulse.testnet_soak --once
```

Bounded 24-hour soak (60-second interval default):

```powershell
python -m algopulse.testnet_soak --duration-hours 24 --interval-seconds 60
```

Optional stable run id for restart continuity:

```powershell
python -m algopulse.testnet_soak --duration-hours 24 --interval-seconds 60 --run-id soak_staging_001
```

Stop safely with Ctrl+C. The current observation finishes or exits; the local lock file is released; earlier observations remain in SQLite.

### Evidence storage and restart behavior

- Observations are stored in the configured market database table `testnet_soak_observations`.
- Default database path comes from settings / `ALGO_PULSE_DATA_DIR` (same store as the scanner).
- Restarts append new observations; sequence numbers continue per `run_id`.
- A local lock file at `{data_dir}/testnet_soak.lock` prevents overlapping runners.
- Mock connector observations are stored and labeled `source=mock` but never count toward live 24-hour coverage.

### Control Room

1. Start the API: `uvicorn algopulse.api:app --host 127.0.0.1 --port 8769`
2. Open the dashboard as the local-review admin role.
3. Open the Control Room view.
4. Inspect the **TestNet Soak** panel for coverage, connector health, gaps, blockers, and paper T+5/T+30 totals.

Admin APIs (backend-enforced mock admin session today):

- `GET /api/ops/testnet-soak`
- `GET /api/ops/testnet-soak/observations?limit=50`

There is no remote start endpoint. Starting the runner remains a local operator action.

### What constitutes gate completion

The 24-hour soak gate can only be considered ready for human review when all are true:

- elapsed live coverage is at least 24 real hours from first to latest live observation
- live observations exist (mock alone is insufficient)
- algod is healthy and rounds progress
- paper-trading evidence is present (candidates and/or T+5 / T+30 rechecks)
- productionReady remains false
- live execution remains locked

A one-shot observation never completes the 24-hour gate.

### What mock evidence cannot prove

- live Tinyman or Pact TestNet availability
- algod/Indexer round health
- quote freshness under real network conditions
- sustained scanner uptime
- paper-trade survival on real quotes

### Known limitations

- Pact TestNet availability is externally uncertain; Pact failure must record degraded/error evidence without erasing Tinyman evidence.
- TestNet PNET ASA remains unconfigured (`PNET_ASA_ID=0` in `.env.testnet.example`) until a human decides.
- No wallet, signer, transaction construction, transaction submission, or live-trading functionality is included in the soak runner or panel.

## Remaining Human Gates

- Complete a real 24-hour read-only soak and review stored evidence.
- Pera Connect and Defly WalletConnect dependency/version review.
- Connect-only session design with no transaction construction or signing calls.
- TestNet PNET ASA ownership, metadata, opt-in, and faucet/distribution plan.
- Tinyman/Pact TestNet app and pool ID verification.
- Wallet challenge/session proof and backend role enforcement.
- Public claims and payment/credit behavior review.

## Stop Conditions

Stop if a change introduces signer material, signed transactions, submission payloads, hot-wallet logic, MainNet IDs in a TestNet profile, a public delay below 900 seconds, or fresh executable routes on public endpoints.

## Source Notes

- [Algorand REST API overview](https://dev.algorand.co/reference/rest-api/overview/)
- [AlgoKit network deployment model](https://developer.algorand.org/docs/get-details/algokit/features/deploy/)
- [Pera Connect network chain IDs](https://docs.perawallet.app/references/pera-connect)
- [Defly WalletConnect usage](https://defly.gitbook.io/defly-manual/app/wallet-actions)
- [Tinyman TestNet](https://docs.tinyman.org/tinyman-v1/tinyman-testnet)
