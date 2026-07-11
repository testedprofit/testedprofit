# Repo Adoption Red Flags

Do not clone, run, fund, or deploy a Web3 trading repo that asks for any of these patterns:

- `secret.json` containing signer secrets or a wallet recovery phrase
- signer secrets or a wallet recovery phrase inside `config.py`
- committed `.env` files containing wallet material
- wallet keys in frontend code or browser environment variables
- unlimited asset routing
- no app ID allowlist
- no max daily loss
- no kill switch
- no paper-trading history

## Operator Response

Treat any one of these as a stop sign. Do not connect a wallet, do not add funds, do not run its execution path, and do not let an AI agent wire it into this project. If the code has useful ideas, copy concepts only after a manual review and rebuild them inside AlgoPulse's read-only-first architecture.
