---
name: smairt-research
description: Use for planning, executing, interpreting, correcting, or publishing research in a SMAIRT v2 project.
---

# SMAIRT Research

1. Run `smairt status --json` and `smairt next --json`.
2. Load only `smairt context --task <planning|code|run|interpretation|paper>` output.
3. Treat `smairt.yaml` and portable event/evidence records as authoritative.
4. Use SMAIRT commands to create hypotheses, experiments, iterations, runs, evidence, claims, and
   paper builds.
5. Stop for explicit human input before contributor attribution, hypothesis selection, scientific
   decisions, claim approval, corrections, safety changes, or repository visibility attestations.
6. Preserve every run and correction. A method change creates a new iteration; an identical retry
   creates a new run.
7. Never read, transmit, or stage secrets, raw protected data, ignored PDFs, or protected local
   summaries contrary to project policy.
8. Validate and verify before reporting completion.
9. End with the completed stage, the recommended next action, and relevant alternatives from
   `smairt next --json`.

Read `references/workflow.md` for the artifact chain, evidence gates, context tiers, and correction
rules.
