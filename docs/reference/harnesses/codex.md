# Codex adapter

## Audience fit

Choose Codex when you want a terminal-first OpenAI workflow with project skills, trusted hooks,
and a native read-only reviewer. An IDE-first or mode-oriented workflow may fit another adapter
better.

## Prerequisites

Install Codex and SMAIRT separately. Confirm both executables are available before changing the
project adapter.

## Setup

Preview the managed-file changes before applying them:

```bash
smairt harness select codex --dry-run
smairt harness select codex
smairt harness status codex
```

Open the project in Codex, review the project trust prompt, and inspect the configured hooks before
using them. Project configuration is inactive until the client trusts the project.

## Generated files

Codex uses `AGENTS.md`, `.agents/skills/`, `.codex/config.toml`, `.codex/agents/`, and
`.codex/hooks.json`, plus one managed hook executable. Optional MCP configuration exposes only
SMAIRT's metadata tools.

## Capabilities

- Invoke `$smairt-next`, `$smairt-literature`, `$smairt-design`, `$smairt-interpret`, and
  `$smairt-paper`, or request the corresponding workflow conversationally.
- Invoke `$smairt-challenge` explicitly to delegate a bounded packet to `smairt-reviewer`.
- The reviewer is project-defined and read-only; it inherits the current model unless deliberately
  customized.
- Session and compact hooks can restore bounded project guidance.

## Limitations

Project hooks require trust and do not cover every possible tool or external process. CLI,
transaction, integrity, and human-decision gates remain authoritative.

## Official references

- [Codex skills](https://developers.openai.com/codex/skills)
- [Codex subagents](https://developers.openai.com/codex/subagents)
- [Codex hooks](https://learn.chatgpt.com/codex/hooks)
