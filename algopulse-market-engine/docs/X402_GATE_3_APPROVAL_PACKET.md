# x402 Gate 3 Approval Packet — AlgoPulse Market Engine

**Status:** Awaiting Rob's decision. Gate 3 is **blocked** until the exact approval sentence at the bottom of this packet is given.

**Scope of this document:** prep / docs only. Nothing here implements Gate 3, runs a payment, changes runtime behavior, or touches signer/wallet/trading/deploy/Mainnet.

---

## 1. The decision you are being asked to make

Approve **Gate 3 TestNet implementation only** — wiring the official GoPlausible `x402-avm` FastAPI path to a single delayed-report endpoint on **Algorand TestNet**, exercised with **TestNet USDC**.

This approval does **not** authorize Mainnet, deploy, signer/wallet custody, transaction signing/submission beyond the approved TestNet exercise, live trading, fresh executable routes, Cloudflare, or any challenge-eligibility claim.

## 2. Scope

**In scope (Gate 3):**
- Managed GoPlausible facilitator (`https://facilitator.goplausible.xyz`).
- Algorand **TestNet** USDC payment.
- A single **delayed market-pulse report** endpoint (read-only; redacted/delayed premium report payload distinct from the unauthenticated public preview).

**Explicitly out of scope:**
- ❌ No Mainnet.
- ❌ No deploy.
- ❌ No signer / wallet custody / private keys / mnemonics / transaction signing / submission changes.
- ❌ No live trading / execution.
- ❌ No fresh executable routes (only the delayed report resource).
- ❌ No Cloudflare.
- ❌ No challenge-eligibility claim.

## 3. Proposed resource

`GET /api/x402/reports/market-pulse/daily`

- Returns the **delayed / redacted** market-pulse report only.
- Responds **402 (Payment Required)** until a valid TestNet payment is verified **and** settled by GoPlausible.

## 4. Payment assumptions (TestNet)

| Field | Value |
|---|---|
| Network | `algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=` (TestNet) |
| Asset (USDC ASA) | `10458941` |
| Decimals | `6` |
| Example price | `$0.01` → `amount: "10000"` |
| Receiver | **placeholder only** — no real address committed unless Rob approves |
| Facilitator fills | `feePayer`, `genesisHash`, `genesisId` |
| Verify/settle body | `{ x402Version, paymentPayload, paymentRequirements }` |

The payment payload / `paymentGroup` is **package-owned** — it will not be hand-rolled, parsed, logged, or rewritten.

**PNET note:** PNET is **not** currently shown in GoPlausible discovery; the official challenge path appears **USDC-only** unless new official support says otherwise. Gate 3 therefore uses TestNet USDC.

## 5. No-secret handling

- No mnemonics / private keys in the repo.
- No full payment-payload logging.
- No wallet secrets in docs or tests.
- `.env` stays local only (enforced by `scripts/repo_guard.py` + `.gitignore`; only `*.example` env files are tracked).
- `scripts/x402_gate3_env_check.py` validates required env var **names** only — it never prints values and performs no network/payment/wallet/signer action.

## 6. Test plan (Gate 3)

1. Unpaid request → **402**.
2. Fake `X-PAYMENT` header → still **402**.
3. Fake `PAYMENT-SIGNATURE` header → still **402**.
4. Valid TestNet payment → **200**, only after GoPlausible verify + settle succeed.
5. Invalid / simulation / settlement failure → **402** (fail closed).
6. Report remains **delayed / redacted** in every case (no fresh data leak).

## 6A. Current paid TestNet evidence caveat

The current Gate 3 paid TestNet proof used the same public TestNet address as payer and receiver. That proves local x402 mechanics only: `402 -> valid TestNet payment retry -> 200` for the delayed report endpoint. It is **not** external usage evidence, challenge usage evidence, leaderboard evidence, Mainnet readiness, or a public claim.

Gate 3.5 must prove an external TestNet payer path where payer and receiver are different addresses before any external-user, Mainnet-readiness, challenge, or leaderboard claim is made.

## 7. Stop conditions (halt immediately if any occur)

- Any signer / wallet / trading / execution file is touched.
- Any secret appears in output or logs.
- Package API mismatch vs. the verified `x402-avm 2.0.2` surface.
- The report would expose fresh (non-delayed) route data.
- The GoPlausible / USDC path fails or behaves unexpectedly.

## 8. Human gates (each requires Rob's explicit OK)

- [ ] Rob approves managed GoPlausible.
- [ ] Rob approves TestNet USDC.
- [ ] Rob approves receiver / payment assumptions.
- [ ] Rob approves a real TestNet wallet/payment exercise.
- [ ] Rob approves the no-secret handling.

## QA checklist (must hold before and during Gate 3)

- [ ] PR #2 merged before Gate 3 starts.
- [ ] Gate 3 work is on a separate branch.
- [ ] Gate 3 is TestNet only.
- [ ] No Mainnet / no deploy.
- [ ] No challenge-eligibility claim.
- [ ] No artificial usage.
- [ ] No live trading / signing / execution.

## Verified facts (from PR #2)

- Package: `x402-avm[fastapi,avm]`; import root `x402`; observed version `x402-avm 2.0.2`.
- FastAPI/ASGI surface: `PaymentMiddlewareASGI`, `PaymentOption`, `RouteConfig`, `x402ResourceServer`, `ExactAvmServerScheme`, `HTTPFacilitatorClient`.
- Managed facilitator: `HTTPFacilitatorClient(FacilitatorConfig(url="https://facilitator.goplausible.xyz"))`.
- Retry header: `PAYMENT-SIGNATURE`.
- A fake `X-PAYMENT` does **not** unlock the Python/FastAPI path.

## Approval

To unlock Gate 3, Rob gives this **exact** sentence:

> "Rob approves Gate 3 TestNet implementation using managed GoPlausible, Algorand TestNet USDC, approved receiver/payment assumptions, approved no-secret handling, and a real TestNet wallet/payment exercise. No Mainnet, deploy, signer, wallet custody, live trading, fresh route exposure, or challenge eligibility claim is approved."

Until that sentence is given, Gate 3 remains blocked.

---

**x402 Challenge Delta:** PR #2 should close Gate 2. Gate 3 can unlock only after Rob approves the TestNet implementation packet; all Mainnet, deploy, signer, wallet, trading, fresh-route, and eligibility work remains blocked.
