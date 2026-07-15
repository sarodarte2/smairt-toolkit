# Claude Code adapter

## Audience fit

Choose Claude Code when you want a terminal-native Claude workflow with project skills, trusted
hooks, merge-owned settings, and a read-only plan-mode reviewer.

## Prerequisites

Install Claude Code and SMAIRT separately. Project trust, authentication, and model selection
remain Claude Code responsibilities.

## Setup

Preview the managed-file changes before applying them:

```bash
smairt harness select claude --dry-run
smairt harness select claude
smairt harness status claude
```

Review the generated files and approve project trust when Claude Code asks about hooks or MCP
configuration.

## Generated files

Claude Code uses `.claude/CLAUDE.md`, `.claude/skills/`, `.claude/agents/`, and a managed hook.
SMAIRT merges only its recorded entries into `.claude/settings.json` and `.mcp.json`.

## Capabilities

- Six explicit project skills expose the shared workflow contract.
- `/smairt-challenge` uses a read-only plan-mode reviewer.
- Session, pre-tool, and compact hooks restore guidance or inspect supported protected operations.
- Optional MCP exposes only bounded reference metadata.

## Limitations

Claude Code controls project trust and hook execution. Existing permissions, hooks, and MCP servers
remain researcher-owned; switching adapters removes only recorded SMAIRT fragments.

## Official references

- [Settings](https://code.claude.com/docs/en/configuration)
- [Hooks](https://code.claude.com/docs/en/hooks)
- [Skills](https://code.claude.com/docs/en/skills)
- [Subagents](https://code.claude.com/docs/en/sub-agents)
