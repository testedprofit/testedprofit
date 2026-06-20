"""
AlgoPool Deployment Script
==========================

Usage:
  python -m contracts.algo_pool.deploy [--network testnet|mainnet]

Prerequisites:
  1. AlgoKit installed: pip install algokit
  2. Artifacts compiled:
     algokit compile python contracts/algo_pool/contract.py -o contracts/artifacts/algo_pool/
  3. Deployer mnemonic in environment:
     $env:DEPLOYER_MNEMONIC = "word1 word2 ... word25"

What this script does:
  1. Loads compiled approval + clear TEAL from artifacts/
  2. Creates the application on TestNet (or MainNet)
  3. Funds the contract with initial ALGO:
       - 0.1 ALGO min balance
       - + 0.1 ALGO buffer
       = ~0.2 ALGO minimum
     Add more for box MBR if you expect many entries (≈0.021 ALGO each)
  4. Calls create() to initialise global state
  5. Prints the App ID for use in the frontend
"""

import os
import sys
import base64
import json
from pathlib import Path

import algosdk
from algosdk.v2client import algod
from algosdk import transaction

ARTIFACTS_DIR = Path(__file__).parent.parent / "artifacts" / "algo_pool"
ALGOD_TESTNET = "https://testnet-api.algonode.cloud"
ALGOD_MAINNET = "https://mainnet-api.algonode.cloud"

PLATFORM_WALLET = "CIVTUU6KLTYO26SPVEBDFBKP3UMZM2DPEO5RINODUVCI5NVIFC6HVNWS7E"

# Funding: 0.1 ALGO base MBR + 0.5 ALGO box MBR buffer (covers ~24 entries)
INITIAL_FUND_MICROALGO = 600_000


def load_teal(name: str) -> bytes:
    """Read compiled TEAL and return bytecode (expects AlgoKit JSON output)."""
    # AlgoKit compile outputs a JSON with 'result' as base64 bytecode
    json_path = ARTIFACTS_DIR / f"{name}.arc32.json"
    if json_path.exists():
        arc32 = json.loads(json_path.read_text())
        src_b64 = arc32["source"]["approval"] if "approval" in name else arc32["source"]["clear"]
        return base64.b64decode(src_b64)

    # Fallback: raw .teal files compiled via algod
    teal_path = ARTIFACTS_DIR / f"{name}.teal"
    if teal_path.exists():
        return teal_path.read_bytes()

    raise FileNotFoundError(
        f"No compiled artifact found at {json_path} or {teal_path}\n"
        f"Run: algokit compile python contracts/algo_pool/contract.py -o contracts/artifacts/algo_pool/"
    )


def compile_teal(client: algod.AlgodClient, teal_source: bytes) -> bytes:
    """Compile TEAL source to bytecode via algod."""
    result = client.compile(teal_source.decode())
    return base64.b64decode(result["result"])


def deploy(network: str = "testnet") -> int:
    mnemonic = os.environ.get("DEPLOYER_MNEMONIC", "")
    if not mnemonic:
        print("Error: set DEPLOYER_MNEMONIC environment variable")
        sys.exit(1)

    private_key = algosdk.mnemonic.to_private_key(mnemonic)
    deployer    = algosdk.account.address_from_private_key(private_key)

    algod_url = ALGOD_MAINNET if network == "mainnet" else ALGOD_TESTNET
    client    = algod.AlgodClient("", algod_url)

    print(f"Deploying AlgoPool to {network}...")
    print(f"  Deployer: {deployer}")

    sp = client.suggested_params()
    sp.fee     = 1_000
    sp.flat_fee = True

    # Load approval and clear TEAL
    approval_arc32 = ARTIFACTS_DIR / "AlgoPool.arc32.json"
    if approval_arc32.exists():
        arc32 = json.loads(approval_arc32.read_text())
        approval_src = base64.b64decode(arc32["source"]["approval"])
        clear_src    = base64.b64decode(arc32["source"]["clear"])
        approval_b   = compile_teal(client, approval_src)
        clear_b      = compile_teal(client, clear_src)
    else:
        print(f"Artifacts not found in {ARTIFACTS_DIR}")
        print("Run: algokit compile python contracts/algo_pool/contract.py -o contracts/artifacts/algo_pool/")
        sys.exit(1)

    # Create application transaction
    # AlgoPool uses box storage — no local state needed
    create_txn = transaction.ApplicationCreateTxn(
        sender=deployer,
        sp=sp,
        on_complete=transaction.OnComplete.NoOpOC,
        approval_program=approval_b,
        clear_program=clear_b,
        global_schema=transaction.StateSchema(num_uints=8, num_byte_slices=1),
        local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
        extra_pages=1,  # AlgoPool approval program may exceed 2048 bytes
    )

    signed_create = create_txn.sign(private_key)
    txid = client.send_transaction(signed_create)
    print(f"  Create txn: {txid}")

    result = transaction.wait_for_confirmation(client, txid, 4)
    app_id = result["application-index"]
    app_addr = algosdk.logic.get_application_address(app_id)
    print(f"  App ID:      {app_id}")
    print(f"  App address: {app_addr}")

    # Fund the contract (min balance + box MBR buffer)
    fund_txn = transaction.PaymentTxn(
        sender=deployer,
        sp=sp,
        receiver=app_addr,
        amt=INITIAL_FUND_MICROALGO,
        note=b"AlgoPool initial funding",
    )
    signed_fund = fund_txn.sign(private_key)
    fund_txid   = client.send_transaction(signed_fund)
    transaction.wait_for_confirmation(client, fund_txid, 4)
    print(f"  Funded:      {INITIAL_FUND_MICROALGO / 1e6:.3f} ALGO")

    print()
    print(f"✓ AlgoPool deployed successfully!")
    print(f"  App ID: {app_id}")
    print()
    print("Next steps:")
    print(f"  1. Add ALGO_POOL_APP_ID={app_id} to your .env")
    print(f"  2. Fund more ALGO if you expect >24 entries (≈0.021 ALGO/entry for box MBR)")
    print(f"  3. Announce draws by calling announce_draw(block_num)")
    print(f"  4. Anyone can call settle() after the draw block is confirmed")

    return app_id


if __name__ == "__main__":
    network = sys.argv[1] if len(sys.argv) > 1 else "testnet"
    if network not in ("testnet", "mainnet"):
        print("Usage: python -m contracts.algo_pool.deploy [testnet|mainnet]")
        sys.exit(1)
    deploy(network)
