# Cursor adapter

## Audience fit

Choose Cursor when most research coding occurs in an IDE and you want project rules, skills, hooks,
CLI permissions, and read-only subagents in the same client family.

## Prerequisites

Install Cursor or Cursor Agent CLI and install SMAIRT on the same machine. Project trust and client
authentication remain Cursor responsibilities.

## Setup

Preview the managed-file changes before applying them:

```bash
smairt harness select cursor --dry-run
smairt harness select cursor
smairt harness status cursor
```

Trust the project, review and enable its hooks, and inspect `.cursor/cli.json` before using Cursor
Agent CLI with write access.

## Generated files

Cursor uses `.agents/skills/`, `.cursor/rules/`, `.cursor/agents/`, `.cursor/hooks.json`,
`.cursor/cli.json`, `.cursorignore`, and optional `.cursor/mcp.json`.

## Capabilities

- Invoke `/smairt-*` skills from the appropriate built-in mode.
- `/smairt-challenge` delegates to a project reviewer with `readonly: true`.
- The reviewer inherits the parent model unless a native override is configured.
- Hooks inspect protected tool calls; CLI permissions restrict sensitive reads and destructive
  command families. Git remains prompt-gated.

## Limitations

Project trust and local hook settings remain controlled by Cursor. Built-in and user-defined modes
are not replaced by SMAIRT.

## Official references

- [Cursor skills](https://cursor.com/docs/skills)
- [Cursor subagents](https://cursor.com/docs/subagents)
- [Cursor modes](https://docs.cursor.com/agent)
- [Cursor CLI permissions](https://docs.cursor.com/cli/reference/permissions)
