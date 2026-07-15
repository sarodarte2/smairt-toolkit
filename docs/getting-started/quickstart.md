# SMAIRT Quickstart

This tour installs no scientific opinion and records no evidence decision. It creates a project,
shows where state lives, and explains how to resume work safely.

## 1. Complete user-wide setup

Run the setup doctor and open the guided setup workspace:

```bash
smairt setup doctor --json
smairt setup
```

Literature and HPC profiles are optional. Skip them unless they are relevant to your work. Setup
belongs to this machine; project policy and research records belong to the project directory.

## 2. Create a project

```bash
smairt new my-study
```

The wizard asks whether to create a named child directory or initialize a directory you selected.
It then asks for project identity, researcher identity, field, license, data classification,
environment, coding harness, and safety mode. A project may begin with an open question; it does
not need a hypothesis during setup.

For a scriptable preview without Git initialization:

```bash
smairt new my-study --name "My Study" --author "Researcher Name" \
  --question "What specific question will this project investigate?" \
  --confirm-contributor --classification unpublished --no-git
```

## 3. Inspect the project

```bash
cd my-study
smairt doctor --json
smairt status --json
smairt next --json
```

`doctor` reports health without changing files or using the network. `status` describes the active
project records. `next` recommends an action from the current state and identifies the files that
matter for that action.

For a copyable handoff to an AI assistant:

```bash
smairt next --prompt
```

The prompt is bounded context, not authorization. It cannot select a hypothesis, approve an
experimental route, accept evidence, or approve a claim.

## 4. Understand the record

Open these files before beginning scientific work:

- `smairt.yaml` — project identity, contributors, policy, environment, safety mode, and active
  harness.
- `background/initial_question.md` — the opening research question.
- `background/project_description.md` — scope and context supplied during setup.
- `AGENTS.md` — shared boundaries for supported coding assistants.
- `docs/PHILOSOPHY.md` and `docs/WORKFLOW.md` — the generated project's scientific conventions.

Local connection bindings, locks, transactions, and caches live under `.smairt/`. Secrets do not
belong in the project configuration. Local reference PDFs and raw research data are ignored by
default.

## 5. Choose the next guide

- Continue through the [research workflow](../guides/research-workflow.md) when you have real
  sources and a question to develop.
- Configure scholarly services in [Literature integrations](../guides/integrations.md).
- Compare coding assistants in the [Harness guide](../reference/harnesses.md).
- Read the [Safety model](../concepts/safety.md) before private work.

Do not fill placeholders merely to advance the state machine. A scientific gate should advance
only when the corresponding researcher judgment is ready to be recorded.
