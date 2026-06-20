# AlgoFlow Smart Contracts

Algorand Python (Puya) smart contracts for AlgoFlow — published for public review.

## Contracts

### AlgoPool — Weekly Prize Draw

**Source:** [`algo_pool/contract.py`](algo_pool/contract.py)  
**Compiled TEAL:** [`artifacts/algo_pool/`](artifacts/algo_pool/)

Fee split per 1 ALGO entry:
- **90%** → winner prize pool (held in contract)
- **5%** → PNET/ALGO liquidity accumulation (held in contract)
- **5%** → AlgoFlow platform (sent immediately via inner txn)

**Winner selection is fully trustless:**
1. Admin calls `announce_draw(block_num)` — pre-commits a future block on-chain
2. After that block is confirmed, **anyone** can call `settle()`
3. Contract reads `block(draw_block).seed` (Algorand VRF output) and computes:
   ```
   winner_idx = btoi(extract(seed, 0, 8)) mod entry_count
   ```
4. Winner is paid automatically via inner transaction — admin cannot intercept

The block seed is public and verifiable on any Algorand node or explorer.

### PROFITLOCK Vaults — Time-Lock Vaults

**Source:** [`profit_lock/contract.py`](profit_lock/contract.py)  
**Compiled TEAL:** [`artifacts/profit_lock/`](artifacts/profit_lock/)

Lock ALGO or any ASA (e.g. PNET) for 30/90/180/365 days. Principal returned automatically at maturity.

- Only the depositing wallet can unlock
- Admin **cannot** bypass individual vault locks
- Pause blocks new deposits but **never** blocks unlocks (user funds always safe)
- Box storage: each vault is an on-chain box — transparent and auditable

## Compiling

Requirements: Python 3.12+, AlgoKit 2+

```powershell
# Windows
.\compile_contracts.ps1

# Or manually
python -m venv .venv
.venv\Scripts\pip install algorand-python==3.5.0 puyapy
.venv\Scripts\puyapy algo_pool/contract.py --out-dir artifacts/algo_pool/
.venv\Scripts\puyapy profit_lock/contract.py --out-dir artifacts/profit_lock/
```

## Deploying

```powershell
$env:DEPLOYER_MNEMONIC = "word1 word2 ... word25"
python -m contracts.algo_pool.deploy testnet
python -m contracts.profit_lock.deploy testnet
```

## Security Review

These contracts have been reviewed against the Algorand smart contract security checklist:

- ✅ `Txn.sender` checks on all admin methods
- ✅ `close_remainder_to` / `asset_close_to` pinned to zero on all user deposits
- ✅ Inner transaction fees set to 0 (sponsored by outer transaction)
- ✅ Block randomness committed before entry close (MIN_DRAW_GAP = 50 rounds)
- ✅ `settle()` callable by anyone — no admin gatekeeping on winner selection
- ✅ Emergency pause blocks new deposits, **never** blocks unlocks
- ✅ Box MBR reclaimed on unlock/weekly reset
- ✅ ARC-28 events emitted for all state changes (indexer subscriptions)
- ✅ ARC-4 ABI compliant method signatures

Found an issue? Open a GitHub issue or contact rob.serrano@wildlifeprotectionsolutions.org
