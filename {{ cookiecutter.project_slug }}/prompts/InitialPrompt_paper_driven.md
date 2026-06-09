# Paper-Driven SMAIRT Project Setup

{% if cookiecutter.project_mode == 'paper_driven' %}
## Your Task

You are helping set up a research project that will produce a scientific paper. The researcher has:
1. A paper outline or structure
2. Real datasets ready for analysis
3. Specific research questions to answer

## Project Information

- **Project**: {{ cookiecutter.project_name }}
- **Author**: {{ cookiecutter.author_name }}
- **Domain**: {{ cookiecutter.domain }}
- **Research Question**: {{ cookiecutter.initial_research_question }}

## Process

1. **Read the paper outline** (`paper/outline.md`) to understand:
   - The overall narrative and structure
   - What results sections are needed
   - What figures/tables are expected

2. **Examine the available data** (`data/`) to understand:
   - What datasets are available
   - Data formats and quality
   - What analyses are feasible

3. **Review/Update the Analysis Plan** (`analysis/ANALYSIS_PLAN.md`) that:
   - Maps each paper section to specific analyses
   - Defines hypotheses for each analysis
   - Specifies data inputs and expected outputs
   - Establishes evaluation criteria and metrics
   - Sets a realistic timeline

4. **Review/Update the Repository Plan** (`analysis/REPOSITORY_PLAN.md`) that:
   - Defines the directory structure
   - Documents shared library functions
   - Establishes naming conventions
   - Specifies iteration tracking approach

5. **Present both plans for review** before implementation

## Key Principles

- **All data is real data** - No synthetic/benchmark phases
- **Iteration tracking** - Separate scripts per iteration (run_analysis_01.py, etc.)
- **Multiple metrics** - Never rely on a single metric
- **Multiple validation approaches** - Validate against multiple sources where possible
- **Reproducibility** - Fixed seeds (default: 1024), documented parameters, version control
- **Final path capture** - FINAL_MANIFEST.md documents exactly which iteration produced each result
- **Pattern reuse** - Check `prompts/KNOWN_PATTERNS.md` before writing code; update it when solving new errors or creating reusable patterns

## Questions to Ask

Before creating the plan, clarify:
1. What is the target journal and format requirements?
2. Are there existing analyses to reproduce/extend?
3. What computational resources are available (local/HPC/GPU)?
4. What is the timeline for completion?
5. Are there specific tools or methods that must be compared against?

## Directory Structure

```
{{ cookiecutter.project_slug }}/
├── paper/                      # Paper documents
│   ├── outline.md              # Paper outline
│   ├── drafts/                 # Version-controlled drafts
│   └── reviewer_feedback/      # Feedback documents
├── data/                       # All datasets
├── analysis/                   # All analyses
│   ├── ANALYSIS_PLAN.md        # Analysis plan
│   ├── REPOSITORY_PLAN.md      # Repository organization
│   ├── BREADCRUMB_TRAIL.md     # Running log
│   └── XX_figures/             # Final publication figures
├── lib/                        # Shared library
├── prompts/                    # AI prompts (you are here)
├── scripts/                    # Utility scripts
├── FINAL_MANIFEST.md           # Maps results to paper
└── README.md
```

## Getting Started

1. Review the paper outline in `paper/outline.md`
2. Check what data is available in `data/`
3. Update `analysis/ANALYSIS_PLAN.md` with specific analyses
4. Begin with the first analysis section
{% else %}
This prompt is for paper-driven mode only.

For standard SMAIRT mode, see:
- `AI_CONTEXT.md` for project context
- `SESSION_START.md` for session prompts
{% endif %}
