"""
ProfitLock Deployment Script
=============================

Usage:
  python -m contracts.profit_lock.deploy [--network testnet|mainnet] [--opt-in-pnet]

Prerequisites:
  1. AlgoKit installed and artifacts compiled:
     algokit compile python contracts/profit_lock/contract.py -o contracts/artifacts/profit_lock/
  2. Deployer mnemonic in environment:
     $env:DEPLOYER_MNEMONIC = "word1 word2 ... word25"

What this script does:
  1. Creates the ProfitLock application
  2. Funds the contract (min balance + box MBR buffer)
  3. Optionally opts the contract into PNET (ASA 3169177585 on MainNet)
  4. Prints App ID for frontend integration

Box MBR per vault:
  key   = b"v" + 8 bytes = 9 bytes
  value = VaultRecord struct ≈ 80 bytes
  MBR   = 2500 + 400 * (9 + 80) = 38 100 µA ≈ 0.038 ALGO per vault
  The deployer funds an initial buffer; box MBR is reclaimed on unlock.
"""

import os
import sys
import base64
import json
from pathlib import Path

import algosdk
from algosdk.v2client import algod
from algosdk import transaction

ARTIFACTS_DIR = Path(__file__).parent.parent / "artifacts" / "profit_lock"
ALGOD_TESTNET = "https://testnet-api.algonode.cloud"
ALGOD_MAINNET = "https://mainnet-api.algonode.cloud"

PNET_ASSET_ID_MAINNET = 3169177585
PNET_ASSET_ID_TESTNET = 0  # set to your TestNet PNET clone if deploying on TestNet

# 0.1 ALGO min balance + 1 ALGO box MBR buffer (covers ~26 vaults)
INITIAL_FUND_MICROALGO = 1_100_000


def deploy(network: str = "testnet", opt_in_pnet: bool = True) -> int:
    mnemonic = os.environ.get("DEPLOYER_MNEMONIC", "")
    if not mnemonic:
        print("Error: set DEPLOYER_MNEMONIC environment variable")
        sys.exit(1)

    private_key = algosdk.mnemonic.to_private_key(mnemonic)
    deployer    = algosdk.account.address_from_private_key(private_key)

    algod_url = ALGOD_MAINNET if network == "mainnet" else ALGOD_TESTNET
    client    = algod.AlgodClient("", algod_url)

    print(f"Deploying ProfitLock to {network}...")
    print(f"  Deployer: {deployer}")

    sp = client.suggested_params()
    sp.fee     = 1_000
    sp.flat_fee = True

    approval_arc32 = ARTIFACTS_DIR / "ProfitLock.arc32.json"
    if not approval_arc32.exists():
        print(f"Artifacts not found in {ARTIFACTS_DIR}")
        print("Run: algokit compile python contracts/profit_lock/contract.py -o contracts/artifacts/profit_lock/")
        sys.exit(1)

    arc32       = json.loads(approval_arc32.read_text())
    approval_b  = base64.b64decode(arc32["source"]["approval"])
    clear_b     = base64.b64decode(arc32["source"]["clear"])

    # Compile via algod if sources aren't pre-compiled bytecode
    try:
        approval_b = base64.b64decode(client.compile(approval_b.decode())["result"])
        clear_b    = base64.b64decode(client.compile(clear_b.decode())["result"])
    except Exception:
        pass  # already bytecode

    create_txn = transaction.ApplicationCreateTxn(
        sender=deployer,
        sp=sp,
        on_complete=transaction.OnComplete.NoOpOC,
        approval_program=approval_b,
        clear_program=clear_b,
        global_schema=transaction.StateSchema(num_uints=2, num_byte_slices=1),
        local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
        extra_pages=1,
    )

    signed = create_txn.sign(private_key)
    txid   = client.send_transaction(signed)
    print(f"  Create txn: {txid}")

    result   = transaction.wait_for_confirmation(client, txid, 4)
    app_id   = result["application-index"]
    app_addr = algosdk.logic.get_application_address(app_id)
    print(f"  App ID:      {app_id}")
    print(f"  App address: {app_addr}")

    # Fund the contract
    fund_txn = transaction.PaymentTxn(
        sender=deployer, sp=sp,
        receiver=app_addr, amt=INITIAL_FUND_MICROALGO,
        note=b"ProfitLock initial funding",
    )
    txid = client.send_transaction(fund_txn.sign(private_key))
    transaction.wait_for_confirmation(client, txid, 4)
    print(f"  Funded:      {INITIAL_FUND_MICROALGO / 1e6:.3f} ALGO")

    # Opt into PNET so the contract can hold it
    if opt_in_pnet:
        pnet_id = PNET_ASSET_ID_MAINNET if network == "mainnet" else PNET_ASSET_ID_TESTNET
        if pnet_id > 0:
            # Call opt_in_asset(pnet_id) on the contract
            sp_optin = client.suggested_params()
            sp_optin.fee, sp_optin.flat_fee = 2_000, True  # covers inner txn fee
            optin_txn = transaction.ApplicationCallTxn(
                sender=deployer, sp=sp_optin,
                index=app_id,
                on_complete=transaction.OnComplete.NoOpOC,
                app_args=[algosdk.abi.Method.from_signature("opt_in_asset(asset)void").get_selector()],
                foreign_assets=[pnet_id],
            )
            txid = client.send_transaction(optin_txn.sign(private_key))
            transaction.wait_for_confirmation(client, txid, 4)
            print(f"  Opted into PNET ({pnet_id})")

    print()
    print(f"✓ ProfitLock deployed successfully!")
    print(f"  App ID: {app_id}")
    print()
    print("Next steps:")
    print(f"  1. Add PROFIT_LOCK_APP_ID={app_id} to your .env")
    print(f"  2. Users can now lock ALGO or ASA via lock_algo() / lock_asa()")
    print(f"  3. Unlock is permissionless after the lock period expires")

    return app_id


if __name__ == "__main__":
    network    = "testnet"
    opt_pnet   = True
    for arg in sys.argv[1:]:
        if arg in ("testnet", "mainnet"):
            network = arg
        elif arg == "--no-pnet":
            opt_pnet = False
    deploy(network, opt_pnet)
