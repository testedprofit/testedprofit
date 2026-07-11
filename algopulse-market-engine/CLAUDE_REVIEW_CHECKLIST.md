# Claude Review Checklist

Review in this order.

## 1. Connector Correctness

- `src/algopulse/connectors/tinyman.py`
- `src/algopulse/connectors/pact.py`
- `src/algopulse/vestige.py`
- Confirm Vestige discovery is only selecting the larger PNET pools intended for Phase 0.
- Confirm pinned PNET testing pairs match `INITIAL_TEST_POOLS.md`.
- Confirm reserves are converted from raw units to display units correctly.
- Confirm fees are represented as basis points.
- Confirm pool IDs preserve enough detail to reconstruct the same pool.

## 2. Route Math

- `src/algopulse/engine.py`
- Confirm two-leg venue-arb routes and three-leg ALGO/ASA/USDC triangle routes are generated as scanner/paper candidates.
- Confirm expected net profit accounts for DEX fees, network fee estimate, and safety buffer.
- Confirm every opportunity stores gross profit, network fees, DEX fee estimate, price impact, slippage buffer, net expected profit, confidence score, and skip reason.
- Confirm DEX fees are reported from quote legs but not subtracted twice from net expected profit.
- Confirm `ALGO_PULSE_TRADE_SIZES` is appropriate for thin PNET pools and does not force oversized trades.
- Confirm routes are rejected unless both `net_profit_after_fees_ok` and `profit_bps_ok` pass.
- Confirm routes are rejected unless `fee_buffer_ok`, `quote_freshness_ok`, `app_ids_allowlisted`, and `route_leg_count_ok` pass.
- Confirm default max price impact is 50 bps and app-ID allowlisting is required before approvals.
- Confirm only fresh opportunities are used by execution.
- Confirm risk rejection reasons are recorded.
- Confirm paper trades are candidate-wide, delayed 5s/30s checks use fresh pool state, and no signing or submitted transactions are required.

## 3. Execution Safety

- `src/algopulse/executor.py`
- Confirm only two-leg routes are executed.
- Confirm executor rejects anything without `status=approved` and a passing non-empty `risk_rules` receipt.
- Confirm non-ALGO starting routes require `ALGO_PULSE_ALLOW_NON_ALGO_STARTING_ROUTES=true`.
- Confirm non-ALGO live signing remains blocked unless `ALGO_PULSE_ALLOW_NON_ALGO_LIVE_SUBMISSION=true` is explicitly reviewed.
- Confirm first-leg minimum output is used as second-leg input.
- Confirm starting-asset profit and ALGO fee budget are not mixed for PNET-starting routes.
- Confirm final minimum output must still clear `ALGO_PULSE_MIN_NET_PROFIT_INPUT_UNITS` after slippage.
- Confirm stale routes older than `ALGO_PULSE_MAX_ROUTE_AGE_SECONDS` are rejected before wallet checks.
- Confirm submitted execution is blocked after `ALGO_PULSE_MAX_DAILY_TRADES` and concurrent execution is capped at 1.
- Confirm unsigned executor mode blocks signing even if live flags are accidentally enabled.
- Confirm group-size checks use the SDK `TX_GROUP_LIMIT` and reject more than 16 transactions.
- Confirm combined transaction group length is at most 16.
- Confirm transaction validation rejects rekey fields.
- Confirm transaction validation rejects payment close and asset close-out fields.
- Confirm transaction validation rejects unexpected app IDs and asset IDs.
- Confirm transaction validation rejects group fees above `ALGO_PULSE_MAX_GROUP_FEE_ALGOS`.
- Confirm transactions are regrouped before signing.
- Confirm API execution is disabled by default.
- Confirm dry-runs record expected balance deltas.
- Confirm submitted trades reconcile post-confirmation balances against expected deltas.
- Confirm the main executor now stops at signer handoff metadata and does not directly sign or submit.

## 4. Isolated Signer

- `src/algopulse/signer.py`
- Confirm signer has no route discovery, route choice, scanner, or API execution imports.
- Confirm `SignerRequest.from_payload` rejects arbitrary executor fields such as `instructions`, `command`, `prompt`, and `tool`.
- Confirm route hash allowlist is required.
- Confirm app IDs and asset IDs are validated against signer policy.
- Confirm actual app IDs, asset IDs, input amount, transaction count, and group id match the route intent.
- Confirm max input amount, max group fee, transaction types, sender wallet, wallet reserve, group size, and atomic group ID are validated.
- Confirm rekey, payment close-out, and asset close-out fields are rejected.
- Confirm kill switch blocks signing.
- Confirm every approval/rejection is logged without signer secrets or signed transaction blobs.
- Confirm signer env defaults are locked: disabled, kill switch on, no route hashes allowlisted.

## 5. Wallet Safety

- Confirm hot wallet only.
- Confirm no user funds.
- Confirm signer secrets are never logged.
- Confirm signer secrets are provisioned outside repo-managed files through a signer-host secret manager, signer-host environment, or sealed file outside this repo.
- Confirm `ALGO_PULSE_TRADER_ADDRESS` matches the signer address before signing.
- Confirm opt-ins are checked before building/submitting.
- Confirm input-asset inventory and spendable ALGO fee budget are checked before building/submitting.

## 6. Operational Gates

- Review `src/algopulse/readiness.py`.
- Confirm `/api/live-readiness` cannot submit transactions.
- Confirm readiness preflight uses disarmed execution settings.
- Confirm tiny-live mode enforces ALGO/USDC only, 10 ALGO max trade, 20 ALGO max daily loss, 20 max daily trades, route length <=3, one concurrent route, 100-250 ALGO wallet, manual route hash, Lora txid, and reconciliation before automation.
- scanner stable for 7 days
- dry-run receipts for 7 days
- balance reconciliation receipts reviewed through `/api/reconciliations`
- first live trade manually watched
- daily loss limit tested
- max trade size tested
- route data delayed if dashboard is public

## 7. Known Limitations

- No CEX routing.
- No flash-loan routing.
- No multi-hop routes beyond two-leg venue arb for live execution; three-leg routes are discovery/paper-only.
- No authenticated execution API included.
- SQLite is fine for Phase 0, but Postgres is preferred if scaling.
- The 5-to-10 dashboard proof is synthetic and must stay visually/API-labeled as non-live.
