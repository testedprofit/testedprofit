from algopulse.dry_run_validator import UnsignedGroupValidationPolicy
from algopulse.dry_run_validator import validate_unsigned_group_summary
from algopulse.risk import ALGORAND_TX_GROUP_LIMIT


def _policy(**overrides) -> UnsignedGroupValidationPolicy:
    values = {
        "approved_route_hashes": ("route-ok",),
        "allowed_app_ids": (1001,),
        "allowed_asset_ids": (0, 31566704),
        "max_total_fee_microalgos": 10_000,
    }
    values.update(overrides)
    return UnsignedGroupValidationPolicy(**values)


def _valid_group(**overrides) -> dict:
    group = {
        "routeHash": "route-ok",
        "approvedRouteHash": "route-ok",
        "unsigned": True,
        "transactions": [
            {
                "type": "pay",
                "feeMicroAlgos": 1000,
                "firstValid": 100,
                "lastValid": 200,
                "assetIds": [0],
            },
            {
                "type": "appl",
                "appId": 1001,
                "feeMicroAlgos": 1000,
                "firstValid": 100,
                "lastValid": 200,
                "assetIds": [31566704],
            },
            {
                "type": "axfer",
                "assetId": 31566704,
                "feeMicroAlgos": 1000,
                "firstValid": 100,
                "lastValid": 200,
            },
        ],
        "validityWindow": {"firstValid": 100, "lastValid": 200},
        "replayProtection": {"status": "lease_planned"},
        "requiredReferences": {
            "apps": [1001],
            "assets": [31566704],
            "accounts": ["TRADER"],
        },
        "references": {
            "apps": [1001],
            "assets": [31566704],
            "accounts": ["TRADER"],
        },
    }
    group.update(overrides)
    return group


def test_valid_unsigned_group_summary_passes_without_signing_or_submission():
    result = validate_unsigned_group_summary(_valid_group(), _policy())

    assert result["ok"] is True
    assert result["reason"] is None
    assert result["txCount"] == 3
    assert result["maxGroupSize"] == ALGORAND_TX_GROUP_LIMIT
    assert result["totalFeeMicroAlgos"] == 3000
    assert result["appIds"] == [1001]
    assert result["assetIds"] == [0, 31566704]
    assert result["transactionTypes"] == ["pay", "appl", "axfer"]
    assert all(result["rules"].values())
    assert result["submitted"] is False
    assert result["signed"] is False
    assert result["dryRunOnly"] is True
    assert result["liveExecutionTouched"] is False
    assert result["signerCodeTouched"] is False


def test_unsigned_group_validator_rejects_group_size_above_algorand_limit():
    group = _valid_group(
        transactions=[
            {
                "type": "pay",
                "feeMicroAlgos": 1000,
                "firstValid": 100,
                "lastValid": 200,
                "assetIds": [0],
            }
            for _ in range(ALGORAND_TX_GROUP_LIMIT + 1)
        ]
    )

    result = validate_unsigned_group_summary(group, _policy())

    assert result["ok"] is False
    assert result["reason"] == "group_size_ok"
    assert result["rules"]["group_size_ok"] is False


def test_unsigned_group_validator_rejects_unknown_app_id():
    group = _valid_group(transactions=[{**_valid_group()["transactions"][1], "appId": 9999}])

    result = validate_unsigned_group_summary(group, _policy())

    assert result["ok"] is False
    assert result["reason"] == "app_ids_allowlisted"
    assert result["rules"]["app_ids_allowlisted"] is False


def test_unsigned_group_validator_rejects_unknown_asset_id():
    group = _valid_group(transactions=[{**_valid_group()["transactions"][2], "assetId": 999999}])

    result = validate_unsigned_group_summary(group, _policy())

    assert result["ok"] is False
    assert result["reason"] == "asset_ids_allowlisted"
    assert result["rules"]["asset_ids_allowlisted"] is False


def test_unsigned_group_validator_rejects_fee_above_policy():
    group = _valid_group(totalFeeMicroAlgos=50_001)

    result = validate_unsigned_group_summary(group, _policy(max_total_fee_microalgos=50_000))

    assert result["ok"] is False
    assert result["reason"] == "fee_cap_ok"
    assert result["rules"]["fee_cap_ok"] is False


def test_unsigned_group_validator_rejects_route_hash_mismatch():
    group = _valid_group(routeHash="unknown-route")

    result = validate_unsigned_group_summary(group, _policy())

    assert result["ok"] is False
    assert result["reason"] == "route_hash_matches"
    assert result["rules"]["route_hash_matches"] is False


def test_unsigned_group_validator_rejects_missing_validity_window():
    group = _valid_group()
    group.pop("validityWindow")
    group["transactions"] = [
        {key: value for key, value in txn.items() if key not in {"firstValid", "lastValid"}}
        for txn in group["transactions"]
    ]

    result = validate_unsigned_group_summary(group, _policy())

    assert result["ok"] is False
    assert result["reason"] == "validity_window_present"
    assert result["rules"]["validity_window_present"] is False


def test_unsigned_group_validator_rejects_signed_payload():
    group = _valid_group(signedPayload="signed-bytes-would-not-be-safe")

    result = validate_unsigned_group_summary(group, _policy())

    assert result["ok"] is False
    assert result["reason"] == "signed_payload_present"
    assert result["rules"]["no_signed_payload"] is False
    assert "signedPayload" in result["forbiddenFields"]


def test_unsigned_group_validator_rejects_submission_payload():
    group = _valid_group(submissionPayload={"txids": ["SHOULD_NOT_EXIST"]})

    result = validate_unsigned_group_summary(group, _policy())

    assert result["ok"] is False
    assert result["reason"] == "submission_payload_present"
    assert result["rules"]["no_submission_payload"] is False
    assert "submissionPayload" in result["forbiddenFields"]


def test_unsigned_group_validator_rejects_secret_material_fields():
    group = _valid_group(transactions=[{**_valid_group()["transactions"][0], "mnemonic": "never here"}])

    result = validate_unsigned_group_summary(group, _policy())

    assert result["ok"] is False
    assert result["reason"] == "secret_material_present"
    assert result["rules"]["no_secret_material"] is False
    assert "transactions[0].mnemonic" in result["forbiddenFields"]


def test_unsigned_group_validator_requires_replay_protection_plan():
    group = _valid_group()
    group.pop("replayProtection")

    result = validate_unsigned_group_summary(group, _policy())

    assert result["ok"] is False
    assert result["reason"] == "lease_or_replay_plan_declared"
    assert result["rules"]["lease_or_replay_plan_declared"] is False


def test_unsigned_group_validator_rejects_unsupported_transaction_type():
    group = _valid_group(transactions=[{**_valid_group()["transactions"][0], "type": "keyreg"}])

    result = validate_unsigned_group_summary(group, _policy())

    assert result["ok"] is False
    assert result["reason"] == "transaction_types_supported"
    assert result["rules"]["transaction_types_supported"] is False


def test_unsigned_group_validator_requires_references_or_explicit_missing_marker():
    group = _valid_group(references={"apps": [], "assets": [], "accounts": []})
    rejected = validate_unsigned_group_summary(group, _policy())

    explicit = _valid_group(
        references={"apps": [], "assets": [], "accounts": []},
        referencesExplicitlyMissing=True,
    )
    allowed_with_warning = validate_unsigned_group_summary(explicit, _policy())

    assert rejected["ok"] is False
    assert rejected["reason"] == "required_references_declared"
    assert rejected["rules"]["required_references_declared"] is False
    assert allowed_with_warning["ok"] is True
    assert allowed_with_warning["warnings"] == ["required_references_explicitly_missing"]
