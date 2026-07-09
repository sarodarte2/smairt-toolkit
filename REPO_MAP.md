# SMAIRT — agent repo map

Purpose: let an agent locate any part of the SMAIRT template without re-exploring, and know
which assets port into OpenScience (see `openscience-smairt/docs/plans/12-smairt-integration.md`
for the destination of each). Paths are relative to this repo root (`smairt-template/`).

What SMAIRT is: **Scientific Method with AI Research Template** — a [cookiecutter](https://cookiecutter.readthedocs.io/)
template (from PNNL) that scaffolds a project directory encoding an AI-assisted, hypothesis-driven
research workflow. It is *pure convention*: no runtime. The rigor lives entirely in the generated
files + two MCP skills; it relies on the AI honoring the template. There is no enforcement code.

## Two things live in this repo

1. **The cookiecutter template** — `{{ cookiecutter.project_slug }}/` (the generated project),
   `cookiecutter.json` (variables), `hooks/` (pre/post-gen validation).
2. **Two MCP skills** — `skills/smairt-research/`, `skills/smairt-paper-driven/` (already in
   `SKILL.md` frontmatter format; these port to OpenScience `skills/research/` nearly as-is).

Plus top-level tutorials/docs and a `paper_draft/` of the SMAIRT paper itself.

## The generated project layout (`{{ cookiecutter.project_slug }}/`)

Jinja-templated. `.py`/`.sh` files are `_copy_without_render` (copied verbatim, not templated).

```
prompts/            AI context + conventions (the "brain" of a SMAIRT project)
  AI_CONTEXT.md            AI role, workflow, environment  → OpenScience: scaffolded AGENTS.md
  CODE_CONVENTIONS.md      Script template, naming, logging → split: rules→manifest, prose→skill
  KNOWN_PATTERNS.md        Accumulated patterns + resolved errors → stays a project file, auto-loaded
  CONTEXT_INDEX.md         What to read for which task
  SESSION_START.md         Priming prompts per situation → OpenScience: .openscience/command/*.md
  00_priming_prompts.md, InitialPrompt_paper_driven.md, iteration_review_prompt.md,
  figure_generation_prompt.md, session_log.md
  intellectual_contribution.md   Human-vs-AI contribution ledger → the ethical differentiator (WS-E)
hypotheses/         HYPOTHESIS_TEMPLATE.md (Status/Background/Prediction/Rationale/Success criteria/Design/Sub-hypotheses)
analysis/           ANALYSIS_TEMPLATE.md, ANALYSIS_PLAN.md, BREADCRUMB_TRAIL.md, REPOSITORY_PLAN.md, XX_figures/
experiments/        01_synthetic/  02_downloaded/  03_real_data/  (dirs created depend on starting_phase)
scripts/            Bookkeeping scripts (see below) + shared/ library
  shared/logging.py        TeeLogger + setup_logging (90 lines) → THE logging contract, port verbatim
  new_script.py, new_experiment.py, new_iteration.py   → OpenScience: `openscience iteration new`
  finalize_iteration.py    → `openscience iteration finalize`
  generate_manifest.py     → folds into `openscience project export`
  monitor_template.py      HPC job progress monitor → slurm-hpc skill
  compile_for_ai.py        Browser-paste context bundler → DROP (obsolete in OpenScience runtime)
results/            logs/  figures/   (TeeLogger writes timestamped logs here)
data/               synthetic/  downloaded/  real/
plans/              Planning docs written before complex work
background/         Research context
docs/               12_STEPS.md, SMAIRT_PHILOSOPHY.md, BEST_PRACTICE_SINGLE.md,
                    BEST_PRACTICE_COLLABORATIVE.md → OpenScience docs site (WS-G)
hpc/                config.yaml, templates/slurm_basic.sh, logs/, README.md → slurm-hpc skill (WS-F)
paper/, paper_draft/   Paper-driven mode: outline.md, drafts/, reviewer_feedback/
FINAL_MANIFEST.md   Reproducibility manifest → folds into `openscience project export`
```

## The audit trail (the core invariant SMAIRT enforces by convention)

```
hypotheses/HYPOTHESIS_XX.md → experiments/<phase>/script_XX_*.py → results/logs/script_XX_*_<ts>.log → analysis/ANALYSIS_XX.md
```
Each `ANALYSIS_XX.md` "Next Steps" seeds the next `HYPOTHESIS_YY.md`. Naming grammar:
`script_NN_desc.py` sequential early; `script_<TRACK><NN>_desc.py` (A/B/C…) once forked;
`X`-track for interpretation; `_hpc` suffix for cluster scripts. **In OpenScience this chain
becomes provenance-DAG links + a machine-checkable manifest, not just filename discipline.**

## cookiecutter.json variables

`project_name`, `project_slug`, `author_name/email`, `description`, `project_mode`
(standard | paper_driven), `workflow_mode` (ide_native | browser_paste — **both obsolete in
OpenScience**), `initial_research_question`, `domain`, `ai_tool` (roo_zoo/cursor/windsurf/claude/
chatgpt — **obsolete**), `include_example_project`, `starting_phase` (synthetic | downloaded |
real), `license`, `create_git_repo`. Hooks: `hooks/pre_gen_project.py` (validate inputs),
`hooks/post_gen_project.py` (prune unused phase dirs, git init). **Port target: reimplement as TS
flags in `openscience project scaffold`, dropping cookiecutter + Python entirely.**

## HPC assets (`hpc/` + `TUTORIAL_HPC.md`) — read before touching WS-F

- `hpc/config.yaml` — cluster type (slurm/pbs/sge), partition, account, resource tiers
  (default/large/gpu), environment (conda_env/virtualenv/modules), paths (scratch/project),
  email notifications. **Gated behind `project_mode == 'paper_driven'` today.**
- `hpc/templates/slurm_basic.sh` — minimal `#SBATCH` script; takes a script path arg; has
  commented-out `module load` / `conda activate` lines the user must fill in.
- `scripts/monitor_template.py` — polls results dirs for partial output (for multi-hour jobs).
- `TUTORIAL_HPC.md` (448 lines) — the real guidance: it repeatedly flags that **partitions,
  accounts, module names, and env paths are all cluster-specific and user-supplied**. This is
  the key HPC reality for the roadmap: there is no universal SLURM; adaptation is manual and
  per-cluster, and many clusters are terminal-only / SSH-only / egress-restricted.

## The two skills (port targets, already frontmatter-compatible)

- `skills/smairt-research/SKILL.md` (~1.4k tok) + `references/workflow.md` + `agents/openai.yaml` —
  standard-mode workflow: core stance, the 10 steps, data progression, required practices, audit
  trail, Active Innovation Detection.
- `skills/smairt-paper-driven/SKILL.md` (~2k tok) + `references/paper_driven_workflow.md` —
  paper-driven variant: analyses mapped to paper sections, iteration loop, reviewer-feedback flow.

Adaptation for OpenScience: strip cookiecutter / `compile_for_ai` / IDE-mode references; replace
"run `new_iteration.py`" with `openscience iteration new`; replace convention prose with "consult
`.openscience/research.jsonc`".

## Top-level docs

`README.md`, `QUICKSTART.md`, `TUTORIAL.md`, `TUTORIAL_PAPER_DRIVEN.md`, `TUTORIAL_HPC.md`;
`docs/MODERNIZATION_PROPOSAL.md` (records what real use kept vs. dropped — **useful signal for
what to port**; §"Not Used / Obsolete" lists browser-paste, compile_for_ai, per-session bundling),
`docs/AI_SKILL_USAGE.md`; `paper_draft/` (the SMAIRT paper, abstract, PLOS draft, genesis
transcript). License: MIT (compatible with OpenScience's Apache-2.0; attribution to PNNL in NOTICE).

## What to port vs. drop (summary — full mapping in openscience-smairt/docs/plans/12)

| Port (enforce in code) | Port (as skill/docs) | Drop |
|---|---|---|
| Directory layout → scaffold | smairt-research / -paper-driven skills | compile_for_ai.py |
| Naming/logging grammar → manifest + hook | 12_STEPS, PHILOSOPHY, tutorials → docs | browser-paste mode |
| TeeLogger → scaffold + validation hook | Active Innovation Detection → skill line | per-IDE ai_tool configs |
| new_iteration/finalize → CLI commands | data-progression judgment → skill | workflow_mode variable |
| intellectual_contribution → ledger + disclosure | HPC guidance → slurm-hpc skill | generate_manifest (folds into export) |
