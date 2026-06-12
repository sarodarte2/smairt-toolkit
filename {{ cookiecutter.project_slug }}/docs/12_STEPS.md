# The SMAIRT 12 Steps

A concise reference for the Scientific Method with AI Research Template workflow.

---

## Overview

These 12 steps define how to work with AI in a research context, maintaining
scientific rigor while moving quickly. Adapted for IDE-native AI tools (VSCode
Roo/Zoo, Cursor, Windsurf) where the AI has direct file access.

---

## Step 1: Record Your Intellectual Contributions

Track where YOU make critical decisions vs. where AI generates ideas.

Record in `prompts/intellectual_contribution.md`:
- The initial framing of the question
- Choices between options the AI presents
- Novel directions YOU suggest
- Interpretive insights that go beyond the AI's analysis
- Decisions to pivot or abandon approaches

**This is the most important documentation in the project.**

---

## Step 2: Write Hypotheses Before Experiments

Before writing code, state what you expect to find and why.

Create `hypotheses/HYPOTHESIS_XX.md` with:
- A specific, testable prediction
- The rationale (based on prior evidence)
- Success criteria (quantitative if possible)
- Experimental design

This forces clarity and prevents post-hoc rationalization.

---

## Step 3: Start with Synthetic Data

Synthetic data enables rapid iteration without external dependencies.

```
Phase 1: Synthetic → Fast feedback, verify code works
Phase 2: Downloaded → Diversity, robustness testing
Phase 3: Real data → Full validation
```

Don't skip to real data prematurely. Synthetic data helps you:
- Verify your code is correct
- Understand algorithm behavior under controlled conditions
- Iterate quickly (seconds vs. hours)

---

## Step 4: Progress to Downloaded Benchmark Data

Benchmark datasets provide:
- **Diversity** — Test across different data characteristics
- **Validation** — Compare against known results
- **Robustness** — Ensure approach isn't overfit to synthetic patterns

---

## Step 5: Then Test on Real Data

Real data is the ultimate test. Expect:
- Noise and messiness
- Missing values and edge cases
- Results that don't match synthetic performance

This is where you learn the true boundaries of your approach.

---

## Step 6: Number Your Scripts Sequentially

Scripts are the atomic unit of experimentation:

```
script_01_initial_smoke_test.py
script_02_add_noise_robustness.py
script_B01_fitness_data_exploration.py  (track-based)
script_D06_hpc.py                        (HPC variant)
```

Each script should:
- Test one hypothesis (or a small set of related sub-hypotheses)
- Be self-contained (runnable independently)
- Use `TeeLogger` for dual console/file output
- Reference its hypothesis file in the docstring

---

## Step 7: Maintain the Audit Trail

Every experiment produces a trail of evidence:

| Artifact | File | Purpose |
|----------|------|---------|
| Hypothesis | `hypotheses/HYPOTHESIS_XX.md` | What we predicted |
| Code | `experiments/XX_phase/script_XX.py` | What we ran |
| Output | `results/logs/script_XX_*.log` | What happened |
| Analysis | `analysis/ANALYSIS_XX.md` | What we learned |

The AI reads these files directly — no need to manually copy anything.

---

## Step 8: Name Log Files to Match Scripts

Log files should be clearly traceable to their source scripts:

```
results/logs/script_01_smoke_test_20240115_143022.log
results/logs/script_B05_multi_organism_20240220_091544.log
```

The `setup_logging()` function from `scripts/shared/` handles this automatically.

---

## Step 9: Use compile_for_ai.py for Cross-Tool Transfer

`scripts/compile_for_ai.py` generates a single document containing the full
project state. Use it when:

- **Switching AI tools** — Moving from Roo to ChatGPT or vice versa
- **Archival** — Creating a snapshot for future reference
- **Onboarding** — Bringing a new team member's AI up to speed
- **Context window limits** — When the project exceeds what the AI can read piecemeal

In normal IDE-native workflow, the AI reads files directly and doesn't need this.

---

## Step 10: Use Priming Prompts

See `prompts/SESSION_START.md` for context-setting prompts appropriate to different
situations (onboarding, context refresh, planning, interpretation, etc.).

### 10b: Maintain Known Patterns & Errors

After each iteration, update `prompts/KNOWN_PATTERNS.md` with:
- **Reusable patterns** — Code that works and should be reused
- **Common errors** — Mistakes encountered and their fixes
- **Consistency rules** — Standards for seeds, formats, etc.
- **Pre-flight checklist** — Things to verify before running experiments

---

## Step 11: Follow the 4-Part Scientific Method Structure

Every iteration follows this structure:

### Part 1: Background
- What's the question?
- What do we know from prior work?
- What gap are we addressing?

### Part 2: Hypothesis
- What do we predict will happen?
- Why do we predict this? (rationale)
- What are the success criteria?

### Part 3: Methods
- The actual code (script)
- The data used
- The experimental design

### Part 4: Results + Interpretation
- What actually happened (log file)
- Does it support or refute the hypothesis?
- Where does it work? Where does it break?
- What are the next steps?

---

## Step 12: Use Future Directions to Seed Next Iteration

The "Next Steps" section of each analysis file seeds the next hypothesis.

```
ANALYSIS_XX.md → Next Steps → HYPOTHESIS_YY.md → script_YY.py → ANALYSIS_YY.md → ...
```

This creates a clear chain of reasoning across iterations.

---

## The Loop

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Hypothesis → Script → Run → Log → Analysis → Next  ──→│
│                                                         │
└─────────────────────────────────────────────────────────┘
```

Each cycle through this loop:
1. Tests a specific prediction
2. Produces machine-readable evidence
3. Generates interpretation and next steps
4. Updates shared knowledge (patterns, errors, contributions)

---

## A Note on Literature

AI can help you quickly survey what's known, but:
- **Be suspicious** of AI-generated literature claims
- **Verify independently** any important references
- **The human decides** what's truly novel vs. well-known

---

## What AI Does Well

- Getting to the frontier of existing knowledge quickly
- Generating and testing code rapidly
- Systematic comparison of approaches
- Maintaining consistency across many experiments
- Identifying patterns in results

## What AI Does NOT Do Well

- Genuine innovation (the human's job)
- Literature accuracy (verify claims)
- Knowing when to abandon an approach (the human decides)
- Understanding the deeper significance of results (the human interprets)

---

## Plan-Driven Development

For complex multi-step work, create planning documents FIRST:

```
plans/PLAN_TRACK_B_FITNESS_DATA.md
plans/PLAN_D06_RAY_TUNE_IMPLEMENTATION.md
```

Plans prevent scope creep and ensure alignment between human intent and AI execution.
See `plans/README.md` for the plan template.
