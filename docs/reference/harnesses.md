# Coding harness guide

SMAIRT supports one active coding-harness adapter per project: Codex, Zoo Code, Cline, OpenCode,
Cursor, or Claude Code. An adapter changes project rules, workflows, hooks, permissions, and
metadata-only MCP configuration. It does not change the portable scientific record.

```bash
smairt harness list
smairt harness info codex
smairt harness select cursor --dry-run
smairt harness status --json
```

Start with a client you already understand. Then compare how it expresses workflows, isolates
review, and enforces project policy.

## Comparison

| Harness | Best fit | Workflow entry | Safety integration | Adversarial review |
| --- | --- | --- | --- | --- |
| [Codex](harnesses/codex.md) | Terminal-first OpenAI workflow | `$smairt-*` skills | Trusted project hooks | Read-only project subagent |
| [Zoo Code](harnesses/zoo-code.md) | Visible roles and orchestration | `/smairt-*` skills | Rules and modes; advisory | Dedicated read-only review mode |
| [Cline](harnesses/cline.md) | Explicit Plan/Act transitions | `/smairt-*` workflows | Blocking hook when enabled | Read-only subagent |
| [OpenCode](harnesses/opencode.md) | Provider-flexible terminal workflow | `/smairt-*` commands | Project permissions | Read-only subagent |
| [Cursor](harnesses/cursor.md) | IDE-centered research coding | `/smairt-*` skills | Hooks and CLI permissions | Read-only project subagent |
| [Claude Code](harnesses/claude-code.md) | Terminal-native Claude workflow | `/smairt-*` skills | Trusted project hooks | Read-only plan-mode subagent |

## Shared workflow contract

Every adapter exposes six researcher-triggered workflows:

- `smairt-next` — orient to project state and recommended actions;
- `smairt-literature` — search, import, and synthesize attributed sources;
- `smairt-design` — compare hypotheses or define an exploratory experiment;
- `smairt-challenge` — request bounded adversarial review;
- `smairt-interpret` — separate results, inference, limitations, and decisions;
- `smairt-paper` — assemble reviewed evidence, claims, and manuscript text.

Invocation syntax differs by client. `smairt-challenge` is always explicit because it may launch
another agent or model.

## Extension surfaces

| Surface | SMAIRT responsibility |
| --- | --- |
| Rules and `AGENTS.md` | Ambient project conventions and decision boundaries |
| Skills, workflows, or commands | Researcher-triggered task procedures |
| Native modes | The client's normal planning, editing, asking, or orchestration behavior |
| Hooks and permissions | Deterministic checks around supported lifecycle or tool events |
| Agents and subagents | Bounded independent investigation or adversarial review |
| MCP | Optional read-only reference metadata |
| SMAIRT CLI | Authoritative state changes, provenance, validation, and approvals |

No adapter is a sandbox, and no agent instruction replaces project integrity checks or researcher
judgment.

## Switching safely

Preview before replacing an active adapter:

```bash
smairt harness select HARNESS --dry-run
```

Managed-file manifests distinguish generated content from user-owned configuration. If a managed
file was edited, review it and use `--backup-and-switch` only when the backup behavior is
appropriate. Run `smairt harness status --json` afterward to distinguish generated-file health
from client trust, hook enablement, or missing local executables.
