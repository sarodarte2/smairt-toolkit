# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

**Author:** {{ cookiecutter.author_name }} ({{ cookiecutter.author_email }})  
**Domain:** {{ cookiecutter.domain }}  
**AI Tool:** {{ cookiecutter.ai_tool }}

---

## Research Question

{{ cookiecutter.initial_research_question }}

---

## About This Project

This project uses the **SMAIRT** (Scientific Method with AI Research Template) framework.

### Core Philosophy

AI excels at regression toward the mean—it can get you quickly to the frontier of what's already known. The human contribution remains essential for:
- Making innovative connections
- Identifying truly novel questions
- Recognizing where AI suggestions fall short

### The Loop

```
Background → Hypothesis → Methods/Code → Results → Analysis → Future Directions → (repeat)
```

### The 4-Part Structure

The template records **4 pieces of information in separate files**:

1. **Background** - The question that went into prompting it, what has been done on that area, what's known about that question from the literature, and a summary of the previous results that have come up to this point
2. **Hypothesis** - Could be in a separate file or at the end of the background
3. **Methods** - The actual code and data required to test the hypothesis
4. **Results + Interpretation** - The output logs plus analysis through the lens of the hypothesis

The **future directions** from your analysis feed right back into the background for the next iteration.

### Data Progression

1. **Synthetic data** (`experiments/01_synthetic/`) - Fast iteration, no dependencies
2. **Downloaded data** (`experiments/02_downloaded/`) - Benchmark datasets for validation
3. **Real data** (`experiments/03_real_data/`) - Your actual target data

---

## Quick Start

1. Review the philosophy: `docs/SMAIRT_PHILOSOPHY.md`
2. Review the 12 steps: `docs/12_STEPS.md`
3. Define your question: `background/01_initial_question.md`
4. Set up your AI session: `prompts/00_priming_prompts.md`
5. Start experimenting: `experiments/01_synthetic/`
6. Track your contributions: `prompts/intellectual_contribution.md`

---

## Project Structure

```
├── docs/              # SMAIRT philosophy and 12-step guide
├── prompts/           # AI prompts, session logs, intellectual contribution tracking
├── background/        # Research question, literature, prior results
├── hypotheses/        # Hypothesis tracking
├── experiments/       # Scripts organized by data phase
│   ├── 01_synthetic/
│   ├── 02_downloaded/
│   └── 03_real_data/
├── results/           # Logs (named to match scripts) and figures
├── analysis/          # Interpretation, future directions
├── data/              # Data files by phase
├── scripts/           # Helper scripts (new_iteration.py, compile_for_ai.py)
└── paper_draft/       # Parallel narrative and figure generation
```

---

## Key Conventions

### Script Naming
```
script_01_description.py
script_02_another_test.py
script_03_noise_robustness.py
```

### Log Files
Save to `results/logs/` with names matching scripts:
```
results/logs/script_01_description_output.log
```

### Output as Comments (Breadcrumb Trail)
Paste output at the bottom of each script as comments:
```python
# === OUTPUT ===
# Accuracy: 0.85
# Loss: 0.23
# Notes: Works on synthetic, need to test with noise
```

This creates a breadcrumb trail so when you feed the repo back to AI, it can immediately see what was tried and what the results were.

### Feeding Back to AI
Use `scripts/compile_for_ai.py` to generate a summary of the entire project state that you can paste into a new AI session to pick up where you left off.

---

## Parallel Story Generation

As a parallel output to the 4-part structure:
- A **paragraph** for each section
- A **figure** for the results section
- A **schematic diagram** for the methods showing the workflow

The final scientific product won't have all experiments together—it will be based on selected results. Use `paper_draft/` to build this narrative alongside your experiments.

---

## Caveats

- **Literature limitations:** LLMs can't do a deep dive on the literature. Be suspicious about what they bring from the literature—verify important claims independently.
- **Regression toward the mean:** AI is good at known approaches but less good at truly innovative connections. That's your job.

---

## License

{{ cookiecutter.license }}
