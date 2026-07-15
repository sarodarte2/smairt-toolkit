# Zoo Code adapter

## Audience fit

Choose Zoo Code when visible roles, custom modes, and orchestrated handoffs are central to the way
you work. Choose another adapter when a documented blocking protected-operation hook is required.

## Prerequisites

Install Zoo Code and SMAIRT separately. SMAIRT does not install or authenticate the client.

## Setup

Preview the managed-file changes before applying them:

```bash
smairt harness select zoo --dry-run
smairt harness select zoo
smairt harness status zoo
```

Review the generated `.roo` rules, `.rooignore`, and `SMAIRT · Evidence Review` mode. SMAIRT does
not reuse a built-in mode slug.

## Generated files

Zoo Code uses `.agents/skills/`, `.roo/rules/`, mode-specific rule folders, `.roomodes`,
`.rooignore`, and optional `.roo/mcp.json` metadata access.

## Capabilities

- `/smairt-*` project skills can be invoked from appropriate native modes.
- Planning can remain in Architect, implementation in Code, and read-only discussion in Ask.
- `/smairt-challenge` delegates to the dedicated read-only review mode when available.
- The review mode may remember a separately chosen model.

## Limitations

Rules and modes are advisory. Zoo Code has no documented blocking protected-operation hook that
SMAIRT can treat as equivalent to its CLI gates.

## Official references

- [Custom modes](https://github.com/zoo-code-org/zoo-code-docs/blob/main/docs/features/custom-modes.mdx)
- [Skills](https://github.com/zoo-code-org/zoo-code-docs/blob/main/docs/features/skills.mdx)
- [Slash commands](https://github.com/zoo-code-org/zoo-code-docs/blob/main/docs/features/slash-commands.mdx)
