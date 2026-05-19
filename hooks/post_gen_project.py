#!/usr/bin/env python
"""
Post-generation hook for SMAIRT template.

This script runs after cookiecutter generates the project structure.
It handles optional setup tasks like initializing a git repository.
"""

import os
import subprocess
import sys

def init_git_repo():
    """Initialize a git repository and make initial commit."""
    try:
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial SMAIRT project structure"],
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        # Git not installed
        return False

def print_standard_mode_message():
    """Print success message for standard mode."""
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   🧪 SMAIRT Project Created Successfully! 🧪                          ║
║                                                                       ║
║   Scientific Method with AI Research Template - STANDARD MODE         ║
║                                                                       ║
║   "It's a breadcrumb trail that allows you to get right back to       ║
║   where you started from—even if you start in a completely new        ║
║   thread, even if you give it to a new API."                          ║
║                                                                       ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   Next steps:                                                         ║
║                                                                       ║
║   1. Review the philosophy:                                           ║
║      docs/SMAIRT_PHILOSOPHY.md                                        ║
║                                                                       ║
║   2. Review the 12 steps:                                             ║
║      docs/12_STEPS.md                                                 ║
║                                                                       ║
║   3. Define your research question:                                   ║
║      background/01_initial_question.md                                ║
║                                                                       ║
║   4. Set up your AI session with:                                     ║
║      prompts/AI_CONTEXT.md (give this to your AI)                     ║
║      prompts/CODE_CONVENTIONS.md (give this to your AI)               ║
║      prompts/SESSION_START.md (ready-to-paste prompts)                ║
║                                                                       ║
║   5. Start experimenting:                                             ║
║      python scripts/new_script.py                                     ║
║                                                                       ║
║   6. Track your intellectual contributions:                           ║
║      prompts/intellectual_contribution.md                             ║
║                                                                       ║
║   7. Compile context for new AI sessions:                             ║
║      python scripts/compile_for_ai.py                                 ║
║                                                                       ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   The 4-Part Structure:                                               ║
║                                                                       ║
║   1. Background - Question, literature, previous results              ║
║   2. Hypothesis - What you're testing                                 ║
║   3. Methods    - The code and data                                   ║
║   4. Results    - Output logs + interpretation                        ║
║                                                                       ║
║   Future directions feed back into Background for the next cycle.     ║
║                                                                       ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   Data Progression:                                                   ║
║                                                                       ║
║   1. Synthetic   (experiments/01_synthetic/)  - Fast iteration        ║
║   2. Downloaded  (experiments/02_downloaded/) - Benchmark validation  ║
║   3. Real data   (experiments/03_real_data/)  - Full test             ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
""")


def print_paper_driven_mode_message():
    """Print success message for paper-driven mode."""
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   📄 SMAIRT Project Created Successfully! 📄                          ║
║                                                                       ║
║   Scientific Method with AI Research Template - PAPER-DRIVEN MODE     ║
║                                                                       ║
║   For research starting with a paper outline and real datasets.       ║
║                                                                       ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   Next steps:                                                         ║
║                                                                       ║
║   1. Add your paper outline:                                          ║
║      paper/outline.md                                                 ║
║                                                                       ║
║   2. Add your datasets:                                               ║
║      data/                                                            ║
║                                                                       ║
║   3. Review/update the analysis plan:                                 ║
║      analysis/ANALYSIS_PLAN.md                                        ║
║                                                                       ║
║   4. Start your AI session with:                                      ║
║      prompts/InitialPrompt_paper_driven.md                            ║
║                                                                       ║
║   5. Create your first analysis:                                      ║
║      python scripts/new_experiment.py --section 01 --name my_analysis ║
║                                                                       ║
║   6. Track iterations:                                                ║
║      python scripts/new_iteration.py --analysis 01_*/01_* --iter 02   ║
║                                                                       ║
║   7. Finalize results:                                                ║
║      python scripts/finalize_iteration.py --analysis ... --iter 02    ║
║                                                                       ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   Paper-Driven Workflow:                                              ║
║                                                                       ║
║   Paper outline + Data → Analysis plan → Iterative execution → Paper  ║
║                                                                       ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   Key Files:                                                          ║
║                                                                       ║
║   - paper/outline.md         - Your paper structure                   ║
║   - analysis/ANALYSIS_PLAN.md - Maps analyses to paper sections       ║
║   - analysis/BREADCRUMB_TRAIL.md - Running log of all work            ║
║   - FINAL_MANIFEST.md        - Maps final results to paper            ║
║                                                                       ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   Iteration Tracking:                                                 ║
║                                                                       ║
║   Each analysis has: iter_01/, iter_02/, ... → final/                 ║
║   Decisions: ACCEPT (use for paper) / REVISE / ABANDON                ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
""")


def main():
    """Main post-generation hook."""

    # Initialize git repo if requested
    if "{{ cookiecutter.create_git_repo }}" == "yes":
        if init_git_repo():
            print("✓ Git repository initialized")
        else:
            print("✗ Could not initialize git repository (is git installed?)")

    # Print success message based on mode
    project_mode = "{{ cookiecutter.project_mode }}"
    
    if project_mode == "paper_driven":
        print_paper_driven_mode_message()
    else:
        print_standard_mode_message()

if __name__ == "__main__":
    main()
