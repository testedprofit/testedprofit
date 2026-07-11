# Community Growth System

Purpose: define safe community growth features for PNET without creating pump mechanics, automatic payouts, yield promises, or binding governance.

## Current Status

Status: local-review beta.

Implemented surfaces:

- `GET /api/community-growth/overview/{wallet}`
- `POST /api/community-growth/referral`
- Access-page community dashboard
- Contribution Protocol categories for:
  - mining evidence receipt
  - bandwidth evidence receipt
  - verification report
- Contract blueprint additions for `record_referral` and `record_reputation_event`

## Referral System

Referrals are local-review receipts, not automatic rewards.

Allowed:

- record referral source/channel
- show a local referral code
- count reviewed referral receipts toward reputation
- manually review referral quality before any recognition

Blocked:

- automatic PNET payouts
- automatic credit grants
- referral yield
- paid referral loops
- fake/self-referral farming
- public claims about growth before evidence exists

## Contributor Leaderboard

Leaderboard rank is based on contribution and reputation activity, not token holdings or earnings amount.

Current categories:

- mining evidence
- bandwidth evidence
- verification
- community

Mining and bandwidth rows mean "submitted evidence for review." They do not mean verified income, guaranteed earnings, or profitability.

## Reputation System

Reputation is non-financial.

Signals:

- contribution submissions
- reviewed evidence receipts
- referral receipts
- credit-spend receipts

Badges:

- Observer
- Contributor
- Evidence Builder
- Community Connector
- Utility User

Reputation does not grant:

- token rewards
- yield
- treasury control
- binding governance
- trading access
- signer or wallet access

## Onboarding Flow

1. Read safety boundaries.
2. Inspect PNET utility.
3. Submit a contribution or evidence receipt.
4. Earn reputation through manual review and useful activity.

## Contract Blueprint Update

`contracts/pnet_credit_usage_reference.py` now includes:

- `record_referral(account, referral_hash, channel_hash)`
- `record_reputation_event(account, event_type, evidence_hash, score_delta)`

The contract remains blueprint-only and is not deployed.

## Abuse Controls Needed Before Production

- durable identity/wallet proof
- self-referral detection
- duplicate evidence detection
- review queue with audit trail
- rate limits
- report/appeal process
- public wording review
- legal/compliance review

## Validation

```powershell
git diff --check
python scripts/repo_guard.py
node --check src/algopulse/static/app.js
python -m pytest tests/test_contribution_protocol.py tests/test_utility_hub_static.py -q
python -m pytest -q
```
