# SMAIRT Modernization Proposal: VSCode/Roo-First Workflow

## Executive Summary

Based on analysis of `vfmini/` — a heavily-used SMAIRT project run through VSCode Roo/Zoo — this document identifies patterns of actual use vs. template assumptions, and proposes concrete changes to modernize the SMAIRT framework for AI-integrated IDE workflows.

**The core insight**: The original SMAIRT was designed for a browser-based LLM workflow (copy/paste context, manual session tracking). In VSCode/Roo, the AI has direct filesystem access, persistent conversation context, and tool-use capabilities. Many template features are either unused, redundant, or could be dramatically improved.

---

## 1. Findings: What's Actually Used vs. What's Ignored

### ✅ Heavily Used (Keep & Enhance)

| Feature | Evidence in vfmini | Notes |
|---------|-------------------|-------|
| `intellectual_contribution.md` | 637 lines of real content | Core value proposition works perfectly |
| Per-iteration hypothesis files | 67 files (HYPOTHESIS_XX.md) | Evolved from single HYPOTHESES.md log |
| Per-iteration analysis files | ~90 files (ANALYSIS_XX.md) | Far more useful than a single log |
| Script numbering convention | 90+ scripts across tracks | Natural and effective |
| Phase directories (01_synthetic, etc.) | Used as designed | Works well |
| Log files in results/ | Every script produces logs | Consistent and valuable |
| 4-part structure (Background→Hypothesis→Methods→Results) | Present in every script docstring | Core of the method |
| `scripts/shared/` library | Evolved organically (4 modules) | Not in template but essential |
| `plans/` directory | 18 planning documents | Not in template but heavily used |
| Code conventions prompts | Two 1500-line HPC convention docs created | Template version outgrown immediately |

### ❌ Not Used / Obsolete

| Feature | Evidence | Why |
|---------|----------|-----|
| `session_log.md` | Still has template placeholders | Roo conversation IS the session log |
| "Paste output as comments" breadcrumb | No scripts have pasted output | Roo reads log files directly |
| `compile_for_ai.py` for every session | Used once (March 2026) | AI has filesystem access already |
| `SESSION_START.md` paste-based prompts | Language references "cut and paste" | AI reads files directly via tools |
| `00_priming_prompts.md` | References "ask AI to read" | In Roo, you can use @-mentions or AI reads directly |
| `BREADCRUMB_TRAIL.md` | Not present in vfmini | Individual analysis files serve this purpose |
| Single `HYPOTHESES.md` log file | Used for first 5 only, then abandoned | Per-file hypothesis tracking is better |

### 🔄 Partially Used / Evolved Beyond Template

| Feature | How It Evolved | Template Gap |
|---------|---------------|--------------|
| Script naming | `script_XX` → lettered tracks (A, B, C, D, E, F, X) | Template doesn't mention tracks |
| CODE_CONVENTIONS.md | Template version unchanged; 2 new 1500-line prompt files created | Template version too basic |
| AI_CONTEXT.md | Template version unchanged; never updated | Missing guidance for evolved workflow |
| Hypothesis tracking | Single file → individual files | Template only has single-file pattern |
| Results logging | `TeeLogger` class in shared/ | Template has inline Logger class |
| HPC integration | Massive HPC conventions, SLURM scripts | Template has basic placeholder |

---

## 2. Proposed Changes

### 2.1 Eliminate Paste-Centric Language & Features

**Problem**: The template repeatedly tells users to "paste output as comments at the end of scripts" and "cut and paste this prompt into your AI assistant." In VSCode/Roo, neither is necessary.

**Changes**:
- Remove `# === PASTE OUTPUT HERE ===` blocks from CODE_CONVENTIONS.md template
- Replace "The Breadcrumb Trail" concept with "The Audit Trail" — log files + analysis files
- Remove `session_log.md` template file (or replace with lightweight session index)
- Rewrite SESSION_START.md to use `@file` reference syntax instead of paste instructions
- Remove `BREADCRUMB_TRAIL.md` from paper-driven mode (analysis files replace it)

### 2.2 Add `plans/` Directory to Template

**Problem**: Every non-trivial SMAIRT project will need planning documents. vfmini organically grew 18 of them.

**Changes**:
- Add `plans/` directory to cookiecutter template
- Include `plans/README.md` with guidance on when/how to create plans
- Template for plan documents: problem statement, approach, success criteria, dependencies

### 2.3 Add `scripts/shared/` Directory to Template

**Problem**: As projects grow past ~10 scripts, shared utilities emerge organically. The template should scaffold this.

**Changes**:
- Add `scripts/shared/__init__.py` with documented pattern
- Add `scripts/shared/logging.py` with TeeLogger (from vfmini's evolved pattern)
- Add `scripts/shared/README.md` explaining when to extract to shared

### 2.4 Support Multi-Track Experimentation

**Problem**: Real projects don't follow a linear 01→02→03...→30 path. They fork into parallel investigation tracks.

**Changes**:
- Document track-based naming in CODE_CONVENTIONS.md: `script_A01`, `script_B01`, etc.
- Add per-track hypothesis file pattern: `HYPOTHESIS_XX.md` (individual files)
- Add per-iteration analysis file pattern: `ANALYSIS_XX.md` (individual files)
- Keep single HYPOTHESES.md as optional summary/index only

### 2.5 Modernize AI_CONTEXT.md for IDE-Native AI

**Problem**: Current AI_CONTEXT.md assumes browser-based LLM that receives pasted text. In Roo, the AI is persistent, has file access, and uses tools.

**Changes**:
- Add "Your Environment" section describing capabilities (file read/write, terminal, search)
- Remove "paste this" language
- Add guidance on using `@file` or direct file reads instead of compile_for_ai
- Add section on when compile_for_ai IS still useful (cross-tool transfer, archival)
- Document that the AI should read files directly rather than asking user to paste

### 2.6 Replace compile_for_ai.py "Every Session" Pattern

**Problem**: In Roo, AI has direct file access. `compile_for_ai.py` is useful for archival/cross-tool transfer but not for session bootstrapping.

**Changes**:
- Keep compile_for_ai.py but reframe its purpose
- Add new `prompts/CONTEXT_INDEX.md` — a structured index of what to read and when
- Roo can read this index to know which files to look at for different task types

### 2.7 Add HPC Integration as First-Class Feature

**Problem**: vfmini developed 1500+ lines of HPC conventions organically. The template's HPC directory is basically empty.

**Changes**:
- Add `prompts/hpc_conventions.md` template with core patterns
- Improve `hpc/templates/slurm_basic.sh` with real-world patterns
- Add guidance for device-agnostic code (CPU/GPU/multi-GPU)
- Document PyTorch Lightning as recommended training framework

### 2.8 Add Monitor Script Pattern

**Problem**: Long-running HPC jobs need monitoring. vfmini has 7+ `monitor_*_progress.py` scripts.

**Changes**:
- Add `scripts/monitor_template.py` showing the pattern
- Document in CODE_CONVENTIONS.md when to create monitor scripts

### 2.9 Restructure SESSION_START.md for Roo

**Problem**: Current prompts assume you're starting a new browser session. In Roo, sessions are persistent and the AI maintains conversation context.

**Changes**:
- "First Session" → "Project Onboarding" (when AI first encounters the project)
- "Continuing Session" → "Context Refresh" (after long gaps or context window limits)
- Remove all "paste this" language
- Add "Quick Task" prompt (for focused work that doesn't need full context)
- Add "Planning Session" prompt (for generating plan docs)
- Add "HPC Submission" prompt (for generating job scripts)

### 2.10 Add Collaboration Guide Template

**Problem**: vfmini created a 575-line collaboration guide. Multi-person SMAIRT projects need this from day one.

**Changes**:
- Add cookiecutter variable `team_size` (solo/team)
- Add `plans/COLLABORATION_GUIDE.md` template for team projects
- Document git workflow, track ownership, handoff patterns

---

## 3. Priority Implementation Order

| Priority | Change | Impact | Effort |
|----------|--------|--------|--------|
| **P0** | Remove paste-centric language from all files | High | Medium |
| **P0** | Add `plans/` directory | High | Low |
| **P0** | Add `scripts/shared/` scaffolding | High | Low |
| **P1** | Rewrite AI_CONTEXT.md for IDE-native AI | High | Medium |
| **P1** | Rewrite SESSION_START.md for Roo workflow | High | Medium |
| **P1** | Add multi-track naming conventions | Medium | Low |
| **P1** | Add per-iteration hypothesis/analysis patterns | Medium | Low |
| **P2** | Add CONTEXT_INDEX.md replacing session-start compile | Medium | Medium |
| **P2** | Add HPC conventions template | Medium | Medium |
| **P2** | Reframe compile_for_ai.py purpose | Low | Low |
| **P3** | Add collaboration guide template | Low | Medium |
| **P3** | Add monitor script template | Low | Low |

---

## 4. Template Mode Additions

### New cookiecutter variable: `workflow_mode`

```json
{
  "workflow_mode": ["ide_native", "browser_paste"]
}
```

- `ide_native` (default): Generates project assuming AI has file access (VSCode/Roo, Cursor, Windsurf, etc.)
- `browser_paste`: Generates project with legacy paste-oriented workflow (ChatGPT web, Claude web)

This allows backward compatibility while making the modern workflow the default.

---

## 5. Specific File-Level Changes

### Files to REMOVE from ide_native mode:
- `prompts/session_log.md` → replaced by conversation history
- `analysis/BREADCRUMB_TRAIL.md` → replaced by per-iteration analysis files

### Files to ADD:
- `plans/README.md` — guidance on planning documents
- `scripts/shared/__init__.py` — shared utility scaffold
- `scripts/shared/logging.py` — TeeLogger implementation
- `scripts/shared/README.md` — when/how to use shared
- `prompts/CONTEXT_INDEX.md` — structured file index for AI orientation
- `hypotheses/HYPOTHESIS_TEMPLATE.md` — per-iteration hypothesis template
- `analysis/ANALYSIS_TEMPLATE.md` — per-iteration analysis template

### Files to REWRITE:
- `prompts/AI_CONTEXT.md` — IDE-native version
- `prompts/SESSION_START.md` — Roo-first prompts
- `prompts/CODE_CONVENTIONS.md` — include tracks, shared lib, HPC basics
- `docs/12_STEPS.md` — remove paste steps, add planning/tracking steps
- `prompts/00_priming_prompts.md` — modernize for direct file access
- `README.md` (template) — updated workflow description

### Files to MODIFY:
- `scripts/compile_for_ai.py` — add archival framing, include plans/
- `cookiecutter.json` — add `workflow_mode` variable
- `hooks/post_gen_project.py` — conditional generation based on workflow_mode

---

## 6. Evidence-Based Patterns from vfmini

### Pattern: Track-Based Organization
```
experiments/03_real_data/
├── script_B01_*.py through script_B15*.py  (Track B: Fitness Data)
├── script_C31_*.py through script_C47*.py  (Track C: Genome Pretraining)
├── script_D01_*.py through script_D15*.py  (Track D: Multi-modal Fusion)
├── script_E01_*.py through script_E05*.py  (Track E: Cross-modal Learning)
├── script_F01_*.py through script_F02*.py  (Track F: Prototype VFM)
└── script_X1_*.py through script_X7*.py   (Track X: Interpretation)
```

### Pattern: Shared Library Evolution
```python
# scripts/shared/__init__.py
from scripts.shared.logging import TeeLogger, setup_logging
from scripts.shared.metrics import compute_auprc, compute_baseline_correlation
from scripts.shared.data_loading import load_transcriptomics_data, load_fitness_data
from scripts.shared.models import FeaturePredictionModel, MultiModalFusionModel
```

### Pattern: Plan-Driven Development
```
plans/
├── PLAN_D05_IMPROVED_ATTENTION.md      # Specific experiment plan
├── PLAN_D06_RAY_TUNE_IMPLEMENTATION.md # Technical implementation plan
├── PLAN_MULTIMODAL_INTEGRATION.md      # Architecture evolution plan
├── PLAN_PROTOTYPE_VFM_ARCHITECTURE.md  # Long-term architecture plan
└── COLLABORATION_GUIDE.md             # Team coordination
```

### Pattern: Individual Hypothesis Files
```markdown
# HYPOTHESIS_E05.md

## Status: PENDING

## Background
[Rich context about WHY this hypothesis exists]

## Root Cause Hypotheses
[Multiple sub-hypotheses]

## E05 Hypotheses
### H_E05A: [Specific prediction with success criteria]
### H_E05B: [Specific prediction with success criteria]

## Experimental Design
[How to test - conditions, metrics, controls]
```

### Pattern: Conventions as Prompts (1500+ lines)
The vfmini project created `prompts/hpc_and_device_upgrading.md` (1506 lines) as a comprehensive prompt that tells the AI exactly how to generate HPC-compatible code. This is the most effective way to ensure consistency — write it once as a prompt, reference it every time.

---

## 7. Philosophical Shift

### Old Model (Browser-Paste)
```
User writes prompt → Pastes context → AI generates → User copies code → 
User runs → User pastes output back → Repeat
```

### New Model (IDE-Native)
```
User describes intent → AI reads relevant files → AI generates code → 
AI can run/test → AI reads output → AI updates documentation → Repeat
```

The key differences:
1. **Context is ambient** — AI reads what it needs, no manual transfer
2. **Documentation is auto-maintained** — AI can write analysis files directly
3. **Iteration is faster** — No copy-paste overhead between steps
4. **Plans are first-class** — AI generates plan docs before implementation
5. **Conventions are prompts** — Detailed prompt files ensure consistent code generation
6. **Session state is implicit** — Conversation history replaces session logs

---

## 8. Backward Compatibility

The `browser_paste` mode preserves all existing functionality for users who:
- Use ChatGPT/Claude web interfaces
- Prefer manual control over context
- Work in environments without AI file access
- Want the pedagogical value of explicit session tracking

The `ide_native` mode (new default) is for users who:
- Use VSCode with Roo/Zoo, Cursor, Windsurf, or similar
- Want maximum velocity with AI-assisted research
- Run long computations (HPC) and need robust tracking
- Work in teams with parallel tracks

---

## Next Steps

1. Implement P0 changes (paste removal, plans/, shared/)
2. Implement P1 changes (AI_CONTEXT rewrite, SESSION_START rewrite, multi-track)
3. Add `workflow_mode` cookiecutter variable with conditional template generation
4. Update tutorials and documentation
5. Test with a fresh project generation
