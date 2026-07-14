# SMAIRT CLI Reference

Run `smairt <command> --help` for option-level help. Noninteractive machine consumers should use
`--json`; mutating confirmation gates support `--yes` where bypassing a prompt is appropriate.

Bare `smairt` prints a deterministic welcome with version, credits, license, and suggested entry
points. `smairt setup` opens machine-wide setup, `smairt new` opens project creation, and `smairt
menu` opens the dashboard for the project containing the current folder. In every menu, Up/Down
and j/k wrap at both ends; Enter accepts, Escape returns one level, and Ctrl-C exits.

```bash
smairt setup
smairt setup doctor [--check-github] [--json]
smairt setup credential list|set|delete|doctor
smairt setup zotero configure|test|remove
smairt setup openalex configure|test|remove
smairt new [DESTINATION]
smairt menu
smairt settings show --json
smairt settings project [--field TEXT]... [--license LICENSE]
smairt env select --mode none
smairt env select --mode existing_conda --prefix PATH
smairt env select --mode new_conda --name NAME --create
smairt next --json|--prompt
smairt integration bind|unbind|status|test
smairt harness list|status [HARNESS] [--json]
smairt harness select HARNESS [--dry-run|--backup-and-switch]
smairt harness upgrade HARNESS
smairt reference add-doi DOI [--openalex] [--confirm-remote]
smairt reference import-zotero --item KEY
smairt reference import-zotero --collection KEY [--limit 1..1000]
smairt reference attach REFERENCE_ID PDF
smairt mcp status|enable|disable --harness codex|zoo|cline|opencode|cursor [--dry-run]
smairt mcp serve
```

| Group                                                   | Purpose                                                                        |
| ------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `setup`                                                 | Configure this machine's credentials and connection profiles                   |
| `new`, `menu`                                           | Create a project or open its five-area dashboard                               |
| `status`, `next`, `context`, `doctor`                   | Inspect local state, bounded context, and health                               |
| `contributor`                                           | Register and select manually confirmed people                                  |
| `reference`, `background`, `hypothesis`                 | Build source-grounded scientific framing                                       |
| `credential`, `integration`, `mcp`                      | Compatibility commands, project bindings, and read-only agent metadata access  |
| `experiment`, `iteration`, `run`, `decision`            | Execute and interpret immutable research work                                  |
| `summary`, `paper`, `amend`, `retract`, `supersede`     | Curate evidence, publication, and corrections                                  |
| `safety`                                                | Inspect modes, attest visibility, explicitly refresh, and run release gates    |
| `harness`                                               | Preview, install, select, and diagnose five maintained coding harness adapters |
| `lock`, `recovery`                                      | Inspect writer ownership and resolve interrupted transactions                  |
| `verify`, `contract`, `code`, `env`, `model`, `upgrade` | Integrity, portability, readability, environment, economy, and framework tools |

`smairt init` and `smairt start project` are deprecated aliases for the creation wizard.
The older nested `integration zotero` and `integration openalex` commands remain compatibility
surfaces; new setup should use `smairt setup ...` plus `smairt integration bind`.

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

| Code | Meaning                                     |
| ---: | ------------------------------------------- |
|    0 | Success                                     |
|    1 | Validation or policy failure                |
|    2 | Invalid usage or project state              |
|    3 | Mutation lock conflict or recovery required |

`smairt run` propagates the child exit status where applicable; launch failure uses 126 or 127 and
interruption uses 130/143 conventions.
