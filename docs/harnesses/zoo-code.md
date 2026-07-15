# Zoo Code

> **At a glance:** Zoo Code fits researchers who want visible roles, custom modes, and orchestrated
> handoffs while keeping SMAIRT's scientific state in portable files.

## Choose Zoo Code if

- Architect, Code, Ask, Debug, and Orchestrator modes match your working style.
- You want a dedicated evidence-review mode with a remembered model choice.
- You prefer explicit mode-based delegation over a terminal-only agent workflow.

Choose another harness if a documented blocking protected-operation hook is a requirement.

## Five-minute setup

```bash
smairt harness select zoo --dry-run
smairt harness select zoo
smairt harness status zoo
```

Open the project in Zoo Code and review the generated `.roo` rules, `.rooignore`, and
`SMAIRT · Evidence Review` mode. SMAIRT never reuses a built-in mode slug.

## Native SMAIRT experience

- Use `/smairt-next` and the other `/smairt-*` project skills from the appropriate native mode.
- Planning stays in Architect, implementation stays in Code, and read-only discussion can remain
  in Ask.
- `/smairt-challenge` delegates to the read-only `smairt-review` mode when available.
- You may choose a different model once for the review mode and let Zoo remember that selection.
- Rules and modes are advisory; SMAIRT CLI gates remain authoritative.

## Managed files

Zoo uses `.agents/skills/`, `.roo/rules/`, mode-specific rule folders, `.roomodes`, `.rooignore`,
and optional `.roo/mcp.json` metadata access.

See Zoo's official [custom modes](https://github.com/zoo-code-org/zoo-code-docs/blob/main/docs/features/custom-modes.mdx),
[skills](https://github.com/zoo-code-org/zoo-code-docs/blob/main/docs/features/skills.mdx), and
[slash commands](https://github.com/zoo-code-org/zoo-code-docs/blob/main/docs/features/slash-commands.mdx)
documentation.
