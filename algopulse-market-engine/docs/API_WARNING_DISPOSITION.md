# API Warning Disposition

Use this document to convert API exposure warnings into an actionable work queue. A warning is not complete until it is placed into one of these buckets:

- **Blocked item**: Do not implement in Phase 0 without a later explicit approval.
- **Human-review item**: Human approval, policy, or architecture decision is required before implementation.
- **Test-planning item**: Define or add tests before changing behavior.
- **Safe implementation item**: Small, non-risky work Codex can implement with tests.
- **Completed item**: Existing docs or tests already cover the current safe behavior.

This document does not approve auth, wallet proof, signer changes, live trading, transaction submission, hot-wallet logic, risk-limit changes, or secrets.

## Disposition Board

| Warning or concern | Disposition | Evidence | Why this bucket | Next action |
|---|---|---|---|---|
| Any route can sign, submit, or trigger live transactions without an approved execution gate. | Blocked item | `docs/API_EXPOSURE_REVIEW_CHECKLIST.md`; `POST /api/execute-best`; `POST /api/admin/live/arm` | Live trading and signing are outside Phase 0 control-plane work. | Keep blocked. No implementation until execution gates and human sign-off exist. |
| `POST /api/execute-best` can become public execution through an environment flag alone. | Blocked item | `docs/API_EXPOSURE_INVENTORY.md`; `src/algopulse/api.py::execute_best` | Public execution is not allowed, even if an env flag changes. | Do not enable. Next safe step is a current-safety test proving default rejection. |
| Mock PNET confirmations can grant real production credits. | Blocked item | `src/algopulse/api.py::pnet_fee_confirm`; inventory notes `mock_` and `mock-` txids | Mock payment confirmation must stay local-review only. | Keep production credits blocked until real on-chain verification policy is reviewed. |
| `POST /api/admin/live/arm` could arm execution. | Blocked item | `src/algopulse/api.py::admin_live_arm`; existing kill-switch/readiness tests | Live arm is an execution boundary. | Keep disabled. Only revisit after scanner, paper, risk, dry-run, signer isolation, and manual micro-trade gates pass. |
| `POST /api/admin/kill-switch/clear` could clear a safety boundary. | Blocked item | `src/algopulse/api.py::admin_kill_switch_clear` | Clearing the kill switch is production-risk policy, not routine control-plane work. | Keep rejected unless a separate human-approved policy is written. |
| Signer, mnemonic, private key, hot-wallet, or transaction submission changes. | Blocked item | `docs/AI_DEVELOPMENT_PROTOCOL.md`; `docs/HUMAN_REVIEW_GATES.md` | These are explicitly out of scope for safe AI changes. | Do not modify. Require separate human-reviewed signer/execution task. |
| Public detailed payment history is exposed through `/api/payment-verifications`. | Human-review item | `docs/API_EXPOSURE_INVENTORY.md`; `src/algopulse/api.py::payment_verifications` | Access policy must decide admin-only vs user-owned redacted receipts. | Human selects intended access and redaction policy before code changes. |
| Public refund queue or refund mutation routes exist. | Human-review item | `/api/refund-cases`; `/api/refund-cases/{case_id}/status` | Refund workflows touch payment disputes and operational records. | Human approves refund visibility and mutation rules before implementation. |
| Public live trade or reconciliation records are exposed. | Human-review item | `/api/live-trades`; `/api/reconciliations` | These may reveal execution timing, wallet, balance, or strategy details. | Human approves public receipt/redaction policy or admin-only scope. |
| Public `/api/live-readiness` exposes execution-readiness details. | Human-review item | `src/algopulse/api.py::live_readiness` | Public readiness copy and detail level are product/security policy. | Human decides split between public status and admin full report. |
| Public `/api/scan` can trigger scanner work. | Human-review item | `src/algopulse/api.py::scan_now` | Scanner triggering affects backend workload and potentially fresh data generation. | Human decides whether this is admin-only, local-only, or rate-limited public. |
| `local-review-mock` wallet/admin proof exists. | Human-review item | `src/algopulse/api.py::_wallet_session`; `docs/API_EXPOSURE_INVENTORY.md` | Replacing mock auth requires real auth architecture. | Human approves wallet proof/auth design before implementation. |
| Public claims could imply guaranteed returns, passive income, copy trading, managed strategy, or user deposits. | Human-review item | `docs/API_EXPOSURE_REVIEW_CHECKLIST.md`; public pages/reports | Claims are legal/product-risk sensitive. | Human reviews public copy before production deployment. |
| Public route freshness/delay policy for opportunities, pulse, reports, heatmaps, and forensics. | Human-review item | `/api/opportunities`; `/api/pulse`; `/api/reports/*`; `/api/ops/*` | Product needs a policy for what is public, delayed, aggregate, or admin-only. | Human approves delay/redaction policy; Codex can then add tests. |
| Payment receiver, PNET fee actions, and credit unlock policy. | Human-review item | `/api/user/pnet/fee-quote`; `/api/user/pnet/fee-confirm`; `/api/verify-payment` | Payment behavior needs business and security approval. | Human approves receiver, fee actions, credit rules, and no-custody language. |
| Static mount could accidentally serve secret-like files. | Test-planning item | `src/algopulse/api.py::app.mount("/static", StaticFiles(...))` | Current behavior should be verified before changing static serving. | Add a negative test or deploy check for `.env`, mnemonic, seed, key, and secret-like files. |
| Public config or health could leak secret-like values. | Test-planning item | `/api/config/public`; `/health`; `/api/health` | The current response should be pinned with regression tests. | Add tests for no secret-like keys or values in public config/health. |
| Public opportunities could expose fresh executable routes. | Test-planning item | `/api/opportunities`; `public_delay_seconds` inventory evidence | Delay behavior should be proven before production review. | Add fresh-route exclusion test. |
| Public pulse could expose fresh best opportunity. | Test-planning item | `/api/pulse`; `store.get_pulse` inventory evidence | Aggregate data still needs freshness protection. | Add pulse best-opportunity delay test. |
| Product analytics event endpoint could accept excessive or sensitive metadata. | Test-planning item | `/api/events/user-action`; existing product validation tests | Payload behavior should be pinned before public exposure grows. | Add invalid action, oversized metadata, and sensitive-field rejection tests. |
| Detailed paper trades may reveal route strategy. | Test-planning item | `/api/paper-trades` | This route may remain useful internally but should not leak fresh strategy publicly. | Add public-vs-admin exposure or redaction test after policy review. |
| Admin observability depends on local-review headers. | Test-planning item | `/api/admin/*`; `/api/ops/*`; existing admin tests | Current rejection behavior should be preserved while auth remains mock. | Add route-parametrized guest/user rejection coverage for every admin route. |
| Admin command endpoints need auditability. | Test-planning item | `/api/admin/scan-now`, scanner, route, paper, dry-run, live, kill-switch commands | Audit records are required before production command use. | Plan command audit tests; implementation requires review if it changes persistence. |
| Dry-run builder must stay unsigned-only. | Test-planning item | `/api/admin/dry-run/build` | Dry-run is safe only while it cannot sign or submit. | Add unsigned-only response test before expanding dry-run behavior. |
| `/api/demo-run` could be mistaken for performance proof. | Test-planning item | `/api/demo-run`; existing demo test reference | Synthetic demos should be visibly labeled. | Add response-label and no-signing-fields tests. |
| Current API inventory exists and lists exposed surfaces. | Completed item | `docs/API_EXPOSURE_INVENTORY.md` | The route surface has been documented for review. | Keep updated when routes change. |
| API exposure review checklist exists. | Completed item | `docs/API_EXPOSURE_REVIEW_CHECKLIST.md` | Review criteria and stop conditions are documented. | Use it before risky endpoint work. |
| API exposure test plan exists. | Completed item | `docs/API_EXPOSURE_TEST_PLAN.md` | Warnings are translated into test coverage areas. | Use it to drive the first small test diff. |
| Safe AI development protocol and human review gates exist. | Completed item | `docs/AI_DEVELOPMENT_PROTOCOL.md`; `docs/HUMAN_REVIEW_GATES.md`; `docs/SAFETY_CHECKLIST.md` | Project-level guardrails exist for future Codex work. | Keep them updated as gates change. |
| Admin mock routes already reject obvious guest/user access in existing tests. | Completed item | `tests/test_control_plane_api.py`; `tests/test_phase0_security.py` | Some backend role checks are already covered. | Preserve coverage; expand parametrized coverage later. |
| Live arm default and kill-switch behavior have existing tests. | Completed item | `tests/test_phase0_security.py`; `tests/test_production_readiness.py` | Current safe default behavior is partially covered. | Preserve coverage; add `/api/execute-best` default-block test next. |
| Add current-safety tests for config, mock wallet session, demo run, and `/api/execute-best`. | Safe implementation item | `docs/API_EXPOSURE_TEST_PLAN.md` recommended first task | This is additive test coverage only and should not alter behavior. | Create `tests/test_api_exposure_current_safety.py` only. |
| Add docs-only review checklist updates when endpoint inventory changes. | Safe implementation item | Existing docs pattern | Docs updates are safe if they do not imply production approval. | Update inventory, checklist, test plan, and this disposition doc whenever routes change. |

## Next Safe Task

Recommended Codex prompt:

```text
Create tests/test_api_exposure_current_safety.py only. Add tests that confirm public config exposes no secret-like keys or values, wallet session labels local-review-mock, demo-run is synthetic/mock with no signing or submission fields, and /api/execute-best is blocked by default with no signed transaction data. Do not change application logic.
```
