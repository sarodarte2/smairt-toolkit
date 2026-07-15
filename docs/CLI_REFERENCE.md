# SMAIRT CLI Reference

Run `smairt <command> --help` for option-level help. Noninteractive machine consumers should use
`--json`; mutating confirmation gates support `--yes` where bypassing a prompt is appropriate.

Bare `smairt` prints a deterministic welcome with version, credits, license, and suggested entry
points. `smairt setup` opens machine-wide setup, `smairt new` opens project creation, and `smairt
menu` opens the dashboard for the project containing the current folder. In every menu, Up/Down
and j/k move through every row, including the visible Back row; Enter accepts, Left/Escape returns
one level immediately, and Ctrl-C exits. Navigation wraps after Back to the first action.

```bash
smairt setup
smairt setup doctor [--check-github] [--json]
smairt setup credential list|set|delete|doctor
smairt setup zotero configure|test|remove
smairt setup openalex configure|test|remove
smairt setup semantic-scholar configure|test|remove
smairt setup unpaywall configure default --email EMAIL
smairt setup hpc configure default --mode native|ssh [--host HOST] --remote-root PATH
smairt new [DESTINATION]
smairt menu [PROJECT]
smairt update [--apply --yes] [--allow-dirty] [--json]
smairt settings show --json
smairt settings project [--field TEXT]... [--license LICENSE]
smairt env select --mode none
smairt env select --mode existing_conda --prefix PATH
smairt env select --mode new_conda --name NAME --create
smairt next --json|--prompt
smairt context --task planning|code|run|interpretation|paper|review [--target PATH]
smairt integration bind|unbind|status|test
smairt harness list|status [HARNESS] [--json]
smairt harness info HARNESS [--json]
smairt harness select HARNESS [--dry-run|--backup-and-switch]
smairt harness upgrade HARNESS
smairt reference add-doi DOI [--openalex] [--confirm-remote]
smairt reference import-zotero --item KEY
smairt reference import-zotero --collection KEY [--limit 1..1000]
smairt reference attach REFERENCE_ID PDF
smairt reference organize-pdfs [--apply --yes]
smairt literature search QUERY [--provider openalex|semantic-scholar|all] [--limit 20] [--json]
smairt literature related REFERENCE_ID --direction references|cited-by [--provider PROVIDER]
smairt literature recommend REFERENCE_ID [--limit 20] [--json]
smairt literature access REFERENCE_ID [--download --yes] [--confirm-remote]
smairt run --backend local|slurm [--compute-profile NAME] [--cpus N] [--memory-mib N] -- COMMAND
smairt hpc status|sync|cancel RUN_ID
smairt mcp status|enable|disable --harness codex|zoo|cline|opencode|cursor|claude [--dry-run]
smairt mcp serve
```

| Group                                                   | Purpose                                                                        |
| ------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `setup`                                                 | Configure this machine's credentials and connection profiles                   |
| `new`, `menu`                                           | Create a project or open its researcher-facing dashboard                       |
| `status`, `next`, `context`, `doctor`                   | Inspect local state, bounded context, and health                               |
| `contributor`                                           | Register and select manually confirmed people                                  |
| `reference`, `background`, `hypothesis`                 | Build source-grounded scientific framing                                       |
| `credential`, `integration`, `mcp`                      | Compatibility commands, project bindings, and read-only agent metadata access  |
| `experiment`, `iteration`, `run`, `decision`            | Execute and interpret immutable research work                                  |
| `summary`, `paper`, `amend`, `retract`, `supersede`     | Curate evidence, publication, and corrections                                  |
| `safety`                                                | Inspect modes, attest visibility, explicitly refresh, and run release gates    |
| `harness`                                               | Preview, install, select, and diagnose six maintained coding harness adapters |
| `literature`, `reference`                               | Discover works, import DOI metadata, resolve access, and organize PDFs         |
| `hpc`                                                   | Reconcile optional Slurm jobs; local runs remain the default                   |
| `lock`, `recovery`                                      | Inspect writer ownership and resolve interrupted transactions                  |
| `update`, `upgrade`                                     | Unified project maintenance and legacy guidance-only compatibility             |
| `verify`, `contract`, `code`, `env`, `model`            | Integrity, portability, readability, environment, and economy tools            |

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

## Completion

Run `smairt --install-completion` once for Bash, Zsh, Fish, or PowerShell completion. The project
menu's action finder provides a fuzzy, multi-column popup without networking or reading outside the
current project. See [Terminal completion](TERMINAL_COMPLETION.md).
