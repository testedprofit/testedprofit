# x402 Gate Assurance Pack — AlgoPulse Market Engine

**Status:** docs only · reusable · prep. Nothing here implements a gate, adds payment code/config, touches signer/wallet/trading/execution/deploy, adds Mainnet, stores secrets, or claims challenge eligibility.

---

## 1. Purpose

This is the **reusable assurance pack** for the AlgoPulse x402 challenge gates. It exists to **move fast *safely*** — to accelerate delivery by making evidence, decision rights, and stop conditions explicit, **not** to slow development.

Operating model:

> **requirements → standards → playbooks → controls → evidence → review → decision**

Each gate ships with **TEVV** evidence (Test, Evaluation, Verification, Validation), named decision rights, pass/fail thresholds, residual-risk acceptance, and a rollback/incident plan. A gate advances only when its evidence meets threshold **and** the accountable owner approves.

## 2. Standards basis (crosswalk)

This pack is deliberately mapped to recognized assurance frameworks so the workstream is audit-ready, not ad hoc.

| Framework | Used here for |
|---|---|
| **ISO/IEC 42001:2023** — AI management system | Gate governance lifecycle, roles/decision rights, continual improvement |
| **ISO/IEC 23894:2023** — AI risk management | Per-gate risk identification, treatment, and **residual-risk acceptance** |
| **ISO 31000:2018** — Risk management | Risk-treatment + acceptance discipline and review cadence |
| **NIST AI RMF 1.0** — Govern · Map · Measure · Manage | **TEVV** evidence model and lifecycle functions per gate |
| **ISO/IEC 27001:2022 + ISO/IEC 27035** — Infosec / incident mgmt | Secret handling, no-secret controls, incident & rollback |

**TEVV** = Test · Evaluation · Verification · Validation (the evidence each gate must produce).

## 3. Milestones (gate path)

| Milestone | Gate | Assurance state | Exit criteria |
|---|---|---|---|
| **M0** | Baseline | ✅ established | Repo guard + tests green; boundaries documented |
| **M1** | Gate 1 — mock delayed report | ✅ merged | PR #1 merged; tests/smoke pass |
| **M2** | Gate 2 — GoPlausible TestNet plan | ✅ merged (PR #2) | Package/API/header/TestNet asset verified; docs/prep only |
| **M3** | Gate 3 — TestNet implementation | 🔒 blocked (needs Rob approval) | Gate 3 assurance requirements (§5) met on TestNet only |
| **M4** | Gate 4 — Mainnet minimal endpoint | 🔒 blocked | Gate 3 proof + abuse controls + legal/compliance + Rob approval |
| **M5** | Gate 5 — real usage / submission | 🔒 blocked | Mainnet endpoint + legitimate-usage evidence + public-safe copy |

## 4. Gate Assurance Template (apply to every gate)

Each gate **must** define all of the following before it can pass:

| Field | What it captures |
|---|---|
| **Intended use** | The single, in-scope thing this gate enables |
| **Prohibited use** | Explicit out-of-scope actions (the boundaries) |
| **Pass condition** | Objective, testable success threshold |
| **Fail / stop condition** | What forces a halt (fail closed) |
| **Required evidence (TEVV)** | The artifacts proving pass: test output, logs, diffs, reviews |
| **Validation commands** | Exact commands a reviewer re-runs to reproduce evidence |
| **Red-team / abuse checks** | Adversarial cases attempted and their results |
| **RACI / decision owner** | Who is Responsible, Accountable, Consulted, Informed |
| **Residual risks** | What risk remains after controls, and who accepts it |
| **Approval expiry / review date** | When this approval lapses and must be re-reviewed |
| **Rollback / incident plan** | How to safely revert and contain if it goes wrong |

## 5. Gate 3 Assurance Requirements (TestNet implementation)

> Gate 3 is **blocked**. These are the requirements it must satisfy *after* Rob's explicit approval. They do not authorize any work today.

**Intended use:** managed GoPlausible + Algorand **TestNet USDC** gating a single delayed/redacted market-pulse report endpoint.
**Prohibited use:** Mainnet · deploy · signer/wallet custody · keys/mnemonics · tx signing/submission beyond the approved TestNet exercise · live trading/execution · fresh executable routes · Cloudflare · eligibility claim.

| # | Requirement (control) | Pass threshold | TEVV evidence |
|---|---|---|---|
| 1 | Unpaid request returns **402** | 402 every time | Test case + response capture |
| 2 | Fake `X-PAYMENT` stays **402** | No unlock | Negative test |
| 3 | Fake `PAYMENT-SIGNATURE` stays **402** | No unlock | Negative test |
| 4 | Valid TestNet payment returns **200** | Only after facilitator **verify + settle** | Integration test against GoPlausible TestNet |
| 5 | Invalid / simulation / settlement failure returns **402** | Fail **closed** | Negative/fault-injection test |
| 6 | Report stays **delayed / redacted** | No fresh data in any path | Response diff vs. mock baseline |
| 7 | **No full payment-payload logging** | Payload never logged in full | Log inspection + code review |
| 8 | **No secrets committed** | `repo_guard.py` clean | Repo guard output + changed-file scan |
| 9 | **No signer/wallet/trading/execution files touched** | Zero such files in diff | `git diff --name-only` review |
| 10 | **No fresh route exposure** | Only the delayed report resource | Route inventory diff |

**Validation commands (re-runnable evidence):**

```bash
git diff --check
python scripts/repo_guard.py
python -m pytest -q
git diff --name-only main...HEAD   # confirm no signer/wallet/trading/execution/deploy files
```

**Red-team / abuse checks:** replayed/forged headers (rows 2–3), settlement-failure injection (row 5), oversized/garbage payloads, attempt to coerce fresh (non-delayed) data (row 6), log-scrape for secrets (rows 7–8).

## 6. RACI

| Activity | Rob | Codex/Claude | ROB OS | Legal/Compliance |
|---|---|---|---|---|
| Gate design / scoping | **A** | R | C | I |
| Implementation + evidence | **A** | **R** | C | I |
| Review / gate discipline | **A** | C | **R** | C |
| Gate approval (advance) | **A** | I | C | I |
| Public / Mainnet / US-restriction claims | **A** | I | C | **R** (required first) |
| Incident response / rollback | **A** | **R** | C | C |

- **Rob** — accountable / final approval.
- **Codex/Claude** — responsible for implementation and evidence.
- **ROB OS** — review / decision support and gate discipline.
- **Legal/compliance review** — **required before** any public, Mainnet, or US-restriction eligibility claim.

(R = Responsible · A = Accountable · C = Consulted · I = Informed.)

## 7. Residual Risk Statement (draft — Rob to accept)

Per ISO/IEC 23894 + ISO 31000. Draft rows; fill owner/date on approval. No risk is "accepted" until Rob signs the row.

| Remaining risk | Mitigation | Owner accepting | Expiration / review date | Evidence link |
|---|---|---|---|---|
| Dependence on managed GoPlausible facilitator availability/behavior | Fail closed to 402; rollback to mock-only mode | _Rob (pending)_ | _set on approval_ | PR #2 plan; §8 rollback |
| TestNet proof may not fully represent Mainnet conditions | Gate 4 requires separate Mainnet review; no eligibility claim from TestNet | _Rob (pending)_ | _set on approval_ | §3 M4 criteria |
| Accidental secret exposure during TestNet exercise | `repo_guard.py`, no-payload-logging, `.env` local-only, env-check script | _Rob (pending)_ | _set on approval_ | §5 rows 7–8 |
| Scope creep into signer/wallet/execution | Stop conditions + `git diff --name-only` gate | _Rob (pending)_ | _set on approval_ | §5 row 9 |

## 8. Incident / Rollback Plan

If any stop condition trips or anomalous behavior appears, execute in order:

1. **Disable** the x402 endpoint (feature-flag off / route disabled).
2. **Return to mock-only mode** (the Gate 1 delayed-report behavior).
3. **Revoke / rotate** any exposed *test* credentials (TestNet only; no Mainnet keys involved).
4. **Remove public links** to the endpoint.
5. **Preserve logs / evidence** for review (do not delete; redact secrets).
6. **Document the incident** and **update `docs/X402_GATE_LOG.md`** with cause, impact, and corrective action (ISO/IEC 27035 close-out).

Recovery resumes only after a fresh review against §5 and renewed approval where required.

## 9. References

- [`docs/X402_GATE_LOG.md`](X402_GATE_LOG.md) — live gate status & boundaries
- [`docs/X402_GOPLAUSIBLE_TESTNET_POC_PLAN.md`](X402_GOPLAUSIBLE_TESTNET_POC_PLAN.md) — Gate 2 plan
- [`docs/X402_GATE_3_APPROVAL_PACKET.md`](X402_GATE_3_APPROVAL_PACKET.md) — Gate 3 decision packet (PR pending)
- `scripts/repo_guard.py`, `scripts/x402_gate3_env_check.py` — automated controls

---

**x402 Challenge Delta:** Gate assurance pack added so Gate 3 can move faster with explicit evidence, decision rights, residual-risk review, and rollback planning while keeping Mainnet, deploy, signer, wallet, trading, and eligibility blocked.
