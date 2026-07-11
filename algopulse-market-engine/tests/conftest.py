from __future__ import annotations

import pytest


@pytest.fixture(scope="session", autouse=True)
def initialize_default_api_store() -> None:
    """Keep API tests independent from any developer-local SQLite database."""
    import algopulse.api as api_module

    api_module.store.initialize(run_backfills=False)
