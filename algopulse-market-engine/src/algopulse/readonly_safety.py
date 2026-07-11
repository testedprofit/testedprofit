from __future__ import annotations

from algopulse.config import Settings


class ReadonlySafetyError(RuntimeError):
    """Raised when a read-only market profile refuses to start."""


MAINNET_READONLY_ENVS = frozenset({"mainnet-readonly", "mainnet_readonly", "staging"})
TESTNET_ENVS = frozenset({"testnet", "staging", "local"})


def assert_execution_disarmed(settings: Settings) -> None:
    """Refuse any path that could arm signing, execution, or load a mnemonic."""
    if settings.enable_live_execution:
        raise ReadonlySafetyError("refused_live_execution_enabled")
    if settings.execute_approved:
        raise ReadonlySafetyError("refused_execute_approved_enabled")
    if settings.allow_api_execution:
        raise ReadonlySafetyError("refused_api_execution_enabled")
    if not settings.unsigned_executor_only:
        raise ReadonlySafetyError("refused_unsigned_executor_only_disabled")
    if settings.signer_enabled:
        raise ReadonlySafetyError("refused_signer_enabled")
    if not settings.signer_kill_switch:
        raise ReadonlySafetyError("refused_kill_switch_inactive")
    if settings.trader_mnemonic.strip():
        raise ReadonlySafetyError("refused_signer_secret_loaded")


def assert_testnet_readonly_safe(settings: Settings) -> None:
    network = (settings.network or "").strip().lower()
    if network != "testnet":
        raise ReadonlySafetyError(f"refused_non_testnet_network:{network or 'unconfigured'}")
    assert_execution_disarmed(settings)


def assert_mainnet_readonly_safe(settings: Settings) -> None:
    """Fail-closed MainNet read-only staging gate."""
    network = (settings.network or "").strip().lower()
    env = (settings.env or "").strip().lower()
    if network != "mainnet":
        raise ReadonlySafetyError(f"refused_non_mainnet_network:{network or 'unconfigured'}")
    if env not in MAINNET_READONLY_ENVS:
        raise ReadonlySafetyError(
            f"refused_mainnet_without_readonly_profile:env={env or 'unconfigured'}"
        )
    assert_execution_disarmed(settings)
    # Extra belt-and-suspenders: public delay must stay conservative on MainNet.
    if int(settings.public_delay_seconds or 0) < 900:
        raise ReadonlySafetyError("refused_public_delay_below_900_seconds")


def assert_readonly_profile_safe(settings: Settings) -> None:
    """Allow TestNet or fail-closed MainNet read-only profiles only."""
    network = (settings.network or "").strip().lower()
    if network == "testnet":
        assert_testnet_readonly_safe(settings)
        return
    if network == "mainnet":
        assert_mainnet_readonly_safe(settings)
        return
    raise ReadonlySafetyError(f"refused_unsupported_network:{network or 'unconfigured'}")
