# Harness Adapters

SMAIRT supports exactly one active harness per project: Codex, Zoo Code, or Cline. Portable
scientific records never change when a harness changes. Preview switches with
`smairt harness select <name> --dry-run`.

| Capability | Codex | Zoo Code | Cline |
|---|---|---|---|
| Shared project rules | Advisory | Advisory | Advisory |
| Protected-operation hook | Advisory | Unsupported | Blocking when enabled |
| Custom research modes | Unsupported | Advisory | Advisory |
| Automatic context restore | Manual | Manual | Advisory on TaskStart/TaskResume |

Codex uses `.codex/config.toml` and shared `AGENTS.md`. The inline `PreToolUse` hook and
project-scoped MCP entry load only after Codex trusts the project configuration; the hook is
advisory and SMAIRT CLI/Git/integrity gates remain authoritative.

Zoo Code is the correct public name. Zoo deliberately preserves the Roo-compatible `.roo/rules-*`,
`.roomodes`, and `.rooignore` project paths so migrated settings and modes remain usable. SMAIRT
validates its generated mode schema and reports malformed or modified files.
`.roo/mcp.json` contains only the SMAIRT server and the exact five read-only tools in
`alwaysAllow`. Zoo protected-operation hooks remain unsupported.

Cline uses conditional `.clinerules`, `.clineignore`, and executable hooks. `PreToolUse` consumes
the upstream JSON payload and can cancel protected operations. `TaskStart` and `TaskResume` inject
current `smairt status --json`, `smairt next --json`, and context-restoration guidance. Cline still
documents `PreCompact` as coming soon, so SMAIRT does not generate it. Hooks must also be enabled
in Cline settings.

SMAIRT owns individual adapter files through hash manifests. It never deletes an adapter directory
wholesale and preserves custom files. Missing files, modified content, corrupt manifests,
unsupported adapter versions, invalid Zoo modes, and non-executable hooks appear in
`smairt harness status` and `smairt doctor`.

Credential values remain environment or OS-keyring settings and never enter adapter files.
SMAIRT stores only provider/profile references and provider-neutral capability recommendations.
