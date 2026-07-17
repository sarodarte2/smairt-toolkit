# CLI reference

Run `smairt <command> --help` for the current option-level contract. This reference groups common
workflows and stable machine-facing behavior rather than reproducing every option.

## Entry points

| Command | Purpose |
| --- | --- |
| `smairt` | Open context-aware Home or the nearest project dashboard in a terminal |
| `smairt setup` | Configure and diagnose user-wide installation and connection profiles |
| `smairt new [DESTINATION]` | Create a project interactively or from explicit options |
| `smairt menu [PROJECT]` | Open the terminal workspace for the nearest or selected project |
| `smairt status` | Describe project identity, active records, and health |
| `smairt next` | Recommend state-aware actions and bounded context |
| `smairt doctor` | Diagnose project and sharing readiness without network access or mutation |
| `smairt validate` | Check structure, safety, code, provenance, and readiness |

Use `smairt --project PATH <command>` from any directory. An explicit project wins over nearest
directory discovery; workspace handoffs add it only when needed.

`smairt init` and `smairt start project` remain deprecated project-creation aliases.

## Setup and local connections

```bash
smairt setup doctor [--check-github] [--json]
smairt setup credential list|set|delete|doctor
smairt setup zotero configure|test|remove
smairt setup openalex configure|test|remove
smairt setup semantic-scholar configure|test|remove
smairt setup unpaywall configure default --email EMAIL
smairt setup hpc configure default --mode native|ssh --remote-root PATH
smairt integration bind|unbind|status|test
```

The nullable starter profile can hold an explicitly entered contributor, project parent, fields of
study, and AI assistant. It never learns from projects and contains no classification, license,
environment, Git, or safety defaults. Connection profiles are user-local; shared YAML contains
policy, not credentials or account identifiers.

## Orientation and bounded context

```bash
smairt status --json
smairt next --json
smairt next --prompt
smairt context --task planning|code|run|interpretation|paper|review
smairt context --task review --target PROJECT_RELATIVE_PATH --json
```

Review context is read-only guidance. It does not grant an assistant authority to mutate records or
approve a scientific transition.

## References and literature

```bash
smairt reference list|scan|inspect|verify|export
smairt reference add PDF
smairt reference add-doi DOI --confirm-remote
smairt reference attach REFERENCE_ID PDF
smairt reference import-zotero --item KEY
smairt reference import-zotero --collection KEY --limit 500
smairt reference organize-pdfs [--apply --yes]
smairt literature search QUERY --provider openalex|semantic-scholar|all
smairt literature related REFERENCE_ID --direction references|cited-by
smairt literature recommend REFERENCE_ID
smairt literature access REFERENCE_ID [--download --yes] [--confirm-remote]
```

Discovery is provisional. Import, attachment, download, manual correction, and human verification
are distinct operations.

## Scientific records

| Group | Responsibility |
| --- | --- |
| `background` | Create and validate source-grounded framing |
| `hypothesis` | Create proposal sets and record explicit human selection |
| `experiment`, `iteration` | Create methods and version meaningful changes |
| `run`, `verify` | Execute through provenance capture and check immutable manifests |
| `decision` | Record attributed interpretation decisions |
| `paper` | Curate evidence, claims, reviews, and builds |
| `amend`, `retract`, `supersede` | Append corrections without rewriting history |
| `summary` | Manage contributor-scoped and promoted context summaries |

Run `--help` on the relevant group before a consequential mutation.

## Harnesses and metadata-only MCP

```bash
smairt harness list
smairt harness info HARNESS [--json]
smairt harness status [HARNESS] [--json]
smairt harness select HARNESS --dry-run
smairt harness select HARNESS [--backup-and-switch]
smairt harness upgrade HARNESS
smairt mcp status --json
smairt mcp enable|disable --harness codex|zoo|cline|opencode|cursor|claude
```

One adapter is active per project. Scientific records remain portable across adapters.

## Runs and optional HPC

Local execution is the default:

```bash
smairt run --experiment EXPERIMENT_ID --iteration ITERATION_ID
```

For an explicitly configured Slurm profile:

```bash
smairt run --backend slurm --compute-profile NAME \
  --cpus N --memory-mib N --time-minutes N -- COMMAND
smairt hpc status|sync|cancel RUN_ID
```

## Safety, recovery, and maintenance

```bash
smairt safety status [--refresh-visibility] [--json]
smairt safety set standard|strict
smairt safety release-check --json
smairt lock status --json
smairt recovery status --json
smairt recovery complete|rollback TRANSACTION_ID --yes
smairt update [--apply --yes] [--allow-dirty] [--json]
```

`update` previews and applies project schema, managed guidance, and active-adapter steps together.

## JSON envelope and exit codes

Machine-readable commands use a versioned envelope:

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

| Code | Meaning |
| ---: | --- |
| 0 | Success |
| 1 | Validation or policy failure |
| 2 | Invalid usage or project state |
| 3 | Mutation lock conflict or recovery required |

`smairt run` propagates child status where applicable; launch failure uses 126 or 127 and common
interruption paths use 130 or 143.

## Completion and terminal navigation

Install shell completion once, or preview the generated script:

```bash
smairt --install-completion
smairt --show-completion
```

Bash, Zsh, Fish, and PowerShell are supported by the underlying completion system. Completion
suggests commands and options but never credential values.

Inside `smairt menu`, arrow keys or j/k move, Enter accepts, Left or Escape returns one level, and
Ctrl-C exits. **Find an action** searches the local command catalog and project identifiers without
network access.

Non-interactive `smairt new` requires all consequential options or the explicit
`--accept-recommended` bundle. In a terminal, incomplete values seed the guided wizard.
