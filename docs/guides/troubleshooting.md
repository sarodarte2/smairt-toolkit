# Troubleshooting

## The project is locked

Run `smairt lock status --json`. If the listed local PID is alive, wait or stop that operation.
Use `smairt lock break --yes` only after confirming that the owner can no longer write.

## Doctor reports an incomplete transaction

Inspect `smairt recovery status --json`. Completing publishes the staged post-state; rolling back
restores backups or removes newly created targets. Review the journal before either action.

## A run failed or was interrupted

The run bundle is intentionally preserved. Read its logs, `run.json`, Git snapshot, and input
snapshots. Fix the cause in a new iteration and rerun; do not edit the prior bundle. Failed or
interrupted runs cannot be accepted as evidence.

## Repository visibility is unknown or stale

Ordinary commands do not contact GitHub. Authenticate `gh`, then explicitly run:

```bash
smairt safety status --refresh-visibility --json
```

The cache records visibility, source, observation time, and a stable status rather than the remote
URL. Strict sharing and release gates reject stale or unknown observations where required.

## A harness switch stops

Preview the switch and reconcile unmanaged conflicts or locally modified managed files:

```bash
smairt harness select cursor --dry-run
smairt harness status --json
```

`--backup-and-switch` backs up modified managed content; it does not delete custom files. Harness
status separates generated adapter health from local requirements such as project trust, hook
enablement, or a missing client binary.

## SMAIRT is not found after installation

Run `uv tool update-shell`, reopen the terminal, and try `smairt --version`. Use
`smairt setup doctor --json` to distinguish a missing install from a stale `PATH` or optional Conda
problem.

## The terminal layout is cramped or prints escapes

Increase terminal height for long forms. Confirm that `TERM` is valid and output is attached to a
TTY. Disable motion under Setup → Appearance or set `SMAIRT_REDUCED_MOTION=1`. Every menu action has
an equivalent command in the [CLI reference](../reference/cli.md).

When reporting a rendering problem, include the terminal application, operating system, `TERM`,
and row/column dimensions without including project data.
