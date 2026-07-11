# Policy Controls

These controls define the Phase 0 hard-stop catalog exposed at `GET /api/admin/policy/catalog`.

This is a control-plane contract only. It does not grant permission to sign, submit, custody funds, bypass the kill switch, or loosen signer policy. Frontend gates are UX only; backend role checks and isolated signer policy remain mandatory.

| Control | Enforced By | Rejects |
| --- | --- | --- |
| `max_input_amount` | risk engine, isolated signer | Any route whose input amount exceeds the configured per-trade cap. |
| `max_transaction_fee` | unsigned executor, isolated signer | Any unsigned group whose estimated or actual fee exceeds the group fee cap. |
| `asset_allowlist` | risk engine, isolated signer | Any route or transaction group that includes an unreviewed asset ID. |
| `app_id_allowlist` | risk engine, isolated signer | Any route or transaction group that calls an unreviewed application ID. |
| `transaction_type_allowlist` | isolated signer | Any transaction type outside the reviewed `pay`, `axfer`, and `appl` set. |
| `route_hash_approval` | isolated signer | Any unsigned group whose route hash was not explicitly reviewed and approved. |
| `daily_spend_limit` | risk engine, operator preflight | Additional routes after daily trade count or gross input exposure reaches policy limits. |
| `wallet_reserve_minimum` | isolated signer, reconciliation | Any group that would take the hot wallet below reserve after fees and minimum balance. |
| `kill_switch` | admin preflight, isolated signer | All live-arm and signing requests while the kill switch is active. |

## Review Notes

- The admin dashboard may display these controls, but display state does not authorize execution.
- The policy catalog must stay role-gated because exact limits can expose operating posture.
- Production changes to limits should land with tests, a changelog entry, and a handoff note.
