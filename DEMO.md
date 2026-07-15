# SMAIRT walkthrough: from installation to a correct result

This is a demo for **you to perform**, one step at a time. It creates a normal SMAIRT project,
uses the experiment scaffold that SMAIRT generates, runs a small local enzyme-kinetics analysis,
and ends with a result you inspect and accept yourself. It does not use HPC or require network
access.

The example is synthetic by design: the known values are `Vmax = 120.0 micromoles/minute` and
`Km = 2.5 mM`. Recovering those values proves that the analysis and provenance path work; it does
not pretend to be a biological discovery.

## 1. Install the current checkout

From the SMAIRT source folder:

```bash
cd ~/Documents/GitHub/smairt-template
uv tool install --force --python 3.11 .
smairt --version
```

Run `smairt setup doctor` if installation reports a problem. No API key is needed for this demo.

## 2. Create your project

```bash
cd ~/Documents
smairt new
```

Choose these answers in the terminal wizard:

- Create a new folder.
- Project name: `SMAIRT Enzyme Demo`
- Project folder: `smairt-enzyme-demo`
- Research question: `Can the workflow recover known Michaelis-Menten parameters?`
- Enter your own name as the primary researcher and register yourself as the active contributor.
- Data classification: `Unpublished`.
- No managed environment is required.
- Keep Codex or choose the harness you actually use.
- Standard safety mode is sufficient.

After creation, Escape returns to the shell. You can reopen this project from any directory:

```bash
smairt menu ~/Documents/smairt-enzyme-demo
```

There is no account login. A SMAIRT project is a local folder containing `smairt.yaml`; the command
above is the explicit way to open one you already know.

## 3. Create the experiment scaffold

```bash
cd ~/Documents/smairt-enzyme-demo
smairt experiment new --title "Enzyme Kinetics" \
  --purpose "Recover known parameters from a deterministic local fixture"
```

SMAIRT now creates:

```text
experiments/EXPERIMENT_001_enzyme-kinetics/
├── experiment.yaml
└── iterations/ITERATION_001/
    ├── config.yaml
    ├── protocol.yaml
    └── script_001_enzyme_kinetics.py
```

The protocol and script begin as reviewable scaffolds. For this short demo, copy the prepared data,
completed protocol, and analysis into that scaffold:

```bash
SMAIRT_SOURCE="$HOME/Documents/GitHub/smairt-template"
ITERATION="$HOME/Documents/smairt-enzyme-demo/experiments/EXPERIMENT_001_enzyme-kinetics/iterations/ITERATION_001"

cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/data.csv" "$ITERATION/data.csv"
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/expected-results.json" "$ITERATION/expected-results.json"
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/protocol.yaml" "$ITERATION/protocol.yaml"
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/analysis.py" \
  "$ITERATION/script_001_enzyme_kinetics.py"
```

Open `protocol.yaml` and read it before continuing. It declares the inputs, controls, outcomes,
failure criteria, stopping rule, and expected output. This review is part of the demo—not busywork.

## 4. Validate and run locally

```bash
cd ~/Documents/smairt-enzyme-demo
smairt code index
smairt validate
smairt run --experiment EXPERIMENT_001 --iteration ITERATION_001
```

The run prints a `run_id` beginning with `RUN_`. Save that value. The result should report:

```text
vmax_umol_min: 120.0
km_mM: 2.5
correct: true
```

If those values are absent or `correct` is false, stop. Do not accept the run.

## 5. Interpret and make the human decision

Copy the prepared interpretation into the normal analysis location:

```bash
mkdir -p analysis/EXPERIMENT_001
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/ANALYSIS_ITERATION_001.md" \
  analysis/EXPERIMENT_001/ANALYSIS_ITERATION_001.md
```

Replace the two values below with the run ID you just received and the same researcher name you
registered during project creation:

```bash
RUN_ID=RUN_REPLACE_WITH_YOUR_RUN_ID
RESEARCHER="Your Registered Name"

smairt verify --run "$RUN_ID"
smairt decision record --experiment EXPERIMENT_001 --iteration ITERATION_001 \
  --run "$RUN_ID" --decision ACCEPT \
  --rationale "The predeclared parameter recovery and blank-control checks passed." \
  --decided-by "$RESEARCHER"
```

SMAIRT checks the immutable run, protocol digest, result-summary checksum, and written interpretation
before recording acceptance. The software validates the evidence trail; **you** make the scientific
decision.

## 6. Inspect the finished state

```bash
smairt status
smairt validate
smairt menu ~/Documents/smairt-enzyme-demo
```

The project should show one experiment and accepted evidence with no validation errors. You can now
inspect the readable files under `experiments/`, `results/`, and `analysis/` to see exactly what
SMAIRT recorded.

## Optional safety check

This asks SMAIRT's hook policy whether an agent may read a protected `.env` file. It uses only a
synthetic request and does not open a real file:

```bash
printf '%s' '{"tool_name":"read_file","tool_input":{"path":".env"}}' | \
  smairt harness hook --harness codex --event PreToolUse
```

The response must deny the operation.
