"""
AlgoPool — Weekly Prize Draw on Algorand
=========================================

Fee split per 1 ALGO entry:
  90%  → winner prize pool (held in contract)
   5%  → LP accumulation  (held in contract, admin deploys to DEX)
   5%  → AlgoFlow platform wallet (sent immediately via inner txn)

Winner selection — fully autonomous, zero admin involvement:
  1. Admin calls announce_draw(block_num), locking entries and pre-committing
     a future block whose seed determines the winner.
  2. After that block is confirmed, ANYONE calls settle().
     Contract reads op.Block.blk_seed(draw_block), computes:
       winner_idx = btoi(extract(seed, 0, 8)) mod entry_count
     and pays the winner via inner transaction automatically.
  3. Admin calls new_week() to reset for next epoch.

Trust model:
  - Winner selection: trustless (on-chain block VRF, no admin)
  - Prize payment: trustless (smart contract inner txn)
  - Fee routing: trustless (5% platform sent immediately on entry)
  - LP deployment: admin-controlled (transparent; any node can audit balance)
  - draw_block announcement: admin (public, pre-committed on-chain before close)

Entry storage: BoxMap (prefix "e") — box key = b"e" + itob(idx), value = address
Box MBR per entry ≈ 0.019 ALGO — deployer funds contract upfront.

ARC-28 events emitted: EntryMade, DrawAnnounced, PrizePaid, LpDeployed.

Source code: https://github.com/WildlifeProtectionSolutions/algoflow-contracts
"""

import algopy
from algopy import (
    ARC4Contract,
    BoxMap,
    GlobalState,
    Txn,
    Global,
    UInt64,
    arc4,
    gtxn,
    itxn,
    op,
)

# Compile-time constants (plain Python ints — converted to UInt64 in AVM exprs)
ENTRY_AMOUNT  = 1_000_000   # 1 ALGO
PRIZE_BPS     = 9_000       # 90% to winner
LP_BPS        = 500         # 5%  to LP pool
PLATFORM_BPS  = 500         # 5%  to platform
MIN_DRAW_GAP  = 50          # draw block must be ≥ 50 rounds ahead

PHASE_OPEN      = 0
PHASE_ANNOUNCED = 1
PHASE_SETTLED   = 2


# ── ARC-28 events ─────────────────────────────────────────────────────────────

class EntryMade(arc4.Struct):
    entrant:  arc4.Address
    idx:      arc4.UInt64
    week:     arc4.UInt64


class DrawAnnounced(arc4.Struct):
    draw_block:  arc4.UInt64
    entry_count: arc4.UInt64


class PrizePaid(arc4.Struct):
    winner:     arc4.Address
    amount:     arc4.UInt64
    winner_idx: arc4.UInt64
    draw_block: arc4.UInt64   # query block(draw_block).seed on any node to reproduce


class LpDeployed(arc4.Struct):
    destination: arc4.Address
    amount:      arc4.UInt64


# ── Contract ──────────────────────────────────────────────────────────────────

class AlgoPool(ARC4Contract):
    """AlgoPool weekly prize draw. Deploy once; runs indefinitely."""

    def __init__(self) -> None:
        self.admin           = GlobalState(algopy.Account, key=b"admin")
        self.platform_wallet = GlobalState(algopy.Account, key=b"platform")
        self.current_week    = GlobalState(UInt64, key=b"week")
        self.entry_count     = GlobalState(UInt64, key=b"count")
        self.prize_pool      = GlobalState(UInt64, key=b"prize")    # 90% accumulated
        self.lp_balance      = GlobalState(UInt64, key=b"lp")       # 5%  accumulated
        self.draw_block      = GlobalState(UInt64, key=b"draw")
        self.phase           = GlobalState(UInt64, key=b"phase")
        self.total_paid      = GlobalState(UInt64, key=b"paid")
        # BoxMap: key_prefix "e", key type UInt64, value type arc4.Address
        self.entries = BoxMap(UInt64, arc4.Address, key_prefix=b"e")

    # ── Create ────────────────────────────────────────────────────────────────

    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def create(self, platform: algopy.Account) -> None:
        """
        Deploy the contract.  Caller becomes admin.
        platform: AlgoFlow wallet receiving the 5% platform cut on each entry.

        Fund the app address with ALGO for box MBR before entries open.
        Rule of thumb: 0.019 ALGO per expected entry + 0.1 ALGO min balance.
        """
        self.admin.value           = Txn.sender
        self.platform_wallet.value = platform
        self.current_week.value    = UInt64(0)
        self.entry_count.value     = UInt64(0)
        self.prize_pool.value      = UInt64(0)
        self.lp_balance.value      = UInt64(0)
        self.draw_block.value      = UInt64(0)
        self.phase.value           = UInt64(PHASE_OPEN)
        self.total_paid.value      = UInt64(0)

    # ── Entry ─────────────────────────────────────────────────────────────────

    @arc4.abimethod
    def enter(self, payment: gtxn.PaymentTransaction) -> UInt64:
        """
        Enter the weekly draw with exactly 1 ALGO.
        Returns the entry index assigned to the caller.

        90% → prize_pool (in contract)
         5% → lp_balance (in contract)
         5% → platform   (inner txn, immediate)
        """
        assert self.phase.value == UInt64(PHASE_OPEN), "Draw announced — entries closed"
        assert payment.receiver == Global.current_application_address, "Payment must go to contract"
        assert payment.amount == UInt64(ENTRY_AMOUNT), "Entry costs exactly 1 ALGO"
        assert payment.close_remainder_to == algopy.Account(), "No close_remainder_to"
        assert payment.rekey_to == algopy.Account(), "No rekeying"
        assert payment.fee <= UInt64(1_000), "Fee too high"

        total        = payment.amount
        platform_cut = total * UInt64(PLATFORM_BPS) // UInt64(10_000)
        lp_cut       = total * UInt64(LP_BPS)        // UInt64(10_000)
        prize_cut    = total - platform_cut - lp_cut

        itxn.Payment(
            receiver=self.platform_wallet.value,
            amount=platform_cut,
            fee=UInt64(0),
            note=b"AlgoPool 5% platform fee",
        ).submit()

        self.lp_balance.value = self.lp_balance.value + lp_cut
        self.prize_pool.value = self.prize_pool.value + prize_cut

        idx = self.entry_count.value
        self.entries[idx] = arc4.Address(Txn.sender)
        self.entry_count.value = idx + UInt64(1)

        arc4.emit(EntryMade(
            entrant=arc4.Address(Txn.sender),
            idx=arc4.UInt64(idx),
            week=arc4.UInt64(self.current_week.value),
        ))

        return idx

    # ── Draw management ───────────────────────────────────────────────────────

    @arc4.abimethod
    def announce_draw(self, draw_block: UInt64) -> None:
        """
        Admin pre-commits to a future block for randomness.
        Once called: no new entries accepted, draw block is public on-chain.

        Block must be ≥ MIN_DRAW_GAP rounds ahead — ensures entrants cannot
        see or predict the block seed at entry time (Algorand VRF output is
        unpredictable until the block is produced).
        """
        assert Txn.sender == self.admin.value, "Admin only"
        assert self.phase.value == UInt64(PHASE_OPEN), "Draw already announced"
        assert self.entry_count.value >= UInt64(1), "No entries yet"
        assert draw_block >= Global.round + UInt64(MIN_DRAW_GAP), "Draw block too soon"

        self.draw_block.value = draw_block
        self.phase.value      = UInt64(PHASE_ANNOUNCED)

        arc4.emit(DrawAnnounced(
            draw_block=arc4.UInt64(draw_block),
            entry_count=arc4.UInt64(self.entry_count.value),
        ))

    @arc4.abimethod
    def settle(self) -> arc4.Address:
        """
        Resolve the draw using Algorand on-chain block randomness.
        Callable by ANYONE after the draw block is confirmed — fully trustless.

        Verification (reproducible on any Algorand node):
          seed       = block(draw_block).seed   [256-bit VRF output, public]
          winner_idx = btoi(extract(seed, 0, 8)) mod entry_count
          winner     = entries[winner_idx]

        Prize is sent automatically by inner transaction; admin cannot intercept.
        """
        assert self.phase.value == UInt64(PHASE_ANNOUNCED), "No draw pending"
        assert Global.round > self.draw_block.value, "Draw block not yet confirmed"

        # Algorand block VRF seed — deterministic, publicly verifiable
        seed = op.Block.blk_seed(self.draw_block.value)

        seed_int   = op.btoi(op.extract(seed, UInt64(0), UInt64(8)))
        winner_idx = seed_int % self.entry_count.value
        winner     = self.entries[winner_idx]

        prize = self.prize_pool.value
        assert prize > UInt64(0), "Empty prize pool"

        itxn.Payment(
            receiver=winner.native,
            amount=prize,
            fee=UInt64(0),
            note=b"AlgoPool weekly prize",
        ).submit()

        self.total_paid.value = self.total_paid.value + prize
        self.prize_pool.value = UInt64(0)
        self.phase.value      = UInt64(PHASE_SETTLED)

        arc4.emit(PrizePaid(
            winner=winner,
            amount=arc4.UInt64(prize),
            winner_idx=arc4.UInt64(winner_idx),
            draw_block=arc4.UInt64(self.draw_block.value),
        ))

        return winner

    @arc4.abimethod
    def new_week(self) -> UInt64:
        """
        Admin resets for the next weekly epoch.
        Deletes all entry boxes to reclaim box MBR.
        Returns the new week number.

        Note: if entry_count > ~700, split into multiple calls to stay
        within the 700 opcode budget per call.  Each box delete costs ~7 opcodes.
        """
        assert Txn.sender == self.admin.value, "Admin only"
        assert self.phase.value == UInt64(PHASE_SETTLED), "Settle draw first"

        count = self.entry_count.value
        i = UInt64(0)
        while i < count:
            del self.entries[i]
            i = i + UInt64(1)

        self.entry_count.value  = UInt64(0)
        self.draw_block.value   = UInt64(0)
        self.phase.value        = UInt64(PHASE_OPEN)
        self.current_week.value = self.current_week.value + UInt64(1)

        return self.current_week.value

    # ── LP management ─────────────────────────────────────────────────────────

    @arc4.abimethod
    def deploy_lp(self, amount: UInt64, destination: algopy.Account) -> None:
        """
        Admin sends accumulated LP funds to a DEX pool or liquidity wallet.
        Funds deepen PNET/ALGO liquidity; balance is publicly auditable on-chain.
        """
        assert Txn.sender == self.admin.value, "Admin only"
        assert amount > UInt64(0), "Amount must be > 0"
        assert amount <= self.lp_balance.value, "Insufficient LP balance"

        itxn.Payment(
            receiver=destination,
            amount=amount,
            fee=UInt64(0),
            note=b"AlgoPool LP deployment",
        ).submit()

        self.lp_balance.value = self.lp_balance.value - amount

        arc4.emit(LpDeployed(
            destination=arc4.Address(destination),
            amount=arc4.UInt64(amount),
        ))

    # ── Admin ─────────────────────────────────────────────────────────────────

    @arc4.abimethod
    def transfer_admin(self, new_admin: algopy.Account) -> None:
        """Transfer admin rights — recommended to use a multisig."""
        assert Txn.sender == self.admin.value, "Admin only"
        self.admin.value = new_admin

    @arc4.abimethod
    def update_platform(self, new_platform: algopy.Account) -> None:
        """Update the platform wallet address."""
        assert Txn.sender == self.admin.value, "Admin only"
        self.platform_wallet.value = new_platform

    # ── Read-only ─────────────────────────────────────────────────────────────

    @arc4.abimethod(readonly=True)
    def get_state(self) -> arc4.Tuple[
        arc4.UInt64, arc4.UInt64, arc4.UInt64,
        arc4.UInt64, arc4.UInt64, arc4.UInt64,
    ]:
        """Returns: (current_week, entry_count, prize_pool, lp_balance, draw_block, phase)"""
        return arc4.Tuple((
            arc4.UInt64(self.current_week.value),
            arc4.UInt64(self.entry_count.value),
            arc4.UInt64(self.prize_pool.value),
            arc4.UInt64(self.lp_balance.value),
            arc4.UInt64(self.draw_block.value),
            arc4.UInt64(self.phase.value),
        ))

    @arc4.abimethod(readonly=True)
    def get_entry(self, idx: UInt64) -> arc4.Address:
        """Returns the entrant address at the given index."""
        assert idx < self.entry_count.value, "Index out of range"
        return self.entries[idx]
