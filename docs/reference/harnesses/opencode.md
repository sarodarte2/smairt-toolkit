# OpenCode adapter

## Audience fit

Choose OpenCode when you want a provider-flexible terminal agent governed primarily by explicit
project permissions.

## Prerequisites

Install OpenCode and SMAIRT separately. Choose and authenticate the model provider through
OpenCode; SMAIRT does not store that credential.

## Setup

Preview the managed-file changes before applying them:

```bash
smairt harness select opencode --dry-run
smairt harness select opencode
smairt harness status opencode
```

Review `opencode.json`, especially shell and external-directory permissions, before starting the
client in the project.

## Generated files

OpenCode uses `AGENTS.md`, `.agents/skills/`, `.opencode/commands/`, `.opencode/agents/`, and
`opencode.json`. Optional MCP configuration exposes read-only metadata.

## Capabilities

- Six `.opencode/commands/smairt-*.md` wrappers expose the shared workflow contract.
- `/smairt-challenge` sends a bounded packet to `smairt-reviewer`.
- The reviewer cannot edit files, run shell commands, or access external directories.
- A reviewer model may be configured natively; inheritance remains the portable default.

## Limitations

SMAIRT does not install an executable TypeScript or JavaScript project plugin merely to gain hook
parity. Permission files supplement SMAIRT's own gates.

## Official references

- [OpenCode agents](https://opencode.ai/docs/agents/)
- [OpenCode skills](https://opencode.ai/docs/skills)
- [OpenCode plugins](https://opencode.ai/docs/plugins/)
