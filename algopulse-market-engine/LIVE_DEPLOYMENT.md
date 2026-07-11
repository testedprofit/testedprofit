# Live Deployment Notes

The current Phase 0 promotion contract has three environments:

- Local: mock data, scanner optional, no signer, no real submission.
- Staging: live scanner, live quotes, paper trading, no live signing, delayed dashboard.
- Production Phase 0: live scanner, route engine, paper trading, risk engine, admin dashboard, public delayed dashboard, isolated signer only after gates, tiny own-funds hot wallet only.

The worker recipes below are implementation recipes inside that contract. They do not authorize live signing by themselves.

For local non-Docker runs, install the package in editable mode once:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

Core Python dependency path:

```bash
pip install py-algorand-sdk fastapi uvicorn pydantic sqlalchemy psycopg2-binary redis python-dotenv
pip install git+https://github.com/tinymanorg/tinyman-py-sdk.git
pip install pactsdk
```

## Mode 1 - Dashboard And Mock Bot

Use this for smoke tests.

```bash
ALGO_PULSE_CONNECTORS=mock
uvicorn algopulse.api:app --host 0.0.0.0 --port 8765
```

## Mode 2 - Live Read-Only Market Scanner

Use this first on a VPS.

```bash
ALGO_PULSE_CONNECTORS=tinyman,pact
ALGO_PULSE_TARGET_ASSET_ID=3169177585
ALGO_PULSE_USE_VESTIGE_DISCOVERY=true
ALGO_PULSE_VESTIGE_PINNED_PAIR_ASSET_IDS=1290751153,3436365167,1893942045,31566704,1390638935,2644742542,3249403496,3427156477,1119722936,3410350791,846652486,3427041827,1674484158,3227174563
ALGO_PULSE_VESTIGE_INCLUDE_FALLBACK_PAIRS=false
ALGO_PULSE_TRADE_SIZES=1,2,5,10
ALGO_PULSE_MAX_ROUTE_AGE_SECONDS=5
ALGO_PULSE_ENABLE_LIVE_EXECUTION=false
ALGO_PULSE_EXECUTE_APPROVED=false
python -m algopulse.cli worker --loop
```

This uses Vestige to discover larger PNET pools, scans live Tinyman and Pact pool state, and records opportunities. It does not build or sign trades.

The pinned list above matches `INITIAL_TEST_POOLS.md`.

## Mode 3 - Worker Dry-Run Execution

Use this after the scanner is stable.

```bash
ALGO_PULSE_CONNECTORS=tinyman,pact
ALGO_PULSE_TARGET_ASSET_ID=3169177585
ALGO_PULSE_USE_VESTIGE_DISCOVERY=true
ALGO_PULSE_VESTIGE_PINNED_PAIR_ASSET_IDS=1290751153,3436365167,1893942045,31566704,1390638935,2644742542,3249403496,3427156477,1119722936,3410350791,846652486,3427041827,1674484158,3227174563
ALGO_PULSE_VESTIGE_INCLUDE_FALLBACK_PAIRS=false
ALGO_PULSE_TRADER_ADDRESS=YOUR_HOT_WALLET
ALGO_PULSE_ALLOW_NON_ALGO_STARTING_ROUTES=true
ALGO_PULSE_ALLOW_NON_ALGO_LIVE_SUBMISSION=false
ALGO_PULSE_TRADE_SIZES=1,2,5,10
ALGO_PULSE_MAX_ROUTE_AGE_SECONDS=5
ALGO_PULSE_ENABLE_LIVE_EXECUTION=false
ALGO_PULSE_EXECUTE_APPROVED=false
python -m algopulse.cli worker --loop --execute-approved
```

This attempts to build an atomic transaction group for the best fresh approved route. It verifies opt-ins, input-asset inventory, spendable ALGO fee budget, and max route age, then stores dry-run receipts without signing.

For PNET-starting routes, keep `ALGO_PULSE_ALLOW_NON_ALGO_STARTING_ROUTES=true` and `ALGO_PULSE_ALLOW_NON_ALGO_LIVE_SUBMISSION=false` during review. The dry-run receipt reports starting-asset profit separately from ALGO fees and records expected balance deltas for reconciliation review.

## Mode 4 - Tiny Live Execution

Use this only after review.

```bash
ALGO_PULSE_CONNECTORS=tinyman,pact
ALGO_PULSE_TARGET_ASSET_ID=3169177585
ALGO_PULSE_USE_VESTIGE_DISCOVERY=true
ALGO_PULSE_TRADER_ADDRESS=YOUR_HOT_WALLET
ALGO_PULSE_ENABLE_LIVE_EXECUTION=true
ALGO_PULSE_EXECUTE_APPROVED=true
ALGO_PULSE_ALLOW_API_EXECUTION=false
ALGO_PULSE_ALLOW_NON_ALGO_STARTING_ROUTES=true
ALGO_PULSE_ALLOW_NON_ALGO_LIVE_SUBMISSION=false
ALGO_PULSE_MAX_LIVE_TRADE_SIZE=10
ALGO_PULSE_TRADE_SIZES=1,2,5,10
ALGO_PULSE_MAX_ROUTE_AGE_SECONDS=5
ALGO_PULSE_MIN_NET_PROFIT_ALGOS=0.25
ALGO_PULSE_MIN_NET_PROFIT_INPUT_UNITS=0.25
ALGO_PULSE_MIN_PROFIT_BPS=35
ALGO_PULSE_MAX_DAILY_LOSS=5
python -m algopulse.cli worker --loop --execute-approved
```

Signer secrets are not stored in repo files or deployment examples. Provision them only on the isolated signer host through a local secret manager, signer-host environment, or sealed file outside this repo.

## Required Before Live Funds

- Use a fresh hot wallet.
- Fund it with a tiny amount only.
- Opt in to USDC and any intermediate ASA.
- Confirm `ALGO_PULSE_ALLOW_API_EXECUTION=false`.
- Confirm dashboard/API is not public or has auth in front of it.
- Start with `ALGO_PULSE_MAX_LIVE_TRADE_SIZE=10` or lower.
- Keep `ALGO_PULSE_MIN_NET_PROFIT_INPUT_UNITS` and `ALGO_PULSE_MIN_PROFIT_BPS` positive so the bot cannot trade for volume.
- Keep `ALGO_PULSE_ALLOW_NON_ALGO_LIVE_SUBMISSION=false` until ALGO-equivalent PNET profit accounting is reviewed.
- Confirm the execution dry-run rejects routes whose final minimum output no longer clears the net-profit floor after slippage.
- Confirm stale routes older than `ALGO_PULSE_MAX_ROUTE_AGE_SECONDS` are rejected before wallet checks.
- Confirm `/api/reconciliations` records expected deltas for dry-runs and actual deltas after submitted trades.
- Confirm group validation rejects rekey, close-out fields, unknown app IDs, unknown asset IDs, and excessive group fees.
- Watch first execution manually.
- Increase limits only after successful reconciliation.

## Docker

Dashboard:

```bash
docker compose up --build algopulse
```

Worker profile:

```bash
docker compose --profile worker up --build worker
```

For production, run dashboard and worker as separate services sharing the same database volume.
