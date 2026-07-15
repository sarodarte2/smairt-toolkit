# Cline

> **At a glance:** Cline fits researchers who want explicit Plan/Act transitions, stable workflow
> commands, lifecycle hooks, and isolated read-only subagents.

## Choose Cline if

- You prefer planning and approval to be visibly separated from implementation.
- You want `/smairt-*` workflows inside a VS Code-compatible editor.
- You are comfortable enabling and reviewing project hooks.

Choose another harness if cross-model adversarial review must work without optional extensions.

## Five-minute setup

```bash
smairt harness select cline --dry-run
smairt harness select cline
smairt harness status cline
```

Enable Cline hooks in its settings, then review `.clinerules`, `.clineignore`, and
`.cline/workflows/` before beginning research work.

## Native SMAIRT experience

- `/smairt-next`, `/smairt-literature`, `/smairt-design`, `/smairt-challenge`,
  `/smairt-interpret`, and `/smairt-paper` are stable project workflows.
- Each workflow labels its planning work and the point at which Act or a human decision is needed.
- Task-start, resume, and compact hooks restore guidance; `PreToolUse` can cancel protected
  operations when hooks are enabled.
- `/smairt-challenge` asks Cline for a standard isolated read-only subagent.
- A guaranteed different-model review requires the optional Agent Squad plugin or SDK. SMAIRT does
  not install it automatically.

## Managed files

Cline uses `.clinerules/`, `.cline/workflows/`, `.clineignore`, executable hook files, and optional
project MCP configuration.

See the official [Plan and Act](https://docs.cline.bot/core-workflows/plan-and-act),
[hooks](https://docs.cline.bot/customization/hooks), and
[subagents](https://docs.cline.bot/features/subagents) documentation.
