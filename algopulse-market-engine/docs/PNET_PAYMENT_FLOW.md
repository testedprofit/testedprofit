# PNET Payment Flow

This flow is only for market-data fees, scan/report credits, delayed route intelligence, and route simulations. It does not accept deposits into the bot and does not grant control over platform execution.

## Sequence

1. User connects Pera.
2. Backend checks wallet address, network, PNET opt-in, and PNET balance with `POST /api/user/pnet/access-check`.
3. User requests a fee quote with `POST /api/user/pnet/fee-quote`.
4. Backend returns a PNET ASA transfer `paymentIntent`.
5. Frontend builds the PNET transfer or app-call flow from that intent.
6. User signs with Pera.
7. Frontend submits the transaction.
8. Frontend sends the txid to `POST /api/user/pnet/fee-confirm`.
9. Backend verifies the tx on-chain before granting production access.
10. Backend records a payment verification receipt.
11. User receives delayed route intelligence, a scan/report, or credits.

## Current Implementation

Local review supports mock txids like `mock-fq_...` so the UI can be tested without a wallet. Real-looking txids use the existing Algorand indexer verifier path and must match:

- PNET ASA id
- expected receiver
- expected sender
- quoted amount
- quote-specific note prefix
- minimum confirmations
- no rekey
- no close-out

## Red Lines

- The frontend never receives platform wallet keys.
- The AI agent never receives wallet keys.
- The payment flow does not submit bot trades.
- PNET fees are not user deposits into an arb wallet.
- A paid scan/report does not guarantee profit.
