# SMAIRT Workflow Reference

## Project layout

```text
docs/                         # Philosophy and 12-step guide
prompts/                      # AI context, session logs, contribution tracking
background/                   # Research question and literature context
hypotheses/                   # Hypotheses tested over time
experiments/01_synthetic/     # Fast synthetic-data experiments
experiments/02_downloaded/    # Public benchmark experiments
experiments/03_real_data/     # Actual target-data experiments
results/logs/                 # Output logs named to match scripts
results/figures/              # Generated figures
analysis/                     # Interpretation and future directions
data/                         # Synthetic, downloaded, and real data
scripts/                      # Helpers such as compile_for_ai.py
paper_draft/                  # Running methods/results narrative
```

## Script output block

Every experiment script should end with a block like this:

```python
# === PASTE OUTPUT HERE ===
"""
=== OUTPUT ===
[Paste console output here]

=== INTERPRETATION ===
[Did this support the hypothesis?]
[What worked? Within what boundaries?]
[What did not work? Where did it break?]

=== NEXT STEPS ===
[What should we try next?]
"""
```

## Starting prompt

Use this when starting a new AI session:

```text
Use the SMAIRT research workflow.

Project:
- Name: [project name]
- Research question: [question]
- Current phase: [synthetic / downloaded / real]
- Current hypothesis: [hypothesis]

Please help me refine the current hypothesis, design the next testable experiment, generate code that logs to console and results/logs, and preserve the breadcrumb trail for future AI sessions.
```

## Continuing prompt

Use this when context already exists:

```text
Use the SMAIRT research workflow and continue from this project state.

I will provide the current hypothesis, recent session log, prior experiment output, and future directions. Interpret the latest results through the hypothesis, identify boundaries and limitations, then propose the next one or two experiments.
```

## MCP connector pattern

The skill itself is static instruction content. An MCP connector does not need to recreate the workflow; it can expose the workflow to an assistant as resources and prompts:

- Resource: `smairt://skill/SKILL.md` -> contents of `skills/smairt-research/SKILL.md`
- Resource: `smairt://skill/workflow.md` -> contents of this file
- Prompt: `start_smairt_session` -> the starting prompt above
- Prompt: `continue_smairt_session` -> the continuing prompt above
- Optional tool: `compile_smairt_context` -> runs `scripts/compile_for_ai.py` in a generated SMAIRT project and returns `prompts/compiled_for_ai.md`

Keep MCP tools read-only by default. Only add write tools when the host application has clear user approval and workspace boundaries.
