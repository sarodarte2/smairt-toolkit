# Contributing to SMAIRT

SMAIRT is a Python CLI for rigorous, AI-assisted research workflows. User documentation starts
in the main `README.md`; this file covers changes to the CLI itself.

## Development setup

```bash
git clone https://github.com/YOUR_USERNAME/smairt-template.git
cd smairt-template
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

Create a focused branch, follow the existing typed Python and docstring conventions, and include
tests for behavior changes. Harness changes must test installation, modified managed files, safe
switching, and preservation of user-owned files.

Before opening a pull request, run:

```bash
ruff format --check src tests scripts
ruff check src tests scripts
mypy src/smairt
python -m pytest -p no:cacheprovider
pip-audit
git diff --check
```

Documentation changes are expected when commands, generated files, safety behavior, harness
ownership, or user journeys change. Keep `README.md`, the architecture, CLI reference, and focused
documents in `docs/` consistent with executable behavior.

Use the issue templates for bugs and feature requests. Bug reports are most useful when they
include the exact command, SMAIRT version, active harness, safety mode, and a minimal reproduction
that contains no protected research data or credentials.
