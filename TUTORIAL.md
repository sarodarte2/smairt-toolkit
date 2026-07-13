# SMAIRT End-to-End Tutorial

Begin with the [Quickstart](QUICKSTART.md) through one accepted run. This tutorial continues from
that run ID and shows evidence review, claims, manuscript review, correction, and collaboration.

## Review evidence and approve a claim

```bash
smairt paper evidence review --run RUN_<timestamp> \
  --purpose "Predeclared purpose" --observed-result "What was directly observed" \
  --limitations "Known limitations and confounders" --decision ACCEPT
smairt paper claim propose --statement "A bounded claim supported by the result" \
  --evidence evidence-run_<timestamp>
smairt paper claim approve claim-<id> --yes
```

References attached to a claim must have current local checksums and human-verified metadata.
Crossref/OpenAlex enrichment remains unverified until a contributor reviews it.

## Draft and review a manuscript

```bash
smairt paper outline
smairt paper begin --title "A Traceable Study"
smairt paper section draft Results --text "Result prose tied to the approved claim." \
  --claim claim-<id>
smairt paper section review Results --claim claim-<id> --yes
```

Repeat draft and review for Abstract, Introduction, Methods, Discussion, and References. Then:

```bash
smairt paper validate
smairt paper build --format md
smairt paper build --format docx --line-numbering
```

A malformed DOCX template or stale evidence fails before replacing a prior build.

## Correct without rewriting history

If an accepted run is invalid, append a retraction:

```bash
smairt retract --run RUN_<timestamp> --reason "Calibration error invalidated the result"
```

The selection, evidence card, and dependent claim become stale. For a corrected run, create a new
iteration, execute it, verify it, then use `smairt supersede --run <old> --replacement-run <new>`.

## Two-contributor collaboration

Each contributor works on a separate Git branch or worktree and selects their confirmed identity:

```bash
smairt contributor add --name "Second Researcher"
smairt contributor use second-researcher
smairt lock status --json
```

The checkout-local lock prevents simultaneous writes to the same state. Git merges branches;
researchers resolve scientific choices and conflicts explicitly. Use immutable contributor
summaries, claim reviews, and correction records instead of overwriting another contributor's
judgment.

Before sharing:

```bash
smairt doctor --json
smairt validate --staged
smairt safety status --refresh-visibility --json
smairt safety release-check --json
```
