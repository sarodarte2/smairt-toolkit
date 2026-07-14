# Troubleshooting

## A command says the project is locked

Run `smairt lock status --json`. If the listed local PID is alive, wait or stop that operation.
Only use `smairt lock break --yes` after confirming the owner cannot still write.

## Doctor reports an incomplete transaction

Inspect `smairt recovery status --json`. Complete publishes the staged post-state; rollback
restores backups or removes newly created targets. Review the journal before either action.

## A run is failed or interrupted

The run bundle is intentionally preserved. Read `run.log`, `run.json`, `git-state.json`, and the
snapshots. Fix the cause in a new iteration and rerun; do not edit the old bundle.

## Strict visibility is unknown or stale

Ordinary commands do not contact GitHub. Authenticate `gh`, then explicitly run
`smairt safety status --refresh-visibility --json`. The cache records only visibility, source,
time, and a stable status—not a sensitive remote URL.

## A harness switch stops

Run the switch with `--dry-run`. Reconcile unmanaged conflicts or review locally modified managed
files. `--backup-and-switch` backs up modified managed content; it does not delete custom files.

Run `smairt harness status --json` afterward. It separates missing or modified adapter files from
runtime requirements such as Codex/Cursor project trust or Cline hook enablement. A missing local
harness binary does not damage the project adapter; install that client before trying to use it.

## The terminal layout looks cramped or moves unexpectedly

SMAIRT automatically switches between compact, medium, and wide layouts. Increase terminal height
when a long form needs scrolling. Current menus redraw in the normal terminal buffer; if escape
sequences are being printed literally, confirm `TERM` is valid and that output is attached to a
TTY. Disable motion under Setup → Appearance or set `SMAIRT_REDUCED_MOTION=1`. All menu actions
have equivalent commands in [CLI Reference](CLI_REFERENCE.md).
