# xChain Accounts Learning Track

Status: Learning and product-access research only. This track is not part of the Phase 0 scanner, quote, route, paper-trading, risk, dry-run, signer, or execution pipeline.

## Purpose

AlgoPulse / PNET may eventually want EVM-wallet users to access paid market-intelligence products without forcing new wallet onboarding. xChain Accounts are worth studying because they map EVM wallet signatures to native Algorand account authorization through Smart Signature Accounts.

This document only defines what to learn, what might become useful, and what remains blocked. It does not approve implementation.

## Confirmed Concepts From Current Sources

- xChain EVM is described as experimental in its docs and the GitHub repository describes xChain Accounts as beta.
- An EVM address can map deterministically to an Algorand Smart Signature Account / LogicSig address.
- The user signs EIP-712 typed data with an EVM wallet such as MetaMask.
- The Algorand-side Smart Account verifies the ECDSA signature on-chain using Algorand ECDSA recovery support.
- EIP-712 domain isolation helps prevent a signature intended for one application or protocol from being replayed as another authorization.
- The signature is tied to a specific transaction ID or group ID, so any transaction-field change invalidates the signature.
- Current xChain examples include sending, receiving, asset management, bridging, and dApp interaction, but AlgoPulse is not adopting these behaviors during Phase 0.

## Why It Might Matter To AlgoPulse / PNET

Potential future product-access uses:

- Let EVM-wallet users authenticate for PNET-gated reports.
- Let users connect familiar wallets for account-linked dashboards.
- Support future paid report or API access flows, including possible x402-style paid access, without AlgoPulse holding keys.
- Reduce wallet-onboarding friction for market-intelligence users who are not already Algorand-wallet users.

This is about access and identity. It is not about live trading, custody, signer operations, or executable route access.

## Strict Boundaries

Do not use this track to add:

- signer changes
- AI-held keys
- wallet custody
- transaction submission by AlgoPulse
- bridge integration
- live trading
- fresh executable route access
- dependency on xChain for Phase 0 scanner, quote, route, risk, paper, or dry-run evidence

Any wallet, payment, signing, bridge, x402, account-linking, or public-claim behavior requires human review before implementation.

## Learning Milestones

1. Read the xChain overview, signing, security, integration, and repository docs.
2. Summarize the architecture in plain English.
3. Identify which parts are relevant to PNET report/API access and which parts are irrelevant to Phase 0 engine work.
4. Create a risk note covering custody, bridge, replay, account-linking, wallet UX, and user-confusion risks.
5. Decide whether xChain belongs in the whitepaper future-access section, an x402 challenge pitch, a Phase 1 onboarding backlog, or the parking lot.

## Risk Notes To Keep Current

- Custody confusion: Users may misunderstand an xChain Account as AlgoPulse custody. Product copy must say AlgoPulse does not hold wallet keys.
- Bridge risk: Bridging introduces third-party/protocol risks and must not be bundled into Phase 0.
- Replay and domain risk: EIP-712 and transaction/group ID binding reduce replay risk, but integration details need review.
- Account-linking risk: Linking EVM and Algorand identities can create privacy and support expectations.
- User-confusion risk: Users may not realize they are authorizing an Algorand account action from an EVM wallet.
- UI trust risk: The xChain security model still depends on users understanding what the dApp UI and wallet prompt show.

## Churn Output Rule

Every review or coding churn should include:

```text
### xChain Learning Delta

- No xChain update needed this churn.
```

Or:

```text
### xChain Learning Delta

- xChain learning update recommended: [specific concept/risk/use-case to document].
```

Or:

```text
### xChain Learning Delta

- xChain implementation not appropriate yet: [reason].
```

Do not let xChain exploration expand Phase 0 scope or touch signer, wallet custody, bridge, transaction submission, live execution, or route-execution code.

## Source Notes

- xChain EVM overview: https://xchain.algorand.co/docs/what-is-algo-x-evm
- xChain EVM security model: https://xchain.algorand.co/docs/security
- xChain EVM signing transactions: https://xchain.algorand.co/docs/signing-transactions
- xChain Accounts repository: https://github.com/algorandfoundation/xchain-accounts
- Algorand xChain Accounts technical blog: https://algorand.co/blog/smartsignatureaccounts
- EIP-712: https://eips.ethereum.org/EIPS/eip-712
