# SMAIRT User Guide

## What SMAIRT records

SMAIRT keeps scientific state in reviewable files. The project contract is `smairt.yaml`;
references, hypotheses, methods, decisions, evidence cards, claims, and manuscript reviews are
linked by validated IDs and hashes. Agent chat is not the scientific record.

## Start a project

Run `smairt new` for the terminal wizard or supply every field noninteractively. The wizard first
offers to create a new child folder or initialize the selected folder in place. Existing files are
reviewed rather than blocked merely because an unrelated ancestor contains SMAIRT files. A
project can start with an open question; no hypothesis is required during setup. Confirming a
contributor is required before consequential decisions and publication actions.

Data classification and safety mode are separate. Use `public`, `unpublished`, or `private` for
the corresponding material. `controlled` is present so SMAIRT can refuse false compliance
assumptions; this beta does not make controlled-data workflows compliant.

## Follow the state-aware workflow

Use these commands whenever a task begins or context is restored:

```bash
smairt status --json
smairt next --json
smairt next --prompt
smairt context --task planning --token-budget 8000
```

The prompt form is a bounded, context-aware handoff for Codex, Zoo Code, Cline, OpenCode, Cursor,
or another assistant; it cannot approve scientific decisions. The JSON response is a versioned
envelope. Scientific choices remain human gates: contributor identity, hypothesis selection,
experimental route, evidence decision, claim approval, correction, and safety-mode changes.

Use `smairt harness status --json` to distinguish installed adapter files from the local client,
trust, and hook settings that remain controlled by each harness. MCP access is metadata-only and
must be enabled explicitly for the active harness.

## Run and review experiments

Create an experiment linked to a complete hypothesis or a clear exploratory purpose. Each
meaningful method change gets a new iteration. `smairt run` reserves an immutable run, executes
without holding the shared mutation lock, then records terminal status, command, entrypoint,
configuration, packages, Git state, logs, results, and integrity hashes.

Failed and interrupted runs remain visible but cannot become accepted evidence. Never edit a run
bundle. Use a new iteration or a correction.

## Collaborate safely

Use a Git branch or worktree per contributor or independent line of work. The project lock
protects one checkout, not multiple worktrees, and does not merge scientific meaning. If a process
stops during a multi-file change:

```bash
smairt recovery status --json
smairt recovery complete <transaction-id> --yes
# or, after review
smairt recovery rollback <transaction-id> --yes
```

Only break a lock after confirming that the owning operation is no longer running.

## Publish and correct

Paper prose can use only current accepted evidence, approved claims, and verified references.
Every section requires explicit review before a build. Markdown and DOCX builds are versioned;
template or validation failure leaves prior builds untouched.

Retractions and supersessions append correction records, invalidate active selections and
dependent evidence, and preserve history. See the [Tutorial](../TUTORIAL.md) for the complete
workflow.

## Safety and remote metadata

Ordinary status, validation, doctor, and TUI refreshes are offline. Crossref/OpenAlex enrichment
is an explicit command. GitHub visibility is refreshed only with:

```bash
smairt safety status --refresh-visibility --json
```

Read [Safety Modes](SAFETY.md) before private work and run `smairt safety release-check` before
sharing or release.

The dashboard's Health area summarizes pass/fail by category and suggests safe managed repairs.
Use JSON or the referenced project files when detailed audit evidence is needed.
