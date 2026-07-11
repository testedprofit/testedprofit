# Contribution Protocol Beta

Purpose: define how PNET contribution credits can unlock useful beta access without turning credits into token rewards, investment returns, binding governance, treasury control, or trading permission.

## Current Status

Status: local-review beta.

Implemented surfaces:

- `GET /api/contribution-protocol/catalog`
- `GET /api/contribution-protocol/session/{wallet}`
- `POST /api/contribution-protocol/submit`
- `POST /api/contribution-protocol/spend`
- Access-page dashboard for credit balance, activity history, contribution submission, and credit spending.
- Reference smart-contract blueprint: `contracts/pnet_credit_usage_reference.py`

Not implemented:

- on-chain credit app deployment
- Mainnet credit state
- token payouts
- staking/rewards/yield
- binding governance
- treasury movement
- transaction signing or submission by AlgoPulse
- live trading or fresh executable route access

## What PNET Credits Can Unlock

| Unlock | Category | Credit cost | Boundary |
| --- | --- | ---: | --- |
| Premium delayed market report | tool access | 2 | Unlocks delayed/redacted report access only. |
| Pair scan credit | tool access | 1 | Queues a delayed pair scan output. |
| Route simulation credit | premium feature | 3 | Paper-only route simulation/replay; no live execution. |
| Governance signal comment | governance signal | 1 | Non-binding proposal comment or priority signal only. |
| AlgoFlow tool preview | integration | 2 | Beta preview for compatible utility tooling, without signer/custody access. |

Credits do not unlock:

- vote buying
- token rewards
- yield, revenue share, or ROI
- treasury control
- production deploys
- signer access
- wallet custody
- transaction submission
- live trading
- fresh executable routes

## Contribution Submission Flow

1. User connects a local-review wallet session.
2. User chooses a contribution type:
   - docs improvement
   - PNET pool observation
   - bug or safety report
   - beta demo feedback
   - data-source suggestion
3. Backend records a `pending_review` contribution event.
4. No credits are automatically granted.
5. A human reviewer decides whether credits should be granted in a future approved workflow.

This keeps beta activity useful without creating automatic payout or governance risk.

## Credit Spend Flow

1. User selects a bounded unlock.
2. Backend checks local-review credit balance.
3. If balance is sufficient, backend records a spend receipt.
4. The receipt states that no live execution, signer, wallet custody, treasury, or binding governance action occurred.

Credit spend receipts are currently in-memory local-review records. They are not durable production accounting.

## AlgoFlow Integration Boundary

AlgoFlow can integrate later by consuming:

- contribution catalog
- contribution submission receipts
- credit-spend receipts
- bounded unlock status
- non-binding governance-signal receipts

AlgoFlow must not receive:

- mnemonics, private keys, seed phrases, or wallet exports
- signer access
- payment payloads or raw headers
- treasury controls
- live trading authority
- deployment authority
- fresh executable routes

## Frontend Dashboard

The Access page now includes:

- credit balance
- pending contribution count
- activity history
- contribution submission buttons
- credit spend buttons
- AlgoFlow integration boundary note

Guests can view the model, but submit/spend actions require a connected local-review wallet session.

## Validation Commands

```powershell
git diff --check
python scripts/repo_guard.py
node --check src/algopulse/static/app.js
python -m pytest tests/test_contribution_protocol.py -q
python -m pytest tests/test_utility_hub_static.py -q
python -m pytest -q
```

## Deployment Instructions

Local API/UI preview:

```powershell
uvicorn algopulse.api:app --host 127.0.0.1 --port 8769
```

Open:

```text
http://127.0.0.1:8769/?fresh=contribution-protocol-v1#access
```

On-chain deployment:

```text
Blocked.
```

Before any on-chain credit app deployment, require:

- TestNet-only implementation plan
- third-party or senior security review of the contract
- state schema review
- admin/manager approval
- abuse/freeze policy review
- no-secret handling review
- legal/public wording review
- explicit Rob approval

Mainnet deployment requires a separate approval gate after TestNet evidence.
