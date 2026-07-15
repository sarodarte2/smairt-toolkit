# OpenCode

> **At a glance:** OpenCode fits researchers who want a provider-flexible, terminal-first agent
> governed by explicit project permissions.

## Choose OpenCode if

- You prefer an open terminal workflow and may change model providers.
- Explicit command and permission configuration is more useful than editor modes.
- You want a native read-only reviewer without installing a project plugin.

Choose another harness if you want editor-native Plan/Act or mode switching.

## Five-minute setup

```bash
smairt harness select opencode --dry-run
smairt harness select opencode
smairt harness status opencode
```

Review `opencode.json`, especially its shell and external-directory permissions, before starting
OpenCode in the project.

## Native SMAIRT experience

- Six `.opencode/commands/smairt-*.md` wrappers expose the portable skill contract.
- `/smairt-challenge` hands a bounded packet to the `smairt-reviewer` subagent.
- The reviewer cannot edit files, run shell commands, or use external directories.
- A reviewer model can be configured natively, but inheritance remains the portable default.
- SMAIRT deliberately does not install an executable TypeScript or JavaScript project plugin.

## Managed files

OpenCode uses `AGENTS.md`, `.agents/skills/`, `.opencode/commands/`, `.opencode/agents/`, and
`opencode.json`. Optional MCP exposes read-only metadata tools.

See the official OpenCode [agents](https://opencode.ai/docs/agents/),
[skills](https://opencode.ai/docs/skills), and [plugins](https://opencode.ai/docs/plugins/)
documentation.
