# SMAIRT CLI Reference

Run `smairt <command> --help` for option-level help. Noninteractive machine consumers should use
`--json`; mutating confirmation gates support `--yes` where bypassing a prompt is appropriate.

Bare `smairt` opens a contextual terminal workflow hub on a TTY. Up/Down moves, Enter accepts,
Escape returns one level, and Ctrl-C exits. Redirected or non-TTY use prints help instead of
waiting for input.

```bash
smairt setup doctor [--check-github] [--json]
smairt settings show --json
smairt settings project [--field TEXT]... [--license LICENSE]
smairt env select --mode none
smairt env select --mode existing_conda --prefix PATH
smairt env select --mode new_conda --name NAME --create
smairt credential list|set|delete|doctor
smairt integration openalex configure|status
smairt integration zotero configure --mode local
smairt integration zotero status|test
smairt reference add-doi DOI [--openalex] [--confirm-remote]
smairt reference import-zotero --item KEY
smairt reference import-zotero --collection KEY [--limit 1..1000]
smairt reference attach REFERENCE_ID PDF
smairt mcp status|enable|disable --harness codex|zoo [--dry-run]
smairt mcp serve
```

| Group | Purpose |
|---|---|
| `new`, `init`, `menu` | Create or inspect a project through the researcher-first UX |
| `status`, `next`, `context`, `doctor` | Inspect local state, bounded context, and health |
| `contributor` | Register and select manually confirmed people |
| `reference`, `background`, `hypothesis` | Build source-grounded scientific framing |
| `credential`, `integration`, `mcp` | Configure non-secret provider references and read-only agent metadata access |
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
