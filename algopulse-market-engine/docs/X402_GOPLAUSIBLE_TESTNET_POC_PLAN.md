# GoPlausible TestNet x402 POC Plan

This is a docs-only Gate 2 plan for connecting AlgoPulse's delayed market-pulse report concept to the official Algorand x402 facilitator path.

It does not implement Mainnet, deploy any service, add real payment configuration, touch signer code, custody wallets, store mnemonics, sign transactions, submit transactions, enable live trading, expose fresh executable routes, or claim Global x402 Challenge eligibility.

Related docs:

- [x402 Gate Log](X402_GATE_LOG.md)
- [x402 Gate Assurance Pack](X402_GATE_ASSURANCE_PACK.md)

## Source Baseline

Primary sources reviewed:

- Algorand developer guide: https://algorand.co/agentic-commerce/x402/developers
- Algorand Developer Portal tutorial: https://dev.algorand.co/resources/x402-on-algorand/
- Algorand Agent Skills repository: https://github.com/algorand-devrel/algorand-agent-skills
- Algorand Agent Skills Python x402 skill: https://raw.githubusercontent.com/algorand-devrel/algorand-agent-skills/main/skills/algorand-x402-python/SKILL.md
- Algorand Agent Skills TypeScript x402 skill: https://raw.githubusercontent.com/algorand-devrel/algorand-agent-skills/main/skills/algorand-x402-typescript/SKILL.md
- Algorand Agent Skills canonical AGENTS setup: https://raw.githubusercontent.com/algorand-devrel/algorand-agent-skills/main/setups/AGENTS.md
- GoPlausible x402 Algorand hub: https://x402.goplausible.xyz/
- GoPlausible facilitator: https://facilitator.goplausible.xyz/
- GoPlausible supported networks: https://facilitator.goplausible.xyz/supported
- GoPlausible payment methods: https://facilitator.goplausible.xyz/discovery/paymentmethods
- Algorand blog, `x402: Unlocking the agentic commerce era`: https://algorand.co/blog/x402-unlocking-the-agentic-commerce-era
- Global x402 Challenge page: https://algorand.co/global-x402-challenge
- Global x402 Challenge Official Rules PDF: https://algorand.co/hubfs/x402%20competition%20Official%20Rules.pdf
- Local copy reviewed: `x402 competition Official Rules.pdf` provided by Rob.

Source reconciliation notes:

- Treat the Official Rules PDF as controlling for deadlines, eligibility, restrictions, and judging criteria.
- The challenge page confirms the public positioning and says finalists present live at Devcon 8 India. The Official Rules PDF says the November 2, 2026 final presentation time and place are to be announced. Use the Devcon 8 India venue as page-confirmed but still verify it in registration/finalist materials before making external commitments.
- The challenge page summarizes evaluation as real usage, use case quality, technical execution, and long-term potential. The Official Rules PDF defines the evenly weighted judging criteria as volume, use case quality, sustained potential, and innovation. Use the Official Rules wording in challenge-readiness gates.

## Confirmed Challenge Facts

- Registration closes at 11:45 PM Eastern Standard Time on September 1, 2026.
- Final project information is due by 11:45 PM Eastern Standard Time on September 29, 2026.
- Final presentation shortlisting runs from 11:45 PM Eastern Standard Time on September 30, 2026 through 11:45 PM Eastern Standard Time on October 8, 2026.
- Selected participants are notified by email on October 9, 2026.
- The final presentation date is November 2, 2026. The Official Rules say time and place are to be announced; the challenge page says finalists present live at Devcon 8 India.
- Winners are announced no later than November 12, 2026.
- Eligibility requires a paid x402 endpoint deployed and reachable on Algorand Mainnet.
- The endpoint must use the GoPlausible facilitator so transactions and volume are automatically tracked in the public competition dashboard.
- Finalist consideration depends on leaderboard review plus submitted project information.
- To be eligible for finalist consideration, a project must be ranked among the top 50 projects on the leaderboard and the Entrant must submit all requested project information.
- Each participant may be affiliated with only one team, and each team may submit one project.
- Judging criteria are evenly weighted across volume, use case quality, sustained potential, and innovation.
- The Official Rules describe volume as USDC processed through the submitted x402 endpoint.
- Leaderboard awards are subject to Administrator review and verification, including checks against artificial volume, wash transactions, repeated self-payments, or other manipulation.
- Challenge content and project information must be in English, lawful, free of malicious components, and must not infringe third-party rights.
- Participation is not an endorsement, investment recommendation, guarantee, legal advice, financial advice, or investment advice from Algorand Foundation, judges, or sponsors.
- Entrants remain responsible for their own operations, marketing, eligibility, taxes, sanctions/export-control compliance, and applicable laws.
- Official dates may change if the Administrator updates the challenge website.

Therefore, AlgoPulse must not claim official challenge eligibility until it has a Mainnet paid endpoint using the GoPlausible facilitator and the required submission information is complete.

## Agentic Commerce Fit

Algorand's x402 agentic-commerce framing treats HTTP `402 Payment Required` as a first-class payment-required flow for software, services, and AI agents. The relevant pattern for AlgoPulse is narrow:

```text
Client or AI agent requests delayed market intelligence
        -> resource server returns 402 + paymentRequirements
        -> client pays through the official x402 flow
        -> facilitator verifies and settles
        -> resource server returns the delayed/redacted report
```

This supports autonomous agent and machine-to-machine payments, but x402 is only the paid access layer. It is not the whole AlgoPulse product and must not become trading, custody, signing, transaction submission, or live route execution.

Best-fit AlgoPulse use cases:

| x402 use case | AlgoPulse position | Boundary |
|---|---|---|
| Pay-per-API access | Primary | Charge per request for delayed market-pulse API output. |
| Premium data/content | Primary | Unlock delayed/redacted market intelligence reports. |
| Metered digital resources | Primary | Price report reads, report exports, or rate-limited data access. |
| Verification | Secondary | Unlock evidence-backed audit summaries explaining stale quotes, connector health, or rejection reasons. |
| Actions | Not allowed | Do not sell live trading, fresh executable routes, signer access, wallet custody, transaction construction, or transaction submission. |

Audience mapping:

| Audience | Useful framing | AlgoPulse boundary |
|---|---|---|
| Developers | Monetize APIs, datasets, reports, and AI services request by request. | The Gate 3 target is one paid delayed-report endpoint, not a generic action marketplace. |
| Businesses | Support auditable market-intelligence and research workflows with clearer usage attribution. | Do not frame this repo as autonomous treasury, procurement, trade execution, or operations optimization. |
| Individuals | Future clients may request user-authorized paid reports or agent-assisted research. | No wallet custody, signer access, automatic purchasing, or transaction submission by AlgoPulse. |

Roles for the planned challenge path:

| Role | AlgoPulse mapping | Responsibility |
|---|---|---|
| Merchant | AlgoPulse / TestedProfit | Defines the report product, price, access rules, safety boundaries, and public copy. |
| Resource server | `GET /api/x402/reports/market-pulse/daily` | Returns `402` with payment requirements when unpaid and serves only delayed/redacted report data after verified settlement. |
| Facilitator | GoPlausible | Abstracts payment rails, verification, simulation, and settlement for the official x402 flow. |
| Client/agent | User, developer, or AI agent requesting report access | Reads payment requirements, pays through the official package flow, and retries with the package-defined payment proof. |
| Settlement layer | Algorand | Provides the on-chain settlement environment for the supported payment asset/network. |

Why Algorand helps this use case:

- Low fees make small pay-per-report/API calls more practical.
- Instant and deterministic finality helps keep payment verification inside a request/response lifecycle.
- Stablecoin support fits predictable report/API pricing and the challenge's USDC-volume framing.
- Atomic transaction grouping can support payment and authorization semantics without partial intermediate states.
- Predictable settlement behavior helps AI agents and automated clients avoid congestion-specific payment logic.

Gate 3 blog-aligned acceptance criteria:

- Unpaid request returns HTTP `402` with a `paymentRequirements`-style body.
- Paid retry uses the official package header/API. For the verified Python/FastAPI path, the retry header is `PAYMENT-SIGNATURE`.
- Facilitator verifies and settles before the resource is returned.
- Resource returns only after verified settlement.
- Invalid payment, failed simulation, failed verification, failed settlement, malformed header, or unsupported asset returns HTTP `402` invalid payment.
- Payment logic remains separated from market engine, signer, wallet, trading, execution, and fresh-route logic.

## Official Algorand x402 Facilitator Flow

The official flow is facilitator-based, not the current PNET tx-id-only proof flow:

1. Client requests a protected resource.
2. Resource server returns HTTP `402 Payment Required` with structured `paymentRequirements`.
3. Client constructs a `paymentGroup` for the required Algorand payment.
4. Client signs only the relevant transactions in the `paymentGroup`.
5. Client retries the resource request with the official payment proof header. For the verified `x402-avm` Python/FastAPI path, this is `PAYMENT-SIGNATURE`.
6. Resource server sends the `paymentGroup` to the GoPlausible facilitator for verification.
7. Facilitator may check or sign the fee-payer transaction, depending on the official flow/configuration.
8. Facilitator simulates the `paymentGroup` on Algorand.
9. If simulation succeeds, facilitator reports the payment as verified.
10. Resource server requests settlement.
11. Facilitator submits the `paymentGroup` to Algorand.
12. If settlement succeeds, the resource server returns HTTP `200` with the delayed/redacted report.
13. If the payment is invalid, simulation fails, or settlement fails, the resource server returns HTTP `402 Payment Required` with an invalid-payment response.

The GoPlausible/Algorand flow is a structured facilitator flow around `paymentRequirements`, signed `paymentGroup` data, simulation, and settlement. It is not equivalent to a bare PNET transaction ID and must not be implemented with hand-rolled header parsing.

Sequence view:

```text
Client
  -> Resource server: GET delayed market-pulse report
Resource server
  -> Client: 402 Payment Required + paymentRequirements
Client
  -> Client wallet: construct paymentGroup and sign relevant transactions
Client
  -> Resource server: retry request with official payment proof header
Resource server
  -> GoPlausible facilitator: verify paymentGroup
GoPlausible facilitator
  -> GoPlausible facilitator: check/sign feePayer transaction if required
GoPlausible facilitator
  -> Algorand TestNet: simulate paymentGroup
Algorand TestNet
  -> GoPlausible facilitator: simulation result
GoPlausible facilitator
  -> Resource server: verified or invalid
Resource server
  -> GoPlausible facilitator: settle paymentGroup if verified
GoPlausible facilitator
  -> Algorand TestNet: submit paymentGroup
Algorand TestNet
  -> GoPlausible facilitator: settlement result
GoPlausible facilitator
  -> Resource server: settled or failed
Resource server
  -> Client: 200 OK + delayed/redacted report, or 402 invalid payment
```

## Header Naming Decision

Gate 3 must follow the official package API and observed wire behavior, not assumptions from generic x402 examples.

Current verification result:

- Rob's Algorand facilitator sequence labels the retry header as `PAYMENT-SIGNATURE`.
- Local package introspection found both `X_PAYMENT_HEADER = "X-PAYMENT"` and `PAYMENT_SIGNATURE_HEADER = "PAYMENT-SIGNATURE"` constants in `x402.http`.
- `PaymentMiddlewareASGI` builds request context from `payment-signature` first and then `x-payment`, but the verified core extractor decodes `PAYMENT_SIGNATURE_HEADER` / `PAYMENT-SIGNATURE`.
- `x402HTTPServerBase._extract_payment(...)` checks `PAYMENT-SIGNATURE` and `payment-signature`; it does not decode `X-PAYMENT` in the verified package path.
- The GoPlausible overview page still describes `X-PAYMENT`, so treat that as generic/overview wording rather than the Python/FastAPI Gate 3 header.
- A throwaway FastAPI/TestClient harness confirmed that a fake `X-PAYMENT` header does not unlock the Python/FastAPI path; it returns HTTP `402`.
- A fake `PAYMENT-SIGNATURE` header also returns HTTP `402`; invalid payment proof fails closed.
- Existing PNET tx-id-only work in the separate package is intentionally not the official GoPlausible facilitator flow.

Decision for Gate 3:

- Use `PAYMENT-SIGNATURE` for the Python/FastAPI implementation path.
- Do not hand-roll or separately accept `X-PAYMENT` unless the installed official middleware path proves it is required.
- Treat the retry header value as a base64-encoded x402 `PaymentPayload` produced by the official package.
- Add tests around the official middleware rather than parsing the header manually in AlgoPulse.
- Do not accept a bare transaction ID as official challenge payment proof unless GoPlausible explicitly documents that mode.
- Keep invalid payment, failed simulation, failed facilitator verification, and failed settlement paths as HTTP `402 Payment Required`; they must not fall through to `200` or expose the delayed report.

## Safe Architecture Invariant

The concept being merged is narrow:

```text
User or agent pays
        -> x402 verifies report access
        -> AlgoPulse returns a delayed/redacted market-pulse report
```

The concept that must never be merged is:

```text
User or agent pays
        -> bot trades
        -> bot reveals a fresh executable route
        -> bot signs or submits a transaction
```

Architecture boundary:

```text
AlgoPulse market engine
  - scans markets
  - computes opportunities
  - records evidence
  - produces delayed/redacted reports
  - keeps live routing, signer, wallet, and execution systems isolated

        -> delayed/redacted report data only

x402 access layer
  - protects the report endpoint
  - returns HTTP 402 when unpaid
  - accepts official x402 payment proof
  - delegates verify/settle to GoPlausible
  - applies replay, rate-limit, logging, and abuse controls

        -> after verified payment only

User or agent
  - receives delayed market-pulse intelligence
  - never receives signer access
  - never receives fresh executable routes
  - never triggers trades through payment
```

Hard invariant: payment unlocks delayed/redacted report access only. It never authorizes trading, reveals fresh executable routes, changes signer state, accesses wallet custody, or submits transactions.

## Facilitator Model Decision

Algorand's x402 developer guidance describes two facilitator deployment models:

| Model | Strength | Cost/risk |
|---|---|---|
| Self-hosted facilitator | Full control over verification, pricing logic, policies, and settlement rules. | Greater operational responsibility for infrastructure, verification, settlement, monitoring, replay/abuse controls, and incident response. |
| Shared or managed facilitator | Faster integration, less infrastructure to maintain, and opinionated defaults. | Less control over internal policies and behavior; the project must follow the managed provider's supported networks, assets, APIs, and availability. |

Decision for the challenge path: use the managed GoPlausible facilitator at `https://facilitator.goplausible.xyz/` for Gate 3 through Gate 5.

Why managed GoPlausible is the right first choice:

- The challenge path requires or strongly aligns with GoPlausible facilitator tracking for public dashboard and leaderboard visibility.
- It is the fastest route to TestNet proof and later Mainnet proof without building payment-verification infrastructure first.
- It keeps the infrastructure burden low while AlgoPulse validates one safe paid report endpoint.
- It lets AlgoPulse focus on delayed market-intelligence product quality, redaction, logging, and abuse controls.
- It avoids forking payment verification, settlement, and replay logic before the official API and challenge tracking behavior are proven.

Gate 3 rules from this decision:

- Do not build a self-hosted facilitator for Gate 3.
- Do not fork payment verification logic.
- Do not hand-roll facilitator verify/settle behavior.
- Gate 3 must use managed GoPlausible facilitator APIs first.
- Self-hosted migration is a future/post-challenge option only, or a fallback if official challenge requirements change.

## GoPlausible TestNet Integration Path

The safest Gate 2 implementation path is a local or staging-only TestNet proof of concept that wraps the delayed market-pulse report behind GoPlausible's x402 flow.

Proposed shape:

- Keep the resource as delayed/redacted market intelligence only.
- Use a disposable Algorand TestNet payer account outside the repo.
- Use a public receiver address approved only for TestNet.
- Use the GoPlausible hosted facilitator URL: `https://facilitator.goplausible.xyz`.
- Use the official Algorand x402 packages rather than custom payment parsing:
  - TypeScript examples: `@x402-avm/*` or current official package names from GoPlausible docs.
  - Python examples: `x402-avm` with FastAPI-related extras if the repo stays Python/FastAPI.
- Keep `.env` local-only and never commit mnemonics, private keys, recovery words, receiver secrets, or payer credentials.

Package choice for Gate 3:

```powershell
pip install "x402-avm[fastapi,avm]"
```

The package installs as `x402-avm`, but the Python import namespace is `x402`.

## Official Package/API Verification

This verification was performed in a throwaway local install outside the repo. No wallet, mnemonic, private key, receiver value, network settlement, or payment exercise was used.

- Throwaway install command confirmed: `pip install "x402-avm[fastapi,avm]"`.
- Installed package version observed during Gate 2 prep: `x402-avm 2.0.2`.
- Import namespaces confirmed locally:
  - `x402`
  - `x402.http`
  - `x402.http.middleware.fastapi`
  - `x402.http.types`
  - `x402.mechanisms.avm.exact`
  - `x402.server`
- FastAPI/ASGI middleware entrypoint:
  - `x402.http.middleware.fastapi.PaymentMiddlewareASGI(app, routes, server, paywall_config=None, paywall_provider=None)`
- Payment requirement config objects:
  - `x402.http.PaymentOption(scheme, pay_to, price, network, max_timeout_seconds=None, extra=None)`
  - `x402.http.types.RouteConfig(accepts, resource=None, description=None, mime_type=None, custom_paywall_html=None, unpaid_response_body=None, extensions=None, hook_timeout_seconds=None)`
- Facilitator client config objects:
  - `x402.http.FacilitatorConfig(url="https://x402.org/facilitator", timeout=30.0, http_client=None, auth_provider=None, identifier=None)`
  - `x402.http.HTTPFacilitatorClient(config=None)`
- AVM server scheme/resource-server objects:
  - `x402.mechanisms.avm.exact.ExactAvmServerScheme()`
  - `x402.server.x402ResourceServer(facilitator_clients=None)`
- Header constants observed:
  - `X_PAYMENT_HEADER`
  - `PAYMENT_REQUIRED_HEADER`
  - `PAYMENT_RESPONSE_HEADER`
  - `PAYMENT_SIGNATURE_HEADER`
- Header values observed:
  - `X_PAYMENT_HEADER = "X-PAYMENT"`
  - `PAYMENT_SIGNATURE_HEADER = "PAYMENT-SIGNATURE"`
  - `PAYMENT_REQUIRED_HEADER = "PAYMENT-REQUIRED"`
  - `PAYMENT_RESPONSE_HEADER = "PAYMENT-RESPONSE"`
- Verified Python/FastAPI retry header:
  - `PAYMENT-SIGNATURE`
- Verified unpaid FastAPI harness behavior:
  - An unpaid request returns HTTP `402`.
  - The response includes `PAYMENT-REQUIRED`.
  - A fake `X-PAYMENT` header returns HTTP `402`; it does not unlock the route.
  - A fake `PAYMENT-SIGNATURE` header returns HTTP `402`; invalid payment proof fails closed.
  - A `$0.01` TestNet USDC price is converted into `amount: "10000"` base units.
  - The facilitator-supported requirement includes `feePayer`, `genesisHash`, and `genesisId` in `extra`.
- Verified payment object/payload boundary:
  - `decode_payment_signature_header(...)` base64-decodes the header into a `PaymentPayload` or `PaymentPayloadV1`.
  - The v2 `PaymentPayload` fields are `x402Version`, `payload`, `accepted`, optional `resource`, and optional `extensions`.
  - For the AVM exact mechanism, the inner `payload` is an `ExactAvmPayload` dictionary with `paymentGroup` and `paymentIndex`.
  - `paymentGroup` is a list of base64-encoded msgpack Algorand transactions; `paymentIndex` identifies which transaction pays the resource server.
  - The resource server verifies with `server.verify_payment(payment_payload, matching_requirements)`.
  - After the protected handler returns a non-error response, settlement uses `server.settle_payment(payment_payload, payment_requirements)`.
  - The facilitator client sends `payload.model_dump(by_alias=True, exclude_none=True)` and `requirements.model_dump(by_alias=True, exclude_none=True)` to `/verify` and `/settle`.
  - The HTTP body sent to the facilitator is `{ "x402Version": version, "paymentPayload": payload_dict, "paymentRequirements": requirements_dict }`.
  - `PaymentRequirements` fields are `scheme`, `network`, `asset`, `amount`, `payTo`, `maxTimeoutSeconds`, and `extra`.

Gate 3 must treat `paymentGroup` as package-owned payment material. AlgoPulse should not parse, log, rewrite, or construct this payload by hand in the resource server. It should configure payment requirements and let the official x402 package/client/facilitator path produce, verify, simulate, settle, and report the payment result.

Gate 3 must explicitly configure the GoPlausible facilitator URL instead of relying on the package default facilitator URL. The FastAPI harness showed route validation fails closed if facilitator-supported kinds are not available to the resource server. The package API findings above were gathered by installing and introspecting the package in a temporary local environment only; no payment, network settlement, wallet, signer, mnemonic, private key, or receiver value was used.

## Algorand Agent Skills Implementation Guidance

Use `algorand-devrel/algorand-agent-skills` as implementation guidance for Gate 3, not as authorization to implement or run real payments.

Confirmed useful guidance:

- The repository is a canonical collection of skills for AI-assisted Algorand development.
- It includes `algorand-x402-python` and `algorand-x402-typescript` skills.
- The Python x402 package path is `pip install "x402-avm[fastapi,avm]"`.
- The Python distribution name is `x402-avm`, but the import root is `x402`.
- The Python skill covers FastAPI server middleware, HTTP clients, facilitators, Bazaar discovery, and the `x402-avm` package.
- The TypeScript skill lists `@x402/core`, `@x402/avm`, `@x402/fetch`, `@x402/axios`, `@x402/express`, `@x402/hono`, and `@x402/next`.
- The TypeScript skill says protocol-boundary serialization occurs at the `PAYMENT-SIGNATURE` header.
- The canonical setup guidance describes x402 as componentized across client, resource server, and facilitator.
- The public managed facilitator URL remains `https://facilitator.goplausible.xyz`.

Gate 3 handling:

- Prefer the Python `algorand-x402-python` / FastAPI path because AlgoPulse is currently a Python/FastAPI service.
- Use `algorand-x402-typescript` only if a TypeScript sidecar, browser client, or agent client becomes necessary.
- Use `PAYMENT-SIGNATURE` for the verified Python/FastAPI retry header.
- Do not import signer, wallet, trading, or execution modules while following these skills.
- Do not add self-hosted facilitator work; use managed GoPlausible first.
- Do not run real TestNet payment, Mainnet payment, deploy, or eligibility work until Rob approves the Gate 3 blocker.

## Gate 3 Implementation Inputs

Use these as the current Gate 3 implementation inputs after Rob approval:

| Input | Current value |
|---|---|
| Python install | `pip install "x402-avm[fastapi,avm]"` |
| Distribution / import root | distribution `x402-avm`; import root `x402` |
| Middleware | `x402.http.middleware.fastapi.PaymentMiddlewareASGI` |
| Resource server | `x402.server.x402ResourceServer` |
| AVM server scheme | `x402.mechanisms.avm.exact.ExactAvmServerScheme` |
| Facilitator client | `x402.http.HTTPFacilitatorClient(FacilitatorConfig(url="https://facilitator.goplausible.xyz"))` |
| Protected route | `GET /api/x402/reports/market-pulse/daily` |
| Retry header | `PAYMENT-SIGNATURE` |
| Payment requirement header | `PAYMENT-REQUIRED` |
| Payment response header | `PAYMENT-RESPONSE` |
| Payment payload | base64-encoded `PaymentPayload`; AVM exact inner payload includes `paymentGroup` and `paymentIndex` |
| Facilitator verify/settle body | `{ x402Version, paymentPayload, paymentRequirements }` posted to `/verify` and `/settle` |
| TestNet network | `algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=` |
| TestNet asset | USDC Testnet, ASA `10458941`, decimals `6` |
| TestNet USDC price conversion | `$0.01` produces `amount: "10000"` |
| Facilitator-filled requirement fields | `feePayer`, `genesisHash`, `genesisId` under `extra` |
| Managed facilitator | `https://facilitator.goplausible.xyz` |

## Gate 3 Approval Checklist

These remain blockers before any Gate 3 implementation or real TestNet exercise:

- [ ] Rob approves managed GoPlausible as the Gate 3 facilitator path.
- [ ] Rob approves Algorand TestNet USDC as the Gate 3 payment asset.
- [ ] Rob approves receiver/payment assumptions before any real TestNet payment.
- [ ] Rob approves a real TestNet wallet/payment exercise and the operator-owned wallet workflow.
- [ ] Rob approves no-secret handling: no committed `.env`, mnemonic, private key, wallet export, recovery words, payment payloads, or screenshots/logs containing secrets.
- [ ] Gate 3 uses the official package middleware and client flow; no hand-rolled header parsing or payment payload creation.
- [ ] Gate 3 tests prove no signer, wallet custody, transaction submission by AlgoPulse, live trading, or fresh executable route data is touched.
- [ ] Hosted staging, Mainnet, Cloudflare deployment, public eligibility claims, and challenge submission remain later human gates.

Primary FastAPI integration approach:

- Use the official `x402-avm[fastapi,avm]` package.
- Configure a single `GET /api/x402/reports/market-pulse/daily` route with an Algorand TestNet USDC payment requirement.
- Use the GoPlausible hosted facilitator URL.
- Let the official middleware/resource-server path handle `402`, the package-defined retry header, `paymentGroup` verification/simulation/settlement, and paid retry semantics.
- Keep the existing handler body responsible only for returning the delayed/redacted report.

Fallback sidecar approach if direct FastAPI integration is unstable:

- Keep AlgoPulse unchanged except for a local-only internal report endpoint that returns delayed/redacted JSON.
- Run a small separate FastAPI resource-server sidecar using `x402-avm[fastapi,avm]`.
- The sidecar gates the public x402 route and calls the internal delayed-report endpoint only after facilitator approval.
- The sidecar must not receive signer access, route execution controls, wallet custody, or live trading permissions.

## Supported Networks And Assets

GoPlausible's live `/supported` endpoint lists exact-scheme x402 v2 support for:

- Algorand Mainnet
- Algorand Testnet
- Base Mainnet
- Base Sepolia
- Solana Mainnet
- Solana Devnet

The live `/discovery/paymentmethods` response lists these Algorand payment assets:

| Network | CAIP-style network | Asset | Asset ID | Decimals |
|---|---|---|---:|---:|
| Algorand Testnet | `algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=` | USDC (Testnet) | `10458941` | 6 |
| Algorand Mainnet | `algorand:wGHE2Pwdvd7S12BL5FaOP20EGYesN73ktiC1qzkkit8=` | USDC | `31566704` | 6 |

PNET ASA `3169177585` does not appear in the current GoPlausible payment-method discovery response. The Official Rules also describe leaderboard volume as USDC processed through the submitted endpoint.

Conclusion: PNET remains a broader ProfitNet/AlgoPulse story and may remain useful for internal/reference payment experiments, but the official challenge path currently appears to require USDC through GoPlausible unless the facilitator/rules explicitly add or approve PNET.

## Required TestNet Configuration

Gate 3 may introduce placeholder-only config names. Values must live in local `.env` or the operator shell and must never be committed.

| Name | Required for | Example placeholder | Secret? | Notes |
|---|---|---|---|---|
| `ALGOPULSE_X402_MODE` | Resource-server guard | `testnet` | No | Must fail closed unless set to a reviewed TestNet mode. |
| `ALGOPULSE_X402_TESTNET_ENABLED` | Local readiness guard | `false` | No | Gate 3 code and smoke scripts must fail closed unless this is explicitly enabled. |
| `ALGOPULSE_X402_TESTNET_CONFIG_CONFIRMED` | Local readiness guard | `false` | No | The no-network env check refuses real-looking values unless this is explicitly `true`. |
| `ALGOPULSE_X402_FACILITATOR_URL` | Facilitator client | `https://facilitator.goplausible.xyz` | No | Public URL, but keep configurable. |
| `ALGOPULSE_X402_NETWORK` | Payment requirement | `algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=` | No | Algorand TestNet network string from GoPlausible discovery. |
| `ALGOPULSE_X402_ASSET_ID` | Payment requirement | `10458941` | No | Algorand TestNet USDC from GoPlausible discovery. |
| `ALGOPULSE_X402_ASSET_SYMBOL` | Operator readability | `USDC` | No | Human-readable asset label; code should validate by asset ID/network, not symbol alone. |
| `ALGOPULSE_X402_ASSET_DECIMALS` | Amount conversion | `6` | No | USDC uses 6 decimals. |
| `ALGOPULSE_X402_AMOUNT` | Payment requirement | `$0.01` | No | The verified package path converts `$0.01` TestNet USDC to `amount: "10000"` base units. |
| `ALGOPULSE_X402_RECEIVER` | Payment destination | `TESTNET_RECEIVER_ADDRESS_PLACEHOLDER` | Public but approval-gated | Receiver must be Rob-approved before any real TestNet payment. |
| `ALGOPULSE_X402_RESOURCE` | Logs/idempotency | `algopulse.market_pulse.daily.v0` | No | Must remain scoped to delayed report access. |
| `ALGOPULSE_X402_PAYER_MNEMONIC` | Local TestNet client smoke only | `DO_NOT_COMMIT_OPERATOR_TESTNET_ONLY` | Yes | Only if the official client smoke needs it; never print, log, or commit. |

No-secret handling:

- Do not commit `.env`, mnemonics, private keys, recovery words, wallet exports, API tokens, or TestNet payer credentials.
- Do not paste secrets into PR comments, CI logs, screenshots, docs, or smoke output.
- The resource server should log only non-secret payment metadata such as request ID, resource ID, network, asset ID, amount, status code, and facilitator decision.
- If the official client requires a mnemonic for local TestNet payment, the operator enters it locally and owns the wallet risk.

Gate 3 local readiness check:

```powershell
python scripts/x402_gate3_env_check.py
```

The env check is intentionally non-executing. It does not connect to the network, import signer/wallet modules, submit payments, or print configured values. It only reports whether expected variable names are missing, placeholder-like, or set. It fails closed when values look real but `ALGOPULSE_X402_TESTNET_CONFIG_CONFIRMED=true` is not present.

## Resource-Server Changes Needed

Gate 3 should adapt the existing delayed market-pulse endpoint shape without touching execution systems.

Target resource:

```text
GET /api/x402/reports/market-pulse/daily
```

Required changes for a TestNet POC:

- Replace the mock proof header boundary with official x402 payment middleware or a small wrapper using the official resource-server APIs.
- Configure one accepted payment requirement for Algorand TestNet USDC.
- Point facilitator verification/settlement to GoPlausible.
- Keep the protected handler returning only delayed/redacted report JSON.
- Preserve response safety flags such as `publicSafe=true`, `liveExecutionTouched=false`, and `signerCodeTouched=false`.
- Add local-only config validation that fails closed if TestNet receiver/payment settings are missing.
- Ensure the resource server never logs official retry header payloads or `paymentGroup` contents in full.

Exact Gate 3 implementation sequence:

1. Add dependency on `x402-avm[fastapi,avm]` only after Rob approves Gate 3 code work.
2. Add an isolated x402 config loader with placeholder env var names above.
3. Keep `scripts/x402_gate3_env_check.py` as the first local guard before any TestNet run.
4. Create a `PaymentMiddlewareASGI` wrapper or sidecar route that protects only `GET /api/x402/reports/market-pulse/daily`.
5. Build a `PaymentOption` for Algorand TestNet USDC and a `RouteConfig` for `algopulse.market_pulse.daily.v0`.
6. Instantiate `HTTPFacilitatorClient(FacilitatorConfig(url="https://facilitator.goplausible.xyz", ...))`.
7. Instantiate `x402ResourceServer(...)` with the GoPlausible facilitator client and AVM exact scheme path required by the package.
8. Preserve the existing delayed report handler and redaction checks.
9. Add tests for unpaid `402`, facilitator-approved `200`, bad payment rejection, no unsafe report fields, and no calls into signer/execution modules.
10. Add a local TestNet smoke script that uses official client tooling and redacts sensitive payment payload details from output.
11. Keep the PR local/TestNet-only until Rob approves any hosted staging or Mainnet step.

Must not change:

- signer code
- wallet custody
- transaction signing
- transaction submission by AlgoPulse
- live trading
- route execution controls
- fresh executable route payloads
- Mainnet configuration
- Cloudflare/deployment settings

## Client And Payment Retry Flow

The official TestNet tutorial uses a disposable payer mnemonic for local development. That is acceptable for a throwaway local TestNet tutorial, but not for committed repo config.

Gate 3 should keep client payment handling outside the production market engine:

- Local TestNet payer setup is operator-owned and `.env`-only.
- No mnemonic or private key is committed, printed, or copied into docs as a real value.
- The client first confirms unpaid `402`.
- The client then uses official x402 client tooling to sign/pay/retry.
- The server returns `200` only after facilitator verification and settlement.
- The smoke evidence records status codes, transaction identifiers, and redacted resource output, but never records private key material.

Local TestNet smoke plan:

1. Start the local API with `ALGOPULSE_X402_MODE=testnet` and approved placeholder-free TestNet config.
2. Request `GET /api/x402/reports/market-pulse/daily` without payment and expect HTTP `402`.
3. Use the official x402 client path to construct/sign the TestNet `paymentGroup` and retry with the package-defined payment proof header.
4. Expect HTTP `200` only after facilitator verify, simulation, settlement request, and settlement success.
5. Assert the body contains `publicSafe=true`, `liveExecutionTouched=false`, `signerCodeTouched=false`, and no raw route legs or execution artifacts.
6. Retry any duplicate payment/proof path supported by the official middleware and record replay/idempotency behavior.

## Logging, Replay, Rate Limits, And Abuse Controls

Minimum Gate 3 controls:

- Log request ID, resource ID, status code, network, amount, asset ID, and facilitator outcome.
- Do not log full payment payloads, mnemonics, private keys, seed phrases, or user wallet secrets.
- Keep paid report output redacted and delayed.
- Add rate limits for unpaid requests and failed payment attempts before any public endpoint.
- Add replay/duplicate-payment evidence based on facilitator response and any local idempotency key the official middleware exposes.
- Add an allowlist for the one resource ID during TestNet POC.
- Add operator-visible smoke output for `402 -> paid retry -> 200`.

Replay and idempotency plan:

- Treat the facilitator decision as authoritative for settlement status.
- Record local request ID, resource ID, payment ID or transaction identifier if exposed by the official SDK, and facilitator result.
- Do not grant report access for ambiguous, pending, failed, or malformed facilitator responses.
- Add a local idempotency guard if the official package exposes a stable payment identifier.
- If duplicate payment handling is fully delegated to the facilitator, document the observed behavior and do not overclaim local replay protection.

Rate-limit and abuse-control plan:

- Rate-limit unpaid `402` requests per client/IP/session before any public endpoint.
- Rate-limit failed payment retries separately from successful paid access.
- Cap report generation frequency and prefer cached/delayed report reads.
- Emit abuse counters without logging secrets or full payment payloads.
- Block any request that asks for fresh executable routes, signer status beyond coarse safety flags, trading actions, or transaction construction.

Mainnet must also add:

- durable logs/evidence retention
- abuse monitoring
- public-safe terms for paid access
- receiver approval
- incident/rollback steps
- confirmation that leaderboard tracking sees the endpoint

## Leaderboard And Volume Tracking Assumptions

Working assumptions to verify before Mainnet:

- Only GoPlausible-facilitated payments count for the public dashboard.
- Challenge volume appears to be USDC-based.
- A bare PNET tx-id proof flow will not satisfy leaderboard tracking unless the challenge/facilitator explicitly supports it.
- Artificial volume, wash activity, repeated self-payments, or leaderboard manipulation are disallowed and would put the project at risk.
- The top-20 leaderboard prize pool is subject to review and verification by the Administrator, so raw volume alone is not enough if the activity is inauthentic or inconsistent with the rules.
- Selection for the final presentation also requires submitted project information; leaderboard position by itself is not a complete submission package.

## Challenge Win Formula

The challenge-page framing can be mapped to AlgoPulse only through a safe paid-data endpoint:

1. Ship a paid x402 endpoint on Algorand Mainnet.
2. Verify and settle payments through the managed GoPlausible facilitator.
3. Ensure activity is tracked on the public leaderboard where supported by the official facilitator flow.
4. Generate real on-chain usage from legitimate testers or users.
5. Submit project details that explain what payment unlocks and who is paying for it.
6. Use top-50 leaderboard status as finalist consideration only; it is not a guaranteed finalist or prize claim.
7. Prepare for 10 finalist spots and possible live presentation at Devcon 8 India if selected and officially notified.

Safe AlgoPulse translation:

- Payment unlocks delayed/redacted market-pulse reports or verification summaries.
- Payment does not unlock live trading, fresh executable routes, signer/wallet access, transaction submission, or trading signals.
- Usage must come from real report demand, not artificial volume or repeated self-payment loops.

## Agent Commerce Flow For AlgoPulse

The safe agent-commerce flow is:

```text
Agent requests delayed market-pulse report or verification summary
        -> server responds with HTTP 402 + price/payment requirements
        -> agent pays via official x402 facilitator flow on Algorand
        -> facilitator verifies and settles payment
        -> server returns delayed/redacted report data
        -> on-chain/payment evidence is tracked where supported
```

Explicit exclusions:

- no live trading
- no fresh executable route
- no signer or wallet access
- no transaction submission by AlgoPulse
- no pay-for-live-trading-signal framing
- no artificial usage, wash payments, repeated self-payments, or leaderboard manipulation

## Proof Of Who Is Paying

Future submission evidence should prove legitimate usage without collecting or exposing unnecessary private data:

- Record legitimate tester/user identity category, such as `developer tester`, `Algorand community tester`, `AI-agent integration tester`, or `market-research workflow`.
- Record wallet/payment evidence only as public transaction/settlement identifiers, network, asset ID, amount, resource ID, request ID, status code, and facilitator outcome.
- Avoid storing private personal data unless required by the official submission flow and approved by Rob.
- Never store or publish wallet secrets, mnemonics, private keys, recovery words, or full payment payloads.
- Avoid self-payment loops, wash activity, repeated self-payments, artificial traffic, or any usage whose main purpose is leaderboard manipulation.
- Keep redacted evidence packets that show what the payment unlocked without exposing private user data or unsafe market-engine internals.

## AgentRAG / ContextVend Positioning

`AgentRAG` and `ContextVend` are optional positioning labels for the same safe product idea: a pay-per-query premium data and verification API for autonomous AI agents, developers, analysts, and market-research workflows.

The positioning should stay anchored to x402's strongest fit for AlgoPulse:

| Use-case category | AlgoPulse position | Handling |
|---|---|---|
| Charge for data/API access | Primary use case | Paid access unlocks delayed market-pulse reports, connector-health summaries, liquidity-health summaries, or redacted evidence-backed scan exports. |
| Charge for verification/audit summaries | Secondary use case | Paid access may unlock explanations of stale quotes, unsafe/rejected route candidates, connector failures, liquidity warnings, or report confidence signals. |
| Charge for actions | Not allowed | Do not sell live trading signals, fresh executable arbitrage routes, signer access, wallet custody, transaction construction, transaction submission, ROI claims, or profit claims. |

What the endpoint sells:

- delayed market-pulse reports
- evidence-backed summaries
- connector health snapshots
- liquidity health checks
- stale/unsafe-route explanations
- redacted report exports suitable for AI-agent context

What it does not sell:

- live trading signals
- trade execution
- fresh executable arbitrage routes
- signer or wallet access
- custody, signing, or transaction submission
- ROI, profit, revenue, prize, or investment claims

## Legitimate Usage Plan

Gate 3 through Gate 5 should aim for useful, auditable paid report usage, not leaderboard gaming:

1. Publish a safe sample or free preview report that shows the delayed/redacted output shape before asking anyone to pay.
2. Create a simple demo flow where a user or AI agent requests the report, receives HTTP `402`, pays through the official x402/GoPlausible path, and receives delayed report data.
3. Recruit real testers or users from developer, Algorand, AI-agent, and market-research communities.
4. Offer useful delayed reports and verification summaries, not fake traffic or throwaway paid calls.
5. Track real paid access events without exposing private data: request IDs, resource IDs, status codes, facilitator outcomes, settlement identifiers if exposed, and redacted response hashes.
6. Cap and review automated agent usage so tests, demos, and evaluation traffic remain legitimate and explainable.
7. Do not self-pay repeatedly to inflate volume.
8. Do not create wash payments, artificial leaderboard activity, repeated self-payment loops, or any usage whose main purpose is metric manipulation.

## AI Acceleration Plan

AI can make the challenge package faster and better, but it cannot replace human gates:

- AI may help generate report summaries, docs, tests, demo scripts, MCP/tool schema drafts, support replies, analytics summaries, and submission materials.
- AI may run QA checklists and compare docs against official rules, challenge criteria, and safety boundaries.
- AI may help compare logs and produce redacted evidence packets for Rob review.
- AI must not bypass human approval for receiver/payment asset choice, wallet/payment exercise, Mainnet work, deployment, compliance wording, public claims, usage-generation strategy, or submission materials.

## Gate 2 QA Checklist

Gate 2 ready-for-review checklist:

- [x] No challenge eligibility claim.
- [x] No guaranteed prize, revenue, usage, volume, or leaderboard outcome claim.
- [x] No "pay for live trading signal" framing.
- [x] No artificial volume, wash-payment, repeated self-payment, or leaderboard-manipulation language.
- [x] Proof-of-payer planning avoids private doxxing and records only approved/public-safe evidence.
- [x] No signer, wallet, trading, execution, transaction-submission, or fresh-route coupling.
- [x] USDC, GoPlausible, and Mainnet requirements remain clear for the official challenge path.
- [x] PNET remains a broader ProfitNet/AlgoPulse story unless official GoPlausible/facilitator support is proven for challenge tracking.
- [x] Algorand Agent Skills are cited as implementation guidance only, not as permission to implement or run payments.
- [x] Gate 3 blockers remain explicit: Rob approval is required for the TestNet facilitator/payment asset path, receiver/payment assumptions, and any real TestNet wallet/payment exercise.

## Rules-Grounded Competition Constraints

These constraints come from the Official Rules and should shape all Gate 3 through Gate 5 work:

| Area | Constraint | AlgoPulse handling |
|---|---|---|
| Eligibility | Entrant must be at least 18 or age of majority, legally able to participate, not excluded by sanctions/export-control restrictions, and able to provide requested identity/status documents. | Rob/team must confirm eligibility before registration or public eligibility claims. |
| Team/project limits | Each participant may be on only one team; each team may submit only one project. | Do not submit multiple variants of the same endpoint or duplicate AlgoPulse/PNET entries. |
| Mainnet requirement | The submitted project needs a paid x402 endpoint deployed and reachable on Algorand Mainnet using GoPlausible tracking. | Gate 2 and Gate 3 are not eligibility; Gate 4 is the first possible eligibility candidate after approval. |
| Volume scoring | Volume is based on USDC processed through the submitted x402 endpoint. | Treat TestNet and PNET work as prep/reference unless GoPlausible/rules confirm otherwise. |
| Use case quality | x402 should be meaningfully integrated into the core payment flow, not bolted on as a secondary feature. | The paid endpoint should unlock delayed/redacted market intelligence that has standalone value. |
| Sustained potential | Judges may consider whether the endpoint could continue after the competition. | Keep the endpoint useful beyond the contest: report access, verification, and safe API monetization. |
| Innovation | Judges may consider novel, thoughtful, or technically meaningful x402 usage. | Emphasize safe market-intelligence access, redaction discipline, and non-custodial settlement. |
| Content restrictions | Content must be English, lawful, non-malicious, non-infringing, and not harmful/offensive/discriminatory. | Submission docs and report samples need a final content review. |
| Data confidentiality | Project/profile information is not treated as confidential except personal data handled under the rules/privacy policy. | Do not submit private trading logic, secrets, signer details, wallet material, or sensitive operational data. |
| Awards/taxes | Awards are discretionary, subject to due diligence/compliance review, and winners are responsible for taxes/reporting. | Public copy must not imply guaranteed awards, compensation, yield, ROI, or investment value. |
| Third-party services | GoPlausible/facilitator/dashboard data are third-party services provided as-is/as-available under the rules. | Keep independent logs/evidence and do not rely solely on the dashboard for operational truth. |

This section is not legal advice. It is a technical planning summary so the repo does not drift into unsafe, ineligible, or overclaimed challenge work.

## Challenge Pitch Guardrails

Allowed challenge framing:

- A delayed/redacted market-pulse report endpoint that uses official x402 payment gating.
- Report/data access only.
- No custody, no signer changes, no transaction submission by AlgoPulse, no live trading, no fresh executable route disclosure.
- Real user demand should come from useful reports, not artificial volume.

Forbidden challenge framing:

- Guaranteed prizes, revenue, profit, ROI, yield, token upside, or investment value.
- Pay-to-trade, pay-to-receive live arbitrage routes, pay-to-trigger execution, or pay-to-access signer/wallet state.
- Claims that TestNet, mock, or PNET tx-id-only work satisfies official challenge tracking.
- Any suggestion that Algorand Foundation, judges, or sponsors endorse AlgoPulse, PNET, or any token.

## Gate Table

| Gate | Name | Pass condition | Stop condition |
|---:|---|---|---|
| 1 | Safe Mock Report | Merged mock/TestNet delayed report endpoint with tests and smoke. | Signer, wallet, live trading, transaction submission, Mainnet, or fresh routes are touched. |
| 2 | GoPlausible TestNet POC Plan | Docs identify the verified package path, FastAPI path, TestNet USDC asset, retry header, payment payload boundary, env vars, tests, and approval blockers. | Safety boundary is unclear or docs imply Gate 3/4 eligibility before approval. |
| 3 | GoPlausible TestNet Implementation | Local/staging TestNet `402 -> official payment proof retry -> 200` works with official facilitator verify/simulate/settle flow and no secret commits. | Real credentials leak, endpoint returns unsafe data, implementation diverges from the verified header/payload behavior, or payment flow cannot be verified. |
| 4 | Mainnet Minimal Endpoint | One delayed/redacted paid endpoint is reachable on Algorand Mainnet through GoPlausible; dashboard tracking verified; abuse controls active. | No durable abuse controls, unclear receiver/payment asset, or compliance wording unresolved. |
| 5 | Real Usage / Submission Package | Legitimate paid usage evidence, conservative project info, screenshots/logs, whitepaper section, no artificial volume, no trading/profit claims. | Artificial volume, overclaiming eligibility, missing evidence, or financial/investment framing. |

## Deadline Calendar

| Date | Deadline | Internal target |
|---|---|---|
| August 15, 2026 | Internal safe-entry package complete | All docs, demo evidence, TestNet proof, safety review, and submission draft ready for Rob review. |
| September 1, 2026 11:45 PM EST | Challenge registration closes | Register only if eligibility, endpoint scope, and public wording are approved. |
| September 29, 2026 11:45 PM EST | Final project information due | Submit only if Mainnet GoPlausible tracking and evidence are complete. |
| September 30, 2026 11:45 PM EST through October 8, 2026 11:45 PM EST | Final presentation shortlist window | Monitor finalist eligibility only if the project is top-50 eligible and project information was submitted. |
| October 9, 2026 | Selected participants notified by email | Watch for notification; do not announce finalist status before official notice. |
| November 2, 2026 | Final presentation | Present only conservative architecture, real evidence, and safety boundaries. The challenge page says Devcon 8 India; the Official Rules PDF says time/place to be announced. |
| No later than November 12, 2026 | Winners announced | Do not imply any award, guarantee, endorsement, or compensation before official announcement and required acceptance/due-diligence steps. |

## Submission Package Checklist

- One-sentence public-safe description of paid delayed report access.
- Protected endpoint URL.
- Payment asset/network/amount evidence.
- GoPlausible dashboard tracking evidence.
- `402 -> official payment proof retry -> 200` screenshots or terminal logs.
- Report output sample showing delayed/redacted data only.
- Replay/idempotency and abuse-control notes.
- Evidence that the endpoint has real, legitimate users or testers and is not generating artificial volume.
- Project information required by the finalist process, prepared in English and reviewed for content restrictions.
- Confirmation that only one team/project is being submitted.
- Reminder that submitted project/profile information should not be treated as confidential.
- Whitepaper section: `x402 Pay-Per-Request Market Intelligence`.
- No investment, ROI, guaranteed-profit, live arbitrage, or trading-signal claims.
- No evidence generated by artificial volume, wash/self-payment loops, or leaderboard manipulation.

## Exact Blockers Before Mainnet

- Rob must confirm challenge eligibility, team/submission constraints, tax/compliance considerations, and deadline calendar.
- Rob must approve the resource, receiver address, payment asset, amount, and public wording.
- Current GoPlausible discovery supports Algorand USDC for the official path. PNET would require new official facilitator/rules proof before use for challenge tracking.
- Gate 3 must use the verified Python/FastAPI `PAYMENT-SIGNATURE` retry header and official package payment-payload flow; do not add `X-PAYMENT` handling unless the official package path later requires it.
- Gate 3 must prove the TestNet facilitator flow against the delayed market-pulse endpoint.
- Abuse controls, rate limits, logging, and evidence capture must be reviewed.
- Gate 4 must include independent logs/evidence because facilitator/dashboard services are third-party and provided as-is/as-available under the rules.
- Gate 5 must include real usage evidence and project information sufficient for the top-50/finalist review process.
- Public copy must avoid ROI, guaranteed profit, live arbitrage, investment, or trading-signal claims.
- Mainnet deployment must be separately approved and isolated from trading/signer systems.

## Human Approval Gates

Rob approval is required before:

- merging this Gate 2 PR if it changes beyond docs/README
- any Gate 3 implementation code
- any TestNet real payment using a real wallet or mnemonic
- any receiver/payment asset choice
- any Mainnet work
- any deploy
- any public/challenge eligibility claim
- any challenge registration or finalist project-information submission
- any use of team member profile information or externally published project materials
- any submission or public announcement

## Gate 3 Implementation Prep Checklist

Gate 3 is still blocked until Rob approves the items in `Gate 3 Approval Checklist`. After that approval, the implementation PR should stay local/TestNet-only and follow this checklist:

1. Use the verified `x402-avm[fastapi,avm]` package path, import root `x402`, and observed package version `2.0.2` unless a later package update is intentionally reviewed.
2. Use the verified `PAYMENT-SIGNATURE` retry header and official `PaymentPayload` / AVM `paymentGroup` flow.
3. Add placeholder-only TestNet configuration using the names in `Required TestNet Configuration`.
4. Add a fail-closed config loader that refuses missing, placeholder, Mainnet, or unconfirmed values.
5. Protect only `GET /api/x402/reports/market-pulse/daily`.
6. Configure only Algorand TestNet USDC unless Rob approves a different facilitator-supported asset.
7. Route verification and settlement through the official GoPlausible/facilitator package APIs.
8. Preserve the existing delayed/redacted report handler and safety flags.
9. Add unit tests for unpaid `402`, approved/facilitator-mocked `200`, invalid payment `402`, unsafe-field redaction, and no signer/execution calls.
10. Add a local-only smoke script for `402 -> official paid retry -> 200` that redacts payment payload details and prints no secrets.
11. Record evidence fields only after success: status codes, resource ID, request ID, network, asset ID, amount, facilitator result, transaction/settlement identifier if exposed, and redacted response hash.
12. Do not build a self-hosted facilitator, fork payment verification logic, or hand-roll facilitator settlement.
13. Keep the PR out of Mainnet, deployment, Cloudflare, public eligibility claims, and live trading systems.

Likely files touched in Gate 3:

- `src/algopulse/api.py` for the isolated report-access route wiring only.
- A new config helper under `src/algopulse/` if needed for x402 TestNet settings.
- `tests/test_x402_market_intelligence_access.py` or a new focused x402 TestNet test file using mocks.
- `scripts/x402_gate3_env_check.py` for no-network readiness checks if not already present.
- A new local-only x402 smoke script if Rob approves a real TestNet exercise.
- This planning doc and API/test matrix docs if behavior changes.

Files and areas forbidden to touch in Gate 3:

- `src/algopulse/signer.py`
- wallet custody, mnemonic, private-key, or transaction-signing modules
- route execution, trade execution, arbitrage routing, or transaction-submission modules
- fresh executable route payloads or route-leg response schemas
- Mainnet config, production deploy config, Cloudflare deploy config, or public challenge-submission files
- any `.env`, credential, wallet export, seed phrase, private key, API token, or real receiver value

TestNet-only env var handling:

- Use only placeholder names from `Required TestNet Configuration`.
- Keep real values in the operator shell or local untracked `.env` only.
- Never commit, print, screenshot, or paste real wallet, mnemonic, receiver, or payer values.
- Treat receiver addresses as public but still approval-gated.
- Fail closed unless `ALGOPULSE_X402_TESTNET_ENABLED=true` and `ALGOPULSE_X402_TESTNET_CONFIG_CONFIRMED=true` are both explicitly set by the operator.

Local smoke acceptance criteria:

- Unpaid request to `GET /api/x402/reports/market-pulse/daily` returns HTTP `402` with official `paymentRequirements`.
- Paid retry uses the official package/client flow and package-defined header, not hand-rolled parsing.
- Facilitator verification, simulation, and settlement complete successfully before any HTTP `200`.
- Invalid payment, failed simulation, failed verification, failed settlement, malformed header, or unsupported asset returns HTTP `402`.
- Paid response is delayed/redacted and contains no raw route legs, signer fields, execution artifacts, private wallet data, or fresh executable routes.
- Smoke output records only public/non-secret evidence and redacted response hashes.

Rollback and abort conditions:

- Abort immediately if any implementation requires signer access, wallet custody, transaction submission by AlgoPulse, live trading, fresh route disclosure, Mainnet, Cloudflare deploy, or committed secrets.
- Abort if a later package version changes the verified API/header/payload behavior or the implementation cannot reproduce the documented `PAYMENT-SIGNATURE` / `PaymentPayload` flow.
- Abort if GoPlausible discovery does not support the selected TestNet asset/network.
- Abort if the report response exposes actionable live route data, raw execution artifacts, or wallet/signer details.
- Roll back Gate 3 by disabling the TestNet mode flag and reverting the isolated x402 wiring PR; Gate 1 mock report access can remain as the safe local fallback.

## Whitepaper Delta

Add or update a future section titled `x402 Pay-Per-Request Market Intelligence`.

Safe wording:

> AlgoPulse can offer delayed market intelligence reports through an HTTP 402-style access layer. For official challenge readiness, the payment path must use the GoPlausible facilitator on Algorand, likely with USDC unless facilitator support for another asset is confirmed. Payments unlock report/data access only. The system does not custody funds, sign transactions for users, submit trading transactions, expose live executable routes, or guarantee trading outcomes.

## x402 Challenge Delta

`x402 update recommended: map the official win formula to safe agent-paid delayed data/verification access, with real usage and leaderboard tracking, while keeping live trading/signing/execution blocked.`
