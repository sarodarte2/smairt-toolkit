# SMAIRT v1 Product Specification

## Purpose

SMAIRT is an installable research toolkit that makes careful AI-assisted computational research
the easiest path. It preserves human judgment, records provenance automatically, protects local
data, and works consistently from Codex App, Codex CLI, or a terminal.

## Product Contract

- The repository, not a chat, owns research state.
- `smairt.yaml` is the machine-readable project contract.
- Markdown conventions explain behavior; commands and validators enforce it.
- Project creation never requires a hypothesis.
- Local indexed references are the default evidence base.
- Codex must ask before academic web research and index every additional source.
- AI presents three distinct hypothesis options; only the human can activate one.
- Runs are immutable. Corrections append amendments, runs, iterations, supersessions, or
  retractions.
- Paper elements may reference only accepted, current run evidence.

## User Experience

`smairt new` and `smairt start project` open a keyboard-accessible Textual wizard. It asks
only for project name, manually entered author, optional question/description, data
classification, optional Git initialization, and one project-level Conda choice. A preview is
required before creation.

`smairt menu` opens the project dashboard and permits later edits. Codex uses equivalent JSON
commands and never drives the TUI.

`smairt next --json` is the state-aware handoff contract. Codex runs routine commands, summarizes
the completed step, and offers adaptive next actions while pausing at explicit human scientific
gates.

Research entrypoints use numbered, descriptive filenames tied to experiment IDs and a
novice-readable skeleton. `smairt code validate` reports readability and traceability warnings;
`smairt code index` creates an AST-derived map without importing research code.

## Artifact Chain

```text
background + indexed references
-> retained three-option proposal set
-> human-selected hypothesis
-> experiment
-> iteration
-> immutable run bundle
-> analysis and human decision
-> optional paper evidence link
```

Exploratory, QC, reproduction, and infrastructure work may use a recorded purpose instead of a
hypothesis.

## Safety

Standard safety protects secrets, private keys, local PDFs, raw-data directories, FAST5, POD5,
FASTQ, BAM, and CRAM through generated ignore rules, staged-file validation, Git hooks, and
Codex hooks. Controlled-data projects receive an explicit warning because approved-storage and
network enforcement are deferred.

## Context

`AGENTS.md` is intentionally short. The repo skill uses progressive disclosure, and
`smairt context --task` returns only the active state and task-relevant files. Full PDFs, logs,
older iterations, and unrelated prompts are loaded on demand.

## v1 Boundaries

Codex supplies AI reasoning without a separate API key. V1 does not implement MCP, plugins,
OpenCode/Cursor adapters, direct model APIs, strict safety, field profiles, standalone binaries,
or automatic manuscript drafting. The artifact interfaces remain provider-neutral so later
OpenAI-compatible institutional endpoints can use custom base URLs, model IDs, and credentials
referenced only through user environment/configuration.
