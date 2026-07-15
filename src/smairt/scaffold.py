"""Safe, low-friction SMAIRT project scaffolding."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

from smairt import __version__
from smairt.licenses import license_manifest, render_license
from smairt.locking import ProjectMutationLock
from smairt.models import (
    Contributor,
    DataClassification,
    DataPolicy,
    EnvironmentConfig,
    EnvironmentMode,
    GitConfig,
    HarnessConfig,
    HarnessName,
    ProjectInfo,
    ProjectLicense,
    SafetyMode,
    SmairtConfig,
)
from smairt.transactions import FileTransaction
from smairt.utils import atomic_write, ensure_within, sha256_text, slugify
from smairt.workflows import shared_skill_files

DIRECTORIES = (
    ".agents/skills",
    ".codex",
    ".cursor",
    ".opencode",
    ".githooks",
    ".smairt/backups",
    ".smairt/events",
    ".smairt/contracts",
    ".smairt/corrections",
    ".smairt/local/summaries",
    ".smairt/locks",
    ".smairt/transactions",
    ".smairt/cache",
    ".smairt/run-manifests",
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
    "paper/evidence",
    "paper/claims",
    "paper/builds",
    "summaries/canonical",
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
.smairt/backups/
.smairt/local/
.smairt/locks/
.smairt/transactions/
.smairt/cache/
"""


SKILL_FILES = shared_skill_files()


CODE_CONVENTIONS = """# Code conventions

Research code must be readable by a new collaborator and structured enough for tools to index.

## Experiment structure

- Name new entrypoints `script_XXX_descriptive_name.py`, using the `EXPERIMENT_XXX` number.
- Begin with a module docstring containing experiment, iteration, hypothesis or purpose,
  dependencies, inputs, outputs, and scientific intent.
- Organize code into imports, SMAIRT paths/configuration, input loading and validation, analysis,
  outputs, and `main()`.
- Keep parameters in iteration `config.yaml`; do not hide scientific choices in code.
- Read paths from `SMAIRT_CONFIG_PATH`, `SMAIRT_RESULTS_DIR`, and `SMAIRT_FIGURES_DIR`.
- Use descriptive variable names. Include units in names when values would otherwise be ambiguous.
- Domain-standard names such as `Km` and `Vmax` are acceptable when defined clearly.
- Add type hints to functions and contract-oriented docstrings to public or reusable functions.
- Validate inputs explicitly and fail with messages that tell the researcher what is wrong.
- Record deterministic seeds whenever randomness is used.
- Print concise stage, input shape/count, configuration, output-path, and completion summaries;
  `smairt run` captures this output in the immutable run bundle.
- Put reusable code in `scripts/shared/` after a pattern genuinely repeats.
- Never hardcode machine-specific absolute paths or credentials.

## Scientific readability

- Comments explain scientific intent, assumptions, units, transformations, and why a choice was
  made. Do not merely translate syntax into English.
- Prefer small, purpose-named functions and straightforward control flow over clever compression.
- Avoid unexplained abbreviations, variable shadowing, and unnecessary reassignment.
- Keep data transformations explicit enough that a reader can track where each important value
  came from and where it is used.
- Update `scripts/CODE_INDEX.yaml` with `smairt code index` after structural code changes.
- Run `smairt code validate` before executing or reporting an experiment.

SMAIRT's runner is the logging authority. Do not add a second timestamped logger or paste raw output
into source comments.
"""


RESEARCH_CONVENTIONS = """# Research conventions

- A project may begin with uncertainty; a hypothesis is not required during setup.
- Hypothesis-driven work states its prediction, rationale, competing explanation, success
  criteria, data, controls, and confounders before execution.
- Exploratory, QC, infrastructure, and reproduction work records a clear purpose instead.
- Treat biological/experimental replicates as independent units; avoid leakage across splits.
- Distinguish source-backed claims, project evidence, inference, and evidence gaps.
- Preserve unsuccessful work and record why it was revised or abandoned.
- Treat validation as an integrity check, not proof that a scientific interpretation is correct.
"""


INTERPRETATION_CONVENTIONS = """# Interpretation conventions

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


PAPER_README = """# Paper workspace

This directory is the single home for evolving scholarly output. `working/` contains the current
narrative and `drafts/` preserves meaningful milestones. Evidence cards, claims, section reviews,
figures, and tables must remain linked through `paper/manifest.yaml`.

Not every experiment belongs in a manuscript. Every result used in one must be traceable to an
accepted run, an approved claim, and the references needed to interpret it. A build is a versioned
artifact, not permission to publish.
"""


PHILOSOPHY = """# Project philosophy

SMAIRT helps researchers use AI without assigning scientific authority to an assistant. AI can
accelerate literature navigation, comparison, implementation, and review. Researchers remain
responsible for framing, novelty, method choice, interpretation, and consequential decisions.

The durable record connects background, hypothesis or exploratory purpose, methods, immutable
runs, interpretation, evidence, and claims. Uncertainty and unsuccessful work remain visible so a
new collaborator can understand not only the current conclusion, but how the project reached it.
"""


WORKFLOW = """# Project workflow

1. Record the initial question, scope, and available references.
2. Build a background that separates source support, inference, limitations, and evidence gaps.
3. Compare three distinct hypotheses, or record a clear exploratory purpose.
4. Let the researcher select or revise the scientific direction.
5. Declare an experiment, iteration, protocol, controls, and interpretation criteria.
6. Execute through `smairt run` so code, configuration, environment, logs, and hashes are captured.
7. Interpret observations separately from derived results and speculation.
8. Record the researcher decision and revise through new iterations or appended corrections.
9. Link only accepted evidence and approved claims into reviewed manuscript text.

Use `smairt status --json` and `smairt next --json` whenever context is restored.
"""


ACKNOWLEDGMENTS = """# Acknowledgments

This project was created with SMAIRT Toolkit, an independent fork of the
[PNNL-CompBio/smairt-template](https://github.com/PNNL-CompBio/smairt-template) framework created
by the Pacific Northwest National Laboratory Computational Biology Group and its contributors.

SMAIRT Toolkit is not an official product of Pacific Northwest National Laboratory or The
University of Texas at El Paso. Optional color-palette names are informal easter eggs and do not
reproduce institutional marks or imply sponsorship, approval, or endorsement.
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
    """Discover available Conda environments without failing when Conda is absent."""
    if not shutil.which("conda"):
        return []
    try:
        result = subprocess.run(
            ["conda", "env", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode:
        return []
    try:
        payload = json.loads(result.stdout)
        environments = payload["envs"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []
    if not isinstance(environments, list) or not all(
        isinstance(item, str) for item in environments
    ):
        return []
    return [{"name": Path(prefix).name or "base", "prefix": prefix} for prefix in environments]


def create_conda_environment(name: str) -> None:
    """Create one Python 3.11 Conda environment owned by the research project."""
    if not shutil.which("conda"):
        raise RuntimeError("Conda is not installed; choose an existing/no-managed environment")
    try:
        subprocess.run(
            ["conda", "create", "-y", "-n", name, "python=3.11"],
            check=True,
            timeout=900,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Conda environment creation timed out after 15 minutes") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Conda could not create the environment; run 'conda info --envs' and retry"
        ) from exc
    except OSError as exc:
        raise RuntimeError(
            "Conda could not start; run 'smairt setup doctor' for shell setup guidance"
        ) from exc


def _write(path: Path, relative: str, content: str) -> None:
    """Write a normalized generated file through the atomic filesystem helper."""
    atomic_write(path / relative, content.rstrip() + "\n")


def _validate_scaffold_paths(root: Path, directories: tuple[str, ...]) -> None:
    """Reject directory symlinks before generated files can follow them."""
    for relative in directories:
        current = root
        for part in Path(relative).parts:
            current /= part
            if current.is_symlink():
                raise ValueError(f"scaffold directory must not be a symlink: {current}")
        ensure_within(root, current)


def _existing_conflicts(root: Path, relatives: set[str]) -> list[str]:
    """Return existing generated targets, including broken symlinks."""
    return sorted(relative for relative in relatives if os.path.lexists(root / relative))


def create_project(
    destination: Path,
    *,
    name: str,
    author: str,
    classification: DataClassification,
    author_email: str | None = None,
    question: str | None = None,
    description: str | None = None,
    fields_of_study: list[str] | None = None,
    license_name: ProjectLicense = ProjectLicense.MIT,
    initialize_git: bool = True,
    environment_mode: EnvironmentMode = EnvironmentMode.NONE,
    environment_name: str | None = None,
    environment_prefix: str | None = None,
    create_environment: bool = False,
    allow_existing: bool = False,
    harness: HarnessName = HarnessName.CODEX,
    safety_mode: str = "standard",
    confirm_contributor: bool = False,
) -> SmairtConfig:
    """Publish a complete new scaffold or safely initialize reviewed existing work.

    New projects are constructed and validated under a temporary sibling name,
    then revealed with one directory rename. Existing Git worktrees are changed
    in place under the project mutation lock.
    """
    destination = destination.expanduser().resolve()
    existing_content = destination.exists() and any(destination.iterdir())
    if existing_content:
        if (destination / "smairt.yaml").exists():
            raise FileExistsError(f"{destination} is already a SMAIRT project")
        if not (destination / ".git").exists() and not allow_existing:
            raise FileExistsError("destination is not empty; review it and pass allow_existing")
        with ProjectMutationLock(destination, "project initialize"):
            return _create_project_in_place(
                destination,
                name=name,
                author=author,
                author_email=author_email,
                classification=classification,
                question=question,
                description=description,
                fields_of_study=fields_of_study or [],
                license_name=license_name,
                initialize_git=initialize_git,
                environment_mode=environment_mode,
                environment_name=environment_name,
                environment_prefix=environment_prefix,
                create_environment=create_environment,
                allow_existing=allow_existing,
                harness=harness,
                safety_mode=safety_mode,
                confirm_contributor=confirm_contributor,
            )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.smairt-", dir=destination.parent)
    )
    try:
        config = _create_project_in_place(
            temporary,
            name=name,
            author=author,
            author_email=author_email,
            classification=classification,
            question=question,
            description=description,
            fields_of_study=fields_of_study or [],
            license_name=license_name,
            initialize_git=initialize_git,
            environment_mode=environment_mode,
            environment_name=environment_name,
            environment_prefix=environment_prefix,
            create_environment=create_environment,
            allow_existing=True,
            harness=harness,
            safety_mode=safety_mode,
            confirm_contributor=confirm_contributor,
        )
        SmairtConfig.load(temporary / "smairt.yaml")
        if destination.exists():
            destination.rmdir()
        temporary.replace(destination)
        return config
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _create_project_in_place(
    destination: Path,
    *,
    name: str,
    author: str,
    author_email: str | None,
    classification: DataClassification,
    question: str | None,
    description: str | None,
    fields_of_study: list[str],
    license_name: ProjectLicense,
    initialize_git: bool,
    environment_mode: EnvironmentMode,
    environment_name: str | None,
    environment_prefix: str | None,
    create_environment: bool,
    allow_existing: bool,
    harness: HarnessName,
    safety_mode: str,
    confirm_contributor: bool,
) -> SmairtConfig:
    """Create files inside a private staging directory or locked worktree."""
    if (destination / "smairt.yaml").exists():
        raise FileExistsError(f"{destination} is already a SMAIRT project")
    destination.mkdir(parents=True, exist_ok=True)
    existing_content = any(destination.iterdir())
    if existing_content and not (destination / ".git").exists() and not allow_existing:
        raise FileExistsError("destination is not empty; use 'smairt init' after reviewing it")

    _validate_scaffold_paths(destination, DIRECTORIES)

    slug = slugify(name)
    if environment_mode is EnvironmentMode.NEW_CONDA:
        environment_name = environment_name or slug
        if create_environment:
            create_conda_environment(environment_name)

    git_exists = (destination / ".git").exists()
    git_enabled = initialize_git or git_exists
    contributor = (
        Contributor(id=slugify(author), name=author, email=author_email)
        if confirm_contributor
        else None
    )
    config = SmairtConfig(
        project=ProjectInfo(
            name=name,
            slug=slug,
            author=author,
            question=question or None,
            description=description or None,
            fields_of_study=fields_of_study,
            license=license_name,
        ),
        data=DataPolicy(classification=classification),
        environment=EnvironmentConfig(
            mode=environment_mode, name=environment_name, prefix=environment_prefix
        ),
        git=GitConfig(enabled=git_enabled, managed_hooks=git_enabled),
        harness=HarnessConfig(active=harness),
        safety_mode=SafetyMode(safety_mode),
        contributors=[contributor] if contributor else [],
        active_contributor=contributor.id if contributor else None,
    )
    files = {
        "references/pdfs/.gitkeep": "",
        "results/.gitkeep": "",
        ".gitignore": GITIGNORE,
        "AGENTS.md": "",
        **SKILL_FILES,
        ".githooks/pre-commit": HOOK,
        "docs/PHILOSOPHY.md": PHILOSOPHY,
        "docs/WORKFLOW.md": WORKFLOW,
        "docs/GIT_AND_COLLABORATION.md": (
            "# Git and collaboration\n\n"
            "Git records file history; SMAIRT records scientific transitions and provenance. "
            "Use a branch or worktree for each contributor or independent line of work, and "
            "commit meaningful research checkpoints. The checkout mutation lock does not "
            "coordinate separate worktrees or resolve scientific conflicts.\n\n"
            "Never commit secrets, raw protected data, ignored local bindings, or local PDF "
            "copies. Before sharing, run `smairt validate --staged` and the safety checks "
            "appropriate to the project's classification.\n"
        ),
        "docs/ACKNOWLEDGMENTS.md": ACKNOWLEDGMENTS,
        "prompts/CODE_CONVENTIONS.md": CODE_CONVENTIONS,
        "prompts/RESEARCH_CONVENTIONS.md": RESEARCH_CONVENTIONS,
        "prompts/INTERPRETATION_CONVENTIONS.md": INTERPRETATION_CONVENTIONS,
        "prompts/KNOWN_PATTERNS.md": (
            "# Known patterns and errors\n\n"
            "Record reusable technical solutions, failed approaches, and costly mistakes. "
            "Link each entry to the affected experiment, iteration, run, or source when "
            "possible. Do not turn this file into an unverified scientific conclusion.\n"
        ),
        "prompts/intellectual_contribution.md": (
            "# Intellectual contribution log\n\n"
            "Record researcher framing, method choices, insights, interpretations, and "
            "decisions that would otherwise be lost in transient conversations. Distinguish "
            "those contributions from assistant-generated proposals or drafts.\n"
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
            "Use this directory for active multi-step implementation or research plans. State "
            "the intended outcome, affected records, decision points, validation, and stop "
            "conditions. Delete or close a plan after its useful content is reflected in the "
            "canonical project record.\n"
        ),
        "hypotheses/README.md": (
            "# Hypotheses\n\n"
            "Proposal sets preserve distinct candidate explanations and their limitations. An "
            "assistant may draft or challenge them; only a confirmed researcher can select, "
            "revise, or activate the project's scientific direction. Exploratory work may "
            "declare a purpose instead of forcing a hypothesis.\n"
        ),
        "hypotheses/HYPOTHESIS_TEMPLATE.md": HYPOTHESIS_TEMPLATE,
        "experiments/README.md": (
            "# Experiments\n\n"
            "Create experiments and iterations through SMAIRT so identifiers, protocols, code, "
            "and run provenance remain linked. Use a new iteration for a meaningful method, "
            "configuration, input, control, or interpretation change. Never rewrite an "
            "immutable run bundle.\n"
        ),
        "scripts/README.md": (
            "# Project scripts\n\n"
            "Experiment entrypoints belong to their experiment iteration. Move code into "
            "`scripts/shared/` only after a project-specific pattern genuinely repeats. Run "
            "`smairt code index` after structural changes.\n"
        ),
        "scripts/shared/README.md": (
            "# Shared project code\n\n"
            "Keep reusable, project-specific functions here. Document inputs, outputs, units, "
            "assumptions, and failure conditions, and avoid hidden scientific parameters or "
            "machine-specific paths.\n"
        ),
        "scripts/CODE_INDEX.yaml": "schema_version: 1\nmodules: []\n",
        "analysis/README.md": (
            "# Analysis\n\n"
            "Interpret results against the linked hypothesis or exploratory purpose and the "
            "predeclared criteria. Separate observations, derived results, interpretation, "
            "limitations, confounders, and future hypotheses. Verification is not a scientific "
            "decision.\n"
        ),
        "analysis/ANALYSIS_TEMPLATE.md": ANALYSIS_TEMPLATE,
        "references/README.md": (
            "# References\n\n"
            "`index.yaml` is the attributed reference record. Remote metadata is provisional "
            "until a contributor reviews it. Local PDFs remain ignored by default; when "
            "attached, their path and checksum are recorded together. Discovery results are "
            "not project evidence until deliberately imported and used.\n"
        ),
        "references/index.yaml": "schema_version: 2\nreferences: []\n",
        "paper/README.md": PAPER_README,
        "paper/manifest.yaml": "elements: []\n",
        "paper/contribution_statement.md": (
            "# Contribution statement\n\n"
            "Describe researcher and collaborator contributions using the authorship framework "
            "appropriate to the eventual venue. Distinguish human framing, decisions, analysis, "
            "and review from assistant-generated proposals, code, or prose.\n"
        ),
        "environment/software_versions.yaml": "tools: {}\n",
    }
    license_content = render_license(license_name, author)
    if license_content is not None:
        files["LICENSE"] = license_content
        files[".smairt/license.json"] = license_manifest(license_name, license_content)
    if environment_mode is EnvironmentMode.NEW_CONDA:
        files["environment/environment.yml"] = (
            f"name: {environment_name}\n"
            "channels:\n  - conda-forge\n"
            "dependencies:\n  - python=3.11\n"
        )
    # Managed-file hashes let later upgrades distinguish framework guidance
    # from researcher-authored scientific artifacts, which are never replaced.
    managed = {
        **SKILL_FILES,
        "prompts/CODE_CONVENTIONS.md": CODE_CONVENTIONS,
    }
    framework_manifest = {
        "framework_version": __version__,
        "managed_files": {
            relative: sha256_text(content.rstrip() + "\n") for relative, content in managed.items()
        },
    }
    config_content = config.to_yaml()
    framework_content = yaml.safe_dump(framework_manifest, sort_keys=False)

    from smairt.harnesses import ADAPTERS, select_harness

    generated_targets = set(files) | {
        "smairt.yaml",
        ".smairt/framework.yaml",
        ".smairt/harnesses/" + harness.value + ".json",
        *ADAPTERS[harness].files,
    }
    if existing_content:
        conflicts = _existing_conflicts(destination, generated_targets)
        if conflicts:
            raise FileExistsError(
                "existing checkout contains unmanaged scaffold targets: " + ", ".join(conflicts)
            )
        if git_enabled:
            configured_hooks = subprocess.run(
                ["git", "config", "--get", "core.hooksPath"],
                cwd=destination,
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            if configured_hooks and configured_hooks != ".githooks":
                raise FileExistsError(
                    "existing Git hooksPath must be reviewed before SMAIRT initialization"
                )

    generated = {relative: content.rstrip() + "\n" for relative, content in files.items()}
    generated["smairt.yaml"] = config_content
    generated[".smairt/framework.yaml"] = framework_content.rstrip() + "\n"
    if existing_content:
        transaction = FileTransaction(destination, "project initialize scaffold")
        for relative, content in generated.items():
            transaction.stage_text(
                destination / relative,
                content,
                mode=0o755 if relative == ".githooks/pre-commit" else None,
            )
        transaction.commit()
    else:
        for relative, content in generated.items():
            atomic_write(
                destination / relative,
                content,
                mode=0o755 if relative == ".githooks/pre-commit" else None,
            )
    for directory in DIRECTORIES:
        (destination / directory).mkdir(parents=True, exist_ok=True)

    select_harness(destination, harness.value)

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
