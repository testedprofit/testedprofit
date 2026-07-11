# PNET Fee Flow

PNET fees buy market-data actions. They do not deposit funds into the bot, do not authorize trading, and do not guarantee returns.

## Pera Wallet User Flow

1. User connects Pera Wallet.
2. Frontend sends wallet, network, and requested action to the backend.
3. Backend checks address presence, network, PNET opt-in state, and PNET balance.
4. User requests a fee quote for a scan, route simulation, delayed report, credit, or pool monitoring request.
5. Frontend builds the PNET payment or app-call intent from the backend response.
6. User signs with Pera using the user's wallet only.
7. Frontend submits the signed transaction.
8. Backend verifies the txid on-chain.
9. Backend grants the scan, report, simulation, monitoring request, or credit.
10. Backend records a receipt.

## Fee Quote Flow

Fee quote responses must include:

- `feeQuoteId`
- action
- wallet
- network
- PNET ASA ID
- fee amount in display units
- fee amount in raw atomic units
- receiver
- note prefix
- expiration
- access-check result
- disclaimer that this is market data only

The quote must not include a signer mnemonic, platform private key, hot-wallet secret, or live execution instruction.

## Tx Verification Flow

The backend verifier must check:

- txid exists on the configured Algorand network
- sender matches the requesting wallet when expected
- receiver matches the platform fee receiver
- asset ID matches PNET
- amount is at least the quoted fee
- note prefix matches the issued fee quote
- transaction is confirmed
- transaction is not rekeyed or closed out when those checks are enabled

Failed verification must not unlock credits or reports. It should create a reviewable failure or refund case when appropriate.

## Credit / Report Unlock Flow

After verification:

- record receipt
- grant requested credits or report access
- record the action unlocked
- preserve txid, quote id, wallet, amount, network, and timestamp
- show delayed route intelligence or report output only
- never expose fresh executable route data to public users

## Non-Admin Restrictions

Non-admin users may:

- request market intelligence
- request spread scans
- request route simulations
- request liquidity monitoring
- view delayed route reports
- view public-safe receipts

Non-admin users may not:

- call admin endpoints
- arm live execution
- clear the kill switch
- approve route hashes
- change allowlists
- submit execution instructions
- access platform wallet controls
- provide funds for the bot to trade

## Required Language

Every PNET fee surface must make this clear:

- PNET fees are for market data, scans, simulations, reports, monitoring, or credits.
- PNET fees are not user deposits.
- AlgoPulse does not trade user funds.
- No result is guaranteed.
- Route intelligence can be stale, delayed, rejected, or unprofitable after fees.
- Future live execution, if enabled, is tiny platform-only execution behind the execution-control gates.
