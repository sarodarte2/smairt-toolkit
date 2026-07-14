"""Shared test isolation for user-local SMAIRT configuration."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_user_setup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Keep connection-profile tests out of the developer's real OS config."""
    monkeypatch.setenv("SMAIRT_CONFIG_HOME", str(tmp_path / "user-setup"))
