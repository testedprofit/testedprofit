# Alert Catalog

Phase 0 treats alerts as control-plane signals. They are not execution instructions, and they do not grant permission to sign, submit, or bypass risk policy.

The admin dashboard reads this catalog from `GET /api/admin/alerts/catalog`, which requires backend admin role headers. Public users should see only delayed or redacted health summaries.

| Code | Severity | Service | Operator response |
| --- | --- | --- | --- |
| `scanner_down` | critical | pool scanner | Restart scanner and confirm read-only/no-key mode. |
| `tinyman_connector_failing` | high | quote engine | Disable Tinyman routes until connector recovery is verified. |
| `pact_connector_failing` | high | quote engine | Disable Pact routes until connector recovery is verified. |
| `quote_age_above_threshold` | warning | quote engine | Reject stale route and refresh quotes. |
| `route_engine_crash` | critical | route engine | Stop route jobs and add a regression test for the failing pair. |
| `database_unavailable` | critical | storage | Stop persistence-dependent jobs and restore database health. |
| `redis_unavailable` | warning | job queue | Pause queued jobs and keep only direct read-only checks. |
| `unknown_asset_detected` | high | risk engine | Reject route and require manual asset allowlist review. |
| `unknown_app_id_detected` | high | risk engine | Reject route before unsigned construction and review connector/app ID. |
| `kill_switch_triggered` | critical | operator control | Keep execution disarmed until separate policy review clears it. |
| `signer_offline` | high | isolated signer | Do not retry through another wallet path; inspect signer host only. |
| `signer_rejection_spike` | critical | isolated signer | Trigger kill switch and inspect route hash/app/asset/fee mismatches. |
| `hot_wallet_balance_changed` | high | reconciliation | Freeze live progression and reconcile wallet history. |
| `daily_loss_limit_near_breach` | critical | risk engine | Stop execution attempts and lower route/trade limits before review resumes. |
| `live_trade_failed` | critical | executor | Disarm automation, inspect Lora, and reconcile wallet deltas. |
| `reconciliation_mismatch` | critical | reconciliation | Freeze live progression and fix accounting before restart. |

## Implementation Rule

Every production alert should eventually write to the `alerts` table, emit a structured log line, and appear in the admin dashboard. Alerts that affect live funds must also preserve the route hash, expected deltas, observed deltas, and operator decision trail.
