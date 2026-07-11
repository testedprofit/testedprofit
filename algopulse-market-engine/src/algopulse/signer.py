from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from algosdk import account, constants, encoding, mnemonic as algo_mnemonic


ALGORAND_TX_GROUP_LIMIT = int(constants.TX_GROUP_LIMIT)
FORBIDDEN_REQUEST_FIELDS = {"instruction", "instructions", "command", "commands", "prompt", "tool", "action"}
MICROALGOS_PER_ALGO = 1_000_000


@dataclass(frozen=True)
class SignerPolicy:
    signer_enabled: bool = False
    kill_switch: bool = True
    wallet_address: str = ""
    wallet_mnemonic: str = ""
    allowed_route_hashes: tuple[str, ...] = ()
    allowed_app_ids: tuple[int, ...] = ()
    allowed_asset_ids: tuple[int, ...] = ()
    max_input_amount: float = 10.0
    max_group_fee_algos: float = 0.05
    min_wallet_reserve_algos: float = 0.2
    allowed_txn_types: tuple[str, ...] = ("pay", "axfer", "appl")
    max_tx_group_size: int = ALGORAND_TX_GROUP_LIMIT


@dataclass(frozen=True)
class SignerRequest:
    route_hash: str
    unsigned_transactions: tuple[Any, ...]
    expected_app_ids: tuple[int, ...]
    expected_asset_ids: tuple[int, ...]
    input_asset_id: int
    input_amount: float
    wallet_balance_algos: float
    wallet_min_balance_algos: float
    input_asset_decimals: int = 6
    expected_tx_count: int | None = None
    expected_group_id_hex: str = ""
    request_id: str = ""
    created_at: float = field(default_factory=time.time)

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, unsigned_transactions: list[Any]) -> "SignerRequest":
        allowed_fields = {
            "route_hash",
            "expected_app_ids",
            "expected_asset_ids",
            "input_asset_id",
            "input_amount",
            "wallet_balance_algos",
            "wallet_min_balance_algos",
            "input_asset_decimals",
            "expected_tx_count",
            "expected_group_id_hex",
            "request_id",
            "created_at",
        }
        unexpected = sorted(set(payload) - allowed_fields)
        forbidden = sorted(set(payload) & FORBIDDEN_REQUEST_FIELDS)
        if forbidden:
            raise ValueError(f"signer request cannot include arbitrary instructions: {', '.join(forbidden)}")
        if unexpected:
            raise ValueError(f"unsupported signer request fields: {', '.join(unexpected)}")
        return cls(
            route_hash=str(payload["route_hash"]),
            unsigned_transactions=tuple(unsigned_transactions),
            expected_app_ids=tuple(int(app_id) for app_id in payload.get("expected_app_ids", ())),
            expected_asset_ids=tuple(int(asset_id) for asset_id in payload.get("expected_asset_ids", ())),
            input_asset_id=int(payload.get("input_asset_id", 0)),
            input_amount=float(payload.get("input_amount", 0.0)),
            wallet_balance_algos=float(payload.get("wallet_balance_algos", 0.0)),
            wallet_min_balance_algos=float(payload.get("wallet_min_balance_algos", 0.0)),
            input_asset_decimals=int(payload.get("input_asset_decimals", 6)),
            expected_tx_count=_optional_int(payload.get("expected_tx_count")),
            expected_group_id_hex=str(payload.get("expected_group_id_hex", "") or ""),
            request_id=str(payload.get("request_id", "")),
            created_at=float(payload.get("created_at", time.time())),
        )


@dataclass(frozen=True)
class SignerDecision:
    approved: bool
    reason: str
    route_hash: str
    request_id: str
    rules: dict[str, dict[str, Any]]
    tx_count: int
    fee_algos: float
    signed_transaction_count: int = 0
    signed_transactions: tuple[str, ...] = ()
    created_at: float = field(default_factory=time.time)

    def to_audit_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "reason": self.reason,
            "route_hash": self.route_hash,
            "request_id": self.request_id,
            "rules": self.rules,
            "tx_count": self.tx_count,
            "fee_algos": self.fee_algos,
            "signed_transaction_count": self.signed_transaction_count,
            "created_at": self.created_at,
        }


class JsonlSignerAuditLog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def record(self, decision: SignerDecision) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(decision.to_audit_dict(), sort_keys=True) + "\n")


class InMemorySignerAuditLog:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def record(self, decision: SignerDecision) -> None:
        self.records.append(decision.to_audit_dict())


class IsolatedSigner:
    def __init__(self, policy: SignerPolicy, audit_log: JsonlSignerAuditLog | InMemorySignerAuditLog | None = None) -> None:
        self.policy = policy
        self.audit_log = audit_log

    def review_and_sign(self, request: SignerRequest) -> SignerDecision:
        txns = list(request.unsigned_transactions)
        rules, fee_algos = self._validate(request, txns)
        failed = next((name for name, rule in rules.items() if not rule["ok"]), None)
        if failed:
            return self._record(
                SignerDecision(
                    approved=False,
                    reason=f"{failed}: {rules[failed]['detail']}",
                    route_hash=request.route_hash,
                    request_id=request.request_id,
                    rules=rules,
                    tx_count=len(txns),
                    fee_algos=fee_algos,
                )
            )

        private_key = algo_mnemonic.to_private_key(self.policy.wallet_mnemonic)
        signed = tuple(encoding.msgpack_encode(txn.sign(private_key)) for txn in txns)
        rules["signed_blob_logging"] = {
            "ok": True,
            "detail": "signed transaction blobs returned to caller but omitted from audit logs",
        }
        return self._record(
            SignerDecision(
                approved=True,
                reason="approved by isolated signer policy",
                route_hash=request.route_hash,
                request_id=request.request_id,
                rules=rules,
                tx_count=len(txns),
                fee_algos=fee_algos,
                signed_transaction_count=len(signed),
                signed_transactions=signed,
            )
        )

    def _validate(self, request: SignerRequest, txns: list[Any]) -> tuple[dict[str, dict[str, Any]], float]:
        policy = self.policy
        rules: dict[str, dict[str, Any]] = {}
        txn_summaries = [_txn_summary(txn) for txn in txns]
        fee_algos = sum(summary["fee"] for summary in txn_summaries) / MICROALGOS_PER_ALGO
        actual_types = {summary["type"] for summary in txn_summaries}
        actual_app_ids = {summary["app_id"] for summary in txn_summaries if summary["app_id"] is not None}
        actual_asset_ids = {summary["asset_id"] for summary in txn_summaries if summary["asset_id"] is not None}
        expected_app_ids = {int(app_id) for app_id in request.expected_app_ids}
        expected_asset_ids = {int(asset_id) for asset_id in request.expected_asset_ids if int(asset_id) != 0}
        allowed_app_ids = {int(app_id) for app_id in policy.allowed_app_ids}
        allowed_asset_ids = {int(asset_id) for asset_id in policy.allowed_asset_ids if int(asset_id) != 0}
        allowed_route_hashes = {route_hash.strip() for route_hash in policy.allowed_route_hashes if route_hash.strip()}
        wallet_address = policy.wallet_address.strip()
        derived_address = _derive_address(policy.wallet_mnemonic)
        available_after_fees = request.wallet_balance_algos - request.wallet_min_balance_algos - fee_algos
        observed_input_outflow = _input_outflow(txn_summaries, request, wallet_address)
        actual_group_id_hex = _group_id_hex(txns)
        expected_group_id_hex = request.expected_group_id_hex.strip()

        _rule(rules, "signer_enabled", policy.signer_enabled, "signer is disabled")
        _rule(rules, "kill_switch", not policy.kill_switch, "kill switch is active")
        _rule(rules, "wallet_address_configured", bool(wallet_address), "wallet address is missing")
        _rule(
            rules,
            "key_material_matches_wallet",
            bool(derived_address) and derived_address == wallet_address,
            "hot-wallet signer secret is missing, invalid, or does not match wallet address",
        )
        _rule(
            rules,
            "route_hash",
            bool(request.route_hash) and bool(allowed_route_hashes) and request.route_hash in allowed_route_hashes,
            "route hash is not in the signer allowlist",
        )
        _rule(
            rules,
            "group_size",
            0 < len(txns) <= min(policy.max_tx_group_size, ALGORAND_TX_GROUP_LIMIT),
            f"group has {len(txns)} txns; max is {min(policy.max_tx_group_size, ALGORAND_TX_GROUP_LIMIT)}",
        )
        _rule(
            rules,
            "atomic_group",
            _atomic_group_ok(txns),
            "multi-transaction requests must already share one atomic group id",
        )
        _rule(
            rules,
            "route_tx_count_intent",
            request.expected_tx_count is None or request.expected_tx_count == len(txns),
            f"expected {request.expected_tx_count} transactions but received {len(txns)}",
        )
        _rule(
            rules,
            "route_group_intent",
            not expected_group_id_hex or actual_group_id_hex == expected_group_id_hex,
            f"expected group {expected_group_id_hex or 'not supplied'} actual {actual_group_id_hex or 'missing'}",
        )
        _rule(
            rules,
            "transaction_types",
            bool(actual_types) and actual_types.issubset(set(policy.allowed_txn_types)),
            f"actual types {sorted(actual_types)} exceed allowlist {sorted(policy.allowed_txn_types)}",
        )
        _rule(
            rules,
            "sender_wallet",
            bool(wallet_address) and all(summary["sender"] == wallet_address for summary in txn_summaries),
            "one or more transactions are not from the signer wallet",
        )
        _rule(
            rules,
            "no_rekey_or_close",
            all(not summary["has_rekey_or_close"] for summary in txn_summaries),
            "rekey, close-out, or asset close-out is present",
        )
        _rule(
            rules,
            "app_ids",
            expected_app_ids.issubset(allowed_app_ids) and actual_app_ids.issubset(allowed_app_ids),
            f"expected {sorted(expected_app_ids)} actual {sorted(actual_app_ids)} allowed {sorted(allowed_app_ids)}",
        )
        _rule(
            rules,
            "route_app_intent",
            actual_app_ids == expected_app_ids,
            f"expected route app ids {sorted(expected_app_ids)} but group used {sorted(actual_app_ids)}",
        )
        _rule(
            rules,
            "asset_ids",
            expected_asset_ids.issubset(allowed_asset_ids) and actual_asset_ids.issubset(allowed_asset_ids),
            f"expected {sorted(expected_asset_ids)} actual {sorted(actual_asset_ids)} allowed {sorted(allowed_asset_ids)}",
        )
        _rule(
            rules,
            "route_asset_intent",
            actual_asset_ids == expected_asset_ids,
            f"expected route asset ids {sorted(expected_asset_ids)} but group used {sorted(actual_asset_ids)}",
        )
        _rule(
            rules,
            "input_asset",
            request.input_asset_id == 0 or int(request.input_asset_id) in allowed_asset_ids,
            f"input asset {request.input_asset_id} is not allowlisted",
        )
        _rule(
            rules,
            "route_input_amount_intent",
            _amounts_match(observed_input_outflow, float(request.input_amount), int(request.input_asset_decimals)),
            (
                f"route expected input {request.input_amount:.6f}, "
                f"group spends {observed_input_outflow:.6f}"
            ),
        )
        _rule(
            rules,
            "max_input_amount",
            max(float(request.input_amount), observed_input_outflow) <= policy.max_input_amount,
            (
                f"requested {request.input_amount:.6f}, observed outflow {observed_input_outflow:.6f}, "
                f"max {policy.max_input_amount:.6f}"
            ),
        )
        _rule(
            rules,
            "max_fees",
            fee_algos <= policy.max_group_fee_algos,
            f"group fee {fee_algos:.6f} exceeds max {policy.max_group_fee_algos:.6f} ALGO",
        )
        _rule(
            rules,
            "wallet_reserve",
            available_after_fees >= policy.min_wallet_reserve_algos,
            (
                f"available after fees {available_after_fees:.6f} ALGO; "
                f"minimum reserve {policy.min_wallet_reserve_algos:.6f} ALGO"
            ),
        )
        return rules, fee_algos

    def _record(self, decision: SignerDecision) -> SignerDecision:
        if self.audit_log is not None:
            self.audit_log.record(decision)
        return decision


def signer_policy_from_settings(settings: Any) -> SignerPolicy:
    return SignerPolicy(
        signer_enabled=bool(getattr(settings, "signer_enabled", False)),
        kill_switch=bool(getattr(settings, "signer_kill_switch", True)),
        wallet_address=str(getattr(settings, "trader_address", "") or ""),
        wallet_mnemonic=str(getattr(settings, "trader_mnemonic", "") or ""),
        allowed_route_hashes=tuple(getattr(settings, "signer_allowed_route_hashes", ()) or ()),
        allowed_app_ids=tuple(int(app_id) for app_id in getattr(settings, "allowed_app_ids", ()) or ()),
        allowed_asset_ids=tuple(int(asset_id) for asset_id in getattr(settings, "allowed_asset_ids", ()) or ()),
        max_input_amount=float(getattr(settings, "max_live_trade_size", 10.0)),
        max_group_fee_algos=float(getattr(settings, "max_group_fee_algos", 0.05)),
        min_wallet_reserve_algos=float(getattr(settings, "signer_min_wallet_reserve_algos", 0.2)),
    )


def _rule(rules: dict[str, dict[str, Any]], name: str, ok: bool, detail: str) -> None:
    rules[name] = {"ok": bool(ok), "detail": "ok" if ok else detail}


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _txn_summary(txn: Any) -> dict[str, Any]:
    txn_dict = txn.dictify()
    txn_type = txn_dict.get("type")
    return {
        "type": txn_type,
        "sender": getattr(txn, "sender", None) or _address_from_value(txn_dict.get("snd")),
        "receiver": getattr(txn, "receiver", None) or _address_from_value(txn_dict.get("rcv") or txn_dict.get("arcv")),
        "fee": int(txn_dict.get("fee") or getattr(txn, "fee", 0) or 0),
        "amount_raw": int(txn_dict.get("amt") or txn_dict.get("aamt") or 0),
        "app_id": int(txn_dict.get("apid") or getattr(txn, "index", 0) or 0) if txn_type == "appl" else None,
        "asset_id": int(txn_dict.get("xaid") or getattr(txn, "index", 0) or 0) if txn_type == "axfer" else None,
        "has_rekey_or_close": _has_rekey_or_close(txn, txn_dict),
        "txn_sha256": _txn_sha256(txn),
    }


def _input_outflow(txn_summaries: list[dict[str, Any]], request: SignerRequest, wallet_address: str) -> float:
    outflow_raw = 0
    for summary in txn_summaries:
        if summary["sender"] != wallet_address:
            continue
        if request.input_asset_id == 0 and summary["type"] == "pay":
            outflow_raw += int(summary["amount_raw"])
        if request.input_asset_id != 0 and summary["type"] == "axfer" and summary["asset_id"] == request.input_asset_id:
            outflow_raw += int(summary["amount_raw"])
    return outflow_raw / (10 ** max(0, int(request.input_asset_decimals)))


def _atomic_group_ok(txns: list[Any]) -> bool:
    if len(txns) <= 1:
        return True
    groups = [getattr(txn, "group", None) for txn in txns]
    return all(groups) and len({group for group in groups}) == 1


def _group_id_hex(txns: list[Any]) -> str:
    groups = [getattr(txn, "group", None) for txn in txns if getattr(txn, "group", None)]
    if not groups:
        return ""
    if len({group for group in groups}) != 1:
        return ""
    return groups[0].hex()


def _amounts_match(observed: float, expected: float, decimals: int) -> bool:
    tolerance = 1 / (10 ** max(0, int(decimals)))
    return abs(float(observed) - float(expected)) <= tolerance


def _has_rekey_or_close(txn: Any, txn_dict: dict[str, Any]) -> bool:
    if any(txn_dict.get(key) for key in ("rekey", "close", "aclose")):
        return True
    return any(
        bool(getattr(txn, attr, None))
        for attr in ("rekey_to", "close_remainder_to", "asset_close_to", "close_assets_to")
    )


def _txn_sha256(txn: Any) -> str:
    encoded = encoding.msgpack_encode(txn)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _derive_address(wallet_mnemonic: str) -> str:
    if not wallet_mnemonic:
        return ""
    try:
        private_key = algo_mnemonic.to_private_key(wallet_mnemonic)
        return account.address_from_private_key(private_key)
    except Exception:
        return ""


def _address_from_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return encoding.encode_address(value)
    return None
