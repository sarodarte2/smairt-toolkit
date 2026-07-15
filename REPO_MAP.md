# SMAIRT repository map

SMAIRT is a Python CLI for creating and enforcing hypothesis-driven, provenance-aware research
projects. The maintained implementation is under `src/smairt/`; the former Cookiecutter template
was removed after the v2 migration.

## Runtime

- `src/smairt/cli.py` — root Typer command tree, project lifecycle, and diagnostics.
- `src/smairt/cli_research.py` — background, hypotheses, experiments, runs, and corrections.
- `src/smairt/cli_publication.py` — evidence, claims, manuscript builds, and summaries.
- `src/smairt/cli_references.py`, `cli_literature.py`, `cli_harness.py`, `cli_safety.py` — commands.
- `src/smairt/cli_shared.py` — consistent project resolution and output rendering.
- `src/smairt/scaffold.py` — project creation and guided setup.
- `src/smairt/models.py` — persisted project configuration and typed records.
- `src/smairt/harnesses.py` — six conflict-aware harness adapters and merge-owned configuration.
- `src/smairt/project.py` — validation, status, next-action guidance, and context capsules.
- `src/smairt/runner.py`, `science.py`, `integrity.py` — protocol gates, run capture, and manifests.
- `src/smairt/hpc.py`, `cli_hpc.py` — optional typed Slurm transport and job reconciliation.
- `src/smairt/completion.py` — local project-aware command and identifier suggestions.
- `src/smairt/paper.py`, `references.py`, `literature.py` — publication, citations, and OA access.
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
artifacts, Cline owns SMAIRT-managed `.clinerules/` and `.cline/`, OpenCode owns its generated
`.opencode/` files and `opencode.json`, and Cursor owns generated `.cursor/` files. The manifest
tracks generated ownership. Claude owns `.claude/` files while merging its fragments into shared
JSON without deleting unrelated user settings or servers. See
`docs/HARNESSES.md`.

## Tests and documentation

- `tests/` — unit, CLI, user-journey, safety, migration, and harness tests.
- `src/smairt/workflows.py` — six portable research workflow definitions.
- `docs/HARNESSES.md` and `docs/harnesses/` — chooser, setup, behavior, and limitations.
- `docs/SAFETY.md` — safety modes, visibility attestations, and release checks.
- `docs/CONTEXT_AND_MODELS.md` — context budgeting, summaries, and model recommendations.
- `docs/TERMINAL_COMPLETION.md`, `docs/HPC.md` — discoverability and optional cluster execution.
- `examples/enzyme-kinetics-demo/` — verified local installation-to-evidence demonstration.
- `docs/DEVELOPMENT.md` — enforceable readability and CLI module conventions.
- `docs/plans/TUI_USABILITY.md` — phased terminal-native TUI redesign and acceptance criteria.
- `README.md`, `QUICKSTART.md`, `TUTORIAL.md`, `DEMO.md` — overview and human-run workflows.

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
