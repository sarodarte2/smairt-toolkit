# Codex

> **At a glance:** Codex is the strongest fit for researchers who want a terminal-first OpenAI
> workflow with project skills, trusted hooks, and native custom subagents.

## Choose Codex if

- You already use Codex CLI or the Codex app for repository work.
- You want explicit `$smairt-*` skills with natural conversational matching.
- You want adversarial review in a project-defined read-only subagent.

Choose another harness if your work is primarily IDE-centered or you need a mode-centric visual
orchestrator.

## Five-minute setup

```bash
smairt harness select codex --dry-run
smairt harness select codex
smairt harness status codex
```

Open the project in Codex, review the project trust prompt, and inspect `/hooks`. Project
configuration and hooks are ignored until the project is trusted.

## Native SMAIRT experience

- Invoke `$smairt-next`, `$smairt-literature`, `$smairt-design`, `$smairt-interpret`, or
  `$smairt-paper` directly, or ask for the corresponding workflow conversationally.
- Invoke `$smairt-challenge` explicitly to delegate a bounded packet to `smairt-reviewer`.
- The reviewer runs with `sandbox_mode = "read-only"` and inherits the current model unless the
  generated project agent is deliberately customized.
- Session and compact hooks restore bounded SMAIRT context. Pre-tool hooks inspect protected
  operations, but CLI and integrity gates remain authoritative.

## Managed files

Codex uses `AGENTS.md`, `.agents/skills/`, `.codex/config.toml`, `.codex/agents/`, and
`.codex/hooks.json`. Optional MCP configuration exposes only SMAIRT's read-only metadata tools.

See the official [Codex skills](https://developers.openai.com/codex/skills),
[subagents](https://developers.openai.com/codex/subagents), and
[hooks](https://learn.chatgpt.com/codex/hooks) documentation.
