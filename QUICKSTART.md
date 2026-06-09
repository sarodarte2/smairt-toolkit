# SMAIRT Quick Start Guide

Get up and running with SMAIRT in 5 minutes.

---

## Prerequisites

- Python 3.8 or higher
- An AI assistant (Claude, ChatGPT, or similar)

---

## Step 1: Install Cookiecutter

```bash
pip install cookiecutter
```

---

## Step 2: Generate Your Project

```bash
cookiecutter gh:yourusername/smairt-cookiecutter
```

You'll be prompted for:
- **Project name**: e.g., "My Classification Study"
- **Author name**: Your name
- **Research question**: e.g., "Can we classify X using Y?"
- **Domain**: Select from computational_biology, machine_learning, etc.
- **AI tool**: Claude, ChatGPT, etc.

This creates a new directory with your project structure.

---

## Step 3: Prime Your AI

Open your AI assistant and paste the contents of these three files:

1. `prompts/AI_CONTEXT.md` - Explains the SMAIRT framework to AI
2. `prompts/CODE_CONVENTIONS.md` - How AI should format code
3. `prompts/KNOWN_PATTERNS.md` - Reusable code patterns and errors to avoid

Or use a ready-made prompt from `prompts/SESSION_START.md`.

---

## Step 4: Run Your First Experiment

Ask your AI to create a synthetic data experiment:

```
Please create a Python script called script_01_synthetic_baseline.py in 
experiments/01_synthetic/ that:

1. Generates simple synthetic data to test [your hypothesis]
2. Runs a basic analysis
3. Outputs results to both console and results/logs/
4. Includes a comment block at the end for pasting output

Follow the conventions in prompts/CODE_CONVENTIONS.md
```

Run the script:

```bash
cd your_project
python experiments/01_synthetic/script_01_synthetic_baseline.py
```

---

## Step 5: Record Your Results

1. **Paste output** into the comment block at the end of your script
2. **Log the session** in `prompts/session_log.md`
3. **Note your contributions** in `prompts/intellectual_contribution.md`
4. **Update patterns/errors** in `prompts/KNOWN_PATTERNS.md` (if you solved a new error or wrote reusable code)

---

## Step 6: Iterate

Ask your AI to interpret results and suggest next experiments:

```
Here are the results from script_01:

[paste output]

Does this support or refute the hypothesis?
What should we try next?
```

Create the next script (`script_02_...`) and repeat.

---

## What's Next?

- Read the full [12 Steps Guide](docs/12_STEPS.md) for the complete methodology
- See the [Complete Tutorial](TUTORIAL.md) for a worked example
- Explore `scripts/README.md` for helper script templates

---

## Quick Reference

| Task | Location |
|------|----------|
| Prime your AI | `prompts/AI_CONTEXT.md`, `prompts/CODE_CONVENTIONS.md` |
| Start a session | `prompts/SESSION_START.md` |
| Log prompts | `prompts/session_log.md` |
| Track your insights | `prompts/intellectual_contribution.md` |
| Synthetic experiments | `experiments/01_synthetic/` |
| Benchmark experiments | `experiments/02_downloaded/` |
| Real data experiments | `experiments/03_real_data/` |
| Output logs | `results/logs/` |
| Compile for AI | `python scripts/compile_for_ai.py` |
