# Harness Adapters

SMAIRT supports exactly one active harness per project: Codex, Zoo Code, Cline, OpenCode, or
Cursor. Portable scientific records never change when a harness changes. Preview switches with
`smairt harness select <name> --dry-run`.

| Capability          | Codex                   | Zoo Code    | Cline             | OpenCode           | Cursor               |
| ------------------- | ----------------------- | ----------- | ----------------- | ------------------ | -------------------- |
| Shared rules        | Advisory                | Advisory    | Advisory          | Advisory           | Advisory             |
| Protected operation | Blocking but incomplete | Unsupported | Blocking          | Permissions        | Blocking             |
| Research mode       | Unsupported             | Advisory    | Advisory          | Read-only subagent | Advisory             |
| Context restore     | Session/compact hook    | Manual      | Task/compact hook | Command            | Session/compact hook |
| Read-only MCP       | Opt-in                  | Opt-in      | Opt-in            | Opt-in             | Opt-in               |

Codex uses `.codex/config.toml`, `.codex/hooks.json`, executable project hooks, and shared
`AGENTS.md`. Hooks restore context and inspect Bash, apply-patch, and MCP calls after the user
trusts their hashes. Codex does not intercept every equivalent tool path, so SMAIRT's CLI, Git,
transaction, integrity, and publication gates remain authoritative.

Zoo Code preserves Roo-compatible `.roo` rules, modes, ignore files, skills, and project MCP.
SMAIRT validates its generated mode schema. Zoo has no documented blocking protected-operation
hook, so status reports that capability as unsupported instead of implying enforcement.

Cline uses conditional rules, `.clineignore`, project MCP, and executable `TaskStart`,
`TaskResume`, `PreToolUse`, and `PreCompact` hooks. Its hooks inject current guidance and can cancel
protected operations. Hooks must also be enabled in Cline settings.

OpenCode uses `opencode.json`, a `/smairt-next` command, and a read-only evidence-review subagent.
External-directory access is denied, safe inspection commands are allowlisted, and other shell
operations require review. SMAIRT does not install an executable TypeScript plugin automatically.

Cursor uses `.cursor/rules`, `.cursorignore`, `.cursor/hooks.json`, executable hooks, and project
MCP. Its protected-operation hook is fail-closed; project trust and hook enablement remain
Cursor-controlled settings.

SMAIRT owns individual adapter files through hash manifests. It never deletes an adapter directory
wholesale and preserves custom files. Status reports the local harness binary and version when
discoverable, missing or modified files, executable errors, invalid schemas, adapter age, and
runtime trust steps that SMAIRT cannot confirm.

Credential values remain environment or OS-keyring settings and never enter adapter files.
