# SMAIRT Quickstart

This tour installs no scientific opinion and records no evidence decision. It creates a project,
shows where state lives, and explains how to resume work safely.

## 1. Open Home

Run one command from any folder:

```bash
smairt
```

First-time setup is recommended but skippable. It checks readiness and saves only profile values
you explicitly enter. Literature and HPC remain optional.

## 2. Create a project

Choose **Create a project**. The four stages are Basics, Research Context, Project Choices, and
Review. The folder follows the project name until edited. Profile values prefill only when present;
classification, license, environment, AI assistant, safety, and Git remain explicit choices.
Additional contributors are added afterward under Project → Contributors.

For a scriptable preview without Git initialization:

```bash
smairt new my-study --name "My Study" --author "Contributor Name" \
  --accept-recommended --confirm-contributor
```

## 3. Inspect the project

Open the project from Home. SMAIRT remembers up to five recent projects and discovers direct
project folders beneath an explicitly saved project parent. It never recursively scans or silently
chooses among projects.

The dashboard highlights Ground, Explore, Test, Interpret, or Share. Choose **Continue** for a
project-aware command or bounded assistant prompt. Advanced users can request it from any folder:

```bash
smairt --project /path/to/my-study next --prompt
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
