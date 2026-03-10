# SMAIRT Complete Tutorial

A comprehensive walkthrough of the SMAIRT framework using a real example: building a simple classifier and testing it across synthetic, benchmark, and real data.

---

## Table of Contents

1. [Overview](#overview)
2. [Setting Up Your Project](#setting-up-your-project)
3. [Phase 1: Synthetic Data](#phase-1-synthetic-data)
4. [Phase 2: Downloaded Benchmark Data](#phase-2-downloaded-benchmark-data)
5. [Phase 3: Real Data](#phase-3-real-data)
6. [Compiling Results](#compiling-results)
7. [Writing Up Findings](#writing-up-findings)

---

## Overview

In this tutorial, we'll work through a complete SMAIRT research cycle investigating the question:

> **"How well does a simple decision boundary approach separate two classes under varying noise conditions?"**

We'll follow the scientific method:
- **Background**: What we know about classification
- **Hypothesis**: Our testable prediction
- **Methods**: Code to test the hypothesis
- **Results + Interpretation**: What we found and what it means

---

## Setting Up Your Project

### Install and Generate

```bash
pip install cookiecutter
cookiecutter gh:yourusername/smairt-cookiecutter
```

Enter these values when prompted:
- **project_name**: Classification Noise Study
- **project_slug**: classification_noise_study
- **author_name**: Your Name
- **initial_research_question**: How does noise affect simple classification boundaries?
- **domain**: machine_learning
- **ai_tool**: claude (or your preferred AI)

### Project Structure

```
classification_noise_study/
├── docs/
├── prompts/
├── background/
├── hypotheses/
├── experiments/
│   ├── 01_synthetic/
│   ├── 02_downloaded/
│   └── 03_real_data/
├── results/
│   ├── logs/
│   └── figures/
├── data/
└── scripts/
```

### Prime Your AI

Start a new AI session and paste the contents of:
1. `prompts/AI_CONTEXT.md`
2. `prompts/CODE_CONVENTIONS.md`

Or use this combined prompt:

```
I'm starting a SMAIRT project called "Classification Noise Study". 

The framework follows the scientific method with iterative cycles through:
Background → Hypothesis → Methods → Results → Interpretation → Next Steps

Key conventions:
- Scripts are numbered sequentially (script_01_..., script_02_...)
- Output goes to both console AND results/logs/
- Paste output as comments at the end of scripts
- Track intellectual contributions separately from AI suggestions

My research question: How does noise affect simple classification boundaries?

Please help me design and run experiments following this framework.
```

---

## Phase 1: Synthetic Data

Synthetic data lets us iterate quickly without external dependencies. We control all parameters, making it easy to isolate variables.

### Iteration 1: Establish Baseline

**Document your hypothesis** in `hypotheses/hypothesis_log.md`:

```markdown
## Hypothesis 01
**Statement**: A linear decision boundary can achieve >90% accuracy on linearly separable synthetic data with no noise.
**Status**: Testing
**Date**: [today]
```

**Ask your AI to create the first script**:

```
Please create script_01_baseline_no_noise.py in experiments/01_synthetic/ that:

1. Generates 2D synthetic data with two linearly separable classes (200 points each)
2. Fits a simple linear classifier (logistic regression or similar)
3. Reports accuracy, plots the decision boundary
4. Saves the plot to results/figures/
5. Outputs to both console and results/logs/script_01_baseline_no_noise_output.log

Hypothesis: A linear boundary achieves >90% accuracy on clean, linearly separable data.

Follow SMAIRT code conventions with the output comment block at the end.
```

**Run the script**:

```bash
cd classification_noise_study
python experiments/01_synthetic/script_01_baseline_no_noise.py
```

**Record results** by pasting output into the script's comment block:

```python
# === PASTE OUTPUT HERE ===
"""
=== OUTPUT ===
Generated 400 samples (200 per class)
Linear classifier accuracy: 0.98
Decision boundary saved to results/figures/script_01_boundary.png

=== INTERPRETATION ===
Hypothesis SUPPORTED. Linear boundary achieves 98% accuracy on clean data.
This establishes our baseline for noise experiments.

=== NEXT STEPS ===
Test with increasing noise levels to find where accuracy degrades.
"""
```

**Log the session** in `prompts/session_log.md`:

```markdown
## Session 1 - [Date]

### Prompt 1
[Paste your prompt here]

### Response Summary
AI generated script_01 with logistic regression classifier.
Baseline accuracy: 98%

### My Observations
- Clean separation as expected
- Ready to test noise robustness
```

**Track intellectual contribution** in `prompts/intellectual_contribution.md`:

```markdown
## Iteration 01 - Baseline

### What AI Suggested
- Use logistic regression for linear boundary
- Standard train/test split

### What I Contributed
- Decided to start with 2D for visualization
- Chose 200 samples per class as reasonable starting point
- Identified that we need noise testing next
```

### Iteration 2: Add Noise

**Update hypothesis log**:

```markdown
## Hypothesis 02
**Statement**: Accuracy will degrade gracefully as Gaussian noise increases, dropping below 90% around noise_std=0.5.
**Status**: Testing
**Builds on**: H01 (baseline established)
```

**Create the next script**:

```
Please create script_02_noise_sweep.py that:

1. Uses the same data generation as script_01
2. Adds Gaussian noise with std values: [0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
3. For each noise level, trains classifier and reports accuracy
4. Plots accuracy vs noise level
5. Identifies the threshold where accuracy drops below 90%

Hypothesis: Accuracy drops below 90% around noise_std=0.5
```

**Run and record**:

```bash
python experiments/01_synthetic/script_02_noise_sweep.py
```

Paste output, interpret results, log session, track contributions.

### Iteration 3: Explore Boundaries

Based on results, you might find the threshold is different than expected. This is where YOUR insight matters:

```markdown
### My Contribution - Iteration 03
Results showed accuracy dropped below 90% at noise_std=0.3, not 0.5.

I noticed the classes were closer together than I assumed. 
AI suggested increasing class separation, but I realized we should 
instead test whether a non-linear boundary helps at the CURRENT separation.

This is a different question than AI suggested - testing boundary 
complexity rather than data properties.
```

---

## Phase 2: Downloaded Benchmark Data

Now we validate our findings on real-world benchmark datasets that others have used.

### Transition to Benchmarks

**Update background** in `background/01_initial_question.md`:

```markdown
## Summary of Synthetic Phase

- Linear boundaries achieve 98% on clean data
- Accuracy degrades to <90% at noise_std=0.3
- Non-linear boundaries provide ~5% improvement at high noise

## Questions for Benchmark Phase

1. Do these patterns hold on real datasets?
2. What noise levels exist in common benchmarks?
3. Are there datasets where linear boundaries fail unexpectedly?
```

### Iteration 4: Download and Characterize Data

```
Please create script_01_download_benchmarks.py in experiments/02_downloaded/ that:

1. Downloads these sklearn datasets: Iris, Wine, Breast Cancer
2. For each dataset:
   - Reports basic statistics (samples, features, classes)
   - Estimates "noise level" via class overlap
   - Tests linear classifier accuracy
3. Saves data to data/downloaded/
4. Creates a summary comparing to our synthetic findings

Based on synthetic results, I expect linear accuracy >90% on clean datasets 
and lower on datasets with more class overlap.
```

### Iteration 5: Validate Noise Findings

```
Please create script_02_benchmark_noise_analysis.py that:

1. Loads the downloaded benchmark datasets
2. For each dataset:
   - Adds artificial noise at levels [0, 0.1, 0.2, 0.3, 0.5]
   - Measures accuracy degradation
   - Compares degradation curve to synthetic results
3. Tests whether our synthetic threshold (0.3) predicts benchmark behavior

Hypothesis: Datasets with inherent noise equivalent to std=0.3 will show 
similar accuracy to our synthetic experiments at that noise level.
```

### Document Cross-Validation

In `analysis/iteration_log.md`:

```markdown
## Benchmark Validation Summary

### Findings
- Iris: Linear accuracy 97%, matches synthetic clean data
- Wine: Linear accuracy 91%, some natural class overlap
- Breast Cancer: Linear accuracy 95%, clean separation

### Comparison to Synthetic
Our synthetic noise threshold (0.3) correctly predicted:
- Iris would have high accuracy (low inherent noise)
- Wine would be borderline (moderate inherent noise)

### Limitations Discovered
- 2D synthetic data doesn't capture high-dimensional effects
- Real datasets have non-Gaussian noise patterns
```

---

## Phase 3: Real Data

Now apply your validated approach to your actual research data.

### Prepare Real Data

Place your data in `data/real/` and document it:

```markdown
# data/real/README.md

## Dataset: [Your Dataset Name]

**Source**: [Where it came from]
**Samples**: [Number]
**Features**: [Number and description]
**Classes**: [What you're classifying]

**Known characteristics**:
- Expected noise level based on collection method
- Any preprocessing applied
```

### Iteration 6: Apply to Real Data

```
Please create script_01_real_data_baseline.py in experiments/03_real_data/ that:

1. Loads my real dataset from data/real/
2. Applies the same linear classifier we validated
3. Reports accuracy and compares to benchmark expectations
4. Identifies whether results match our noise-accuracy model

Based on synthetic and benchmark phases, I expect:
- If data is clean: >95% accuracy
- If data has moderate noise: 85-95% accuracy
- If data has high noise: <85% accuracy
```

### Iteration 7: Apply Insights

Based on your real data results, apply what you learned:

```
Results show 82% accuracy on real data, suggesting high noise.

From our synthetic experiments, we found non-linear boundaries 
improved accuracy by ~5% at high noise levels.

Please create script_02_nonlinear_comparison.py that:
1. Tests non-linear classifiers (SVM with RBF, Random Forest)
2. Compares to linear baseline
3. Determines if the ~5% improvement holds on real data
```

---

## Compiling Results

### Generate AI Context

When starting a new session or switching AI tools:

```bash
python scripts/compile_for_ai.py
```

This creates a summary of:
- All scripts and their outputs
- Hypotheses tested and results
- Current state of the research

Paste this into your new AI session to continue seamlessly.

### Review the Breadcrumb Trail

Your project now contains:

```
experiments/
├── 01_synthetic/
│   ├── script_01_baseline_no_noise.py      # Baseline: 98% accuracy
│   ├── script_02_noise_sweep.py            # Threshold: 0.3 std
│   └── script_03_nonlinear_test.py         # +5% with non-linear
├── 02_downloaded/
│   ├── script_01_download_benchmarks.py    # Iris, Wine, BC
│   └── script_02_benchmark_noise_analysis.py # Validated threshold
└── 03_real_data/
    ├── script_01_real_data_baseline.py     # 82% linear
    └── script_02_nonlinear_comparison.py   # 87% non-linear
```

Each script contains its output as comments, creating a complete record.

---

## Writing Up Findings

### Export for Paper

Use the paper_draft/ directory to compile findings:

**methods_schematic.md**:
```markdown
## Methods

1. Established baseline on synthetic data (N=400, 2 classes)
2. Characterized noise-accuracy relationship
3. Validated on 3 benchmark datasets
4. Applied to real dataset (N=[your N])
```

**results_narrative.md**:
```markdown
## Results

### Synthetic Phase
Linear classification achieved 98% accuracy on clean synthetic data.
Accuracy degraded below 90% at noise std=0.3.

### Benchmark Validation  
The noise threshold correctly predicted accuracy on Iris (97%), 
Wine (91%), and Breast Cancer (95%) datasets.

### Real Data Application
Real data showed 82% linear accuracy, consistent with high noise.
Non-linear methods improved accuracy to 87%, matching synthetic predictions.
```

### Track Final Contributions

In `prompts/intellectual_contribution.md`:

```markdown
## Project Summary - Intellectual Contributions

### Key Insights I Provided
1. Identified noise threshold as the key variable to characterize
2. Recognized that benchmark validation should precede real data
3. Connected synthetic findings to real data interpretation

### Where AI Helped
1. Generated boilerplate code quickly
2. Suggested standard datasets for validation
3. Implemented visualization consistently

### Novel Contribution
The systematic characterization of noise thresholds across synthetic, 
benchmark, and real data provides a framework for predicting classifier 
performance on new datasets.
```

---

## Summary

You've now completed a full SMAIRT cycle:

1. ✅ **Synthetic**: Fast iteration, established baseline and thresholds
2. ✅ **Benchmark**: Validated findings on known datasets
3. ✅ **Real Data**: Applied validated approach to actual research
4. ✅ **Documentation**: Complete breadcrumb trail for reproducibility

### Key Practices

- **Number scripts sequentially** for clear timeline
- **Paste output as comments** for the breadcrumb trail
- **Log sessions** to track prompts and responses
- **Track intellectual contributions** to document your insights
- **Use compile_for_ai.py** to maintain context across sessions

### Next Steps

- Explore `scripts/README.md` for additional helper scripts
- Read `docs/SMAIRT_PHILOSOPHY.md` for deeper framework understanding
- Check `docs/BEST_PRACTICE_SINGLE.md` or `BEST_PRACTICE_COLLABORATIVE.md` for workflow tips
