# Enzyme-kinetics preview example

> **Status: unverified.** The automated fixture and human walkthrough are retained for future
> validation. They have not completed the manual review required to support a software-validation,
> release-readiness, or scientific claim.

This example is designed to exercise a local SMAIRT path with a small synthetic
Michaelis–Menten dataset. The generating values are `Vmax = 120.0 µmol/min` and `Km = 2.5 mM`.
Recovering those values would test one analysis and provenance path; it would not establish
biological validity, performance on real measurements, or general software correctness.

The directory contains two related materials:

- `run-demo.sh` is an automated smoke fixture for maintainers. It creates records and executes the
  analysis, but automation cannot perform genuine human scientific review.
- The walkthrough below is a planned researcher-operated path from installation through one narrow
  claim. It remains unverified until completed and documented by a reviewer.

## Automated smoke fixture

From the repository root:

```bash
./examples/enzyme-kinetics-demo/run-demo.sh /tmp/smairt-enzyme-preview
```

The default path creates a virtual environment and installs the current repository so packaging
failures remain visible. To use an existing development install:

```bash
SMAIRT_BIN=/path/to/smairt \
  ./examples/enzyme-kinetics-demo/run-demo.sh /tmp/smairt-enzyme-preview
```

The script checks its predeclared numerical ranges and a synthetic hook-policy denial. Passing the
script means only that the automated fixture completed those checks in that environment. It does
not verify the human walkthrough or accept evidence on behalf of a researcher.

## Planned human walkthrough

### 1. Install the source preview

```bash
git clone https://github.com/sarodarte2/smairt-toolkit.git
cd smairt-toolkit
uv tool install --force --python 3.11 .
smairt --version
smairt setup
```

Literature connections are optional except for the disclosed DOI import below. This walkthrough
uses local execution rather than HPC.

### 2. Create a project

```bash
cd ~/Documents
smairt new
```

Suggested wizard values:

- folder: `smairt-enzyme-preview`;
- project name: `SMAIRT Enzyme Preview`;
- question: `Can this workflow recover known Michaelis-Menten parameters?`;
- your own confirmed contributor identity;
- classification: `Unpublished`;
- environment: none;
- a maintained harness you actually use;
- safety mode: Standard.

Then inspect the local project:

```bash
cd ~/Documents/smairt-enzyme-preview
smairt doctor --json
smairt status --json
smairt next --json
```

### 3. Add the contextual source

The DOI is a translation and reanalysis of the Michaelis–Menten paper. The command performs a
disclosed Crossref request and imports metadata only.

```bash
smairt reference add-doi 10.1021/bi201284u --confirm-remote
smairt reference list
smairt background create
```

Copy the prepared synthesis from this example and review it before validation:

```bash
SMAIRT_SOURCE="$HOME/Documents/GitHub/smairt-toolkit"
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/initial_background.md" \
  background/initial_background.md
smairt background validate
```

Stop if the expected DOI reference ID differs or validation fails. The source supplies historical
context; it is not evidence that this implementation is correct.

### 4. Compare proposals and record the selection

```bash
smairt hypothesis proposals new
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/proposal_options.md" \
  hypotheses/proposals/PROPOSAL_SET_001.md
smairt hypothesis proposals validate hypotheses/proposals/PROPOSAL_SET_001.md
```

Read the nonlinear fit, reciprocal linearization, and constant-rate null options. If option A is
scientifically appropriate, record that choice using the exact active contributor name:

```bash
RESEARCHER="Your Registered Name"
smairt hypothesis activate \
  --proposal-set hypotheses/proposals/PROPOSAL_SET_001.md \
  --option A \
  --title "Nonlinear Michaelis-Menten recovery" \
  --statement "Nonlinear fitting recovers the declared Vmax and Km within tolerance." \
  --selected-by "$RESEARCHER" \
  --rationale "It estimates the parameters directly and matches the predeclared check."
```

Complete and review the generated canonical hypothesis. Do not continue merely to make the demo
advance.

### 5. Create the experiment and declared protocol

```bash
smairt experiment new --title "Enzyme Kinetics" --hypothesis HYPOTHESIS_001 \
  --purpose "Recover declared parameters from a deterministic local fixture"

ITERATION="$PWD/experiments/EXPERIMENT_001_enzyme-kinetics/iterations/ITERATION_001"
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/data.csv" "$ITERATION/data.csv"
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/expected-results.json" \
  "$ITERATION/expected-results.json"
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/protocol.yaml" "$ITERATION/protocol.yaml"
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/analysis.py" \
  "$ITERATION/script_001_enzyme_kinetics.py"
```

Read `protocol.yaml` before execution. It declares inputs, controls, outcomes, uncertainty,
failure criteria, interpretation limits, and the expected output.

### 6. Run and inspect

```bash
smairt code index
smairt validate
smairt run --experiment EXPERIMENT_001 --iteration ITERATION_001
```

Record the printed run ID. The fixture expects `vmax_umol_min: 120.0`, `km_mM: 2.5`, and
`correct: true`. Stop rather than accept the run if a declared check fails.

### 7. Verify and interpret

```bash
RUN_ID=RUN_REPLACE_WITH_THE_PRINTED_ID
mkdir -p analysis/EXPERIMENT_001
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/ANALYSIS_ITERATION_001.md" \
  analysis/EXPERIMENT_001/ANALYSIS_ITERATION_001.md

smairt verify --run "$RUN_ID"
smairt decision record --experiment EXPERIMENT_001 --iteration ITERATION_001 \
  --run "$RUN_ID" --decision ACCEPT \
  --rationale "Every predeclared recovery and blank-control check passed." \
  --decided-by "$RESEARCHER"
```

Only a researcher who has inspected the protocol, run, logs, and analysis should record the
decision.

### 8. Review evidence and one bounded claim

```bash
smairt paper evidence review --run "$RUN_ID" \
  --purpose "Test deterministic parameter recovery and provenance" \
  --observed-result "Vmax 120.0 and Km 2.5 were recovered; the blank check passed." \
  --limitations "Synthetic deterministic fixture; no biological generalization." \
  --decision ACCEPT
```

Use the printed evidence ID to propose a narrow claim, inspect the JSON, and approve it only if it
matches the accepted evidence:

```bash
smairt paper claim propose \
  --statement "This preview analysis recovered its declared Michaelis-Menten parameters." \
  --evidence EVIDENCE_ID
smairt paper claim approve CLAIM_ID
smairt validate
smairt status
```

Completion of these commands would still demonstrate only this synthetic path. The walkthrough
remains unverified until a human reviewer performs it, records the environment and observations,
and reviews any discrepancies.

## Known limitations

- The dataset is synthetic, small, deterministic, and intentionally well behaved.
- The analysis uses a bounded grid search rather than a general kinetic-analysis package.
- There is no wet-laboratory replication, instrument uncertainty, or biological dataset.
- Semantic Scholar, OpenAlex, Unpaywall, and HPC are outside the correctness path.
- Automated acceptance in `run-demo.sh` is fixture mechanics, not researcher judgment.
