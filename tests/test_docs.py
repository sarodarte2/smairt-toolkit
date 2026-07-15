"""Documentation contract tests for public commands and repository presentation."""

import re
from pathlib import Path

from typer.main import get_command

from scripts.validate_docs import validate_repository
from smairt.cli import app

ROOT = Path(__file__).parents[1]


def test_documentation_validator_passes() -> None:
    """Keep the public repository contract covered by the same validator CI runs."""
    assert validate_repository() == []


def test_documented_root_command_groups_exist() -> None:
    """Prevent curated workflow documentation from naming missing root commands."""
    sources = [
        ROOT / "README.md",
        ROOT / "docs/reference/cli.md",
        ROOT / "docs/getting-started/installation.md",
        ROOT / "docs/getting-started/quickstart.md",
    ]
    documented = {
        match
        for source in sources
        for match in re.findall(r"\bsmairt\s+([a-z][a-z0-9-]*)", source.read_text())
    }
    available = set(get_command(app).commands)
    assert documented <= available, (
        f"documented root commands are missing: {documented - available}"
    )
