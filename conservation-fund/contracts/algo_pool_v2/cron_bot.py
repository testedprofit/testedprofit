"""
AlgoPool v2 Cron Bot
====================
Automates the weekly draw cycle for AlgoPool v2.

Phase flow (permissionless — bot just calls public methods):
  OPEN (0)     → announce_draw()    (after open_duration blocks + min_entries met)
  ANNOUNCED(1) → compute_winner()   (after draw_block confirmed, within 1001 blocks)
  COMPUTED (2) → pay_winner()       (reads winner_idx from global state, passes box ref)
  SETTLED  (3) → cleanup(50)        (repeat until all boxes deleted, phase resets to OPEN)

The bot is not privileged — any wallet can call these same methods.
Bot just makes the cycle automatic so users don't have to.

Run:
  python cron_bot.py --network mainnet --loop --interval 60

Environment:
  $env:CALLER_MNEMONIC = "word1 word2 ... word25"
  (does not need to be admin — any wallet works for permissionless calls)
"""

import os
import sys
import time
import base64
import argparse
import logging

import algosdk
from algosdk.v2client import algod
from algosdk import transaction, abi as algoabi

# ── Config ────────────────────────────────────────────────────────────────────

APP_ID        = 3609625951
ALGOD_MAINNET = "https://mainnet-api.algonode.cloud"
ALGOD_TESTNET = "https://testnet-api.algonode.cloud"

PHASE_OPEN      = 0
PHASE_ANNOUNCED = 1
PHASE_COMPUTED  = 2
PHASE_SETTLED   = 3

CLEANUP_BATCH = 50  # boxes to delete per cleanup() call

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("algopool-v2-bot")


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_client(network: str) -> algod.AlgodClient:
    url = ALGOD_MAINNET if network == "mainnet" else ALGOD_TESTNET
    return algod.AlgodClient("", url)


def load_key(mnemonic: str):
    pk = algosdk.mnemonic.to_private_key(mnemonic)
    addr = algosdk.account.address_from_private_key(pk)
    return pk, addr


def read_global_state(client: algod.AlgodClient) -> dict:
    app = client.application_info(APP_ID)
    raw = {}
    for kv in app["params"].get("global-state", []):
        key = base64.b64decode(kv["key"]).decode("utf-8", errors="replace")
        val = kv["value"]
        if val["type"] == 1:
            raw[key] = base64.b64decode(val["bytes"])
        else:
            raw[key] = val.get("uint", 0)
    return raw


def send_app_call(
    client, private_key, sender, method_sig,
    args=(), fee=1000, boxes=None
):
    """Submit a single-transaction ABI app call."""
    selector = algoabi.Method.from_signature(method_sig).get_selector()
    sp = client.suggested_params()
    sp.fee, sp.flat_fee = fee, True

    txn = transaction.ApplicationCallTxn(
        sender=sender,
        sp=sp,
        index=APP_ID,
        on_complete=transaction.OnComplete.NoOpOC,
        app_args=[selector, *args],
        boxes=boxes or [],
    )
    signed = txn.sign(private_key)
    txid = client.send_transaction(signed)
    result = transaction.wait_for_confirmation(client, txid, 8)
    log.info("  confirmed: %s", txid)
    return result


def entry_box_key(idx: int) -> bytes:
    """Build the box key for entries[idx]: prefix 'e' + ABI uint64 (8 bytes big-endian)."""
    return b"e" + idx.to_bytes(8, "big")


# ── Draw cycle steps ──────────────────────────────────────────────────────────

def do_announce_draw(client, pk, sender):
    log.info("  announce_draw() — committing draw block")
    send_app_call(client, pk, sender, "announce_draw()uint64")


def do_compute_winner(client, pk, sender):
    log.info("  compute_winner() — reading block VRF seed")
    result = send_app_call(client, pk, sender, "compute_winner()uint64", fee=1000)
    # Parse the returned winner_idx from the ABI return value in the log
    # (we'll re-read global state rather than parse the log bytes)


def do_pay_winner(client, pk, sender, winner_idx: int):
    log.info("  pay_winner() — paying winner at entry index %d", winner_idx)
    box_key = entry_box_key(winner_idx)
    send_app_call(
        client, pk, sender,
        "pay_winner()address",
        fee=2000,
        boxes=[(APP_ID, box_key)],
    )


def do_cleanup(client, pk, sender) -> bool:
    """Delete one batch of 50 entry boxes. Returns True if cleanup is complete (phase=OPEN)."""
    log.info("  cleanup(%d) — deleting entry boxes", CLEANUP_BATCH)
    batch_arg = CLEANUP_BATCH.to_bytes(8, "big")
    result = send_app_call(
        client, pk, sender,
        "cleanup(uint64)bool",
        args=[batch_arg],
        fee=1000,
    )
    # ABI return value is in result["logs"] — True if all boxes cleared
    # Simpler: re-read phase from global state after the call
    return True  # caller will re-read state on next tick to confirm


# ── Main tick ─────────────────────────────────────────────────────────────────

def tick(client, pk, sender):
    state        = read_global_state(client)
    phase        = state.get("phase",    PHASE_OPEN)
    count        = state.get("count",    0)
    draw_block   = state.get("draw",     0)
    winner_idx   = state.get("win_idx",  0)
    open_rnd     = state.get("open_rnd", 0)
    open_dur     = state.get("open_dur", 0)
    min_entries  = state.get("min_e",    1)
    cursor       = state.get("cursor",   0)
    prize        = state.get("prize",    0)

    sp = client.suggested_params()
    current_block = sp.first

    log.info(
        "phase=%d  entries=%d  draw_block=%d  current=%d  winner_idx=%d  cursor=%d",
        phase, count, draw_block, current_block, winner_idx, cursor,
    )

    # ── OPEN: announce when conditions are met ─────────────────────────────
    if phase == PHASE_OPEN:
        if count < min_entries:
            log.info("  %d/%d entries — waiting for min_entries", count, min_entries)
            return

        unlock_at = open_rnd + open_dur
        if current_block < unlock_at:
            blocks_left = unlock_at - current_block
            secs_left   = blocks_left * 3.7
            log.info(
                "  %d entries ready, but open window not elapsed yet "
                "(%d blocks / ~%d min remaining)",
                count, blocks_left, int(secs_left // 60),
            )
            return

        log.info("  conditions met (%d entries, window elapsed) → announcing draw", count)
        do_announce_draw(client, pk, sender)

    # ── ANNOUNCED: compute winner once draw block is confirmed ─────────────
    elif phase == PHASE_ANNOUNCED:
        if current_block <= draw_block:
            blocks_left = draw_block - current_block + 1
            log.info("  waiting for draw block %d (%d blocks to go)", draw_block, blocks_left)
            return

        # Safety: if more than 900 blocks past draw_block, seed may expire soon
        blocks_since = current_block - draw_block
        if blocks_since > 1001:
            log.warning(
                "  draw block %d expired (%d blocks ago) — admin must call rescue_announce()",
                draw_block, blocks_since,
            )
            return

        if blocks_since > 900:
            log.warning(
                "  seed window closing soon (%d/1001 blocks) — calling compute_winner() now",
                blocks_since,
            )

        log.info("  draw block confirmed → computing winner")
        do_compute_winner(client, pk, sender)

    # ── COMPUTED: pay the winner (box reference required) ─────────────────
    elif phase == PHASE_COMPUTED:
        log.info("  winner index %d computed → paying prize of %d µA", winner_idx, prize)
        do_pay_winner(client, pk, sender, winner_idx)

    # ── SETTLED: paginated cleanup ─────────────────────────────────────────
    elif phase == PHASE_SETTLED:
        log.info("  prize paid → cleanup (cursor=%d, total=%d boxes)", cursor, count)
        do_cleanup(client, pk, sender)

    else:
        log.warning("  unknown phase %d — nothing to do", phase)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AlgoPool v2 draw automation bot")
    parser.add_argument("--network",  default="testnet", choices=["testnet", "mainnet"])
    parser.add_argument("--once",     action="store_true", help="Run one tick and exit")
    parser.add_argument("--loop",     action="store_true", help="Run in a loop")
    parser.add_argument("--interval", type=int, default=60,
                        help="Seconds between ticks in loop mode (default 60)")
    args = parser.parse_args()

    mnemonic = os.environ.get("CALLER_MNEMONIC", "").strip()
    if not mnemonic:
        log.error("Set $env:CALLER_MNEMONIC (any wallet works — calls are permissionless)")
        sys.exit(1)

    pk, sender = load_key(mnemonic)
    client     = get_client(args.network)

    if APP_ID == 0:
        log.error("Update APP_ID in cron_bot.py after deploying the v2 contract")
        sys.exit(1)

    log.info("AlgoPool v2 Bot  app=%d  network=%s  sender=%s", APP_ID, args.network, sender)

    if args.once or not args.loop:
        tick(client, pk, sender)
        return

    log.info("Loop mode — tick every %ds", args.interval)
    while True:
        try:
            tick(client, pk, sender)
        except Exception as exc:
            log.error("tick error: %s", exc, exc_info=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
