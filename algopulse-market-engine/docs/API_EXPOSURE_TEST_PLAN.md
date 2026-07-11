# API Exposure Test Plan

This plan turns `docs/API_EXPOSURE_REVIEW_CHECKLIST.md` into concrete test coverage before changing application logic. It does not add tests, auth, endpoint removals, signer behavior, live trading, transaction submission, hot-wallet logic, risk-limit changes, or secrets.

The plan is not proof that the app is production-secure. It is a map of tests needed to make the API exposure reviewable.

## Evidence Used

Repo facts:

- `src/algopulse/api.py` exposes `59` decorated FastAPI endpoints plus `1` `/static/*` mount.
- `docs/API_EXPOSURE_INVENTORY.md` classifies `60` exposed surfaces by intended access and risk.
- `docs/API_EXPOSURE_REVIEW_CHECKLIST.md` defines stop conditions and review gates.
- Existing tests already cover some admin mock checks, payment verification logic, refunds, readiness, control-plane responses, and execution kill-switch behavior.

Assumptions:

- Intended access levels in the inventory are production recommendations, not current behavior.
- Current local-review headers are acceptable only for local development and tests.
- Future production auth, wallet proof, and redaction policy still require human review.

Unknowns:

- Final deployment-layer auth, proxy rules, rate limits, and static file serving rules are not known from the repo alone.
- Real Pera wallet proof is not implemented in the inspected route layer.
- Final public receipt and delayed-data policy needs human approval.

## Endpoint Categories That Need Tests

| Category | Routes | Current behavior | Intended behavior | Test goal | Human review |
|---|---|---|---|---|---|
| Static/health/config | `/`, `/static/*`, `/health`, `/api/health`, `/api/config/public` | Public. | Public, minimal, no secrets. | Prove public operational responses are safe and static assets do not expose private files. | Public config wording review required. |
| Public market intelligence | `/api/pulse`, `/api/pools`, `/api/opportunities`, `/api/risk-policy`, report endpoints | Public. Some route data is delayed or aggregate. | Public only if delayed, redacted, aggregate, or non-actionable. | Prove public users cannot see fresh executable opportunities or private operational detail. | Public data policy review required. |
| Product validation | `/api/events/user-action` | Public write with taxonomy validation. | Public only with bounded payloads, taxonomy checks, privacy review, and abuse controls. | Prove invalid actions are rejected and metadata stays bounded. | Analytics/privacy review required. |
| Mock/local-only | `/api/session/wallet/{address}`, `/api/demo-run` | Public local-review behavior. | Local-only or clearly synthetic/mock. | Prove mock auth and synthetic demos are labeled and cannot masquerade as production evidence. | Wallet/public-claims review required. |
| Connected user/PNET | `/api/user/pnet/access-check`, `/api/user/pnet/fee-quote`, `/api/user/pnet/fee-confirm`, `/api/verify-payment` | Public local-review/stubbed user flows. | Connected user with backend wallet/session proof. | Prove these routes do not sign, trade, custody funds, or grant production credits from mock txids. | Wallet/payment review required. |
| Payment/refund records | `/api/payment-verifications`, `/api/refund-cases`, refund status mutation | Some detailed records are public today. | Admin-only or user-owned and redacted. | Prove detailed payment/refund records are not publicly visible before production. | Payment/refund policy review required. |
| Trade/reconciliation records | `/api/paper-trades`, `/api/live-trades`, `/api/reconciliations` | Some detailed records are public today. | Admin-only or public-redacted aggregate receipts. | Prove public users cannot see sensitive strategy, wallet, timing, or reconciliation details. | Execution/public receipt review required. |
| Readiness/scanner controls | `/api/live-readiness`, `/api/scan` | Public readiness and scanner trigger surfaces. | Admin-only full report and admin/local-only scanner trigger. | Prove public users cannot trigger backend work or see execution-readiness internals. | Deployment/risk review required. |
| Admin observability | `/api/admin/*`, `/api/ops/*` GET routes | Backend mock-admin gated via local-review headers. | Backend-enforced admin proof. | Prove guest/user headers are rejected and frontend role alone does not grant admin access. | Auth/admin review required. |
| Admin commands | `/api/admin/scan-now`, scanner, route, paper, dry-run, live, kill-switch commands | Backend mock-admin gated; some execution-adjacent commands are blocked. | Admin-only, audited, no signing/submission. | Prove commands require admin and execution-adjacent commands stay locked. | Execution/risk review required. |
| Disabled/execution-adjacent | `/api/execute-best`, `/api/admin/live/arm`, `/api/admin/kill-switch/clear`, `/api/admin/dry-run/build` | Default safe blocks for execution; dry-run is mock queued; live arm/kill clear blocked by config/policy. | Disabled or admin-only with human-approved gates. | Prove no public execution path exists, especially when environment flags change. | Execution/signing review required. |

## Highest-Risk Routes Needing Coverage

| Route | Current behavior to document | Intended behavior to enforce later | Test would prove |
|---|---|---|---|
| `GET /api/session/wallet/{address}` | Local-review wallet role mock can return role metadata. | Local-only or real signed wallet challenge. | Mock wallet role cannot be mistaken for production wallet proof. |
| `GET /api/payment-verifications` | Public detailed payment history surface. | Admin-only or user-owned redacted records. | Public users cannot read payment history. |
| `GET /api/refund-cases` | Public refund queue surface. | Admin-only. | Public users cannot inspect refund workflow. |
| `POST /api/refund-cases` | Public refund case creation surface. | Admin-only/manual workflow. | Public users cannot create arbitrary refund cases. |
| `POST /api/refund-cases/{case_id}/status` | Public refund mutation surface. | Admin-only. | Public users cannot mutate refund status. |
| `GET /api/live-trades` | Public live/dry-run receipt surface. | Admin-only or public-redacted receipts. | Public users cannot inspect execution-adjacent details. |
| `GET /api/reconciliations` | Public balance/reconciliation surface. | Admin-only. | Public users cannot inspect balance deltas. |
| `GET /api/live-readiness` | Public full readiness surface. | Admin-only full report; public redacted status only. | Public users cannot see execution-readiness internals. |
| `POST /api/scan` | Public scanner trigger. | Admin or local-only. | Public users cannot trigger backend scanner work. |
| `POST /api/admin/dry-run/build` | Admin mock queued dry-run command. | Admin-only and unsigned-only. | Dry-run route cannot sign or submit. |
| `POST /api/admin/live/arm` | Admin route blocked by config/kill switch. | Disabled until human gates pass. | Live execution remains locked by default. |
| `POST /api/admin/kill-switch/clear` | Admin route explicitly rejected. | Disabled unless separately approved. | Safety lock cannot be cleared casually. |
| `POST /api/user/pnet/fee-confirm` | Mock txids can confirm in local review. | Mock txids rejected outside local review. | Mock payments cannot grant production credits. |
| `POST /api/execute-best` | Public route blocked unless execution env flag is enabled. | Disabled or admin-only with all gates. | Environment flag alone cannot create public execution. |

## Expected Allowed And Blocked Behavior

Current-behavior tests should document what the app does today without pretending it is production-ready:

- Public static/health/config routes return successful responses and no secrets.
- Public market reports return aggregate or delayed data shapes.
- Admin routes reject missing headers and non-allowlisted user headers.
- Execution-adjacent defaults stay blocked.
- Local-review mock routes identify themselves as mock or synthetic.

Intended-behavior tests should be added when the matching implementation is approved:

- Detailed payment/refund/live/reconciliation records reject guests and non-admins.
- Public readiness is redacted and cannot trigger scans.
- Mock PNET confirmations are rejected outside local review.
- `/api/execute-best` rejects non-admin requests even if execution env flags are enabled.
- Static file serving cannot expose secret-like files.

Tests that assert intended behavior before implementation may fail. If written early, mark them as skipped with a clear reason or keep them in this plan until the implementation task is approved.

## Mock And Local-Only Behavior Tests

| Test | Route | Expected result | Proves |
|---|---|---|---|
| `test_wallet_session_declares_local_review_mock` | `GET /api/session/wallet/{address}` | Response includes `authMode: local-review-mock` or equivalent explicit marker. | Wallet session is not silently presented as real wallet proof. |
| `test_wallet_session_does_not_grant_admin_to_unallowlisted_wallet` | `GET /api/session/wallet/{address}` | Unknown wallet is not admin. | Frontend role state cannot create admin access. |
| `test_wallet_session_rejected_in_production_mode` | same | Skipped until production-mode behavior exists, then rejects or hides route. | Local-only route cannot ship as production auth. |
| `test_demo_run_is_synthetic_and_non_production` | `GET /api/demo-run` | Response labels itself synthetic/demo/mock. | Demo cannot be mistaken for real performance. |
| `test_demo_run_has_no_signing_or_execution_fields` | `GET /api/demo-run` | No wallet key, signer, tx group, or submit field. | Demo cannot become execution guidance. |

Human review required for wallet/session changes and public demo wording.

## Payment And Refund Visibility Tests

| Test | Route | Current or intended | Expected result | Proves |
|---|---|---|---|---|
| `test_payment_verification_endpoint_does_not_sign_or_submit` | `POST /api/verify-payment` | Current. | Response records verification only; no signing/submission fields. | Payment verification is not execution. |
| `test_payment_verification_history_requires_admin_or_user_scope` | `GET /api/payment-verifications` | Intended. | Guest is rejected or receives redacted/user-owned data. | Public users cannot read global payment history. |
| `test_refund_case_list_requires_admin` | `GET /api/refund-cases` | Intended. | Guest/user rejected. | Refund queue is not public. |
| `test_refund_case_create_requires_admin` | `POST /api/refund-cases` | Intended. | Guest/user rejected. | Public users cannot create refund cases. |
| `test_refund_case_status_update_requires_admin` | `POST /api/refund-cases/{case_id}/status` | Intended. | Guest/user rejected. | Public users cannot mutate refunds. |
| `test_refund_responses_never_trigger_auto_send` | refund routes | Current/intended. | Guardrails say manual refund only; no tx submission fields. | Refund flow does not move funds automatically. |
| `test_pnet_fee_quote_is_market_data_only` | `POST /api/user/pnet/fee-quote` | Current. | Quote is for scans/reports/simulations/credits; no execution permission. | PNET payment is access control, not trading. |
| `test_pnet_fee_confirm_rejects_mock_txid_outside_local_review` | `POST /api/user/pnet/fee-confirm` | Intended. | Mock txid rejected outside local review. | Mock confirmation cannot grant production credits. |

Human review required for wallet, payment receiver, refund policy, PNET credit policy, and user receipt scope.

## Execution-Adjacent Route Tests

| Test | Route | Current or intended | Expected result | Proves |
|---|---|---|---|---|
| `test_execute_best_default_is_blocked` | `POST /api/execute-best` | Current. | Default settings reject execution. | Safe default blocks public execution. |
| `test_execute_best_env_flag_alone_cannot_execute_publicly` | `POST /api/execute-best` | Intended. | Even with execution flag enabled, guest/non-admin cannot execute. | Env flag alone cannot create a public trading API. |
| `test_execute_best_response_contains_no_signed_transactions` | `POST /api/execute-best` | Current/intended. | No signed tx, mnemonic, private key, or submission receipt. | Endpoint does not leak signing artifacts. |
| `test_admin_dry_run_build_is_unsigned_only` | `POST /api/admin/dry-run/build` | Current/intended. | Admin response is queued/mock/unsigned; no submission. | Dry-run cannot become live execution. |
| `test_admin_live_arm_blocked_when_execution_disabled` | `POST /api/admin/live/arm` | Current. | Rejected while execution is disabled. | Live execution is disarmed by default. |
| `test_admin_live_arm_blocked_when_kill_switch_active` | `POST /api/admin/live/arm` | Current. | Rejected while kill switch is active. | Kill switch overrides live arm. |
| `test_admin_kill_switch_clear_is_rejected` | `POST /api/admin/kill-switch/clear` | Current. | Rejected. | Safety lock cannot be cleared through normal control-plane flow. |
| `test_execution_adjacent_routes_require_admin_headers` | admin execution routes | Current. | Guest/user rejected. | Execution controls are not public. |

Human review required for all execution, dry-run, signer, kill-switch, risk-policy, and public-claims changes.

## Public Data Freshness And Delay Tests

| Test | Route | Expected result | Proves |
|---|---|---|---|
| `test_public_opportunities_exclude_fresh_routes` | `GET /api/opportunities` | Fresh opportunities inside delay window are absent or redacted. | Public users cannot see actionable routes. |
| `test_public_pulse_best_opportunity_is_delayed` | `GET /api/pulse` | Best opportunity respects `public_delay_seconds`. | Aggregate pulse cannot leak fresh execution data. |
| `test_public_reports_are_aggregate_or_delayed` | report endpoints | Reports do not include fresh route instructions, wallet data, or private tx details. | Reports remain market intelligence/research. |
| `test_public_risk_policy_exposes_no_secret_allowlists` | `GET /api/risk-policy` | No private signer, wallet, or secret config appears. | Public policy summary is safe. |
| `test_public_live_readiness_is_redacted_or_admin_only` | `GET /api/live-readiness` | Public response is redacted or rejected once intended behavior is implemented. | Execution readiness internals are not public. |
| `test_static_mount_does_not_serve_secret_like_files` | `/static/*` | `.env`, key, mnemonic, seed, and secret-like filenames are not served. | Static exposure is limited to public assets. |

Human review required for the final public data delay, redaction, and claims policy.

## Admin And Session Spoofing Tests

| Test | Routes | Expected result | Proves |
|---|---|---|---|
| `test_all_admin_get_routes_reject_guest` | `/api/admin/*`, `/api/ops/*` GET | Guest rejected. | Admin observability is backend-gated. |
| `test_all_admin_post_routes_reject_guest` | `/api/admin/*` POST | Guest rejected. | Admin commands are backend-gated. |
| `test_frontend_role_header_without_allowlisted_wallet_is_rejected` | admin routes | `X-Algopulse-Role: admin` alone is not enough. | Frontend role cannot spoof backend role. |
| `test_user_role_cannot_call_admin_routes` | admin routes | User rejected. | Connected user is not admin. |
| `test_admin_mock_auth_labels_local_review` | admin/session responses | Auth mode or test fixture clearly identifies local-review mock. | Mock auth cannot be mistaken for production. |
| `test_ops_routes_return_source_labels` | `/api/ops/*` | Every metric has source `mock`, `stored`, `live`, `delayed`, or `unavailable`. | Admin UI can distinguish real vs mock evidence. |

Human review required before replacing local-review mock auth with real production auth.

## Existing Coverage To Preserve

Do not remove or weaken existing coverage in these areas:

- `tests/test_control_plane_api.py`: admin mock gates, control-room endpoints, PNET fee quote/confirm stubs, product validation, paper report endpoint.
- `tests/test_phase0_security.py`: non-admin admin rejection, frontend role spoof rejection, kill-switch blocks live arm.
- `tests/test_payment_verification.py`: Algorand payment verification logic.
- `tests/test_refunds.py`: refund decision guardrails.
- `tests/test_readiness.py` and `tests/test_production_readiness.py`: readiness and kill-switch safety.
- `tests/test_executor_validation.py`: executor validation and signer-handoff guardrails.

Any new API exposure test should be additive and small.

## Recommended First Small Test Implementation Task

Start with a current-behavior safety test that should pass without changing application logic:

```text
Create tests/test_api_exposure_current_safety.py only. Add tests that confirm:
1. /api/config/public exposes no secret-like keys or values.
2. /api/session/wallet/{address} labels wallet auth as local-review-mock.
3. /api/demo-run is labeled synthetic/mock and contains no signing/submission fields.
4. /api/execute-best is blocked by default and returns no signed transaction data.
Do not change application logic, auth, signer code, live execution, transaction submission, hot-wallet logic, risk limits, or secrets.
```

Why this first:

- It is small and reviewable.
- It documents current safe defaults and local-review boundaries.
- It avoids risky production auth/payment/execution changes.
- It creates a base for later intended-behavior tests after human review.
