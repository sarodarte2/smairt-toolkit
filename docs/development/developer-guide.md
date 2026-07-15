# Developer guide

SMAIRT requires Python 3.11–3.13. Linux and macOS are CI targets; WSL is supported as Linux and
requires a manual clean-wheel smoke test. Native Windows is not supported in this preview.

## Setup and checks

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
ruff format --check src tests scripts
ruff check src tests scripts
mypy src/smairt
python scripts/validate_docs.py
python -m pytest -p no:cacheprovider
```

Runtime code lives under `src/smairt/`; tests live under `tests/`. Public functions and classes use
contract-oriented docstrings. Comments explain scientific invariants, provenance, safety
boundaries, compatibility behavior, or non-obvious ordering rather than ordinary syntax.

## Module boundaries

`cli.py` owns the root Typer tree and cross-domain lifecycle. Focused `cli_*.py` modules own
cohesive command groups and use `cli_shared.py` for project resolution and output. Domain modules
own state transitions, validation, and persistence. The TUI and adapters call those shared
services; they do not create parallel scientific truth.

The architectural map is maintained in [Architecture](../concepts/architecture.md), not as a
separate file inventory.

## Engineering contracts

- Durable Pydantic models reject extra fields and unsafe identifiers or paths.
- Machine output uses `schema_version`, `command`, `ok`, `data`, `warnings`, and `errors`.
- Exit codes distinguish success, policy/validation, usage/project-state, and lock/recovery errors.
- Consequential domain functions acquire the project mutation lock.
- Multi-file changes stage hashes and backups in transaction journals before atomic replacement.
- Ordinary diagnostics are offline; network access must be explicit.
- CLI, Git, transaction, and integrity gates are authoritative. Harness instructions are not
  security policy.

## Generated project compatibility

Scientific artifacts are researcher-owned and are never replaced by a framework upgrade. Managed
guidance has recorded hashes so upgrades can distinguish untouched generated content from local
edits. A documentation rewrite must preserve expected scaffold paths and test modified-file
behavior.

User-local setup and project configuration have separate schemas. A user-local appearance
migration must not bump or rewrite the scientific project schema.

## Extending a harness

Add a manifest, managed files, executable set, capability levels, conflict behavior, and
compatibility fixtures. Test installation, switching, modified and missing files, executable bits,
upstream payload translation, MCP enable/disable, and preservation of custom content.

Capabilities distinguish `blocking`, `permissions`, `advisory`, `manual`, and `unsupported`.
Executable project plugins are not generated solely to claim hook parity when a safer native
permission surface exists.

## Test responsibilities

Functional tests protect locking, transactions, runner behavior, safety, corrections, migrations,
integrity, research transitions, documentation, and harness switching. The security workflow adds
CodeQL, dependency audit/review, and secret scanning. See the [Release process](release.md) for the
complete gate.
