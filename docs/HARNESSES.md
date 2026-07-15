# Choose a Coding Harness

SMAIRT supports one active coding-harness adapter per project: Codex, Zoo Code, Cline, OpenCode,
Cursor, or Claude Code. Choosing a harness changes rules, workflows, hooks, and permissions;
it does not change portable scientific records.

Start with the tool in which you already work comfortably. Then compare its safety integration,
review isolation, and setup requirements. No adapter replaces SMAIRT's CLI, Git, integrity checks,
or human scientific gates.

```bash
smairt harness list
smairt harness info codex
smairt harness select cursor --dry-run
```

## At a glance

| Harness | Best fit | Workflow calls | Safety integration | Adversarial review |
| --- | --- | --- | --- | --- |
| [Codex](harnesses/codex.md) | Terminal-first OpenAI agent work | `$smairt-*` skills | Trusted project hooks | Native read-only project subagent |
| [Zoo Code](harnesses/zoo-code.md) | Visible roles, modes, and orchestration | `/smairt-*` skills | Rules and read-only review mode | Dedicated mode with optional sticky model |
| [Cline](harnesses/cline.md) | Explicit Plan/Act transitions | `/smairt-*` workflows | Blocking hook when enabled | Standard read-only subagent |
| [OpenCode](harnesses/opencode.md) | Open, provider-flexible terminal work | `/smairt-*` commands | Project permissions | Native read-only subagent |
| [Cursor](harnesses/cursor.md) | IDE-centered research and coding | `/smairt-*` skills | Hooks and CLI permissions | Native read-only project subagent |
| [Claude Code](harnesses/claude-code.md) | Terminal-native Claude projects | `/smairt-*` skills | Trusted project hooks | Read-only plan-mode project subagent |

## A practical decision path

1. Choose **Codex** for a terminal-first OpenAI workflow with project skills and native custom
   agents.
2. Choose **Zoo Code** when explicit roles, modes, and orchestrated handoffs are central to how you
   work.
3. Choose **Cline** when you value an obvious Plan-to-Act transition and lifecycle hooks in a
   VS Code-compatible editor.
4. Choose **OpenCode** for a provider-flexible terminal workflow governed primarily by explicit
   permissions.
5. Choose **Cursor** when your research coding happens primarily inside Cursor and you want native
   rules, skills, hooks, and subagents.
6. Choose **Claude Code** for its terminal workflow, project skills, hooks, and plan-mode reviewer.

If two harnesses seem equally suitable, prefer the one whose editor or terminal experience you
already trust. Switching later is safe: preview it first, and use `--backup-and-switch` only after
reviewing any modified managed files.

## What each extension surface does

| Surface | SMAIRT purpose |
| --- | --- |
| `AGENTS.md` and rules | Ambient project conventions and human decision boundaries |
| Skills and commands | Researcher-triggered workflows such as literature, design, and interpretation |
| Native modes | The harness's normal planning, coding, asking, or orchestrating behavior |
| Hooks and permissions | Deterministic checks around tool calls and lifecycle events |
| Agents and subagents | Isolated adversarial review or bounded independent investigation |
| MCP | Optional read-only reference metadata access |
| SMAIRT CLI | Authoritative scientific state changes, provenance, validation, and approvals |

The six maintained workflow entrypoints are `smairt-next`, `smairt-literature`, `smairt-design`,
`smairt-challenge`, `smairt-interpret`, and `smairt-paper`. `smairt-challenge` is intentionally an
explicit action because it may launch another agent or model.

## Limits that status reports honestly

- Codex, Cursor, and Claude Code project hooks require project trust.
- Cline hooks must be enabled in Cline settings.
- Zoo Code has no documented blocking protected-operation hook.
- OpenCode uses permissions; SMAIRT does not install executable project plugins automatically.
- A different reviewer model is optional. Cline requires its advanced Agent Squad path to
  guarantee one; the portable workflow still works with an isolated same-model reviewer.

Run `smairt harness status --json` to distinguish generated adapter health from settings controlled
by the local harness. Credential values remain in environment variables or the OS keyring and are
never written to adapter files.

Claude settings and MCP files are merge-owned: SMAIRT preserves unrelated user configuration and
removes only its recorded permissions, hooks, and server entry when switching away.

Google Antigravity is under evaluation, not presented as a maintained seventh adapter. See the
[feasibility gate](harnesses/antigravity-feasibility.md) for the mapped surfaces and missing
compatibility evidence.
