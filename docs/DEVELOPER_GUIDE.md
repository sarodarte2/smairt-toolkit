# SMAIRT Developer Guide

## Setup

SMAIRT requires Python 3.11–3.13. Linux and macOS are tested in CI; WSL is supported as Linux and
has a manual release smoke test. Native Windows is not supported in this beta.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
ruff format --check src tests scripts
ruff check src tests scripts
mypy src/smairt
python -m pytest -p no:cacheprovider
```

Runtime code is under `src/smairt/`; tests are under `tests/`. Public functions and classes need
contract-oriented docstrings. Comments explain scientific invariants, provenance, safety
boundaries, or non-obvious ordering rather than syntax.

## Engineering contracts

- Durable Pydantic models reject extra fields and unsafe identifiers or paths.
- Machine output uses `schema_version`, `command`, `ok`, `data`, `warnings`, and `errors`.
- Exit codes are 0 success, 1 policy/validation, 2 usage/project state, and 3 lock/recovery.
- Consequential domain functions acquire the project mutation lock.
- Multi-file state changes stage pre/post hashes and backups in transaction journals.
- Normal diagnostics are offline; remote operations must be explicit.
- CLI/Git/integrity gates are authoritative. Harness instructions are not treated as policy.

## Extending a harness

Add an adapter manifest, managed files, executable set, capability levels, conflict behavior, and
compatibility fixture. Test installation, switching, modified and missing files, executable bits,
upstream JSON, MCP enable/disable, and custom-file preservation. New lifecycle payloads must pass
through the 1 MiB-bounded offline hook policy and emit the harness's documented response shape.
Capabilities must distinguish `blocking`, `permissions`, `advisory`, `manual`, and `unsupported`.

Schema v7 maintains Codex, Zoo Code, Cline, OpenCode, Cursor, and Claude Code. Executable project
plugins are never generated merely to gain hook parity when a safer native permission surface is
available.

## Tests and release gates

Functional tests protect locking, transactions, runner behavior, safety, corrections, migrations,
integrity, research transitions, and harness switching. The security workflow runs separate
CodeQL, third-party dependency audit, dependency review, and gitleaks jobs. See
[Release](RELEASE.md).
