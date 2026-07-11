# PNET Dashboard Cockpit

This brief turns the current public scanner page into a role-based PNET Market Engine dashboard.

## Product Shape

The UI has two primary modes:

- Admin Cockpit: operational controls, readiness checks, route review, risk policy, execution queue, receipts, and alerts.
- Connected User / PNET Access Portal: PNET-gated market intelligence, route simulation requests, fee receipts, and delayed route results.

Guest users see public delayed data and connect prompts. Connected PNET users see more detailed delayed intelligence and paid request surfaces. Admin wallets see the control cockpit, but frontend role gates are only presentation; backend role checks remain mandatory.

## Frontend Safety Rules

- The frontend can request actions, but it must not bypass backend policy.
- Non-admin users must not see controls for platform execution, signer policy, hot-wallet settings, app allowlists, or live kill-switch actions.
- Public data must stay delayed or already executed before becoming visible.
- Paid PNET actions are market-data or route-simulation fees, not deposits into the bot.
- Copy must avoid guaranteed-return, copy-trading, managed-strategy, and passive-income claims.

## Current Implementation

The first implementation is a mock-driven vanilla HTML/CSS/JS cockpit layered onto the existing FastAPI-served dashboard. It adds:

- persistent Pera Wallet UI states
- role badge, network badge, PNET balance, and credit balance
- locked admin nav treatment for non-admin wallet states
- role-gate notices for admin-only cockpit surfaces
- admin/user/guest dashboard rendering
- admin preflight checklist, bot controls, route console, risk policy, queue, receipts, and logs
- PNET access gate and fee modal
- route detail modal
- live-arm confirmation modal that does not submit any backend execution action

Real Pera SDK integration and backend session endpoints are next-step work. The current UI uses review-safe mock states and existing scanner data where available.

The backend now exposes a small mock control-plane slice for Phase 0 review: public config/session endpoints, admin preflight, safe admin job-queue endpoints, and PNET fee quote shape. Admin endpoints require backend role headers plus an allowlisted review wallet; frontend gates remain UX only.
