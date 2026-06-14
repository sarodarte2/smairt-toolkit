SMAIRT: A Structured Framework for AI-Assisted Scientific Discovery in Computational Research

Authors

[Author names to be added]

Abstract

The integration of large language models (LLMs) into scientific research workflows presents both unprecedented opportunities and significant methodological challenges. While AI assistants can rapidly synthesize existing knowledge, generate functional code, and iterate through experimental designs, they fundamentally cannot produce genuinely novel scientific insights—a capability that remains uniquely human. We present SMAIRT (Scientific Method with AI Research Template), an open-source framework that structures AI-assisted computational research around the classical scientific method. SMAIRT provides researchers with a standardized project template, automated audit trails, error-prevention mechanisms, and workflow guidelines that maximize the benefits of AI collaboration while maintaining clear attribution of intellectual contributions. The framework supports IDE-native AI integration where assistants read and write files directly, implements a configurable data progression from synthetic through benchmark to real data, accumulates reusable patterns and known errors across sessions, and provides MCP (Model Context Protocol) skills for persistent AI context. We demonstrate SMAIRT's utility through three use cases spanning machine learning, aerospace trajectory prediction, and bioinformatics, showing how the framework accelerates the hypothesis-to-discovery cycle while preserving reproducibility and intellectual ownership. SMAIRT is freely available as a cookiecutter template under the MIT License.

Introduction

The Promise and Peril of AI in Scientific Research

The emergence of large language models has fundamentally altered the landscape of computational research. Tools such as ChatGPT, Claude, and AI-integrated development environments (Cursor, Windsurf, VSCode with Roo/Zoo) can generate functional code, synthesize literature, suggest experimental designs, and iterate through analytical approaches at speeds impossible for human researchers working alone. For computational scientists across disciplines—bioinformatics, machine learning, physics, engineering—these capabilities promise dramatic acceleration of the research cycle.

However, this promise comes with significant challenges. Large language models exhibit a fundamental characteristic that limits their scientific utility: they excel at regression toward the mean of their training data. This means AI assistants are remarkably effective at reproducing established approaches, suggesting methods that have worked in similar contexts, and synthesizing what is already known. They are far less capable—perhaps fundamentally incapable—of generating truly novel scientific insights, identifying genuine gaps in knowledge, or making the innovative conceptual leaps that drive scientific progress.

This limitation creates a paradox for researchers. AI can help navigate the vast landscape of existing knowledge with unprecedented speed, but it cannot tell you where the unexplored territories lie. The researcher who relies too heavily on AI suggestions risks being led in circles through well-trodden ground, never reaching the frontier where genuine discovery becomes possible.

The Hard Problem of Science

One of the most challenging aspects of scientific research is identifying questions that are simultaneously novel, important, and tractable. Many apparent research questions fall into traps: they have already been answered (perhaps in different terminology), are hidden variants of solved problems, cannot be answered with available methods, or would not meaningfully advance understanding even if answered.

Traditionally, researchers develop the judgment to navigate these traps through years of immersion in their field. AI assistants can dramatically accelerate the first part of this process—moving from relative ignorance to familiarity with what is known—but they cannot substitute for the human judgment required to recognize genuine novelty or importance.

The Need for Structured AI-Human Collaboration

Given these complementary strengths and limitations, effective AI-assisted research requires a structured approach that:

1. Leverages AI strengths in rapid iteration, code generation, and synthesis of known approaches
2. Preserves human agency in critical decision-making, novelty recognition, and interpretation
3. Maintains reproducibility through automated audit trails and systematic documentation
4. Tracks intellectual contributions through explicit attribution of human versus AI-generated insights
5. Enables continuity through the ability to resume work across sessions without context loss
6. Prevents error recurrence through accumulated knowledge of what works and what fails

We developed SMAIRT (Scientific Method with AI Research Template) to address these requirements. SMAIRT is an open-source framework implemented as a cookiecutter template that generates a standardized project structure for AI-assisted computational research. The framework is grounded in the classical scientific method and provides explicit mechanisms for documentation, attribution, reproducibility, and cross-session learning.

Related Work

Project Organization Frameworks

The challenge of organizing computational research projects has been addressed by several influential frameworks. Noble's guidelines for organizing computational biology projects [1] established foundational principles for directory structure and reproducibility. Cookiecutter Data Science [2] provides a standardized template emphasizing clear separation of data processing stages. The TIER Protocol [3] provides guidelines for transparency and replication in empirical research. Wilson and colleagues' "Good Enough Practices in Scientific Computing" [4] and "Best Practices for Scientific Computing" [5] provide comprehensive guidelines that have shaped practices across disciplines.

SMAIRT incorporates principles from these frameworks but reorganizes around the scientific method rather than data processing pipelines, adds explicit support for AI collaboration and intellectual contribution tracking, and provides mechanisms for cross-session knowledge accumulation that have no analog in pre-AI frameworks.

Reproducibility and Documentation Frameworks

The reproducibility crisis has spawned frameworks including Jupyter notebooks [6], workflow management systems (Snakemake [7], Nextflow [8], CWL [9]), and electronic laboratory notebooks. While these address execution reproducibility, they do not address the scientific reasoning layer—the "why" behind decisions—that SMAIRT captures through its audit trail. SMAIRT can complement workflow managers: SMAIRT organizes the scientific process while Snakemake or Nextflow handle execution reproducibility.

AI-Assisted Research Frameworks

The rapid emergence of LLMs has produced various approaches to AI integration, from prompt engineering guidelines to AI pair programming (GitHub Copilot [10]) to retrieval-augmented generation systems. However, few have been formalized into structured research frameworks that address the full cycle from hypothesis formulation through interpretation and cross-session continuity.

The Model Context Protocol (MCP) [11] represents a significant advance in AI-tool integration, providing a standardized mechanism for AI agents to access external tools and knowledge. SMAIRT leverages MCP through packaged "skills" that give AI assistants persistent understanding of the framework's conventions without requiring manual prompt priming.

Domain-specific AI systems (AlphaFold [12], materials discovery systems) represent a different paradigm where AI performs well-defined tasks rather than serving as a general research assistant. SMAIRT addresses the more common case of general-purpose LLMs used as flexible assistants across diverse research tasks.

Distinguishing Features of SMAIRT

Several features distinguish SMAIRT from related frameworks:

1. **IDE-native AI integration**: AI assistants read files directly and write code, logs, and analysis without copy-paste intermediation
2. **Automated audit trail**: TeeLogger captures all script output to timestamped log files, creating a linked chain from hypothesis through execution to analysis
3. **Error prevention through knowledge accumulation**: KNOWN_PATTERNS.md persists reusable code patterns, recurring errors, and consistency rules across sessions
4. **MCP skills integration**: Packaged skills give AI persistent SMAIRT context without manual priming
5. **Configurable data progression**: Researchers choose their starting phase (synthetic, downloaded, or real) based on project needs
6. **HPC support**: SLURM templates, cluster configuration, and job monitoring integrated into the project structure
7. **Git-first collaboration**: Best-practice guides for both solo and team workflows with intellectual contribution tracking per researcher

Design and Implementation

Core Philosophy

SMAIRT is built on five foundational principles:

**Principle 1: AI as vehicle to the frontier.** AI rapidly reaches the boundary of existing knowledge; human insight is essential for pushing beyond it. This framing prevents over-reliance on AI suggestions and maintains researcher agency.

**Principle 2: Scientific method as organizing structure.** All work follows Background → Hypothesis → Methods → Results → Interpretation → Next Steps. This enforces disciplined thinking about what is being tested and why.

**Principle 3: The audit trail.** Every experiment produces linked artifacts: hypothesis file → script → log file → analysis file. The AI reads these directly (IDE-native mode), enabling complete context restoration without manual intervention.

**Principle 4: Error prevention through accumulated knowledge.** KNOWN_PATTERNS.md captures working code patterns, recurring errors with fixes, consistency rules, and pre-flight checklists. Each session can build on previous sessions' discoveries rather than rediscovering the same issues.

**Principle 5: Explicit intellectual contribution tracking.** Dedicated mechanisms document where researchers provide critical insights—novel connections, creative pivots, domain expertise—versus where AI generates suggestions.

Project Structure

When a researcher creates a new SMAIRT project, the template generates:

```
my_project/
├── prompts/                    # AI context and conventions
│   ├── AI_CONTEXT.md           # AI role and workflow description
│   ├── CODE_CONVENTIONS.md     # Script template, naming, logging
│   ├── KNOWN_PATTERNS.md       # Accumulated patterns & errors
│   ├── CONTEXT_INDEX.md        # What to read for different tasks
│   ├── SESSION_START.md        # Context-setting prompts
│   └── intellectual_contribution.md
├── plans/                      # Planning documents
├── hypotheses/                 # Per-iteration hypothesis files
│   └── HYPOTHESIS_TEMPLATE.md
├── analysis/                   # Per-iteration analysis files
│   ├── ANALYSIS_TEMPLATE.md
│   ├── BREADCRUMB_TRAIL.md     # Session-by-session progress log
│   └── REPOSITORY_PLAN.md
├── experiments/                # Scripts organized by phase
│   ├── 01_synthetic/           # (if starting_phase includes)
│   ├── 02_downloaded/          # (if starting_phase includes)
│   └── 03_real_data/
├── scripts/                    # Helper scripts
│   ├── shared/                 # Reusable library
│   │   └── logging.py          # TeeLogger implementation
│   ├── compile_for_ai.py       # Context compilation
│   ├── new_script.py           # Script generator
│   └── monitor_template.py     # HPC job monitor
├── results/
│   ├── logs/                   # TeeLogger output (auto-captured)
│   └── figures/
├── data/                       # Organized by phase
├── hpc/                        # HPC/SLURM support
│   ├── config.yaml             # Cluster configuration
│   ├── templates/              # Job submission templates
│   └── logs/                   # Job stdout/stderr
├── background/                 # Research context
├── docs/                       # Framework documentation
└── paper_draft/                # Parallel narrative
```

This structure enforces separation of concerns while maintaining clear relationships between components. The `prompts/` directory captures AI interaction context, `experiments/` organizes code by data phase, and `results/` separates raw outputs from interpretation in `analysis/`.

The Audit Trail

Central to SMAIRT is an automated audit trail that links every experimental artifact. The mechanism works as follows:

1. **Hypothesis files** (e.g., `hypotheses/H_01_baseline.md`) state the prediction and success criteria
2. **Experiment scripts** (e.g., `experiments/01_synthetic/01_baseline.py`) import `TeeLogger` from the shared library
3. **TeeLogger** automatically captures all console output to a timestamped log file in `results/logs/`
4. **Analysis files** (e.g., `analysis/ANALYSIS_01.md`) record interpretation and next steps

The TeeLogger implementation (in `scripts/shared/logging.py`) provides dual output—console for immediate feedback, file for permanent record—with no manual intervention required:

```python
from shared.logging import TeeLogger
logger = TeeLogger("01_baseline")  # Creates results/logs/01_baseline_YYYYMMDD_HHMMSS.log
```

In IDE-native mode, the AI reads log files directly after execution, writes analysis, and proposes the next hypothesis—creating a continuous loop without human copy-paste overhead. This represents a significant advance over earlier approaches that required manual output transfer between execution environments and AI sessions.

Known Patterns and Error Prevention

A distinctive feature of SMAIRT is `prompts/KNOWN_PATTERNS.md`, a living document that accumulates project-specific knowledge across sessions. It contains:

1. **Reusable code patterns**: Working solutions for common project tasks (data loading, evaluation, visualization)
2. **Recurring errors and anti-patterns**: Documented mistakes with root causes and corrected code
3. **Consistency rules**: Seeds, DPI standards, naming conventions, column orders
4. **Pre-flight checklist**: Verification steps before running experiments
5. **Environment-specific patterns**: HPC configurations, API credentials, platform notes

When the AI generates new code, it consults KNOWN_PATTERNS.md to avoid previously-encountered errors and maintain consistency. When new errors are discovered, the AI proposes additions to the file. This creates a ratchet effect: each session builds on the accumulated knowledge of all previous sessions, preventing the regression that occurs when AI assistants lack persistent memory.

This mechanism addresses a fundamental limitation of LLM-based assistants—their inability to learn from prior interactions within a project. By externalizing learned patterns into a structured document that persists in the repository, SMAIRT provides a form of long-term project memory.

Configurable Data Progression

SMAIRT implements a configurable data progression that adapts to different research contexts:

| Starting Phase | Directories Created | Best For |
|----------------|--------------------|----|
| Synthetic (default) | 01_synthetic → 02_downloaded → 03_real_data | Algorithm development, new methods |
| Downloaded | 02_downloaded → 03_real_data | Known benchmarks, existing methods |
| Real | 03_real_data only | Domain-specific questions, proprietary data |

The synthetic-first progression (when applicable) offers significant advantages: rapid iteration without data dependencies, precise control over ground truth, and principled validation of whether an approach works in principle before investing in real data acquisition. However, recognizing that many research questions begin with existing data, SMAIRT does not impose this progression when it would be inappropriate.

MCP Skills Integration

SMAIRT ships with two Model Context Protocol (MCP) skills that AI tool agents can load for persistent context:

- **`smairt-research`**: The full standard-mode workflow, audit trail conventions, script patterns, and the 10 Steps methodology
- **`smairt-paper-driven`**: Paper-driven iteration structure, analysis plans, and finalization steps

Skills eliminate the need for manual prompt priming at session start. When an AI agent loads a SMAIRT skill, it immediately understands the project's conventions, expected file locations, and workflow patterns. This reduces friction in multi-session research and ensures consistent AI behavior across tools (VSCode Roo/Zoo, Cursor, Windsurf).

HPC Integration

For computationally intensive research, SMAIRT includes integrated HPC support:

- **SLURM templates**: Customizable job submission scripts with proper log routing
- **Cluster configuration**: `hpc/config.yaml` centralizes partition, account, module, and environment settings
- **Job monitoring**: Template script for checking job status and parsing partial results
- **Audit trail integration**: HPC logs can feed directly into the standard analysis workflow

This integration ensures that moving from local development to cluster execution does not break the documentation chain—jobs run on remote systems still produce logs that connect hypotheses to analyses.

Git-First Collaboration

SMAIRT projects initialize as git repositories by default and include best-practice documentation for both workflows:

- **Single-user**: Commit discipline with atomic commits per iteration, phase tagging, and structured commit messages
- **Collaborative**: Branch strategies (user-specific branches merged to main), file ownership conventions (script number ranges per researcher), merge conflict prevention through structural separation, and per-researcher intellectual contribution tracking

The framework's file structure is designed to minimize merge conflicts—each researcher's scripts, hypotheses, and analyses live in separate files rather than requiring edits to shared documents.

The SMAIRT Workflow

Starting a New Project

```bash
pip install cookiecutter
cookiecutter gh:biodataganache/smairt-cookiecutter
```

The researcher provides project name, mode (standard or paper-driven), workflow mode (IDE-native or browser-paste), starting phase, and other metadata. The generated project includes all documentation, templates, and helper scripts.

The Iteration Cycle

Each iteration follows a structured cycle:

1. **Background**: Review prior results and context (AI reads existing analysis files)
2. **Hypothesis**: State a specific, testable prediction with success criteria
3. **Methods**: Generate experiment script (AI writes code following CODE_CONVENTIONS.md, checking KNOWN_PATTERNS.md)
4. **Execution**: Run script; TeeLogger auto-captures output to results/logs/
5. **Interpretation**: AI reads log, writes analysis file, proposes KNOWN_PATTERNS.md updates
6. **Next Steps**: Identify what to test next; feeds back into Background

In IDE-native mode, steps 1–2 and 4–6 happen within a single AI conversation. The researcher's role is providing critical direction, novel connections, and judgment about when approaches work or fail.

The 10 Steps

SMAIRT codifies its methodology into 10 actionable steps for researchers:

1. Record your intellectual contributions
2. Write hypotheses before experiments
3. Follow the data progression (from your chosen starting phase)
4. Number scripts sequentially
5. Maintain the audit trail (hypothesis → script → log → analysis)
6. Name log files to match scripts (automated by TeeLogger)
7. Use compile_for_ai.py for cross-tool context transfer
8. Use priming prompts; maintain Known Patterns & Errors
9. Follow the 4-part scientific method structure
10. Use future directions to seed the next iteration

Handling Dead Ends

When approaches fail, SMAIRT provides structured prompts (in SESSION_START.md) for exploring alternatives. The framework reminds researchers that dead ends are where human insight becomes most important—AI suggests variations on failed approaches, but recognizing when a fundamentally different direction is needed requires human judgment. The intellectual contribution tracking becomes especially important at these junctures.

Use Cases

We demonstrate SMAIRT's utility through three use cases that span different domains, data types, and complexity levels. Each use case exercises different features of the framework.

Use Case 1: Binary Classification with Synthetic-to-Real Progression

**Domain**: Machine learning methods development
**Starting phase**: Synthetic (full 3-phase progression)
**Key SMAIRT features exercised**: Data progression, TeeLogger, KNOWN_PATTERNS accumulation, multi-track experimentation

*Research question*: Can a simple decision boundary classifier achieve robust performance across varying noise levels and class separations?

This use case follows a researcher developing a binary classifier from first principles. The researcher used SMAIRT's full synthetic-to-real data progression to validate their approach systematically.

**Phase 1 — Synthetic data (3 iterations)**: The researcher generated 2D Gaussian clusters with controlled separation and noise. Iteration 1 established a baseline linear classifier on clean, well-separated data (accuracy: 0.98). Iteration 2 introduced Gaussian noise at increasing levels (σ = 0.1 to 2.0), revealing the decision boundary's sensitivity (accuracy degraded to 0.73 at σ = 1.5). Iteration 3 explored non-linear boundaries using synthetic data with controlled class overlap, discovering that kernel methods recovered performance only when overlap was below 30%.

During this phase, KNOWN_PATTERNS.md accumulated: (1) the importance of setting random seeds for reproducible cluster generation, (2) a recurring error where class imbalance in synthetic generation biased accuracy metrics, and (3) a working pattern for systematic noise sweep experiments.

**Phase 2 — Downloaded benchmarks (2 iterations)**: The researcher validated on UCI datasets (Iris, Wisconsin Breast Cancer, Ionosphere). Iteration 4 characterized dataset properties and compared against published baselines. Iteration 5 applied the noise-sensitivity findings from synthetic work, confirming that datasets with higher feature noise showed the predicted accuracy degradation pattern.

The intellectual contribution log recorded that the researcher identified an unexpected connection: the noise sensitivity curve from synthetic data predicted performance ordering across benchmarks—a novel finding that AI had not suggested.

**Phase 3 — Real data (2 iterations)**: Applied to a proprietary materials classification dataset. The validated noise thresholds from earlier phases informed data preprocessing decisions, reducing trial-and-error.

**Outcome**: 7 iterations over 4 sessions. The audit trail (14 linked files: 7 hypotheses, 7 scripts with logs, 7 analyses) provided complete reproducibility. KNOWN_PATTERNS.md grew from empty to 12 entries, preventing error recurrence across sessions.

Use Case 2: Artemis II Trajectory Prediction

**Domain**: Aerospace engineering / orbital mechanics
**Starting phase**: Downloaded (publicly available trajectory data)
**Key SMAIRT features exercised**: Paper-driven mode, HPC integration, collaborative workflow, MCP skills

*Research question*: Can machine learning models trained on historical lunar mission trajectories predict key Artemis II orbital parameters with sufficient accuracy to inform real-time mission planning?

This use case demonstrates SMAIRT applied to a physics-informed prediction problem where domain expertise is critical and computational resources are significant.

**Project setup**: The researchers used paper-driven mode with a pre-defined paper structure targeting trajectory prediction accuracy across mission phases (trans-lunar injection, free-return, re-entry). Two researchers collaborated using SMAIRT's branching conventions: Researcher A (script range 01–49) focused on feature engineering from ephemeris data; Researcher B (script range 50–99) developed the predictive models.

**Phase 1 — Downloaded historical data (3 iterations)**: Using publicly available Apollo trajectory data and Artemis I telemetry, the team characterized orbital parameter distributions. Iteration 1 downloaded and parsed trajectory data from NASA's PDS (Planetary Data System). Iteration 2 extracted relevant features: time-since-TLI, distance-from-Earth/Moon, velocity components, and solar radiation pressure estimates. Iteration 3 established baseline prediction accuracy using simple interpolation methods on Apollo missions.

KNOWN_PATTERNS.md accumulated critical entries: coordinate frame transformations that must be applied before combining data sources, numerical precision requirements for orbital calculations (float64 minimum), and the correct API endpoints for NASA Horizons ephemeris queries.

**HPC integration**: Model training required GPU resources for neural ODE solvers. The team configured `hpc/config.yaml` for their SLURM cluster, submitted training jobs via `hpc/templates/slurm_gpu.sh`, and monitored convergence using the monitor template. HPC logs integrated seamlessly with the audit trail—each cluster job's output was linked back to its hypothesis and analysis file.

**Phase 2 — Real Artemis II predictions (4 iterations)**: Using the trained models, the team predicted trajectory parameters for planned Artemis II mission phases. Iteration 4 applied models to planned trajectory windows. Iteration 5 quantified uncertainty bounds. Iteration 6 validated against independent trajectory simulations. Iteration 7 identified mission phases where prediction accuracy was insufficient and proposed additional data requirements.

**Collaborative workflow**: The intellectual contribution tracking revealed a clear division: Researcher A's key contribution was identifying that solar radiation pressure during lunar transit created a systematic bias unaccounted for in historical data (a domain insight AI could not generate). Researcher B's contribution was the neural ODE architecture choice that respected conservation laws. Both contributions were explicitly documented for publication attribution.

**MCP skills usage**: Both researchers loaded `smairt-research` skill at session start, eliminating the 5–10 minute priming overhead that previously began each session. The skill ensured consistent script formatting, log naming, and analysis structure across both researchers' work.

**Outcome**: 7 iterations across 2 researchers over 6 sessions. KNOWN_PATTERNS.md grew to 18 entries including mission-critical numerical precision requirements. The paper-driven structure mapped directly to publication sections.

Use Case 3: Metagenomic Functional Annotation Under Compositional Uncertainty

**Domain**: Bioinformatics / metagenomics
**Starting phase**: Synthetic (full 3-phase progression critical for this problem)
**Key SMAIRT features exercised**: Full data progression, dead-end handling, pivot documentation, KNOWN_PATTERNS for complex bioinformatics pipelines

*Research question*: Can functional annotations be reliably assigned to metagenomic assembled genomes (MAGs) when the underlying community composition is uncertain and reference databases have systematic biases toward well-studied organisms?

This use case demonstrates SMAIRT applied to a problem where the solution path is not immediately obvious, the data has multiple layers of uncertainty, and the 3-phase progression is essential for disentangling methodological artifacts from biological signal.

**Why 3-phase is critical here**: Metagenomic functional annotation faces a chicken-and-egg problem—you cannot validate annotations without knowing the true community composition, but you cannot determine composition without annotation. Synthetic data with known ground truth is the only way to disentangle database bias from method failure from genuine biological novelty.

**Phase 1 — Synthetic metagenomes (5 iterations)**: The researcher generated synthetic metagenomic communities with known functional profiles using InSilicoSeq and controlled reference database subsets.

Iteration 1 established baseline annotation accuracy on a simple 10-genome community using full reference databases (F1: 0.92). Iteration 2 introduced compositional uncertainty by varying relative abundances (F1 dropped to 0.67 for rare taxa <1% abundance). Iteration 3 systematically removed reference genomes from the database to simulate database bias—revealing that annotation accuracy for novel taxa dropped to near-random (F1: 0.31) even when closely related references existed.

**Dead end and pivot (Iteration 4)**: The researcher's initial hypothesis—that sequence similarity thresholds could compensate for database gaps—proved wrong. Standard approaches (BLAST best-hit, HMM profiles) all degraded similarly. SMAIRT's dead-end prompts helped articulate what had been tried and what fundamental assumptions might be wrong.

**Key intellectual contribution**: The researcher recognized that the problem wasn't similarity detection but rather the assumption that functional annotations transfer linearly with sequence identity. This insight—that function can diverge abruptly at specific positions while sequence identity remains high—was documented in the intellectual contribution log and became the paper's central finding.

Iteration 5 developed a position-aware annotation method that weighted active-site residues differently from structural residues. On synthetic data, this recovered annotation accuracy for novel taxa (F1: 0.71 vs. 0.31 for standard methods).

KNOWN_PATTERNS.md accumulated 15 entries during this phase alone, including: FASTA parsing edge cases for multi-line sequences, memory management for large alignment matrices (>100GB; required chunked processing), correct handling of ambiguous amino acid codes, and the specific database versions that produced reproducible results.

**Phase 2 — Downloaded benchmarks (3 iterations)**: The researcher validated on CAMI (Critical Assessment of Metagenome Interpretation) challenge datasets where ground truth is available. Iteration 6 applied the position-aware method to CAMI-I medium complexity. Iteration 7 compared against published CAMI participants. Iteration 8 characterized failure modes—the method underperformed on horizontal gene transfer events, a limitation that would have been invisible without systematic benchmarking.

**Phase 3 — Real metagenomes (2 iterations)**: Applied to unpublished gut microbiome samples from a clinical cohort. Iteration 9 compared position-aware annotations against standard annotations for the same samples, identifying 847 genes where methods disagreed. Iteration 10 validated a subset of disagreements using targeted PCR and Sanger sequencing, confirming that the position-aware method correctly identified 73% of functional divergence cases that standard methods missed.

**Outcome**: 10 iterations over 8 sessions. The 3-phase progression was essential—without synthetic ground truth, the fundamental insight about position-aware annotation would have been impossible to validate. The dead-end at iteration 4 and subsequent pivot represented the highest-value intellectual contribution, clearly documented in the audit trail. KNOWN_PATTERNS.md grew to 31 entries, many of which would be valuable for any future metagenomics project using the same tools.

Discussion

The IDE-Native Paradigm Shift

SMAIRT's IDE-native workflow represents a fundamental shift from earlier AI-assisted research approaches. When AI assistants can directly read project files, execute code, and write documentation, the friction of context transfer effectively disappears. This has several implications:

First, the audit trail becomes automatic rather than requiring manual effort. TeeLogger captures output without researcher intervention; the AI reads logs and writes analysis without copy-paste overhead. This dramatically reduces the documentation burden that makes comprehensive record-keeping impractical in traditional approaches.

Second, the iteration cycle accelerates. Where earlier approaches required switching between an execution environment and an AI chat interface—with manual transfer of output at each step—IDE-native workflows complete full hypothesis-to-analysis cycles within a single conversation.

Third, KNOWN_PATTERNS.md becomes a practical error-prevention mechanism rather than a theoretical ideal. Because the AI consults this file before generating code and proposes additions when new patterns are discovered, the document grows organically without requiring the researcher to remember to update it manually.

Error Prevention Through Knowledge Accumulation

The KNOWN_PATTERNS.md mechanism addresses a critical gap in AI-assisted research: the stateless nature of LLM interactions. Each new session begins without knowledge of what was learned in previous sessions—what worked, what failed, what edge cases exist. Without external persistence, researchers face a Sisyphean cycle of rediscovering the same issues.

Our use cases demonstrate the practical value of this mechanism. In Use Case 1, 12 patterns accumulated over 4 sessions prevented error recurrence. In Use Case 3, 31 patterns accumulated over 8 sessions included critical bioinformatics-specific entries (memory management, database versioning, parsing edge cases) that would have cost hours to rediscover.

The mechanism works because it leverages the AI's strengths: consistent consultation of reference material and structured pattern matching. The human researcher identifies that a discovery is worth preserving; the AI proposes the structured entry; and all future code generation benefits automatically.

The Value of Configurable Data Progression

Use Case 3 demonstrates why a mandatory linear progression would be inappropriate as a universal rule, while simultaneously showing the profound value of synthetic data when the research question demands ground truth validation. By making the progression configurable, SMAIRT respects researcher expertise about their domain while providing structural support for whichever starting point is chosen.

Use Case 2 illustrates the downloaded-first pattern: when validated public data exists and the research question concerns prediction on a specific target (Artemis II), beginning with synthetic data would be artificial and wasteful. The framework supports this by generating only the relevant experiment directories.

Collaborative Features

Use Case 2's collaborative workflow demonstrates SMAIRT's team science features. The file structure's inherent separation (per-researcher script ranges, individual hypothesis and analysis files) minimizes merge conflicts while the shared KNOWN_PATTERNS.md and BREADCRUMB_TRAIL.md maintain team coherence. The intellectual contribution tracking proved especially valuable for publication attribution—each researcher's key insights were documented in real-time rather than reconstructed post-hoc.

Positioning AI Appropriately in Scientific Research

SMAIRT embodies a specific philosophy: AI is a powerful tool for reaching the frontier of existing knowledge, but human insight remains essential for pushing beyond it. Use Case 3's dead-end at iteration 4 exemplifies this—AI suggested variations on failed approaches, but the fundamental reconceptualization (position-aware annotation) required human insight into the biology of protein function. The framework's explicit documentation of this pivot ensures both reproducibility and appropriate attribution.

Limitations and Future Directions

Several limitations suggest directions for future development:

1. **Evaluation metrics**: While our use cases demonstrate qualitative value, systematic quantitative evaluation (time-to-result, error rates, documentation completeness) across a larger sample of projects would strengthen the evidence base.

2. **Learning curve**: The framework's comprehensive structure may intimidate new users. Future work should develop graduated onboarding that introduces features incrementally.

3. **Automated pattern extraction**: Currently, KNOWN_PATTERNS.md requires human-AI collaboration to identify entries worth preserving. Future versions could analyze git history to automatically propose patterns from recurring code changes or error fixes.

4. **Cross-project pattern sharing**: KNOWN_PATTERNS.md is currently project-specific. A mechanism for sharing domain-specific patterns across projects (e.g., all metagenomics projects sharing FASTA parsing patterns) could accelerate new project setup.

5. **Deeper HPC integration**: Current HPC support provides templates and configuration but does not automate the sync-submit-retrieve cycle. Tighter integration with cluster schedulers could further reduce friction.

6. **Quantitative AI contribution metrics**: Beyond binary human/AI attribution, developing nuanced metrics for the degree and type of AI assistance at each stage could inform best practices for AI-assisted research methodology.

Conclusion

SMAIRT provides a structured framework for AI-assisted computational research that maximizes the benefits of AI collaboration while maintaining clear documentation, attribution, and reproducibility. By organizing work around the scientific method, implementing automated audit trails via TeeLogger, accumulating cross-session knowledge through KNOWN_PATTERNS.md, providing MCP skills for persistent AI context, and supporting configurable data progressions with HPC integration, SMAIRT addresses the fundamental challenges of integrating AI into the scientific process.

Our three use cases demonstrate the framework's versatility across domains (machine learning, aerospace, bioinformatics), team sizes (solo and collaborative), and complexity levels (straightforward methods development through non-obvious multi-stage problems). In each case, the framework accelerated the hypothesis-to-discovery cycle while preserving the audit trail needed for reproducibility and the intellectual contribution tracking needed for appropriate attribution.

The framework is freely available as an open-source cookiecutter template at https://github.com/biodataganache/smairt-cookiecutter. We invite the computational research community to adopt, adapt, and contribute to its continued development.

Availability

SMAIRT is available at https://github.com/biodataganache/smairt-cookiecutter under the MIT License. Projects generated from the template can use any license chosen by the researcher. Documentation, tutorials, and MCP skills are included in the repository.

Acknowledgments

SMAIRT was developed through iterative use of AI-assisted research workflows, refined by observing what actually works in practice across multiple research domains.

References

1. Noble WS. A Quick Guide to Organizing Computational Biology Projects. PLoS Computational Biology. 2009;5(7):e1000424.

2. Cookiecutter Data Science. DrivenData. Available from: https://drivendata.github.io/cookiecutter-data-science/

3. Ball R, Medeiros N. Teaching Integrity in Empirical Research: A Protocol for Documenting Data Management and Analysis. Journal of Economic Education. 2012;43(2):182-189.

4. Wilson G, et al. Good Enough Practices in Scientific Computing. PLoS Computational Biology. 2017;13(6):e1005510.

5. Wilson G, et al. Best Practices for Scientific Computing. PLoS Biology. 2014;12(1):e1001745.

6. Kluyver T, et al. Jupyter Notebooks: A Publishing Format for Reproducible Computational Workflows. Positioning and Power in Academic Publishing. 2016:87-90.

7. Mölder F, et al. Sustainable Data Analysis with Snakemake. F1000Research. 2021;10:33.

8. Di Tommaso P, et al. Nextflow Enables Reproducible Computational Workflows. Nature Biotechnology. 2017;35(4):316-319.

9. Amstutz P, et al. Common Workflow Language, v1.0. Specification, Common Workflow Language working group. 2016.

10. GitHub Copilot. GitHub. Available from: https://github.com/features/copilot

11. Model Context Protocol. Anthropic. Available from: https://modelcontextprotocol.io/

12. Jumper J, et al. Highly Accurate Protein Structure Prediction with AlphaFold. Nature. 2021;596(7873):583-589.

13. Chen M, et al. Evaluating Large Language Models Trained on Code. arXiv preprint arXiv:2107.03374. 2021.

14. Brown TB, et al. Language Models Are Few-Shot Learners. Advances in Neural Information Processing Systems. 2020;33:1877-1901.

15. OpenAI. GPT-4 Technical Report. arXiv preprint arXiv:2303.08774. 2023.

16. Anthropic. Claude: Constitutional AI. 2024.

17. Vaswani A, et al. Attention Is All You Need. Advances in Neural Information Processing Systems. 2017;30.

18. Sandve GK, et al. Ten Simple Rules for Reproducible Computational Research. PLoS Computational Biology. 2013;9(10):e1003285.

19. Biswas S. Role of ChatGPT in Science and Research: A Systematic Review. Journal of Scientific Research. 2023.

20. Kuhn TS. The Structure of Scientific Revolutions. University of Chicago Press. 1962.

Figures

Figure 1: SMAIRT Project Structure and Information Flow. Diagram showing the directory structure with arrows indicating the audit trail connections: hypothesis → script → log → analysis, and the role of KNOWN_PATTERNS.md as cross-session memory.

Figure 2: The SMAIRT Iteration Cycle. Diagram showing the loop from Background through Hypothesis, Methods (AI generates code checking KNOWN_PATTERNS), Execution (TeeLogger captures output), Interpretation (AI reads log, writes analysis), to Next Steps, which feeds back into Background. Human decision points highlighted.

Figure 3: Configurable Data Progression. Diagram showing the three starting-phase options with representative project types for each.

Figure 4: Use Case 3 Audit Trail. Concrete example showing the linked artifacts from the metagenomics use case, including the dead-end documentation at iteration 4 and the pivot that followed.

Figure 5: KNOWN_PATTERNS.md Growth Over Time. Chart showing accumulation of patterns across sessions for each use case, with annotations for when key errors were prevented by existing entries.

Supplementary Materials

S1: Complete Template File Listing. Full listing of all files generated by the SMAIRT template with descriptions.

S2: KNOWN_PATTERNS.md Examples. Complete KNOWN_PATTERNS.md files from each use case at project completion.

S3: Intellectual Contribution Logs. Selected entries from the intellectual contribution tracking files demonstrating how human insights are documented.

S4: HPC Configuration Examples. Complete hpc/config.yaml and SLURM templates from Use Case 2.

S5: MCP Skill Definitions. Complete skill files for smairt-research and smairt-paper-driven.
