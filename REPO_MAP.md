# SMAIRT repository map

SMAIRT is a Python CLI for creating and enforcing hypothesis-driven, provenance-aware research
projects. The maintained implementation is under `src/smairt/`; the former Cookiecutter template
was removed after the v2 migration.

## Runtime

- `src/smairt/cli.py` — Typer command tree and user-facing diagnostics.
- `src/smairt/scaffold.py` — project creation and guided setup.
- `src/smairt/models.py` — persisted project configuration and typed records.
- `src/smairt/harnesses.py` — exclusive Codex, Zoo, and Cline adapter installation and switching.
- `src/smairt/project.py` — validation, status, next-action guidance, and context capsules.
- `src/smairt/runner.py`, `integrity.py` — run capture and tamper-evident manifests.
- `src/smairt/paper.py`, `references.py` — evidence, claims, drafting, publication, and citations.
- `src/smairt/safety.py`, `contributors.py` — repository policy and contribution identity.
- `src/smairt/summaries.py`, `model_policy.py` — canonical summaries and advisory model tiers.
- `src/smairt/migrations.py`, `upgrade.py`, `contracts.py` — migration, managed-file upgrades,
  and cross-repository contracts.

## Project created by `smairt new`

```text
.smairt/                  local state, harness manifest, locks, and context capsules
config/smairt.yaml        project policy and active harness
hypotheses/               versioned hypotheses
experiments/              scripts and run records
analysis/                 analyses and evidence cards
paper/                    claims, outline, reviewed sections, and builds
references/               structured references and cached metadata
prompts/                  project context and conventions
AGENTS.md                 shared SMAIRT managed instructions plus user-owned text
```

Only one harness adapter is active. Codex owns `.codex/`, Zoo owns SMAIRT-managed `.roo/`
artifacts, and Cline owns SMAIRT-managed `.clinerules/`, `.cline/`, and ignore files. The manifest
tracks generated ownership so switching does not delete unrelated user files. See
`docs/HARNESSES.md`.

## Tests and documentation

- `tests/` — unit, CLI, user-journey, safety, migration, and harness tests.
- `skills/smairt-research/` — maintained research workflow skill.
- `docs/HARNESSES.md` — adapter behavior and conflict recovery.
- `docs/SAFETY.md` — safety modes, visibility attestations, and release checks.
- `docs/CONTEXT_AND_MODELS.md` — context budgeting, summaries, and model recommendations.
- `README.md`, `QUICKSTART.md`, `TUTORIAL.md` — product overview and end-to-end usage.

## Verification

```bash
ruff check src tests
pytest
python -m coverage run -m pytest
python -m coverage report
python -m build
```

The package metadata and console entry point are in `pyproject.toml`. Generated build artifacts
and local `.smairt/` runtime state must not be committed.
