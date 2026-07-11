# API Exposure Inventory

This document makes the FastAPI route surface reviewable before production deployment, wallet/payment work, or execution work. It is documentation only and does not change application behavior.

## Summary Counts

Total FastAPI endpoint/exposure surfaces inspected: **80** (`79` decorated endpoints plus `1` static asset mount)

By intended access level:

| Intended access | Count |
|---|---:|
| public | 23 |
| public/connected user | 1 |
| connected user | 8 |
| admin | 43 |
| local-only | 2 |
| disabled | 3 |

By mutation/exposure risk:

| Risk | Count |
|---|---:|
| none | 3 |
| low | 32 |
| medium | 33 |
| high | 9 |
| critical | 3 |

High or critical routes to review first:

- `GET /api/session/wallet/{address}`
- `GET /api/live-trades`
- `GET /api/reconciliations`
- `GET /api/payment-verifications`
- `GET /api/refund-cases`
- `POST /api/refund-cases`
- `POST /api/refund-cases/{case_id}/status`
- `POST /api/admin/dry-run/build`
- `POST /api/admin/live/arm`
- `POST /api/admin/kill-switch/clear`
- `POST /api/user/pnet/fee-confirm`
- `POST /api/execute-best`

## Scope And Evidence

Facts:

- Route declarations are in `src/algopulse/api.py`.
- Static assets are exposed through `src/algopulse/api.py::app.mount("/static", StaticFiles(...))`.
- Admin-gated routes use `src/algopulse/api.py::_require_admin_session`.
- Current admin session proof is local review only; `src/algopulse/api.py::_wallet_session` returns `authMode: local-review-mock`.
- Public opportunity routes use `public_delay_seconds` through `src/algopulse/store.py::get_pulse` and `src/algopulse/store.py::list_opportunities`.
- Mock PNET confirmations are accepted by `src/algopulse/api.py::pnet_fee_confirm` for txids beginning `mock_` or `mock-`.
- Current tests include admin role checks, payment verification, refund logic, production readiness, and phase security coverage.

Assumptions:

- Intended access levels below are recommendations for production hardening, not current implementation.
- `public` means safe without wallet proof after redaction/delay review.
- `connected user` means wallet/session proof is required before production use.
- `admin` means backend-enforced admin proof is required.
- `local-only` means useful for development/demo but not production exposure.
- `disabled` means the endpoint should remain blocked or removed before production.

Unknowns:

- Deployment-layer routing, reverse proxy rules, and external auth are not known from this repo alone.
- Real Pera wallet proof is not implemented in the inspected code.
- Final public receipt/redaction policy still needs human approval.

## Static, Health, And Config

| Method | Route | Evidence | Current access behavior | Intended access | Data type | Risk | Wallet/signing/execution relevance | Redaction or delay | Production recommendation | Tests that should cover it | Human review |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GET | `/` | `src/algopulse/api.py::index` | Public static page. | public | operational/static | none | None. | None. | Safe to expose if public copy stays conservative. | Page smoke test. | No |
| GET | `/static/*` | `src/algopulse/api.py::app.mount("/static", StaticFiles(...))` | Public static asset mount. | public | operational/static | low | None directly. | Must not serve `.env`, source secrets, or private build artifacts. | Safe only if static directory contains frontend assets and no secrets. | Static asset smoke test; add negative test or deploy check that `.env` and secret files are not served. | No |
| GET | `/health` | `src/algopulse/api.py::health` | Public coarse health. | public | operational | none | Exposes execution enabled flag only. | No secrets. | Keep coarse. | Health smoke test. | No |
| GET | `/api/health` | `src/algopulse/api.py::api_health` | Public API health envelope. | public | operational | none | Exposes signer/execution flags. | No secrets; keep coarse. | Safe if no private configuration is added. | Health smoke test. | No |
| GET | `/api/config/public` | `src/algopulse/api.py::public_config` | Public review-safe config. | public | operational | low | Shows live/signing enabled flags, not keys. | No secrets; label mock auth mode. | Keep public config minimal and non-secret. | `test_public_config_exposes_review_safe_values_only`. | Yes for public claims/config wording |
| GET | `/api/testnet/readiness` | `src/algopulse/api.py::testnet_readiness` | Public redacted runtime-config readiness evidence. | public | operational/TestNet readiness | low | Explicitly reports signing, submission, and live trading as disabled without returning secrets or endpoint URLs. | No raw URLs, tokens, asset metadata, or wallet proof. | Keep as a coarse pre-TestNet gate; it is not production proof. | `tests/test_testnet_readiness.py`. | Yes before wallet integration or TestNet promotion |
| GET | `/api/session/wallet/{address}` | `src/algopulse/api.py::wallet_session` | Public local-review wallet role mock. | local-only | mock/wallet | high | Wallet/admin boundary; no signature proof. | Must show `local-review-mock`. | Replace with signed wallet challenge before production. | `test_wallet_session_marks_allowlisted_admin_wallet`; add production-mode rejection test. | Yes |

## Public Market Intelligence

| Method | Route | Evidence | Current access behavior | Intended access | Data type | Risk | Wallet/signing/execution relevance | Redaction or delay | Production recommendation | Tests that should cover it | Human review |
|---|---|---|---|---|---|---|---|---|---|---|---|
| POST | `/api/events/user-action` | `src/algopulse/api.py::record_product_user_action` | Public write into product-validation store with taxonomy check. | public | operational/product analytics | medium | No wallet signing, but stores role/wallet-connected metadata. | Metadata must stay safe and bounded. | Add payload size/rate limits before public deployment. | `test_product_validation_event_endpoint_records_only_taxonomy_actions`. | Yes for analytics/privacy policy |
| GET | `/api/pulse` | `src/algopulse/api.py::pulse` | Public stored pulse, uses delayed best opportunity. | public | delayed/route aggregate | low | No signing. | Uses public delay for best opportunity. | Safe as delayed aggregate. | Add test proving fresh route is not surfaced. | Yes for public data policy |
| GET | `/api/pools` | `src/algopulse/api.py::pools` | Public latest pool snapshot list. | public | live/stored market data | low | No signing. | No executable route data. | Safe if pool data is intended public. | Pool list integration test. | No |
| GET | `/api/opportunities` | `src/algopulse/api.py::opportunities` | Public stored opportunities with `public_delay_seconds`. | public | delayed/route | medium | Route intelligence but no execution. | Delay and redact actionable freshness. | Never expose fresh executable routes publicly. | Add fresh-route exclusion test. | Yes |
| GET | `/api/risk-policy` | `src/algopulse/api.py::risk_policy` | Public risk-policy summary. | public | operational/risk | low | Execution policy visibility only. | No secret allowlists. | Safe if values are intentionally public. | Risk policy smoke test. | Yes for risk-policy public copy |
| GET | `/api/demo-run` | `src/algopulse/api.py::demo_run` | Public synthetic 5-to-10 demo. | local-only | mock/synthetic | low | No signing; could confuse users. | Must be labeled synthetic. | Keep local/demo only or label strongly if public. | `test_five_to_ten_demo_is_synthetic_and_doubles_algo`. | Yes for public claims |
| GET | `/api/reports/paper/daily` | `src/algopulse/api.py::paper_daily_report` | Public aggregate paper report. | public | delayed/operational aggregate | low | No signing. | Aggregate only. | Safe if no fresh route data. | `test_paper_daily_report_endpoint_returns_aggregate_shape`. | Yes for public report policy |
| GET | `/api/reports/market/daily` | `src/algopulse/api.py::market_daily_report` | Public daily market report preview. | public | delayed/operational aggregate | low | No signing. | Aggregate/delayed preview; detailed sections omitted and labeled. | Safe if framed as research preview. | Market report tests. | Yes for public report policy |
| GET | `/api/reports/market/archive` | `src/algopulse/api.py::market_report_archive` | Public report archive. | public | delayed/operational aggregate | low | No signing. | Aggregate/delayed. | Safe if archive has no fresh route execution data. | Archive tests. | Yes for public report policy |
| GET | `/api/reports/market/daily/export` | `src/algopulse/api.py::market_daily_report_export` | Public JSON/Markdown export. | public | delayed/operational aggregate | low | No signing. | Export must match redaction policy. | Safe after report redaction review. | Export format tests. | Yes for public report policy |
| GET | `/api/market/pnet/recent-swaps` | `src/algopulse/api.py::pnet_recent_swaps` | Public read-only Vestige swap activity for the configured PNET ASA. | public | live/read-only market data | low | No signing, no route approval, no execution permission. | Normalize and omit raw payloads, wallet addresses, group IDs, signer state, hot-wallet fields, submission payloads, and executable route instructions. | Safe as source-labeled market observation if the payload stays non-executable. | `tests/test_recent_swaps.py`. | Yes for public market-data wording |
| GET | `/api/x402/reports/market-pulse/daily` | `src/algopulse/api.py::x402_market_pulse_daily_report` | Public mock/TestNet readiness access boundary; unpaid returns HTTP 402 and local-review mock proof or TestNet x402 middleware path unlocks a distinct premium delayed-intelligence payload. | public | delayed/operational aggregate | low | No signing, no custody, no transaction submission. | Uses market daily report redaction plus x402-only premium markers; still no raw routes or executable artifacts. | Safe only as mock/TestNet readiness; real facilitator/Mainnet integration requires separate review. | `test_x402_market_pulse_*`. | Yes for x402 payment wording and challenge scope |
| GET | `/api/transparency/system` | `src/algopulse/api.py::transparency_system` | Public transparency dashboard payload. | public | proof/audit aggregate | low | No signing, no custody, no transaction submission. | Hash/suffix references only; no full txids, wallets, headers, payloads, or secrets. | Safe as a public proof index after redaction review. | `tests/test_transparency_system.py`. | Yes for public claims |
| GET | `/api/transparency/proofs` | `src/algopulse/api.py::transparency_proofs` | Public automated proof status rows. | public | proof aggregate | low | No signing, no custody, no transaction submission. | Status rows and counts only. | Safe if proof statuses do not overclaim Mainnet, audit, or eligibility. | `tests/test_transparency_system.py`. | Yes for public claims |
| GET | `/api/transparency/public-ledger` | `src/algopulse/api.py::transparency_public_ledger` | Public redacted payment/review ledger. | public | proof/review aggregate | low | Payment-verification references only; no payload handling. | Full txids and wallets are omitted; hashed/suffixed references only. | Safe after redaction tests; never replace admin payment/refund records. | `tests/test_transparency_system.py`. | Yes for privacy/redaction |
| GET | `/api/transparency/github-snapshot` | `src/algopulse/api.py::transparency_github_snapshot` | Public GitHub dossier snapshot summary. | public | proof/audit aggregate | low | No signing, no custody, no transaction submission. | Snapshot metadata only. | Use for local snapshot generation after human review. | `tests/test_transparency_system.py`. | Yes before publication |
| GET | `/api/transparency/audit-readiness` | `src/algopulse/api.py::transparency_audit_readiness` | Public audit checklist and threat-model summary. | public | audit aggregate | low | No signing, no custody, no transaction submission. | No secret or payment material. | Internal-facing until human public wording review. | `tests/test_transparency_system.py`. | Yes before publication |

### Market Report Preview vs. Paid x402 Payload

- Public preview fields: `reportTier=public-preview`, `marketSummary`, `summary`, `topPairs`, `opportunityCounts`, `scannerHealth`, safety flags, and `excludedDetailSections`.
- Paid x402 delayed-intelligence fields: `accessTier=premium-delayed-intelligence`, `premiumSections`, `topSpreads`, `liquidityChanges`, `routePerformance`, `paperTradePerformance`, `riskEvents`, `exportMetadata`, and redaction policy metadata.
- Always omitted/redacted: raw routes, route legs, signer or wallet custody data, secrets, payment payload material, executable transaction artifacts, and fresh executable route instructions.

## Receipts, Payments, Refunds, And Records

| Method | Route | Evidence | Current access behavior | Intended access | Data type | Risk | Wallet/signing/execution relevance | Redaction or delay | Production recommendation | Tests that should cover it | Human review |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GET | `/api/paper-trades` | `src/algopulse/api.py::paper_trades` | Public detailed paper-trade records. | admin | route/operational | medium | No signing; may reveal strategy detail. | Redact or aggregate before public use. | Gate detailed records; expose aggregate public report separately. | Add public-vs-admin exposure test. | Yes |
| GET | `/api/live-trades` | `src/algopulse/api.py::live_trades` | Public live/dry-run receipts. | admin | execution/operational | high | Execution-adjacent receipts. | Redact tx details, wallet details, and fresh timing. | Gate before production; consider public redacted receipts separately. | Add non-admin rejection or redaction test. | Yes |
| GET | `/api/reconciliations` | `src/algopulse/api.py::reconciliations` | Public balance reconciliations. | admin | execution/operational | high | Balance/execution-adjacent. | Redact wallet and balance deltas. | Gate before production. | Add non-admin rejection test. | Yes |
| GET | `/api/payment-verifications` | `src/algopulse/api.py::payment_verifications` | Public payment verification history. | admin | payment | high | Wallet/payment metadata. | User-owned or admin-only; redact sender/receiver if public. | Do not expose full payment history publicly. | `test_store_records_payment_verification_receipts`; add auth/redaction test. | Yes |
| GET | `/api/refund-cases` | `src/algopulse/api.py::refund_cases` | Public refund queue. | admin | refund | high | Payment/refund workflow. | No public refund queue. | Make admin-only before deployment. | `tests/test_refunds.py`; add non-admin rejection test. | Yes |
| POST | `/api/verify-payment` | `src/algopulse/api.py::verify_payment` | Public tx verification and receipt write. | connected user | payment | medium | Wallet payment verification; no signing by backend. | Validate txid; rate-limit; avoid leaking stored history. | Require user/session context and abuse controls before production. | `tests/test_payment_verification.py`. | Yes |
| POST | `/api/refund-cases` | `src/algopulse/api.py::create_refund_case` | Public refund case creation. | admin | refund | high | Payment/refund workflow. | No public arbitrary case creation. | Gate before production; keep refund manual. | `tests/test_refunds.py`; add non-admin rejection test. | Yes |
| POST | `/api/refund-cases/{case_id}/status` | `src/algopulse/api.py::update_refund_case` | Public refund status mutation. | admin | refund | high | Payment/refund workflow. | No public mutation. | Make admin-only before deployment. | Add non-admin rejection and admin happy-path tests. | Yes |

## PNET User Flow

| Method | Route | Evidence | Current access behavior | Intended access | Data type | Risk | Wallet/signing/execution relevance | Redaction or delay | Production recommendation | Tests that should cover it | Human review |
|---|---|---|---|---|---|---|---|---|---|---|---|
| POST | `/api/user/pnet/access-check` | `src/algopulse/api.py::pnet_access_check` | Public local-review PNET access check. | connected user | mock/payment | medium | Wallet opt-in/balance assumptions are mocked. | Label mock; no secrets. | Replace mock checks with on-chain wallet proof before production. | `test_admin_preflight_and_user_pnet_access_endpoints`. | Yes |
| POST | `/api/user/pnet/fee-quote` | `src/algopulse/api.py::pnet_fee_quote` | Public market-data fee quote. | connected user | payment | medium | User wallet signs payment in future; backend does not sign. | No custody; no execution permission. | Safe after wallet proof, receiver review, and action allowlist. | `test_pnet_fee_quote_is_market_data_only_shape`. | Yes |
| POST | `/api/user/pnet/fee-confirm` | `src/algopulse/api.py::pnet_fee_confirm` | Public mock or on-chain fee confirmation; grants credit. | connected user | payment/mock | high | Wallet payment verification; no backend signing. | Mock confirmations local-only. | Reject mock txids outside local; require on-chain verification. | `test_pnet_fee_confirm_is_stubbed_and_does_not_touch_execution`; `test_pnet_fee_confirm_uses_on_chain_verifier_for_real_txid`; add non-local mock rejection test. | Yes |
| GET | `/api/contribution-protocol/catalog` | `src/algopulse/api.py::contribution_protocol_catalog` | Public local-review contribution and credit-unlock catalog. | public | contribution/credits | low | No signing; no payment payload. | Label local-review. | Keep claims bounded; no token rewards or binding governance. | `tests/test_contribution_protocol.py`. | Yes |
| GET | `/api/contribution-protocol/session/{wallet}` | `src/algopulse/api.py::contribution_protocol_session` | Local-review contribution-credit dashboard envelope. | connected user | contribution/credits | medium | Mock wallet identity; no backend signing. | User-owned activity only. | Require real wallet proof and durable ledger before production. | `tests/test_contribution_protocol.py`. | Yes |
| POST | `/api/contribution-protocol/submit` | `src/algopulse/api.py::contribution_protocol_submit` | Records contribution for manual review. | connected user | contribution/credits | medium | No auto payout; no token reward. | User-owned submission receipt. | Add abuse controls and durable reviewer workflow before production. | `tests/test_contribution_protocol.py`. | Yes |
| POST | `/api/contribution-protocol/spend` | `src/algopulse/api.py::contribution_protocol_spend` | Spends local-review credits for bounded access. | connected user | contribution/credits | medium | No contract deployment, signer, trading, treasury, or binding governance. | User-owned spend receipt. | Require durable credit ledger and on-chain contract review before production. | `tests/test_contribution_protocol.py`. | Yes |
| GET | `/api/community-growth/overview/{wallet}` | `src/algopulse/api.py::community_growth_overview` | Local-review onboarding, referral, leaderboard, and reputation model. | public/connected user | community/reputation | medium | No signing; no earnings ranking. | Label local-review and sample rows. | Add durable identity, anti-sybil, abuse controls, and privacy review before production. | `tests/test_contribution_protocol.py`. | Yes |
| POST | `/api/community-growth/referral` | `src/algopulse/api.py::community_growth_referral` | Records referral receipt for manual review. | connected user | referral/reputation | medium | No auto payout, token reward, or binding governance. | User-owned referral receipt. | Add self-referral, duplicate, and spam controls before production. | `tests/test_contribution_protocol.py`. | Yes |

## Readiness And Scanner Controls

| Method | Route | Evidence | Current access behavior | Intended access | Data type | Risk | Wallet/signing/execution relevance | Redaction or delay | Production recommendation | Tests that should cover it | Human review |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GET | `/api/live-readiness` | `src/algopulse/api.py::live_readiness` | Public full readiness report; optional scan/build flags. | admin | operational/execution | medium | Execution readiness details; no signing. | Public version should be redacted. | Split admin full report from public redacted status; admin-gate `run_scan=true`. | `tests/test_readiness.py`; add public redaction test. | Yes |
| POST | `/api/scan` | `src/algopulse/api.py::scan_now` | Public scanner run. | admin | live/route scanner | medium | No signing, but can trigger backend work. | No fresh route leakage. | Admin-gate or local-only before production. | Add non-admin rejection or local-only test. | Yes |
| POST | `/api/execute-best` | `src/algopulse/api.py::execute_best` | Public route that is blocked unless `ALGO_PULSE_ALLOW_API_EXECUTION=true`. | disabled | execution | critical | Direct execution-adjacent route. | No public execution. | Remove or admin-gate with kill-switch/risk checks before any deployment. | Add non-admin rejection even when env flag is true. | Yes |

## Admin Observability

All endpoints in this section currently use `src/algopulse/api.py::_require_admin_session`, which is still local-review mock auth. Intended production access assumes real backend admin proof.

| Method | Route | Evidence | Current access behavior | Intended access | Data type | Risk | Wallet/signing/execution relevance | Redaction or delay | Production recommendation | Tests that should cover it | Human review |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GET | `/api/admin/preflight` | `src/algopulse/api.py::admin_preflight` | Admin mock. | admin | operational/execution readiness | low | Execution readiness, no signing. | Admin-only. | Keep admin-only; replace mock auth. | `test_admin_preflight_requires_role_and_returns_checklist`. | Yes |
| GET | `/api/admin/alerts/catalog` | `src/algopulse/api.py::admin_alert_catalog` | Admin mock. | admin | operational | low | No signing. | Admin-only. | Keep admin-only. | `test_admin_alert_catalog_requires_role_and_lists_phase0_failures`. | Yes |
| GET | `/api/admin/policy/catalog` | `src/algopulse/api.py::admin_policy_catalog` | Admin mock. | admin | operational/risk/execution | low | Policy visibility. | Admin-only. | Keep admin-only if policy internals should not be public. | `test_admin_policy_catalog_requires_role_and_lists_hard_stops`. | Yes |
| GET | `/api/ops/pipeline` | `src/algopulse/api.py::ops_pipeline` | Admin mock. | admin | operational | low | Shows signer/execution lock state only. | Admin-only. | Keep admin-only; separate delayed public summary later. | `test_ops_control_room_endpoints_require_admin_and_report_locked_state`. | Yes |
| GET | `/api/ops/phase-gates` | `src/algopulse/api.py::ops_phase_gates` | Admin mock. | admin | operational | low | Production gate evidence. | Admin-only. | Keep admin-only until public-safe summary exists. | Control-plane endpoint tests. | Yes |
| GET | `/api/ops/production-readiness` | `src/algopulse/api.py::ops_production_readiness` | Admin mock. | admin | operational | low | Readiness evidence. | Admin-only. | Keep admin-only; public status should be redacted. | Production readiness tests. | Yes |
| GET | `/api/ops/readiness-report` | `src/algopulse/api.py::ops_readiness_report` | Admin mock. | admin | operational/staging evidence | low | Read-only staging readiness; no signing. | Admin-only. | Keep detailed evidence admin-only. | `tests/test_read_only_staging_report.py`; control-plane API contract tests. | Yes |
| GET | `/api/ops/pipeline-evidence` | `src/algopulse/api.py::ops_pipeline_evidence` | Admin mock. | admin | stored route/risk/paper evidence | medium | Execution-adjacent evidence only; no signing. | Admin-only; do not expose raw route detail publicly. | Keep detailed scanner-to-paper linkage admin-only. | Scanner-to-paper pipeline evidence tests and control-plane API tests. | Yes |
| GET | `/api/ops/quote-freshness` | `src/algopulse/api.py::ops_quote_freshness` | Admin mock. | admin | stored quote evidence | medium | Quote readiness only; no signing. | Admin-only or delayed aggregate. | Keep quote-level freshness evidence admin-only. | Quote freshness tests and control-plane API tests. | Yes |
| GET | `/api/ops/connectors` | `src/algopulse/api.py::ops_connectors` | Admin mock. | admin | connector health evidence | low | No signing; reports readiness impact. | Admin-only; public status should stay coarse. | Keep connector internals admin-only. | Connector degradation and API contract tests. | Yes |
| GET | `/api/ops/testnet-soak` | `src/algopulse/api.py::ops_testnet_soak` | Admin mock. | admin | operational/TestNet soak rollup | low | No signing; read-only stored soak evidence. | Admin-only; no secrets, wallets, or raw routes. | Keep admin-only; never add remote runner start. | `tests/test_testnet_soak.py`. | Yes before wallet review |
| GET | `/api/ops/testnet-soak/observations` | `src/algopulse/api.py::ops_testnet_soak_observations` | Admin mock. | admin | operational/TestNet soak rows | medium | No signing; recent observation records only. | Admin-only; public-safe operational fields only. | Keep admin-only; cap limit; no executable payloads. | `tests/test_testnet_soak.py`. | Yes before wallet review |
| GET | `/api/ops/activity` | `src/algopulse/api.py::ops_activity` | Admin mock. | admin | operational | low | No signing. | Admin-only. | Keep admin-only. | Control-plane endpoint tests. | Yes |
| GET | `/api/ops/rejections` | `src/algopulse/api.py::ops_rejections` | Admin mock. | admin | route/operational | medium | Route/risk intelligence. | Admin-only or delayed aggregate. | Keep detailed rejections admin-only. | Control-plane endpoint tests. | Yes |
| GET | `/api/ops/paper-summary` | `src/algopulse/api.py::ops_paper_summary` | Admin mock. | admin | route/operational | low | Paper evidence only. | Admin-only or aggregate public. | Keep detailed view admin-only. | Control-plane endpoint tests. | Yes |
| GET | `/api/ops/risk-gates` | `src/algopulse/api.py::ops_risk_gates` | Admin mock. | admin | operational/risk | low | Execution lock reasons. | Admin-only. | Keep admin-only. | Control-plane endpoint tests. | Yes |
| GET | `/api/ops/environment` | `src/algopulse/api.py::ops_environment` | Admin mock. | admin | operational | medium | Deployment posture. | Admin-only. | Keep admin-only if it reveals internals. | Control-plane endpoint tests. | Yes |
| GET | `/api/ops/replay-lab` | `src/algopulse/api.py::ops_replay_lab` | Admin mock. | admin | route/operational | medium | Historical opportunity detail. | Admin-only. | Avoid fresh actionable route exposure. | Replay endpoint tests. | Yes |
| GET | `/api/ops/route-forensics` | `src/algopulse/api.py::ops_route_forensics` | Admin mock. | admin | route/operational | medium | Route decision detail. | Admin-only or delayed/redacted public education. | Keep detailed route forensics admin-only. | Route forensics tests. | Yes |
| GET | `/api/ops/market-heatmap` | `src/algopulse/api.py::ops_market_heatmap` | Admin mock. | admin | delayed/live route aggregate | medium | Opportunity density. | Aggregate/delayed before public use. | Separate public delayed heatmap later if needed. | Market heatmap tests. | Yes |
| GET | `/api/ops/failure-lab` | `src/algopulse/api.py::ops_failure_lab` | Admin mock. | admin | mock/operational | low | Simulated failure modes only. | Label mock. | Keep admin-only and clearly simulated. | Failure simulation tests. | Yes |
| GET | `/api/ops/provenance` | `src/algopulse/api.py::ops_data_provenance` | Admin mock. | admin | route/operational | medium | Traceable route/risk lineage. | Admin-only unless redacted. | Keep detailed lineage admin-only. | Data provenance tests. | Yes |
| GET | `/api/ops/evidence` | `src/algopulse/api.py::ops_evidence_records` | Admin mock. | admin | operational/evidence | medium | May reveal production gate details. | Admin-only. | Keep admin-only; public evidence should be curated. | Evidence system tests. | Yes |
| GET | `/api/ops/confidence-calibration` | `src/algopulse/api.py::ops_confidence_calibration` | Admin mock. | admin | route/operational | medium | Paper-trade performance analytics. | Admin-only or aggregate delayed. | Keep detailed calibration admin-only. | Confidence calibration tests. | Yes |
| GET | `/api/ops/opportunity-decay` | `src/algopulse/api.py::ops_opportunity_decay` | Admin mock. | admin | route/operational | medium | Opportunity timing/half-life. | Remove actionable route detail before public use. | Keep detailed decay admin-only. | Opportunity decay tests. | Yes |
| GET | `/api/ops/product-validation` | `src/algopulse/api.py::ops_product_validation` | Admin mock. | admin | operational/user analytics | medium | User/product behavior metadata. | Aggregate/anonymize before any public use. | Keep admin-only. | Product validation tests. | Yes |

## Admin Commands

All endpoints in this section currently use `src/algopulse/api.py::_require_admin_session`. Production requires real admin proof, audit logging, and explicit review for execution-adjacent behavior.

| Method | Route | Evidence | Current access behavior | Intended access | Data type | Risk | Wallet/signing/execution relevance | Redaction or delay | Production recommendation | Tests that should cover it | Human review |
|---|---|---|---|---|---|---|---|---|---|---|---|
| POST | `/api/admin/scan-now` | `src/algopulse/api.py::admin_scan_now` | Admin mock queued response. | admin | operational/live scanner | medium | No signing; triggers scan workflow. | Admin-only. | Safe after real auth/audit. | `test_admin_scan_now_returns_safe_queued_job_only`. | Yes |
| POST | `/api/admin/scanner/start` | `src/algopulse/api.py::admin_scanner_start` | Admin mock queued response. | admin | operational/live scanner | medium | No signing; controls scanner. | Admin-only. | Safe after real auth/audit. | Add command audit test. | Yes |
| POST | `/api/admin/scanner/pause` | `src/algopulse/api.py::admin_scanner_pause` | Admin mock queued response. | admin | operational/live scanner | medium | No signing; controls scanner. | Admin-only. | Safe after real auth/audit. | Add command audit test. | Yes |
| POST | `/api/admin/routes/run` | `src/algopulse/api.py::admin_routes_run` | Admin mock queued response. | admin | route/operational | medium | No signing; route generation. | Admin-only. | Safe if route generation remains read-only/paper. | Add command audit test. | Yes |
| POST | `/api/admin/paper/start` | `src/algopulse/api.py::admin_paper_start` | Admin mock queued response. | admin | route/operational | medium | No funds/signing. | Admin-only. | Safe if paper-only. | Add command audit test. | Yes |
| POST | `/api/admin/dry-run/build` | `src/algopulse/api.py::admin_dry_run_build` | Admin mock queued response. | admin | execution/dry-run | high | Builds unsigned execution plans in future workflow. | Admin-only. | Must remain unsigned-only unless separately reviewed. | `test_non_admin_cannot_call_admin_endpoints`; add unsigned-only assertion. | Yes |
| POST | `/api/admin/live/arm` | `src/algopulse/api.py::admin_live_arm` | Admin mock, currently blocked by config/kill switch. | disabled | execution | critical | Live execution boundary. | Admin-only; no public path. | Keep disabled until human production gate review. | `test_live_arm_stays_blocked_when_execution_disabled`; kill-switch tests. | Yes |
| POST | `/api/admin/live/disarm` | `src/algopulse/api.py::admin_live_disarm` | Admin mock queued response. | admin | execution/control | medium | Disarms execution. | Admin-only. | Safe if it only disarms/queues. | Add command audit test. | Yes |
| POST | `/api/admin/kill-switch/trigger` | `src/algopulse/api.py::admin_kill_switch_trigger` | Admin mock queued response. | admin | execution/control | medium | Locks execution. | Admin-only. | Safe if it only triggers lock. | Add command audit test. | Yes |
| POST | `/api/admin/kill-switch/clear` | `src/algopulse/api.py::admin_kill_switch_clear` | Admin mock, explicitly rejected. | disabled | execution/control | critical | Unlocks execution safety boundary. | Admin-only; disabled. | Keep rejected unless separate production policy approves. | Kill-switch clear rejection test. | Yes |

## Production Gaps To Close

- Replace `local-review-mock` admin and wallet sessions with signed wallet proof or another reviewed auth mechanism.
- Reject mock PNET confirmations outside local review mode.
- Gate or redact payment verifications, refund cases, live trades, and reconciliations.
- Admin-gate public scanner mutation routes before production.
- Ensure `/api/execute-best` cannot become public execution through an environment flag alone.
- Add public redaction/delay tests for opportunity, receipt, payment, refund, readiness, and route-intelligence surfaces.
- Add command audit tests for admin queue endpoints.
