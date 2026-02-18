# {{ cookiecutter.project_slug }}/docs/12_STEPS.md

```markdown
# The 12 Steps of SMAIRT

## Overview

These 12 steps outline a way that works pretty well for doing tightly integrated AI-assisted computational research. The goal is to follow the scientific method in an iterative process, recording everything so you can feed it back to AI and maintain context across sessions.

---

## Step 1: Record All Your Prompts

Keep prompts in a separate file (`prompts/session_log.md`). This provides:
- A track record of all the things you've asked AI
- Keep the answers there as well
- Documentation of your intellectual contribution to the effort

---

## Step 2: Track Your Intellectual Contribution

In `prompts/intellectual_contribution.md`, document where YOU made critical steps vs. where AI generated ideas.

Know where you provided the key insights.

---

## Step 3: Start with Synthetic Data

Begin in `experiments/01_synthetic/`. Synthetic data allows:
- Very easy iteration in this cycle
- Not dependent on large datasets
- Get an idea of what might work and what might not just from the code itself
- Not dependent on outside sources
- Iterate in a tight loop

Synthetic data is often a good place to start for exploration of an idea
but it is not likely to be a good test of the ideas since real data will
have many more hidden patterns and pitfalls that synthetic data doesn't.
---

## Step 4: Progress to Downloaded Benchmark Data

Move to `experiments/02_downloaded/`. Have Claude and the scripts download test data. This provides:
- Data that many people have looked at before
- Diversity: easy data, hard data, messy experimental data, cleaner data like the Iris dataset
- A nice range of things to test on
- Validation that your approach is robust across different datasets

For those problems where it is possible, it is a good idea to test it on
publicly available datasets that may have been used many times previously.
This is nicely repeatable with the modern repositories for training data
and will provide a diverse pool of datasets to look at. It's likely that
many important questions won't have publicly available datasets that make sense
for the problems however.

---

## Step 5: Then Test on Real Data

Finally use `experiments/03_real_data/`. Now you're testing:
- The actual hypothesis with actual target data
- Whether approaches that worked on benchmarks transfer
- Internal checks become possible

---

## Step 6: Number Your Scripts Sequentially

Keep individual scripts numbered for each round:

```
script_01_initial_test.py
script_02_add_noise.py
script_03_different_architecture.py
```

This creates a clear timeline of what was tried and allows very rapid turnaround time.

---

## Step 7: Paste Output as Comments (The Breadcrumb Trail)

At the bottom of each script, paste the output as comments:

```python
# === OUTPUT ===
# Accuracy: 0.85
# Loss: 0.23
# Notes: Works well with synthetic, need to test noise
```

This provides a record for you so you can go back and say "oh that's what the output was." But almost more importantly, it provides a record for AI.

The point of this process is to provide the AI with a list of:
- Here are all the things we tried
- Here's the different datasets we ran it on
- Here's the algorithms we tried
- Here's the prompts that went into it
- Here's what the output was

Now it can recreate the thought process through this whole thing and come out on the other end basically starting right up where you were. **It's a breadcrumb trail that allows you to get right back to where you started from**—even if you start in a completely new thread, even if you give it to a new API.

Use the scripts/compile_for_ai.py script to compile all results in to one
single file for feeding a new AI thread.

---

## Step 8: Name Log Files to Match Scripts

Output should go to both the command line AND a log file. Save detailed output to `results/logs/` with matching names:

```
results/logs/script_01_initial_test_output.log
```

That way you have all the log files in one place and the scripts are closely associated with them. The log file can also output the name of the script.

---

## Step 9: Feed the Whole Repo Back to AI

When starting a new session, compile your repo state and feed it back. AI can then recreate the thought process and continue where you left off.

Use `scripts/compile_for_ai.py` to generate a summary.

You could also try feeding your repo to a different AI and see what kinds of insights you get out the other end.

---

## Step 10: Use Priming Prompts

Make things even better by developing an input set of prompts that will be in the background. It will prime your AI thread to just do these things:
- Provide output on the command line
- Provide an output log file named the same as the script
- Follow the 4-part structure
- Generate code that can be tested immediately

See `prompts/00_priming_prompts.md` for templates.

---

## Step 11: Follow the 4-Part Scientific Method Structure

Record **4 pieces of information in separate files**:

### Part 1: Background
- The question that went into prompting it
- What has been done on that area
- What's known about that question from the literature dive
- A summary of the previous results (the thread of results that have come up to this point)

### Part 2: Hypothesis
- Could be in a separate file
- Could be at the end of the background
- What you're testing in this iteration

### Part 3: Methods
- The actual code
- The data required to run and test the experiment
- The experimental design

### Part 4: Results + Interpretation
- The log file output
- What did this tell us through the lens of the hypothesis?
- Whether it supported the hypothesis or not
- Secondary hypotheses and observations
- Human interpretation additions

---

## Step 12: Use Future Directions to Seed Next Iteration

The final part of the interpretation is the **future directions**—this leads right back into the background section for the next iteration.

`analysis/future_directions.md` feeds back into `background/` for the next cycle.

There's some selectivity here: future directions might have lots of options, but you want to select probably one or two main things to focus on for the next steps. The rest might come up in future iterations.

Sometimes there are splits where you test this first thing first, and then the second thing actually harkens back to something previous. You might have complicated relationships between
the different steps at the end.

---

## The Loop

```
Background → Hypothesis → Methods → Results → Analysis → Future Directions
     ↑                                                          │
     └──────────────────────────────────────────────────────────┘
```

This is an iterative process. The SMAIRT process structures things
following the scientific method, and records all the relevant information.

---

## A Note on Literature

- **Literature limitations:** LLMs can't do a deep dive on the literature. Be suspicious about what they bring from the literature—verify important claims independently.

Use AI to explore quickly, but verify important literature claims independently.

---

## What AI Does Well

AI allows you to move very quickly to the frontier. It's easier to find the questions that have been asked than to find places where you're asking a question that sounds novel but actually:
- Doesn't need to be asked
- Is a hidden variant of a question already answered (perhaps in another domain or with different language)

Those are the really tricky places to find. AI lets you get there faster so you can see where the real gaps are.
```
