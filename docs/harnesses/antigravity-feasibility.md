# Google Antigravity feasibility

Google Antigravity appears technically feasible as a future SMAIRT harness, but it is deliberately
not added to the maintained harness enum yet. Its documented rules/workflows, skills, hooks, MCP,
and CLI permission surfaces map to SMAIRT's shared guidance, explicit workflows, deterministic hook
policy, metadata-only server, and bounded command permissions.

The remaining gate is compatibility evidence, not file generation. A maintained adapter should be
added only after fixture tests prove project-trust behavior, hook blocking semantics, merge-safe MCP
ownership, read-only reviewer isolation, removal of only SMAIRT-owned fragments, and stable behavior
across Antigravity updates. Until then, researchers can use SMAIRT's portable CLI and `AGENTS.md`
without SMAIRT claiming native integration.

Primary documentation reviewed for this decision:

- [Rules and workflows](https://antigravity.google/docs/rules-workflows)
- [Hooks](https://www.antigravity.google/docs/hooks)
- [MCP](https://antigravity.google/docs/mcp)
- [Skills](https://antigravity.google/docs/skills)
- [CLI permissions](https://www.antigravity.google/docs/cli-permissions)
