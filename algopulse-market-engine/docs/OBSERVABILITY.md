# Observability

AlgoPulse Phase 0 needs observability before scale. Logs, metrics, alerts, and receipts are evidence for scanner reliability, quote quality, risk rejection, PNET payments, execution-control locks, and later tiny platform-only execution if gates pass.

## Required Metrics

| Service | Metrics |
| --- | --- |
| Scanner | scan cycles, scan duration, pools seen, pools skipped, connector errors, latest block round, data freshness seconds |
| Quote Engine | quotes captured, quote failures, quote age, expected output, fee estimate, price impact, expires-at drift |
| Route Engine | routes generated, routes rejected, skip reason counts, route length, gross profit, net expected profit, confidence score |
| Risk Engine | approvals, rejections, rule failure counts, stale quote count, allowlist rejection count, max-trade rejection count |
| Paper Trader | candidates recorded, would-execute count, 5s recheck count, 30s recheck count, quote decay, expected-vs-simulated profit |
| Unsigned Executor | build attempts, rejected groups, tx count, fee estimate, unsigned-only status, SDK group-limit rejections |
| Signer | online state, rejection count, approval count, route-hash rejects, app/asset rejects, fee/input/reserve rejects, kill-switch rejects |
| PNET Fee Flow | access checks, fee quotes, tx verification successes, tx verification failures, credits granted, refunds queued |
| Reconciliation | expected output, actual output, fee delta, balance delta, mismatch count, unresolved receipts |

## Required Alerts

These alerts must exist before production promotion:

- scanner down
- Tinyman connector failing
- Pact connector failing
- quote age above threshold
- route engine crash
- database unavailable
- Redis unavailable
- unknown asset detected
- unknown app ID detected
- kill switch triggered
- signer offline
- signer rejection spike
- hot wallet balance changed
- daily loss limit near breach
- live trade failed
- reconciliation mismatch
- PNET fee verification failed
- refund queue backlog

## Service Health States

| State | Meaning | Public Behavior |
| --- | --- | --- |
| `ok` | Service is current and within policy. | Show normal delayed data. |
| `degraded` | Service works with stale, partial, or delayed inputs. | Show delayed data and health warning. |
| `blocked` | Policy, allowlist, kill switch, or risk gate prevents action. | Show safe blocked state, no execution controls. |
| `down` | Service is not responding or cannot reach dependency. | Hide fresh intelligence and show operator alert. |
| `unknown` | Health has not been observed yet. | Treat as blocked for execution and delayed for public data. |

## Required Log Fields

All services:

- `timestamp`
- `service`
- `environment`
- `network`
- `correlation_id`
- `route_hash` when available
- `wallet_address` only when required and safe to log
- `decision`
- `reason`
- `duration_ms`
- `block_round`
- `data_freshness_seconds`

Scanner:

- `venue`
- `pool_id`
- `app_id`
- `asset_a_id`
- `asset_b_id`
- `reserve_a`
- `reserve_b`
- `fee_bps`
- `liquidity_estimate`

Quote engine:

- `input_asset_id`
- `output_asset_id`
- `input_amount`
- `expected_output`
- `fee_estimate`
- `price_impact_bps`
- `captured_at`
- `expires_at`

Route engine:

- `route_leg_count`
- `venues`
- `gross_profit`
- `network_fees`
- `dex_fees`
- `slippage_buffer`
- `net_expected_profit`
- `confidence_score`
- `skip_reason`

Risk engine:

- `approved`
- `failed_rule`
- `rule_map`
- `quote_age_seconds`
- `max_trade_size`
- `daily_trades`
- `daily_loss`
- `concurrent_executions`

Paper trader:

- `would_execute`
- `recheck_after_seconds`
- `simulated_actual_output`
- `quote_decay`
- `expected_vs_simulated_profit`

Executor:

- `unsigned_only`
- `tx_count`
- `group_limit`
- `estimated_group_fee`
- `risk_decision_id`
- `submitted=false`

Signer:

- `route_hash_approved`
- `asset_ids_valid`
- `app_ids_valid`
- `transaction_types_valid`
- `max_input_valid`
- `max_fee_valid`
- `wallet_reserve_valid`
- `kill_switch_state`
- `approved=false` for every rejection

## Reconciliation Requirements

- Every live or dry-run receipt needs a route hash.
- Expected output, actual output, network fees, DEX fees, and slippage buffer must be stored.
- Wallet balance deltas must be compared against expected deltas.
- Mismatches block additional live attempts until resolved.
- Public receipts can be delayed or redacted, but must not hide losses, failed trades, refunds, or skipped routes.
- PNET fee receipts must reconcile payment intent, submitted txid, on-chain verification, credit/report unlock, and refund status.
