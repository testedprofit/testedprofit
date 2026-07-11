# Human Review Gates

Use these gates before approving AI-assisted changes.

## Safe For Codex

Codex can implement these with tests and a small diff:

- documentation and handoff updates
- scanner evidence and stale-data warnings
- mock/local admin dashboard improvements
- route, risk, paper-trading, replay, provenance, and report analytics
- public-safe delayed market intelligence
- product validation metrics
- CI and test coverage that does not loosen safety

Required evidence:

- changed files are scoped
- tests pass or skipped tests are explained
- no signer, secret, live submission, hot-wallet, or risk-limit changes
- mock/stored/live/delayed/unavailable data is labeled

## Human Review Required

These require explicit human approval before implementation:

- real Pera wallet integration
- production fee receiver address
- live Tinyman/Pact staging configuration
- public dashboard freshness and redaction policy
- app ID or asset allowlist changes
- production database or deployment changes
- risk-limit changes
- dry-run executor behavior changes
- any public claims about profitability or returns
- new dependencies
- new modules or systems that overlap an existing repo pattern
- changes that mix scanner, dashboard, wallet, signer, or execution responsibilities
- public behavior changes
- large files or broad refactors
- temporary, local-review, or mock code that is not clearly labeled and isolated

### x402 Challenge Workstream

Use the 4D loop for x402 work:

- Delegation: AI may prepare docs, smoke scripts, tests, mocks, and small isolated implementation changes. Rob retains wallet/signing, real TestNet payment, Mainnet, deploy, public-claims, eligibility-claim, and merge decisions.
- Description: every PR must name the gate, route, package, env vars, tests, evidence, and explicit safety boundaries. The x402 route is delayed/redacted report access only: `GET /api/x402/reports/market-pulse/daily`.
- Discernment: verify the diff, current-head GitHub CI, secret/payment-payload handling, challenge-rule fit, and gate scope before acting on AI output.
- Diligence: Rob owns the final result. No merge, paid smoke, deploy, Mainnet action, public claim, or eligibility claim without explicit approval.

x402-specific human approval is required before:

- any real TestNet wallet/payment exercise
- any receiver/payment asset assumption
- any Mainnet work or deployment
- any GoPlausible-tracked public endpoint claim
- any challenge eligibility claim
- any public wording, legal/US-user notice, or challenge submission text
- any public wording that implies live trading, actions, guaranteed volume, revenue, profits, ROI, or prize outcomes

Current challenge constraints:

- Official eligibility requires a paid x402 endpoint deployed and reachable on Algorand Mainnet using the GoPlausible facilitator.
- Judging emphasizes real USDC volume, use-case quality, sustained potential, and innovation.
- AlgoPulse x402 positioning is charge-for-data and charge-for-verification: delayed/redacted reports only.
- x402 must not unlock live trading, fresh executable routes, signer/wallet access, custody, or transaction submission by AlgoPulse.
- Every gate needs assurance evidence, safety boundaries, tests or smoke proof, and explicit human approval before moving to wallet/payment, Mainnet, deploy, public-claim, or eligibility-claim work.
- Gate 4 remains blocked until Gate 3 evidence is reviewed and merged, settlement-failure limitations are accepted or covered by a safe plan, abuse controls are defined, legal/compliance and US-user notice wording is reviewed, Mainnet receiver/payment is approved, and Rob gives explicit Mainnet approval.

Required evidence:

- written reason for the change
- affected files and code paths
- rollback plan
- test plan
- public/user impact review
- explanation of why existing patterns were not enough, if a new pattern is introduced
- dependency justification, if a dependency is added

## Blocked For Now

Do not implement these in Phase 0 control-plane work:

- live transaction submission
- signer feature changes
- mnemonic, private key, seed phrase, or signer secret handling
- hot-wallet funding or custody logic
- user deposits
- public execution API
- fresh raw opportunity feed for public users
- guaranteed-return, passive-income, or profit-promise language

## Execution Gates

Live micro-execution cannot be considered until all are true:

- scanner-only mode has 24h no-key/no-crash evidence
- quote freshness is under threshold
- paper trading has enough 5s/30s replay history
- risk engine blocks stale, unprofitable, high-impact, over-limit, and unallowlisted routes
- unsigned dry-run receipts are reviewed
- signer isolation review is complete
- kill switch behavior is proven
- first tiny own-funds route is manually approved
- Lora transaction and reconciliation are recorded

Until then, any execution-related work is documentation, simulation, or unsigned dry-run only.

## Approval Record

For every human-reviewed risky change, record:

- reviewer
- date
- change summary
- evidence reviewed
- approved scope
- explicit exclusions
- rollback path
