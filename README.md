# SMAIRT

SMAIRT is a local-first research harness for scientists working with coding agents. It preserves
the chain from research question to references, hypotheses, experiments, immutable runs, accepted
evidence, approved claims, and a reviewable manuscript.

SMAIRT currently supports one active harness per project: Codex, Zoo Code, or Cline. Scientific
state remains in portable YAML, JSON, and Markdown; harness adapters provide instructions and
guardrails without creating a second research record.

## Install and create a project

```bash
python -m pip install -e '.[dev]'
smairt new my-study \
  --name "My Study" \
  --author "Researcher Name" \
  --confirm-contributor \
  --classification unpublished \
  --harness codex
cd my-study
smairt status --json
smairt next --json
```

Run `smairt new` without `--name` and `--author` to use the interactive wizard. The wizard
explains data classification, Standard and Strict safety, contributor confirmation, environment,
Git, and harness selection before it writes the project.

## Core workflow

```text
question + references -> background -> three proposal options
-> human-selected hypothesis -> experiment -> iteration -> immutable run
-> human decision -> evidence card -> approved claim
-> reviewed Markdown manuscript -> versioned Markdown/DOCX build
```

Useful commands:

| Goal | Command |
|---|---|
| Inspect project health | `smairt doctor --json` |
| Get the next state-aware action | `smairt next --json` |
| Build bounded context | `smairt context --task planning --token-budget 8000` |
| Get an economical model tier | `smairt model recommend --task metadata` |
| Confirm a contributor | `smairt contributor add --name "Name"` then `smairt contributor use <id>` |
| Inspect safety | `smairt safety status --json` |
| Validate before commit | `smairt validate --staged` |
| Index and verify a reference | `smairt reference add paper.pdf`, then `smairt reference verify <id>` |
| Create three hypotheses | `smairt hypothesis proposals new` |
| Run registered research code | `smairt run --experiment EXPERIMENT_001 --iteration ITERATION_001` |
| Verify immutable runs | `smairt verify --json` |
| Build the paper | `smairt paper build --format docx` |

Human confirmation is required for contributor identity, hypothesis selection, scientific
decisions, claim approval, evidence corrections, safety-mode changes, and repository visibility.

## Harness selection

The active adapter is stored in `smairt.yaml`. Preview every switch:

```bash
smairt harness status --json
smairt harness select zoo --dry-run
smairt harness select zoo
```

SMAIRT keeps a marked shared block in `AGENTS.md`. Text outside that block is preserved. It owns
individual adapter files through hash manifests and never deletes an entire `.codex`, `.roo`,
`.cline`, or `.clinerules` directory. A locally modified managed file stops switching; use
`--backup-and-switch` only after reviewing the preview.

- Codex: `.codex/`, shared `AGENTS.md`, and the portable SMAIRT skill.
- Zoo: `.roo/rules/`, mode-specific rules, `.roomodes`, and `.rooignore`.
- Cline: conditional `.clinerules/`, safety/compaction hooks, workflows, and `.clineignore`.

Model/provider credentials remain in the harness or operating-system secret store. SMAIRT records
only provider-neutral `cheap`, `balanced`, and `strong` task recommendations.

See [docs/HARNESSES.md](docs/HARNESSES.md) and
[docs/CONTEXT_AND_MODELS.md](docs/CONTEXT_AND_MODELS.md).

## Safety modes

Both modes prohibit secrets, private keys, raw protected data, ignored reference PDFs, and unsafe
research data from Git.

- Standard supports ordinary collaboration and requires a private-repository acknowledgment for
  private or controlled projects.
- Strict keeps protected summaries local unless they are explicitly shareable and redaction is
  confirmed. Unknown/public visibility and unconfirmed remote metadata queries are errors.

Before changing visibility or publishing:

```bash
smairt safety release-check --json
```

A private repository is collaboration infrastructure, not institutional compliance
certification. See [docs/SAFETY.md](docs/SAFETY.md).

## Development

```bash
ruff check src tests
python -m pytest -p no:cacheprovider
python -m pip wheel . --no-deps --wheel-dir /tmp/smairt-dist
```

The maintained package is the CLI under `src/smairt/`. The former Cookiecutter and paper-driven
products have been removed; original Cookiecutter projects are not automatically migrated.

SMAIRT is distributed under the MIT License. See [LICENSE](LICENSE) and [CITATION.cff](CITATION.cff).
