# SMAIRT Quickstart

Create a project with an explicitly confirmed contributor and harness:

```bash
smairt new enzyme-kinetics \
  --name "Enzyme Kinetics" \
  --author "Researcher Name" \
  --confirm-contributor \
  --question "Which kinetic model best explains the observations?" \
  --classification unpublished \
  --harness codex
cd enzyme-kinetics
```

Then follow the state machine instead of memorizing the workflow:

```bash
smairt doctor --json
smairt next --json
smairt context --task planning --token-budget 8000 --json
```

Add and verify references, complete the generated background, review three proposed hypotheses,
and explicitly activate one. Create and execute experiments only through SMAIRT so runs receive
immutable provenance bundles.

```bash
smairt reference add paper.pdf
smairt reference list --json
smairt background create
smairt hypothesis proposals new
smairt experiment new --title "Initial model comparison" --purpose "Compare candidate fits"
smairt run --experiment EXPERIMENT_001 --iteration ITERATION_001
smairt verify --json
```

Use `smairt next --json` after every step. It will route accepted results into evidence review,
claim approval, manuscript review, and versioned Markdown/DOCX builds.

To change coding harnesses safely:

```bash
smairt harness select cline --dry-run
smairt harness select cline
```

Read [docs/SAFETY.md](docs/SAFETY.md) before working with private or controlled data.
