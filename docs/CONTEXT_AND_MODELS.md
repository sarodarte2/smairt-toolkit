# Context and Model Efficiency

`smairt context` ranks task-relevant files and enforces a token budget. Active research artifacts
and fresh promoted summaries outrank generic conventions. PDFs, stale summaries, old runs, and
unrelated logs are deferred unless explicitly requested.

Use `--save` to store a disposable, Git-ignored capsule containing source hashes, freshness,
included/deferred files, selection reasons, and estimates.

SMAIRT uses portable model capability tiers:

- `cheap`: metadata normalization, summaries, formatting, and deterministic checks.
- `balanced`: routine implementation and bounded code changes.
- `strong`: scientific reasoning, ambiguous planning, difficult debugging, and manuscript
  synthesis.

Run `smairt model recommend --task <task>`. Concrete model mappings and credentials remain local
to the selected harness.
