# Cursor

> **At a glance:** Cursor fits researchers who want SMAIRT rules, skills, hooks, and read-only
> subagents embedded in an IDE-first workflow.

## Choose Cursor if

- Most research coding already happens inside Cursor.
- You want `/smairt-*` project skills and clickable file-oriented conversations.
- You use both Cursor IDE and Cursor CLI and want project-level restrictions for each.

Choose another harness if you prefer a terminal-first or mode-orchestration experience.

## Five-minute setup

```bash
smairt harness select cursor --dry-run
smairt harness select cursor
smairt harness status cursor
```

Trust the project, review and enable its hooks, then inspect `.cursor/cli.json` before using Cursor
Agent CLI with write access.

## Native SMAIRT experience

- Use `/smairt-next` and the other `/smairt-*` project skills from Agent or Ask as appropriate.
- Built-in Agent, Ask, Manual, and user-defined modes remain untouched.
- `/smairt-challenge` delegates to the `smairt-reviewer` project agent with `readonly: true`.
- The reviewer inherits the parent model by default; a native model override is optional.
- Project hooks inspect protected tool calls, while CLI permissions deny sensitive reads and
  destructive command families. Git remains prompt-gated rather than broadly allowlisted.

## Managed files

Cursor uses `.agents/skills/`, `.cursor/rules/`, `.cursor/agents/`, `.cursor/hooks.json`,
`.cursor/cli.json`, `.cursorignore`, and optional `.cursor/mcp.json`.

See the official Cursor [skills](https://cursor.com/docs/skills),
[subagents](https://cursor.com/docs/subagents), [modes](https://docs.cursor.com/agent), and
[CLI permissions](https://docs.cursor.com/cli/reference/permissions) documentation.
