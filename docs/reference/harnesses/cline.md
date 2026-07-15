# Cline adapter

## Audience fit

Choose Cline when you want visible Plan/Act transitions, project workflows, lifecycle hooks, and an
isolated read-only reviewer inside a VS Code-compatible editor.

## Prerequisites

Install Cline in a supported editor and install SMAIRT on the same machine. Hooks remain inactive
until enabled in Cline.

## Setup

Preview the managed-file changes before applying them:

```bash
smairt harness select cline --dry-run
smairt harness select cline
smairt harness status cline
```

Enable Cline hooks in its settings, then review `.clinerules`, `.clineignore`, and
`.cline/workflows/`.

## Generated files

Cline uses `.clinerules/`, `.cline/workflows/`, `.clineignore`, managed hook executables, and
optional project MCP configuration.

## Capabilities

- Six `/smairt-*` workflows label planning work and the boundary where Act or a human decision is
  needed.
- Task-start, resume, and compact hooks restore guidance.
- `PreToolUse` can cancel matching protected operations when hooks are enabled.
- `/smairt-challenge` requests an isolated read-only subagent.

## Limitations

Hook enforcement depends on the client setting. A guaranteed different-model reviewer requires an
optional extension path that SMAIRT does not install automatically.

## Official references

- [Plan and Act](https://docs.cline.bot/core-workflows/plan-and-act)
- [Hooks](https://docs.cline.bot/customization/hooks)
- [Subagents](https://docs.cline.bot/features/subagents)
