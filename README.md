<div align="center">

# SMAIRT

### Scientific Method with AI Research Toolkit

**A local-first, auditable research harness for scientists working with coding agents.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-f28c28.svg)](LICENSE)
[![Platforms](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-101820)](#install)
[![Status](https://img.shields.io/badge/status-v1%20development-f28c28)](#implementation-status)

<sub>Human judgment stays explicit. Research state stays in the repository. AI work stays
inspectable.</sub>

</div>

---

SMAIRT is a local-first research framework for scientists working with coding agents such as
Codex. It gives the researcher and the AI a shared, inspectable project structure so that ideas,
evidence, code, experiment runs, corrections, and decisions remain connected.

The aim is not to automate scientific judgment. It is to make AI-assisted research easier to
conduct without losing provenance, reproducibility, data safeguards, or the researcher's own
intellectual contribution.

> AI can help a researcher reach the frontier of what is known more quickly. The researcher is
> still responsible for deciding which questions matter, judging evidence, and making the novel
> connections that move the frontier.

SMAIRT originated with the Pacific Northwest National Laboratory computational biology team and
is evolving here into an installable, harness-aware research tool.

## Why this exists

Coding agents can search literature, write analysis code, run experiments, and help interpret
results with remarkable speed. That speed creates a research-record problem: the chat remembers
one thing, the filesystem says another, failed attempts disappear, parameters become difficult to
trace, and a manuscript can drift away from the evidence that supports it.

SMAIRT makes the repository—not a particular conversation or AI vendor—the durable source of
truth. The harness supplies structure and guardrails; the coding agent supplies adaptable
reasoning; the researcher supplies the scientific questions, choices, interpretation, and
accountability.

## Implementation status

The evolved v1 is a working installable Python application, not only a Cookiecutter template.

| Capability | Current state |
|---|---|
| Interactive project wizard and editable menu | Implemented |
| Codex App and Codex CLI project guidance | Implemented |
| Adaptive `completed / next / alternatives` workflow | Implemented |
| Local PDF indexing, metadata confirmation, and checksums | Implemented |
| Background and three-hypothesis development | Implemented |
| Explicit human hypothesis and evidence decisions | Implemented |
| Numbered, novice-readable experiment scripts | Implemented |
| Immutable runs with logs, config, environment, code, and Git provenance | Implemented |
| AST-derived code index and readability validation | Implemented |
| Retractions, supersession status, and amendments | Implemented |
| Paper-to-accepted-run provenance checks | Implemented |
| Safe synchronization of existing SMAIRT projects | Implemented |
| macOS/Linux and Python 3.11/3.12 CI definition | Implemented; requires branch push to run |
| PyPI publication and release automation | Planned |
| OpenCode and other coding-agent adapters | Planned |
| MCP server and optional direct model adapters | Planned after the portable core stabilizes |

The source currently has automated lifecycle, TUI, safety, guidance, indexing, upgrade, and
package-install coverage. The next milestone is sustained dogfooding on real research projects.

## What SMAIRT changes

A normal AI coding conversation is flexible, but its conventions can disappear between sessions.
Important outputs may land in arbitrary folders, failed experiments may be overwritten, and a
paper may slowly become disconnected from the runs that support it.

SMAIRT makes those expectations part of the project itself:

- `smairt.yaml` is the machine-readable project contract.
- A small `AGENTS.md` and project skill teach Codex how to work in the repository.
- Task-specific context is loaded progressively instead of reading every prompt every time.
- Research artifacts are created with stable IDs and linked in a traceable chain.
- Experiment commands, configurations, logs, environment details, Git state, and outputs are
  recorded together.
- Human selections and scientific decisions remain explicit.
- Corrections append or supersede evidence rather than silently rewriting history.
- Git protections keep common secrets, local references, and raw scientific data out of commits.

The framework lives in the research folder. After setup, a researcher can open that folder in the
Codex app or Codex CLI and begin working normally—there is no separate SMAIRT service to start.

## Research workflow

```text
initial question + local references
              |
              v
      initial background
              |
              v
  three distinct hypothesis options
              |
       human selection/edit
              |
              v
 hypothesis -> experiment -> iteration -> run -> analysis -> decision
                                                        |
                                      accept / revise / abandon / block
                                                        |
                                              supported paper elements
```

A project does not need a hypothesis at creation time. It can begin with an uncertain question,
a short description, and a folder of reference PDFs. Codex can help synthesize an initial
background and propose exactly three scientifically distinct hypotheses. A hypothesis becomes
active only after a researcher selects or edits it.

Exploratory, quality-control, infrastructure, and reproduction work can instead be created with a
clearly recorded purpose.

## Repository-owned architecture

```text
                    researcher
                        |
             explicit scientific choices
                        |
        +---------------v----------------+
        |  coding-agent harness          |
        |  Codex today; others later     |
        +---------------+----------------+
                        |
              smairt next / commands
                        |
        +---------------v----------------+
        |  portable SMAIRT project       |
        |                                |
        |  smairt.yaml      project state|
        |  AGENTS + skill   agent policy |
        |  references       evidence     |
        |  hypotheses       predictions  |
        |  experiments      methods      |
        |  results          immutable runs|
        |  analysis         interpretation|
        |  paper            accepted use |
        +--------------------------------+
```

The portable project contract is intentionally independent of Codex-specific conversation state.
Codex integration lives in a thin generated instruction layer. Future harness adapters should
consume the same JSON status, guidance, validation findings, artifact IDs, and filesystem
conventions rather than inventing parallel research records.

## Install

SMAIRT supports macOS and Linux and requires Python 3.11 or newer.

For an isolated command-line installation, use either `pipx` or `uv`:

```bash
pipx install smairt
```

```bash
uv tool install smairt
```

During development, install from a clone:

```bash
git clone https://github.com/PNNL-CompBio/smairt-template.git
cd smairt-template
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

The `smairt` package is not yet published to PyPI. The `pipx` and `uv` commands above describe the
intended installation once the first release is published; use the development installation for
now.

## Create a project

Launch the interactive wizard:

```bash
smairt start project
```

or:

```bash
smairt new my-research-project
```

The wizard asks only for information needed at setup:

- Project name
- Author, entered manually and never inferred
- Optional initial question and description
- Data classification: public, unpublished, private, or controlled
- Optional Git initialization
- Environment: a new project Conda environment, an existing Conda environment, or no managed
  environment

It previews the project before writing anything. Git initialization does not create an automatic
commit.

To add SMAIRT to the current repository, run:

```bash
smairt init
```

## Work in Codex

Open the generated project folder in the Codex app or start Codex CLI from that folder. Codex will
discover the repository instructions and use the included SMAIRT skill when the task involves
research planning, execution, interpretation, or documentation.

Useful commands remain available when you want an explicit project action:

```bash
smairt menu
smairt status
smairt next
smairt validate
smairt context --task code
```

`smairt menu` reopens the project interface so the manually maintained project details can be
reviewed or edited later.

Codex can run routine SMAIRT actions itself. After each research step, `smairt next --json`
provides the completed stage, one recommended action, relevant alternatives, files to read, and
whether the next choice must come from the researcher. Human hypothesis selections and scientific
decisions are never inferred.

A typical Codex interaction can simply begin with:

> Check this SMAIRT project, tell me what was completed, and help me take the recommended next
> step.

Codex reads `smairt next --json`, performs routine safe actions, and returns to the researcher with
adaptive choices when judgment is required. Terminal use remains available for installation,
environment troubleshooting, and direct inspection, but it is not intended to be the everyday
research interface.

## Command map

| Goal | Command |
|---|---|
| Create a project | `smairt start project` |
| Reopen project details | `smairt menu` |
| Inspect current state | `smairt status --json` |
| Ask what comes next | `smairt next --json` |
| Select minimal task context | `smairt context --task code` |
| Validate the whole project | `smairt validate --json` |
| Index a PDF | `smairt reference add paper.pdf` |
| Create background workspace | `smairt background create` |
| Create three hypothesis options | `smairt hypothesis proposals new` |
| Create an experiment | `smairt experiment new ...` |
| Validate readable code | `smairt code validate` |
| Refresh the code map | `smairt code index` |
| Run the registered entrypoint | `smairt run --experiment ... --iteration ...` |
| Record interpretation decision | `smairt decision record ...` |
| Preview framework updates | `smairt upgrade` |

## References, background, and hypotheses

Add local reference PDFs and build their index:

```bash
smairt reference add paper.pdf
smairt reference scan
smairt reference list
```

SMAIRT stores source metadata, file checksums, and extracted PDF metadata in
`references/index.yaml`. Reference PDFs are local by default and excluded from Git.

Then create the research artifacts that Codex will complete with you:

```bash
smairt background create
smairt hypothesis proposals new
smairt hypothesis proposals validate hypotheses/proposals/PROPOSAL_SET_001.md
smairt hypothesis activate \
  --proposal-set hypotheses/proposals/PROPOSAL_SET_001.md \
  --option A \
  --title "Selected direction" \
  --statement "A specific and falsifiable statement" \
  --selected-by "Researcher Name" \
  --rationale "Why this direction was selected"
```

The proposal format requires three options, each with its reasoning, falsifiable prediction,
competing explanation, data and test requirements, feasibility, confounders, and meaningful
difference from the alternatives.

## Experiments and reproducible runs

Create an experiment and execute its first iteration:

```bash
smairt experiment new --title "Test selected mechanism" --hypothesis HYPOTHESIS_001
smairt run --experiment EXPERIMENT_001 --iteration ITERATION_001
```

Every recorded run receives an immutable run directory containing:

- The original command and exit status
- Standard output and error log
- Iteration configuration snapshot and checksum
- Entrypoint snapshot when identifiable
- Python and managed-environment information
- Git commit and working-tree state
- Figures and result artifacts produced through SMAIRT output paths

After interpretation, record the human decision:

```bash
smairt decision record \
  --experiment EXPERIMENT_001 \
  --iteration ITERATION_001 \
  --run RUN_20260101T120000000000Z \
  --decision ACCEPT \
  --decided-by "Researcher Name" \
  --rationale "The controls passed and the result supports the stated criterion"
```

Method, data, split, code-logic, or parameter changes create a new iteration. A failed identical
execution creates another run in the same iteration.

New experiment entrypoints use `script_XXX_descriptive_name.py`, where `XXX` matches the
experiment number. Scripts include a traceable module header, explicit configuration and input
validation, descriptive functions and variables, and a clear `main()` boundary. Check and index
research code with:

```bash
smairt code validate
smairt code index
```

To bring an older generated project up to the current Codex guidance without overwriting research
artifacts, preview and apply managed-file updates with:

```bash
smairt upgrade
smairt upgrade --apply
```

Differing managed guidance is backed up under `.smairt/backups/` before replacement.

## Corrections without erasing history

SMAIRT treats corrections as part of the scientific record:

```bash
smairt amend \
  --record results/EXPERIMENT_001/ITERATION_001/RUN_ID/run.json \
  --field "sample_count" --previous "10" --corrected "12" \
  --reason "Corrected metadata"
smairt retract --experiment EXPERIMENT_001 --reason "Invalid input data"
smairt supersede --experiment EXPERIMENT_001 --reason "Replaced by corrected analysis"
```

Amendments append context. Retractions preserve the invalidated record. Supersession marks the
previously accepted experiment selection as replaced so a corrected selection can be recorded.
The paper validator rejects links to evidence that is not accepted and current.

## Generated project structure

```text
project/
├── smairt.yaml                 # Authoritative project contract
├── AGENTS.md                   # Short cross-harness instructions
├── .agents/skills/             # Progressive SMAIRT research guidance
├── .codex/                     # Codex project configuration and hooks
├── prompts/                    # Coding, research, interpretation, and paper conventions
├── references/
│   ├── index.yaml              # Machine-readable source index
│   └── pdfs/                   # Local, Git-ignored source documents
├── background/                 # Initial question, description, and synthesis
├── plans/                      # Research and implementation plans
├── hypotheses/                 # Proposal sets and selected hypotheses
├── experiments/                # Experiment definitions and versioned iterations
├── scripts/shared/             # Reusable project code
├── results/                    # Immutable recorded runs and artifacts
├── analysis/                   # Interpretation separated from raw results
└── paper/                      # Working prose, drafts, figures, tables, and provenance
```

## Safety and responsibility

SMAIRT provides safeguards, not institutional compliance certification. Researchers remain
responsible for their applicable policies, data-use agreements, security controls, ethics review,
and publication requirements.

The selected data classification is visible to the harness and validator. Generated Git rules
exclude common credential files, private reference PDFs, raw sequencing formats, and local data
directories. Controlled-data projects receive additional warnings. Secrets should still be kept
in environment variables or an approved secret manager—not entered into prompts or committed.

## Current v1 scope

Version 1 focuses on:

- Local macOS and Linux projects
- Codex app and Codex CLI workflows
- A portable on-disk contract usable by other harnesses in the future
- Conda or externally managed execution environments
- Research provenance and paper-evidence validation

Direct model API calls, automatic manuscript generation, browser-only workflows, hosted project
services, OpenCode-specific integration, institutional policy engines, and domain profiles are
intentionally deferred. The core is generic so those capabilities can be added without changing
the research record.

## Multi-harness roadmap

SMAIRT is being built as a research harness that can travel across agent tools. The sequence
matters: first stabilize the portable artifact and safety contracts; then add thin integrations.

1. **Codex reference implementation** — exercise guided actions, project skills, local execution,
   and explicit human gates in Codex App and CLI.
2. **Portable adapter contract** — formalize `status`, `next`, validation, command, and artifact
   schemas with compatibility fixtures.
3. **OpenCode adapter** — translate SMAIRT guidance and human gates into OpenCode's project and
   tool conventions without duplicating project state.
4. **MCP surface** — expose read-only state/context resources plus narrowly scoped project actions
   for clients that support MCP.
5. **Provider-neutral AI adapters** — optionally support OpenAI-compatible institutional endpoints
   and other providers through separate adapters, never by embedding credentials in projects.
6. **Domain and policy profiles** — add opt-in scientific-field conventions and stricter
   institutional safety policies after the generic core has real-world evidence.

No adapter should weaken the central guarantees: author identity is manual, scientific decisions
are human, runs are immutable, protected data stays local, and paper claims point to accepted
evidence.

## What remains before a stable v1 release

- Dogfood complete workflows on the enzyme-kinetics example and the PhD research repository.
- Refine guidance from real Codex conversations and failure recovery.
- Add explicit paper-element creation and replacement-run linking commands.
- Exercise real Conda creation and existing-environment selection on macOS and Linux.
- Push the branch and confirm the CI matrix on GitHub.
- Add versioning, changelog, release automation, source-distribution checks, and PyPI publication.
- Freeze and document the portable adapter schemas before implementing other harnesses.

## Development

```bash
python -m pytest
ruff check src tests
python -m pip wheel . --no-deps --wheel-dir dist
```

The detailed design and roadmap live in:

- [`docs/specs/SMAIRT_V1_SPEC.md`](docs/specs/SMAIRT_V1_SPEC.md)
- [`docs/plans/SMAIRT_V1_IMPLEMENTATION.md`](docs/plans/SMAIRT_V1_IMPLEMENTATION.md)

## License and acknowledgment

SMAIRT is distributed under the MIT License. See [`LICENSE`](LICENSE) and
[`CITATION.cff`](CITATION.cff).

This evolution acknowledges the original SMAIRT work and conventions developed by the Pacific
Northwest National Laboratory computational biology team. Subsequent contributors are building on
that foundation to make careful, reproducible AI-assisted research easier to practice across
tools.
