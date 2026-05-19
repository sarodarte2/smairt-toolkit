# SMAIRT Paper-Driven Mode: Implementation Guide

## Overview

This document provides instructions for adding a new "Paper-Driven" mode to the SMAIRT cookiecutter template. This mode is designed for researchers who start with a paper outline and datasets, then develop an analysis plan that follows SMAIRT principles.

**Key Difference from Standard SMAIRT:**
- Standard SMAIRT: Hypothesis → Synthetic data → Benchmark data → Real data
- Paper-Driven SMAIRT: Paper outline + Real datasets → Analysis plan → Iterative execution

---

## Context: What This Mode Accomplishes

The Paper-Driven mode helps researchers who:
1. Have a paper outline or structure in mind
2. Have real datasets ready for analysis
3. Need to develop a comprehensive analysis plan
4. Want to maintain SMAIRT's reproducibility and iteration tracking benefits

This mode was developed based on the VaLPAS paper project, where we transformed an application note into a full research paper using real multi-omics data from multiple organisms.

---

## Changes Required to SMAIRT Cookiecutter

### 1. Add New Cookiecutter Variable

In `cookiecutter.json`, add a new variable for project mode:

```json
{
    "project_name": "my_smairt_project",
    "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '_') }}",
    "author_name": "Your Name",
    "project_mode": ["standard", "paper_driven"],
    "description": "A short description of the project",
    "python_version": "3.12.0"
}
```

### 2. Create Conditional Directory Structure

The paper-driven mode uses a different directory structure. Use Jinja2 conditionals in the template:

#### Standard Mode Structure (existing):
```
{{ cookiecutter.project_slug }}/
├── data/
│   ├── synthetic/
│   ├── benchmark/
│   └── real/
├── experiments/
│   ├── 01_synthetic/
│   ├── 02_benchmark/
│   └── 03_real/
└── ...
```

#### Paper-Driven Mode Structure (new):
```
{{ cookiecutter.project_slug }}/
├── paper/
│   ├── outline.md              # Paper outline/structure
│   ├── drafts/                 # Version-controlled drafts
│   └── reviewer_feedback/      # Feedback documents
│
├── data/
│   ├── README.md               # Data documentation
│   └── {organism_or_dataset}/  # Organized by data source
│
├── analysis/
│   ├── ANALYSIS_PLAN.md        # Comprehensive analysis plan
│   ├── REPOSITORY_PLAN.md      # Repository organization
│   ├── BREADCRUMB_TRAIL.md     # Running log of analyses
│   │
│   ├── 01_{results_section_a}/ # Maps to paper section
│   │   ├── README.md
│   │   ├── hypotheses.md
│   │   ├── 01_{analysis_name}/
│   │   │   ├── iterations/
│   │   │   │   ├── ITERATION_LOG.md
│   │   │   │   ├── iter_01/
│   │   │   │   │   ├── run_analysis_01.py
│   │   │   │   │   ├── config_01.yaml
│   │   │   │   │   ├── results/
│   │   │   │   │   ├── figures/
│   │   │   │   │   └── NOTES.md
│   │   │   │   └── iter_02/
│   │   │   └── final/
│   │   │       ├── SELECTED.md
│   │   │       ├── results/
│   │   │       └── figures/
│   │   └── 02_{analysis_name}/
│   │
│   ├── 02_{results_section_b}/
│   └── XX_figures/             # Final publication figures
│
├── lib/                        # Shared library
│   ├── evaluation/             # Standardized evaluation
│   ├── data_sources/           # External data APIs
│   ├── annotations/            # ID mapping, configs
│   ├── comparison/             # Comparison with existing tools
│   └── visualization/          # Consistent plotting
│
├── prompts/                    # AI prompts
│   ├── InitialPrompt.txt       # Project setup prompt
│   ├── evaluation_prompt.md
│   ├── iteration_review_prompt.md
│   └── figure_generation_prompt.md
│
├── hpc/                        # HPC/SLURM configuration
│   ├── config.yaml
│   ├── templates/
│   └── logs/
│
├── scripts/                    # Utility scripts
│   ├── new_experiment.py
│   ├── new_iteration.py
│   ├── finalize_iteration.py
│   ├── generate_manifest.py
│   └── submit_job.py
│
├── FINAL_MANIFEST.md           # Maps final results to paper
├── AI_CONTEXT.md               # Current state for AI
└── README.md
```

### 3. New Prompts for Paper-Driven Mode

Create these new prompt templates:

#### `prompts/InitialPrompt_paper_driven.txt`

```markdown
# Paper-Driven SMAIRT Project Setup

## Your Task

You are helping set up a research project that will produce a scientific paper. The researcher has:
1. A paper outline or structure
2. Real datasets ready for analysis
3. Specific research questions to answer

## Process

1. **Read the paper outline** to understand:
   - The overall narrative and structure
   - What results sections are needed
   - What figures/tables are expected

2. **Examine the available data** to understand:
   - What datasets are available
   - Data formats and quality
   - What analyses are feasible

3. **Create an Analysis Plan** (`analysis/ANALYSIS_PLAN.md`) that:
   - Maps each paper section to specific analyses
   - Defines hypotheses for each analysis
   - Specifies data inputs and expected outputs
   - Establishes evaluation criteria and metrics
   - Sets a realistic timeline

4. **Create a Repository Plan** (`analysis/REPOSITORY_PLAN.md`) that:
   - Defines the directory structure
   - Documents shared library functions
   - Establishes naming conventions
   - Specifies iteration tracking approach

5. **Present both plans for review** before implementation

## Key Principles

- **All data is real data** - No synthetic/benchmark phases
- **Iteration tracking** - Separate scripts per iteration (run_analysis_01.py, etc.)
- **Multiple metrics** - Never rely on a single metric
- **Multiple ground truths** - Validate against multiple sources where possible
- **Reproducibility** - Fixed seeds, documented parameters, version control
- **Final path capture** - FINAL_MANIFEST.md documents exactly which iteration produced each result

## Questions to Ask

Before creating the plan, clarify:
1. What is the target journal and format requirements?
2. Are there existing analyses to reproduce/extend?
3. What computational resources are available (local/HPC/GPU)?
4. What is the timeline for completion?
5. Are there specific tools or methods that must be compared against?
```

#### `prompts/analysis_plan_prompt.md`

```markdown
# Analysis Plan Creation Prompt

When creating an analysis plan for a paper-driven project:

## Structure

1. **Overview** - Brief description of the project
2. **Paper Structure Mapping** - How analyses map to paper sections
3. **Execution Framework** - Iteration workflow, shared library usage, HPC
4. **Detailed Analysis Plan** - Each analysis with:
   - Directory location
   - Data inputs
   - Analysis steps
   - Expected iterations
   - Outputs
5. **Evaluation Framework** - Metrics, ground truth sources
6. **Figure Plan** - Main and supplementary figures
7. **Timeline** - Realistic schedule (days for AI-assisted, weeks for manual)
8. **Data Requirements** - Summary table of all data
9. **Hypotheses** - Testable hypotheses
10. **Execution Notes** - Reproducibility, resources, quality checklists

## Key Elements

- **Multiple benchmark sets** where available (e.g., KEGG, STRING, GO)
- **Multiple metrics** (PPV, TPR, F-score, enrichment, FDR, AUROC, AUPRC)
- **Comparison with existing tools** where applicable
- **Cross-dataset/organism comparisons** where applicable
- **Default seed: 1024** for reproducibility
```

#### `prompts/iteration_workflow_prompt.md`

```markdown
# Iteration Workflow for Paper-Driven Projects

## Iteration Structure

Each analysis maintains separate scripts per iteration:

```
analysis_name/
├── iterations/
│   ├── ITERATION_LOG.md      # Summary table
│   ├── iter_01/
│   │   ├── run_analysis_01.py
│   │   ├── config_01.yaml
│   │   ├── results/
│   │   ├── figures/
│   │   └── NOTES.md
│   └── iter_02/
│       └── ...
└── final/
    ├── SELECTED.md           # Which iteration and why
    └── ...                   # Final results
```

## ITERATION_LOG.md Format

| Iter | Date | Description | Key Change | Metrics | Decision |
|------|------|-------------|------------|---------|----------|
| 01 | YYYY-MM-DD | Baseline | Initial params | PPV=0.42, F=0.35 | Revise |
| 02 | YYYY-MM-DD | Tuned LR | lr: 0.001→0.0005 | PPV=0.51, F=0.44 | **ACCEPT** |

## Decision Criteria

- **ACCEPT**: Metrics meet targets, results stable and interpretable
- **REVISE**: Promising but needs parameter tuning
- **ABANDON**: Fundamental issue, try different approach

## NOTES.md Template

```markdown
# Iteration XX Notes

## Date
YYYY-MM-DD

## Changes from Previous
- [List changes]

## Results
- [Key metrics]

## Observations
- [What worked, what didn't]

## Decision
[ACCEPT/REVISE/ABANDON] - [Rationale]

## Next Steps
- [If REVISE, what to try next]
```
```

### 4. New Script Templates

#### `scripts/new_experiment.py` (Paper-Driven Version)

```python
#!/usr/bin/env python
"""
Create a new experiment directory for paper-driven SMAIRT project.

Usage:
    python scripts/new_experiment.py --section 01 --name ecoli_autoencoder
"""

import argparse
from pathlib import Path
import shutil

TEMPLATE = '''# {name}

## Purpose
[What question does this analysis answer?]

## Hypothesis
[What do we expect to find?]

## Data
- Input: [data files]
- Annotations: [annotation files]

## Methods
[Brief description of approach]

## Outputs
- `results/` - [description]
- `figures/` - [description]

## Status
- [ ] Not started
- [ ] In progress
- [ ] Complete

## Final Iteration
[To be filled when complete]
'''

def create_experiment(section: str, name: str):
    base = Path(f"analysis/{section}_{name}")
    
    # Create directories
    (base / "iterations" / "iter_01" / "results").mkdir(parents=True)
    (base / "iterations" / "iter_01" / "figures").mkdir(parents=True)
    (base / "final" / "results").mkdir(parents=True)
    (base / "final" / "figures").mkdir(parents=True)
    
    # Create files
    (base / "README.md").write_text(TEMPLATE.format(name=name))
    (base / "iterations" / "ITERATION_LOG.md").write_text(
        "# Iteration Log\n\n| Iter | Date | Description | Key Change | Metrics | Decision |\n|------|------|-------------|------------|---------|----------|\n"
    )
    (base / "iterations" / "iter_01" / "NOTES.md").write_text(
        "# Iteration 01 Notes\n\n## Date\n\n## Changes from Previous\n- Initial implementation\n\n## Results\n\n## Observations\n\n## Decision\n\n## Next Steps\n"
    )
    
    print(f"Created experiment: {base}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--section", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    create_experiment(args.section, args.name)
```

#### `scripts/new_iteration.py`

```python
#!/usr/bin/env python
"""
Create a new iteration for an existing analysis.

Usage:
    python scripts/new_iteration.py --analysis 01_bacterial/01_ecoli --iteration 02
"""

import argparse
from pathlib import Path
import shutil

def create_iteration(analysis: str, iteration: str):
    base = Path(f"analysis/{analysis}/iterations/iter_{iteration}")
    
    # Create directories
    (base / "results").mkdir(parents=True)
    (base / "figures").mkdir(parents=True)
    
    # Create NOTES.md
    (base / "NOTES.md").write_text(
        f"# Iteration {iteration} Notes\n\n## Date\n\n## Changes from Previous\n\n## Results\n\n## Observations\n\n## Decision\n\n## Next Steps\n"
    )
    
    # Copy previous iteration's script as starting point
    prev_iter = int(iteration) - 1
    prev_script = base.parent / f"iter_{prev_iter:02d}" / f"run_analysis_{prev_iter:02d}.py"
    if prev_script.exists():
        shutil.copy(prev_script, base / f"run_analysis_{iteration}.py")
        print(f"Copied previous script as starting point")
    
    print(f"Created iteration: {base}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True)
    parser.add_argument("--iteration", required=True)
    args = parser.parse_args()
    create_iteration(args.analysis, args.iteration)
```

### 5. Shared Library Templates

Create template files for the `lib/` directory:

#### `lib/evaluation/benchmark.py` Template

```python
"""
Standardized benchmarking interface for paper-driven SMAIRT projects.

Supports multiple ground truth sources and reports all metrics.
"""

from typing import List, Dict, Optional
import pandas as pd
from pathlib import Path

def run_standard_benchmark(
    associations_file: str,
    organism: str,
    output_dir: str,
    thresholds: List[float] = None,
    ground_truth_sources: List[str] = None
) -> Dict:
    """
    Run standardized benchmark with multiple ground truth sources.
    
    Parameters:
    -----------
    associations_file : str
        Path to associations CSV
    organism : str
        Organism key for loading annotations
    output_dir : str
        Directory for output files
    thresholds : List[float]
        Thresholds to evaluate (default: [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99])
    ground_truth_sources : List[str]
        Ground truth sources (default: ["kegg_reactions"])
        Options: "kegg_reactions", "kegg_modules", "kegg_pathways", "string", "go"
    
    Returns:
    --------
    Dict with metrics_by_source and file_paths
    """
    if thresholds is None:
        thresholds = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
    if ground_truth_sources is None:
        ground_truth_sources = ["kegg_reactions"]
    
    # Implementation here
    pass
```

#### `lib/visualization/style.py` Template

```python
"""
Consistent plot styling for paper-driven SMAIRT projects.
"""

import matplotlib.pyplot as plt

# Color palette
COLORS = {
    "primary": "#2ecc71",
    "secondary": "#3498db",
    "tertiary": "#9b59b6",
    "quaternary": "#e74c3c",
    "quinary": "#f39c12",
}

METHOD_COLORS = {
    "autoencoder": "#2ecc71",
    "pearson": "#3498db",
    "spearman": "#9b59b6",
    "mutual_info": "#e74c3c",
    "jaccard": "#f39c12",
}

def setup_plot_style():
    """Set up matplotlib style for publication."""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['figure.dpi'] = 150
```

### 6. Update README and Documentation

Add documentation explaining the paper-driven mode:

#### In main README.md:

```markdown
## Project Modes

SMAIRT supports two project modes:

### Standard Mode (default)
For hypothesis-driven research following the traditional scientific method:
- Synthetic data → Benchmark data → Real data progression
- Best for: Method development, algorithm validation

### Paper-Driven Mode
For research starting with a paper outline and real datasets:
- Paper outline + Real data → Analysis plan → Iterative execution
- Best for: Transforming existing work into papers, multi-dataset studies

To create a paper-driven project:
```bash
cookiecutter gh:your-org/smairt-cookiecutter --project_mode paper_driven
```
```

---

## Implementation Checklist

When implementing these changes to SMAIRT cookiecutter:

- [ ] Add `project_mode` variable to `cookiecutter.json`
- [ ] Create conditional directory structure using Jinja2
- [ ] Add paper-driven prompt templates to `prompts/`
- [ ] Create paper-driven script templates
- [ ] Add shared library templates to `lib/`
- [ ] Update main README with mode documentation
- [ ] Add TUTORIAL_PAPER_DRIVEN.md with walkthrough
- [ ] Test both modes generate correctly
- [ ] Update any CI/CD to test both modes

---

## Example Workflow

Here's how a researcher would use paper-driven mode:

1. **Generate project**:
   ```bash
   cookiecutter gh:your-org/smairt-cookiecutter --project_mode paper_driven
   ```

2. **Add paper outline** to `paper/outline.md`

3. **Add datasets** to `data/` directory

4. **Run initial prompt** with AI assistant:
   ```
   Please read prompts/InitialPrompt.txt and follow the instructions.
   My paper outline is in paper/outline.md and my data is in data/.
   ```

5. **Review and refine** the generated analysis and repository plans

6. **Execute analyses** following the iteration workflow

7. **Generate final manifest** when complete:
   ```bash
   python scripts/generate_manifest.py
   ```

---

## Key Differences Summary

| Aspect | Standard SMAIRT | Paper-Driven SMAIRT |
|--------|-----------------|---------------------|
| Starting point | Hypothesis | Paper outline + data |
| Data progression | Synthetic → Benchmark → Real | All real data |
| Directory structure | By data type | By paper section |
| Iteration focus | Method refinement | Parameter tuning |
| Final output | Validated method | Paper-ready results |
| Timeline unit | Weeks | Days (AI-assisted) |

---

## Notes from VaLPAS Project

The paper-driven mode was developed based on lessons learned from the VaLPAS paper project:

1. **Multiple ground truths are essential** - Never rely on a single benchmark
2. **Multiple metrics matter** - PPV alone is insufficient
3. **Cross-dataset comparisons** - Map to common identifiers (e.g., KO) for comparison
4. **Tool comparisons** - Include existing tools for context
5. **Iteration tracking** - Separate scripts prevent confusion
6. **Final manifest** - Critical for reproducibility and paper writing
7. **AI-assisted timeline** - Days not weeks with good AI support
