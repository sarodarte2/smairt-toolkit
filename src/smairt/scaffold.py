"""Safe, low-friction SMAIRT project scaffolding."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from smairt.models import (
    DataClassification,
    DataPolicy,
    EnvironmentConfig,
    EnvironmentMode,
    GitConfig,
    ProjectInfo,
    SmairtConfig,
)
from smairt.utils import atomic_write, slugify

DIRECTORIES = (
    ".agents/skills/smairt-research/references",
    ".codex",
    ".githooks",
    "docs",
    "prompts",
    "environment",
    "references/pdfs",
    "background",
    "plans",
    "hypotheses/proposals",
    "experiments",
    "scripts/shared",
    "results",
    "analysis",
    "paper/working",
    "paper/drafts",
    "paper/figures",
    "paper/tables",
    "paper/reviewer_feedback",
    "paper/permissions",
)


GITIGNORE = """# Secrets
.env
.env.*
!.env.example
*.pem
*.key
*.p12
credentials*.json
secrets*.json
secrets*.yaml

# Local reference documents
references/pdfs/*
!references/pdfs/.gitkeep

# Raw and large scientific data
data/raw/
data/local/
*.fast5
*.pod5
*.fastq
*.fastq.gz
*.fq
*.fq.gz
*.bam
*.cram
*.bai
*.crai

# Environments and caches
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.DS_Store
"""


AGENTS = """# SMAIRT Project Guidance

This repository uses SMAIRT. The authoritative project contract is `smairt.yaml`.

Before research work:
1. Run `smairt status --json`.
2. Use the repository skill in `.agents/skills/smairt-research/`.
3. Load only the convention relevant to the current task.
4. Create research artifacts through SMAIRT commands.
5. Execute experiments through `smairt run`.
6. Run `smairt validate` before reporting completion.

Never place secrets or raw research data in Git. Never rewrite an immutable run record.
Do not activate or finalize a hypothesis without an explicit human decision.
"""


SKILL = """---
name: smairt-research
description: >
  Use for planning, executing, interpreting, or documenting research
  in this SMAIRT project.
---

# SMAIRT Research Workflow

1. Run `smairt status --json` and identify the current task.
2. Run `smairt context --task <planning|code|run|interpretation|paper>`.
3. Read only the returned files.
4. Use SMAIRT commands to create hypotheses, experiments, iterations, runs, and decisions.
5. For an initial background, use indexed local references first. Ask before academic web
   research and index every added source.
6. When asked for hypotheses, create exactly three meaningfully distinct options in a proposal
   set. Explain rationale, falsifiable prediction, competing explanation, required data,
   feasibility, confounders, and differences. Never activate one without human selection.
7. Record human choices in `prompts/intellectual_contribution.md`.
8. Validate before claiming an artifact is complete or accepted.

See `references/workflow.md` for the artifact chain and correction rules.
"""


SKILL_REFERENCE = """# Workflow Reference

```text
question + references -> initial background -> three proposal options
-> human-selected hypothesis -> experiment -> iteration -> run
-> interpretation -> ACCEPT | REVISE | ABANDON | BLOCKED
```

- Failed identical execution: create a new run in the same iteration.
- Changed method, data, split, code logic, or parameters: create a new iteration.
- Metadata correction: append an amendment.
- Invalid accepted evidence: supersede or retract it; never erase it.
- Paper elements may reference only accepted, non-retracted runs.
"""


CODE_CONVENTIONS = """# Code Conventions

- Use numbered experiment and iteration IDs created by SMAIRT.
- Keep parameters in the iteration `config.yaml`, not embedded in code.
- Read output locations from `SMAIRT_RESULTS_DIR`, `SMAIRT_FIGURES_DIR`, and
  `SMAIRT_CONFIG_PATH`.
- Validate inputs explicitly and fail loudly on malformed data.
- Record deterministic seeds when randomness is used.
- Put reusable project code in `scripts/shared/`.
- Keep scripts independently runnable and include hypothesis/purpose references in docstrings.
- Do not hardcode machine-specific absolute paths in committed code.
"""


RESEARCH_CONVENTIONS = """# Research Conventions

- A project may begin with uncertainty; a hypothesis is not required during setup.
- Hypothesis-driven work states its prediction, rationale, competing explanation, success
  criteria, data, controls, and confounders before execution.
- Exploratory, QC, infrastructure, and reproduction work records a clear purpose instead.
- Treat biological/experimental replicates as independent units; avoid leakage across splits.
- Distinguish source-backed claims, project evidence, inference, and evidence gaps.
- Preserve unsuccessful work and record why it was revised or abandoned.
"""


INTERPRETATION_CONVENTIONS = """# Interpretation Conventions

Separate:
1. Observed results.
2. Derived statistical results.
3. Scientific interpretation.
4. Speculation or future hypotheses.

Assess the stated hypothesis or purpose, identify where the result works and fails, state
limitations and confounders, and request an explicit ACCEPT, REVISE, ABANDON, or BLOCKED
decision from the human researcher.
"""


HYPOTHESIS_TEMPLATE = """---
id: HYPOTHESIS_XXX
status: PENDING
proposal_set: null
selected_by: null
background_sha256: null
reference_index_sha256: null
---

# Hypothesis XXX: Title

## Statement
## Rationale
## Falsifiable Prediction
## Null or Competing Explanation
## Required Data and Controls
## Success and Failure Criteria
## Known Confounders
## Human Selection Rationale
"""


ANALYSIS_TEMPLATE = """# Analysis: EXPERIMENT_XXX / ITERATION_XXX

## Executive Summary
## Hypothesis or Purpose
## Run Records
## Observed Results
## Derived Results
## Interpretation
## Where It Works
## Where It Breaks Down
## Limitations and Confounders
## Decision
## Next Steps
## Intellectual Contribution Notes
"""


PAPER_README = """# Paper

This is the single home for evolving scholarly output. `working/` contains the live narrative;
`drafts/` contains meaningful milestones; figures and tables must be mapped in
`paper/manifest.yaml` to accepted run evidence. Not every experiment belongs in the paper,
but every result used in the paper must be traceable.
"""


PHILOSOPHY = """# SMAIRT Philosophy

SMAIRT uses the scientific method to make AI-assisted research rapid, traceable, and
reproducible. AI can accelerate navigation of existing knowledge and implementation; humans
remain responsible for framing, novelty, judgment, interpretation, and decisions.

The core record is Background -> Hypothesis or Purpose -> Methods -> Results and Interpretation.
Next steps seed later work, and intellectual contributions remain visible.
"""


WORKFLOW = """# SMAIRT Workflow

1. Record the initial question and local reference material.
2. Build a source-grounded working background.
3. Generate three distinct hypothesis options and let the human choose or edit.
4. Create a linked experiment and iteration.
5. Execute through `smairt run` for automatic provenance and logs.
6. Interpret observed evidence separately from inference.
7. Record a human decision and revise without rewriting history.
8. Link only accepted evidence into the paper manifest.
"""


ACKNOWLEDGMENTS = """# Acknowledgments

SMAIRT originated in the Pacific Northwest National Laboratory Computational Biology
community and was refined through practical AI-assisted research workflows. This evolved
toolkit builds on the PNNL-CompBio/smairt-template repository and its contributors.

The orange terminal accent is a small acknowledgment of those PNNL origins. This project does
not imply endorsement by Pacific Northwest National Laboratory.
"""


HOOK = """#!/bin/sh
if command -v smairt >/dev/null 2>&1; then
  smairt validate --staged
else
  echo "SMAIRT is required to validate this research repository." >&2
  exit 1
fi
"""


CODEX_HOOKS = {
    "hooks": {
        "PreToolUse": [
            {
                "matcher": "^Bash$",
                "hooks": [
                    {
                        "type": "command",
                        "command": "smairt validate --tool-input",
                        "timeout": 30,
                        "statusMessage": "Checking SMAIRT safety policy",
                    }
                ],
            }
        ]
    }
}


def conda_environments() -> list[dict[str, str]]:
    if not shutil.which("conda"):
        return []
    result = subprocess.run(
        ["conda", "env", "list", "--json"], capture_output=True, text=True, check=False
    )
    if result.returncode:
        return []
    payload = json.loads(result.stdout)
    return [{"name": Path(prefix).name or "base", "prefix": prefix} for prefix in payload["envs"]]


def create_conda_environment(name: str) -> None:
    if not shutil.which("conda"):
        raise RuntimeError("Conda is not installed; choose an existing/no-managed environment")
    subprocess.run(["conda", "create", "-y", "-n", name, "python=3.11"], check=True)


def _write(path: Path, relative: str, content: str) -> None:
    atomic_write(path / relative, content.rstrip() + "\n")


def create_project(
    destination: Path,
    *,
    name: str,
    author: str,
    classification: DataClassification,
    question: str | None = None,
    description: str | None = None,
    initialize_git: bool = True,
    environment_mode: EnvironmentMode = EnvironmentMode.NONE,
    environment_name: str | None = None,
    environment_prefix: str | None = None,
    create_environment: bool = False,
) -> SmairtConfig:
    destination = destination.expanduser().resolve()
    if (destination / "smairt.yaml").exists():
        raise FileExistsError(f"{destination} is already a SMAIRT project")
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()) and not (destination / ".git").exists():
        raise FileExistsError("destination is not empty; use 'smairt init' after reviewing it")

    for directory in DIRECTORIES:
        (destination / directory).mkdir(parents=True, exist_ok=True)
    for keep in ("references/pdfs/.gitkeep", "results/.gitkeep"):
        _write(destination, keep, "")

    slug = slugify(name)
    if environment_mode is EnvironmentMode.NEW_CONDA:
        environment_name = environment_name or f"smairt-{slug}"
        if create_environment:
            create_conda_environment(environment_name)

    git_exists = (destination / ".git").exists()
    git_enabled = initialize_git or git_exists
    config = SmairtConfig(
        project=ProjectInfo(
            name=name,
            slug=slug,
            author=author,
            question=question or None,
            description=description or None,
        ),
        data=DataPolicy(classification=classification),
        environment=EnvironmentConfig(
            mode=environment_mode, name=environment_name, prefix=environment_prefix
        ),
        git=GitConfig(enabled=git_enabled, managed_hooks=git_enabled),
    )
    config.dump(destination / "smairt.yaml")

    files = {
        ".gitignore": GITIGNORE,
        "AGENTS.md": AGENTS,
        ".agents/skills/smairt-research/SKILL.md": SKILL,
        ".agents/skills/smairt-research/references/workflow.md": SKILL_REFERENCE,
        ".codex/config.toml": 'model_instructions_file = "../AGENTS.md"\n',
        ".codex/hooks.json": json.dumps(CODEX_HOOKS, indent=2),
        ".githooks/pre-commit": HOOK,
        "docs/PHILOSOPHY.md": PHILOSOPHY,
        "docs/WORKFLOW.md": WORKFLOW,
        "docs/GIT_AND_COLLABORATION.md": (
            "# Git and Collaboration\n\n"
            "Commit meaningful research checkpoints; Git is recommended but optional.\n"
        ),
        "docs/ACKNOWLEDGMENTS.md": ACKNOWLEDGMENTS,
        "prompts/CODE_CONVENTIONS.md": CODE_CONVENTIONS,
        "prompts/RESEARCH_CONVENTIONS.md": RESEARCH_CONVENTIONS,
        "prompts/INTERPRETATION_CONVENTIONS.md": INTERPRETATION_CONVENTIONS,
        "prompts/KNOWN_PATTERNS.md": (
            "# Known Patterns and Errors\n\n"
            "Record reusable solutions and costly mistakes here.\n"
        ),
        "prompts/intellectual_contribution.md": (
            "# Intellectual Contribution Log\n\n"
            "Record human framing, choices, insights, and decisions.\n"
        ),
        "background/initial_question.md": (
            f"# Initial Question\n\n{question or '[Not specified yet]'}\n"
        ),
        "background/project_description.md": (
            f"# Project Description\n\n{description or '[Not specified yet]'}\n"
        ),
        "background/initial_background.md": "# Initial Background\n\nStatus: DRAFT\n",
        "plans/README.md": (
            "# Plans\n\n"
            "Create a plan before multi-step work, pivots, or architecture changes.\n"
        ),
        "hypotheses/README.md": (
            "# Hypotheses\n\n"
            "Proposal sets preserve AI options; only a human can activate one.\n"
        ),
        "hypotheses/HYPOTHESIS_TEMPLATE.md": HYPOTHESIS_TEMPLATE,
        "experiments/README.md": (
            "# Experiments\n\n"
            "Experiment and iteration directories are created by SMAIRT.\n"
        ),
        "scripts/README.md": (
            "# Scripts\n\nUse scripts/shared for reusable project-specific code.\n"
        ),
        "scripts/shared/README.md": (
            "# Shared Code\n\nExtract patterns reused across project experiments.\n"
        ),
        "analysis/README.md": (
            "# Analysis\n\nInterpret results against their linked hypothesis or purpose.\n"
        ),
        "analysis/ANALYSIS_TEMPLATE.md": ANALYSIS_TEMPLATE,
        "references/README.md": (
            "# References\n\n"
            "PDFs remain local; verified metadata and checksums live in index.yaml.\n"
        ),
        "references/index.yaml": "references: []\n",
        "paper/README.md": PAPER_README,
        "paper/manifest.yaml": "elements: []\n",
        "paper/contribution_statement.md": "# Contribution Statement\n",
        "environment/software_versions.yaml": "tools: {}\n",
    }
    if environment_mode is EnvironmentMode.NEW_CONDA:
        files["environment/environment.yml"] = (
            f"name: {environment_name}\n"
            "channels:\n  - conda-forge\n"
            "dependencies:\n  - python=3.11\n"
        )
    for relative, content in files.items():
        _write(destination, relative, content)

    hook = destination / ".githooks/pre-commit"
    hook.chmod(0o755)
    if initialize_git and not git_exists:
        subprocess.run(["git", "init"], cwd=destination, check=True, capture_output=True)
    if git_enabled:
        subprocess.run(
            ["git", "config", "core.hooksPath", ".githooks"],
            cwd=destination,
            check=True,
            capture_output=True,
        )
    return config
