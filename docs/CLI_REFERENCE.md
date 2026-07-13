# SMAIRT CLI Reference

Run `smairt <command> --help` for option-level help. Noninteractive machine consumers should use
`--json`; mutating confirmation gates support `--yes` where bypassing a prompt is appropriate.

| Group | Purpose |
|---|---|
| `new`, `init`, `menu` | Create or inspect a project through the researcher-first UX |
| `status`, `next`, `context`, `doctor` | Inspect local state, bounded context, and health |
| `contributor` | Register and select manually confirmed people |
| `reference`, `background`, `hypothesis` | Build source-grounded scientific framing |
| `experiment`, `iteration`, `run`, `decision` | Execute and interpret immutable research work |
| `summary`, `paper`, `amend`, `retract`, `supersede` | Curate evidence, publication, and corrections |
| `safety` | Inspect modes, attest visibility, explicitly refresh, and run release gates |
| `harness` | Preview, install, select, and diagnose Codex, Zoo, or Cline adapters |
| `lock`, `recovery` | Inspect writer ownership and resolve interrupted transactions |
| `verify`, `contract`, `code`, `env`, `model`, `upgrade` | Integrity, portability, readability, environment, economy, and framework tools |

## JSON envelope

```json
{
  "schema_version": 1,
  "command": "smairt status",
  "ok": true,
  "data": {},
  "warnings": [],
  "errors": []
}
```

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | Success |
| 1 | Validation or policy failure |
| 2 | Invalid usage or project state |
| 3 | Mutation lock conflict or recovery required |

`smairt run` propagates the child exit status where applicable; launch failure uses 126 or 127 and
interruption uses 130/143 conventions.
