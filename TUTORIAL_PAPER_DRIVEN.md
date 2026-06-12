# SMAIRT Paper-Driven Mode Tutorial

This tutorial walks you through using SMAIRT's paper-driven mode to transform your research into a publication-ready paper.

---

## Overview

Paper-driven mode is designed for researchers who:
- Have a paper outline or structure in mind
- Have real datasets ready for analysis
- Need to develop a comprehensive analysis plan
- Want to maintain SMAIRT's reproducibility and iteration tracking benefits

**Key Difference from Standard SMAIRT:**
- Standard SMAIRT: Hypothesis → Synthetic data → Benchmark data → Real data
- Paper-Driven SMAIRT: Paper outline + Real datasets → Analysis plan → Iterative execution

---

## Step 1: Create Your Project

```bash
# Install cookiecutter if needed
pip install cookiecutter

# Create a new SMAIRT project
cookiecutter gh:yourusername/smairt-template
```

When prompted, select `paper_driven` for the `project_mode` option.

You'll see output like:
```
📄 SMAIRT Project Created Successfully! 📄

Scientific Method with AI Research Template - PAPER-DRIVEN MODE
```

---

## Step 2: Set Up Your Paper Outline

Navigate to your project and edit `paper/outline.md`:

```markdown
# My Research Paper

## 1. Introduction
- Background on the problem
- Gap in current knowledge
- Our contribution

## 2. Methods
- Data sources
- Analysis approach

## 3. Results
### 3.1 First Analysis
- Expected figures: Fig 1, Fig 2
- Expected tables: Table 1

### 3.2 Second Analysis
- Expected figures: Fig 3
- Expected tables: Table 2

## 4. Discussion
## 5. Conclusion
```

---

## Step 3: Add Your Data

Organize your data in the `data/` directory:

```
data/
├── README.md           # Document your data sources
├── dataset_a/
│   ├── raw/
│   └── processed/
└── dataset_b/
    ├── raw/
    └── processed/
```

Update `data/README.md` with:
- Data sources and citations
- Data formats
- Any preprocessing steps
- Data access instructions (if restricted)

---

## Step 4: Create Your Analysis Plan

Edit `analysis/ANALYSIS_PLAN.md` to map your paper sections to specific analyses:

```markdown
## Paper Structure Mapping

| Paper Section | Analysis Directory | Status |
|---------------|-------------------|--------|
| Results 3.1 | `01_first_analysis/` | Not started |
| Results 3.2 | `02_second_analysis/` | Not started |

## Detailed Analysis Plan

### 01_first_analysis

**Purpose**: Answer [specific question]

**Data Inputs**:
- `data/dataset_a/processed/data.csv`

**Analysis Steps**:
1. Load and validate data
2. Apply method X
3. Generate Figure 1

**Expected Iterations**: 2-3

**Outputs**:
- Figure 1: Comparison plot
- Table 1: Summary statistics
```

---

## Step 5: Start Your First Analysis

Use the helper script to create an analysis directory:

```bash
python scripts/new_experiment.py --section 01 --name first_analysis
```

This creates:
```
analysis/01_first_analysis/
├── README.md
├── hypotheses.md
└── iterations/
    ├── ITERATION_LOG.md
    └── iter_01/
        ├── NOTES.md
        ├── config_01.yaml
        ├── results/
        └── figures/
```

---

## Step 6: Run Your First Iteration

### 6.1 Create Your Analysis Script

Create `analysis/01_first_analysis/iterations/iter_01/run_analysis_01.py`:

```python
#!/usr/bin/env python
"""
First analysis - Iteration 01
Hypothesis: [Your hypothesis]
"""

import sys
sys.path.insert(0, '../../../..')  # Add project root to path

from lib.core.utils import load_config, set_seed, save_results
from lib.visualization.style import setup_plot_style, save_figure
import matplotlib.pyplot as plt

# Load config
config = load_config('config_01.yaml')
set_seed(config.get('seed', 1024))

# Set up plotting
setup_plot_style()

# Your analysis code here
# ...

# Save results
results = {
    'metric_a': 0.85,
    'metric_b': 0.72,
}
save_results(results, 'results/metrics.json')

# Create figure
fig, ax = plt.subplots(figsize=(8, 6))
# ... your plotting code ...
save_figure(fig, 'figures/fig_01_comparison')

print("Analysis complete!")
print(f"Results: {results}")
```

### 6.2 Configure Your Analysis

Edit `config_01.yaml`:

```yaml
seed: 1024

data:
  input: "../../../../data/dataset_a/processed/data.csv"

parameters:
  threshold: 0.5
  method: "approach_a"

output:
  results_dir: "results/"
  figures_dir: "figures/"
```

### 6.3 Run and Document

```bash
cd analysis/01_first_analysis/iterations/iter_01
python run_analysis_01.py
```

Update `NOTES.md` with your observations:

```markdown
# Iteration 01 Notes

## Date
2024-01-15

## Changes from Previous
- Initial implementation

## Results
- metric_a: 0.85
- metric_b: 0.72

## Observations
- Method works but threshold may need tuning
- Figure shows expected pattern

## Decision
REVISE - Try different threshold values

## Next Steps
- Test threshold = 0.6, 0.7
```

---

## Step 7: Iterate

### 7.1 Create Next Iteration

```bash
python scripts/new_iteration.py --analysis 01_first_analysis --iteration 02
```

This copies your previous config and script as starting points.

### 7.2 Make Changes

Edit `config_02.yaml`:
```yaml
parameters:
  threshold: 0.6  # Changed from 0.5
```

### 7.3 Run and Compare

Run the new iteration and update `ITERATION_LOG.md`:

```markdown
| Iter | Date | Description | Key Change | Metrics | Decision |
|------|------|-------------|------------|---------|----------|
| 01 | 2024-01-15 | Baseline | Initial | a=0.85, b=0.72 | Revise |
| 02 | 2024-01-16 | Tuned threshold | 0.5→0.6 | a=0.89, b=0.78 | **ACCEPT** |
```

---

## Step 8: Finalize Results

When you're satisfied with an iteration:

```bash
python scripts/finalize_iteration.py --analysis 01_first_analysis --iteration 02
```

This:
1. Copies results and figures to `final/`
2. Creates `SELECTED.md` documenting your choice
3. Updates `FINAL_MANIFEST.md`

Edit `final/SELECTED.md` with your rationale:

```markdown
# Selected Iteration

**Selected**: iter_02
**Date**: 2024-01-16

## Rationale
Iteration 02 achieved better metrics (a=0.89 vs 0.85) with the
adjusted threshold. Results are stable across multiple runs.

## Key Metrics
| Metric | Value |
|--------|-------|
| metric_a | 0.89 |
| metric_b | 0.78 |
```

---

## Step 9: Track Progress

### Update the Breadcrumb Trail

Add entries to `analysis/BREADCRUMB_TRAIL.md`:

```markdown
### 2024-01-16 - First Analysis Complete

**What was done**:
- Completed first analysis with 2 iterations
- Final threshold: 0.6
- Generated Figure 1

**Key findings**:
- Method X shows 89% accuracy
- Threshold of 0.6 optimal for this dataset

**Next steps**:
- Begin second analysis
- Apply same approach to dataset_b
```

### Generate Manifest

```bash
python scripts/generate_manifest.py
```

---

## Step 10: Prepare for Publication

### Final Figures

Copy publication-ready figures to `analysis/XX_figures/`:

```
analysis/XX_figures/
├── main/
│   ├── fig_01_comparison.pdf
│   ├── fig_02_results.pdf
│   └── fig_03_summary.pdf
└── supplementary/
    ├── fig_s01_details.pdf
    └── fig_s02_additional.pdf
```

### Review FINAL_MANIFEST.md

Ensure all paper elements are documented:

```markdown
## Summary

| Paper Element | Analysis | Iteration | Status |
|---------------|----------|-----------|--------|
| Figure 1 | 01_first_analysis | iter_02 | ✓ Finalized |
| Figure 2 | 02_second_analysis | iter_03 | ✓ Finalized |
| Table 1 | 01_first_analysis | iter_02 | ✓ Finalized |
```

---

## Tips for Success

### 1. Use AI Effectively

Point your AI to the right context:
```
Please read prompts/InitialPrompt_paper_driven.md and prompts/KNOWN_PATTERNS.md and help me with my analysis.
```

For iteration reviews:
```
Please read the most recent analysis file and prompts/iteration_review_prompt.md to help me evaluate this iteration.
```

### 2. Document Everything

- Update `NOTES.md` after every iteration
- Keep `ITERATION_LOG.md` current
- Write per-iteration analysis files (`analysis/ANALYSIS_XX.md`)
- Update `prompts/KNOWN_PATTERNS.md` when you solve errors or create reusable code

### 3. Use Consistent Styling

Always use the shared library for plots:
```python
from lib.visualization.style import setup_plot_style, save_figure, COLORS
setup_plot_style()
```

### 4. Set Seeds for Reproducibility

```python
from lib.core.utils import set_seed
set_seed(1024)  # Default seed
```

### 5. Keep Iterations Separate

Never modify a previous iteration's files. Always create a new iteration for changes.

---

## Directory Structure Reference

```
your_project/
├── paper/
│   ├── outline.md              # Paper structure
│   ├── drafts/                 # Version-controlled drafts
│   └── reviewer_feedback/      # Feedback documents
│
├── data/
│   └── {dataset}/              # Your datasets
│
├── analysis/
│   ├── ANALYSIS_PLAN.md        # Maps analyses to paper
│   ├── REPOSITORY_PLAN.md      # Repository organization
│   ├── BREADCRUMB_TRAIL.md     # Running log
│   ├── 01_{analysis}/
│   │   ├── README.md
│   │   ├── hypotheses.md
│   │   ├── iterations/
│   │   │   ├── ITERATION_LOG.md
│   │   │   ├── iter_01/
│   │   │   └── iter_02/
│   │   └── final/
│   │       ├── SELECTED.md
│   │       ├── results/
│   │       └── figures/
│   └── XX_figures/             # Final publication figures
│
├── lib/                        # Shared library
│   ├── core/utils.py
│   ├── io/data_loader.py
│   ├── processing/transforms.py
│   └── visualization/style.py
│
├── scripts/
│   ├── new_experiment.py
│   ├── new_iteration.py
│   ├── finalize_iteration.py
│   └── generate_manifest.py
│
├── FINAL_MANIFEST.md           # Maps results to paper
└── README.md
```

---

## Common Workflows

### Starting Fresh
1. Create project with `paper_driven` mode
2. Add paper outline
3. Add data
4. Create analysis plan
5. Start first analysis

### Continuing Work
1. AI reads recent analysis files for context
2. Review `prompts/KNOWN_PATTERNS.md` for reusable patterns and errors to avoid
3. Review `ANALYSIS_PLAN.md` for next steps
4. Create new iteration or new analysis
5. Update documentation (including KNOWN_PATTERNS.md)

### Preparing Submission
1. Run `generate_manifest.py`
2. Review all `SELECTED.md` files
3. Collect final figures
4. Verify reproducibility

---

## Getting Help

- Review `prompts/InitialPrompt_paper_driven.md` for AI assistance
- Check `analysis/REPOSITORY_PLAN.md` for conventions
- See `lib/README.md` for shared library usage

Happy researching! 🔬📄
