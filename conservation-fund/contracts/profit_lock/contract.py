"""
PROFITLOCK Vaults — Non-Custodial Time-Lock Vaults on Algorand
==============================================================

Users deposit any ASA (e.g. PNET) or native ALGO and lock it for a
fixed period.  Only the depositing wallet can unlock after maturity.
No admin bypass exists on individual vaults.

Lock periods (converted to approximate Algorand rounds at ~3.7 s/block):
  30 days  → 702 000 rounds
  90 days  → 2 106 000 rounds
  180 days → 4 212 000 rounds
  365 days → 8 541 000 rounds

Storage: BoxMap per vault — vault_id (uint64) → VaultRecord (ARC4 struct)
Box MBR ≈ 0.036 ALGO per vault — deployer funds contract upfront.

Security properties:
  - Only vault owner can call unlock()
  - Global.round >= unlock_round enforced by contract, not by admin
  - pause() blocks new deposits but NEVER blocks unlocks (user funds safe)
  - close_remainder_to / asset_close_to pinned to zero on all deposits
  - Inner transaction fees set to 0 (sponsored by outer transaction)
  - ARC-28 events for indexer subscriptions

Future yield:
  AlgoPool routes 5% LP from every prize pot.  A portion of that will
  distribute as yield to PNET vault holders in a future upgrade.

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
    subroutine,
)

# Rounds per day at ~3.7 s/block (conservative — slightly under true value)
ROUNDS_PER_DAY = 23_400


# ── Vault data ─────────────────────────────────────────────────────────────────

class VaultRecord(arc4.Struct):
    owner:        arc4.Address
    asset_id:     arc4.UInt64   # 0 = native ALGO
    amount:       arc4.UInt64
    unlock_round: arc4.UInt64
    lock_days:    arc4.UInt64
    created:      arc4.UInt64   # round vault was created
    claimed:      arc4.Bool


# ── ARC-28 events ──────────────────────────────────────────────────────────────

class VaultCreated(arc4.Struct):
    vault_id:     arc4.UInt64
    owner:        arc4.Address
    asset_id:     arc4.UInt64
    amount:       arc4.UInt64
    unlock_round: arc4.UInt64


class VaultUnlocked(arc4.Struct):
    vault_id: arc4.UInt64
    owner:    arc4.Address
    amount:   arc4.UInt64


# ── Contract ───────────────────────────────────────────────────────────────────

class ProfitLock(ARC4Contract):
    """
    PROFITLOCK Vaults — time-lock vaults.  Deploy once; supports unlimited vaults.
    """

    def __init__(self) -> None:
        self.admin       = GlobalState(algopy.Account, key=b"admin")
        self.vault_count = GlobalState(UInt64, key=b"count")
        self.paused      = GlobalState(bool, key=b"paused")
        # BoxMap: key_prefix "v", key type UInt64, value type VaultRecord
        self.vaults = BoxMap(UInt64, VaultRecord, key_prefix=b"v")

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def create(self) -> None:
        """Deploy.  Caller becomes admin."""
        self.admin.value       = Txn.sender
        self.vault_count.value = UInt64(0)
        self.paused.value      = False

    # ── Locking ───────────────────────────────────────────────────────────────

    @arc4.abimethod
    def lock_algo(
        self,
        payment: gtxn.PaymentTransaction,
        lock_days: arc4.UInt64,
    ) -> UInt64:
        """
        Lock native ALGO for a fixed period.

        payment:   PaymentTransaction sending ALGO to this contract.
        lock_days: 30, 90, 180, or 365.

        Returns vault_id.
        """
        assert not self.paused.value, "Contract paused"
        assert payment.receiver == Global.current_application_address, "Wrong receiver"
        assert payment.amount > UInt64(0), "Must lock > 0"
        assert payment.close_remainder_to == algopy.Account(), "No close_remainder_to"
        assert payment.rekey_to == algopy.Account(), "No rekeying"
        assert payment.fee <= UInt64(1_000), "Fee too high"

        days = lock_days.native
        assert self._valid_period(days), "lock_days must be 30, 90, 180, or 365"

        vault_id     = self.vault_count.value
        unlock_round = Global.round + days * UInt64(ROUNDS_PER_DAY)

        self.vaults[vault_id] = VaultRecord(
            owner=arc4.Address(Txn.sender),
            asset_id=arc4.UInt64(UInt64(0)),
            amount=arc4.UInt64(payment.amount),
            unlock_round=arc4.UInt64(unlock_round),
            lock_days=arc4.UInt64(days),
            created=arc4.UInt64(Global.round),
            claimed=arc4.Bool(False),
        )
        self.vault_count.value = vault_id + UInt64(1)

        arc4.emit(VaultCreated(
            vault_id=arc4.UInt64(vault_id),
            owner=arc4.Address(Txn.sender),
            asset_id=arc4.UInt64(UInt64(0)),
            amount=arc4.UInt64(payment.amount),
            unlock_round=arc4.UInt64(unlock_round),
        ))

        return vault_id

    @arc4.abimethod
    def lock_asa(
        self,
        deposit: gtxn.AssetTransferTransaction,
        lock_days: arc4.UInt64,
    ) -> UInt64:
        """
        Lock any ASA (e.g. PNET) for a fixed period.

        deposit:   AssetTransfer sending the ASA to this contract.
                   Contract must be opted into the ASA first (call opt_in_asset).
        lock_days: 30, 90, 180, or 365.

        Returns vault_id.
        """
        assert not self.paused.value, "Contract paused"
        assert deposit.asset_receiver == Global.current_application_address, "Wrong receiver"
        assert deposit.asset_amount > UInt64(0), "Must lock > 0"
        assert deposit.asset_close_to == algopy.Account(), "No asset_close_to"
        assert deposit.rekey_to == algopy.Account(), "No rekeying"
        assert deposit.fee <= UInt64(1_000), "Fee too high"
        assert deposit.sender == Txn.sender, "Deposit sender must match caller"

        days = lock_days.native
        assert self._valid_period(days), "lock_days must be 30, 90, 180, or 365"

        vault_id     = self.vault_count.value
        unlock_round = Global.round + days * UInt64(ROUNDS_PER_DAY)

        self.vaults[vault_id] = VaultRecord(
            owner=arc4.Address(Txn.sender),
            asset_id=arc4.UInt64(deposit.xfer_asset.id),
            amount=arc4.UInt64(deposit.asset_amount),
            unlock_round=arc4.UInt64(unlock_round),
            lock_days=arc4.UInt64(days),
            created=arc4.UInt64(Global.round),
            claimed=arc4.Bool(False),
        )
        self.vault_count.value = vault_id + UInt64(1)

        arc4.emit(VaultCreated(
            vault_id=arc4.UInt64(vault_id),
            owner=arc4.Address(Txn.sender),
            asset_id=arc4.UInt64(deposit.xfer_asset.id),
            amount=arc4.UInt64(deposit.asset_amount),
            unlock_round=arc4.UInt64(unlock_round),
        ))

        return vault_id

    # ── Unlock ─────────────────────────────────────────────────────────────────

    @arc4.abimethod
    def unlock(self, vault_id: UInt64) -> UInt64:
        """
        Unlock a matured vault and return the principal to the owner.

        Only the vault owner may call this.
        Reverts if the lock period has not elapsed.
        For ASA vaults: include the asset ID in the foreign assets array.

        Returns amount returned.
        """
        vault = self.vaults[vault_id].copy()

        assert arc4.Address(Txn.sender) == vault.owner, "Not vault owner"
        assert not vault.claimed.native, "Already claimed"
        assert Global.round >= vault.unlock_round.native, "Still locked"

        amount   = vault.amount.native
        asset_id = vault.asset_id.native

        # Mark claimed before sending (reentrancy guard)
        vault.claimed = arc4.Bool(True)
        self.vaults[vault_id] = vault.copy()

        if asset_id == UInt64(0):
            itxn.Payment(
                receiver=Txn.sender,
                amount=amount,
                fee=UInt64(0),
                note=b"ProfitLock unlock",
            ).submit()
        else:
            itxn.AssetTransfer(
                asset_receiver=Txn.sender,
                xfer_asset=algopy.Asset(asset_id),
                asset_amount=amount,
                fee=UInt64(0),
                note=b"ProfitLock unlock",
            ).submit()

        arc4.emit(VaultUnlocked(
            vault_id=arc4.UInt64(vault_id),
            owner=arc4.Address(Txn.sender),
            amount=arc4.UInt64(amount),
        ))

        # Delete box to reclaim MBR to contract
        del self.vaults[vault_id]

        return amount

    # ── Admin ──────────────────────────────────────────────────────────────────

    @arc4.abimethod
    def opt_in_asset(self, asset: algopy.Asset) -> None:
        """Opt the contract into an ASA so it can receive deposits."""
        assert Txn.sender == self.admin.value, "Admin only"
        itxn.AssetTransfer(
            asset_receiver=Global.current_application_address,
            xfer_asset=asset,
            asset_amount=UInt64(0),
            fee=UInt64(0),
        ).submit()

    @arc4.abimethod
    def set_paused(self, paused: bool) -> None:
        """
        Pause new deposits.
        DOES NOT affect unlock — users can always retrieve their principal.
        """
        assert Txn.sender == self.admin.value, "Admin only"
        self.paused.value = paused

    @arc4.abimethod
    def transfer_admin(self, new_admin: algopy.Account) -> None:
        """Transfer admin rights."""
        assert Txn.sender == self.admin.value, "Admin only"
        self.admin.value = new_admin

    # ── Read-only ──────────────────────────────────────────────────────────────

    @arc4.abimethod(readonly=True)
    def get_vault(self, vault_id: UInt64) -> VaultRecord:
        """Return full vault details.  Reverts if vault does not exist."""
        return self.vaults[vault_id].copy()

    @arc4.abimethod(readonly=True)
    def rounds_remaining(self, vault_id: UInt64) -> UInt64:
        """Rounds until the vault can be unlocked (0 if ready now)."""
        vault = self.vaults[vault_id].copy()
        unlock = vault.unlock_round.native
        if Global.round >= unlock:
            return UInt64(0)
        return unlock - Global.round

    # ── Helpers ────────────────────────────────────────────────────────────────

    @subroutine
    def _valid_period(self, days: UInt64) -> bool:
        return (
            days == UInt64(30)
            or days == UInt64(90)
            or days == UInt64(180)
            or days == UInt64(365)
        )
