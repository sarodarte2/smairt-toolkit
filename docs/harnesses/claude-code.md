# Claude Code

SMAIRT's Claude Code adapter is project-scoped. Select it with
`smairt harness select claude`, review the generated files, and then approve the
project when Claude Code asks whether to trust its hooks and MCP configuration.

The adapter generates `.claude/CLAUDE.md`, six explicit project skills, a
read-only plan-mode reviewer, and a bounded hook for session restoration and
protected operations. `smairt integration mcp claude --enabled` adds the
read-only SMAIRT server to `.mcp.json`.

SMAIRT merges its entries into `.claude/settings.json` and `.mcp.json`. Existing
permissions, hooks, and MCP servers remain researcher-owned; switching away
removes only the SMAIRT entries. Credentials never belong in either file.

Claude Code remains responsible for project trust and hook execution. The
adapter supplements, but never replaces, SMAIRT's CLI validation, transactions,
integrity checks, and human scientific gates.
