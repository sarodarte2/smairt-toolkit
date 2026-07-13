# SMAIRT Tutorial

This tutorial follows one complete v2 research path. Commands intentionally rely on
`smairt next --json`; the durable project state, not a pasted chat transcript, determines what
happens next.

1. Create the project with a confirmed contributor, safety mode, and active harness.
2. Index local PDFs, enrich only when policy permits remote queries, and explicitly verify
   citation metadata.
3. Complete the background and have the agent develop exactly three distinct hypothesis options.
4. Select a hypothesis yourself and record the rationale.
5. Create an experiment and keep scientific parameters in its iteration `config.yaml`.
6. Run through `smairt run`; inspect and verify the immutable bundle.
7. Record ACCEPT, REVISE, ABANDON, or BLOCKED as a human decision.
8. Review accepted evidence, approve supported claims, and begin `paper/manuscript.md`.
9. Review every section against approved claims and verified references.
10. Build versioned Markdown and DOCX snapshots, then run the safety release check.

At any point:

```bash
smairt status --json
smairt next --json
smairt validate --json
smairt model recommend --task interpretation --json
```

Failed runs remain evidence about the process. Method changes create new iterations. Retractions
and supersessions append correction records and never erase the original run.
