# SMAIRT demo: installation to one approved claim

This is a demo for **you to perform**, not an experiment that SMAIRT secretly ran for you. It
starts with installation, creates a normal project, and ends after you approve one narrow claim.
Every research command runs inside that project. The computation is local; HPC is not used.

The synthetic fixture has independently declared values of `Vmax = 120.0 µmol/min` and
`Km = 2.5 mM`. Recovering them checks this analysis and evidence path. It is not a biological
discovery.

## 1. Install and set up SMAIRT

From the SMAIRT source checkout:

```bash
cd ~/Documents/GitHub/smairt-template
uv tool install --force --python 3.11 .
smairt --version
smairt setup
```

In Setup, open **Installation & version**. A working installation can still recommend an update;
that is not a blocking Doctor problem. Literature connections are optional for everything except
the DOI step below. To enable normal shell suggestions once, run `smairt --install-completion` and
restart the shell.

## 2. Create and enter a real project

```bash
cd ~/Documents
smairt new
```

Use these wizard values:

- New folder: `smairt-enzyme-demo`
- Project name: `SMAIRT Enzyme Demo`
- Question: `Can the workflow recover known Michaelis-Menten parameters?`
- Your own name, confirmed as the active contributor
- Classification: `Unpublished`
- Environment: none (the demo uses the SMAIRT installation)
- Harness: Codex, or the maintained harness you actually use
- Safety: Standard

Now enter the project. There is no SMAIRT account login: a project is a local folder containing
`smairt.yaml`.

```bash
cd ~/Documents/smairt-enzyme-demo
smairt doctor
smairt menu
```

If **Health & updates** recommends schema, guidance, or adapter work, open **Project updates**, read
the preview, and apply it there. The one action explains every version step before changing files.

## 3. Add one source and review the background

This command makes one disclosed Crossref request. It imports metadata only and does not download a
PDF. The DOI is the 2011 translation and reanalysis of the Michaelis-Menten paper.

```bash
smairt reference add-doi 10.1021/bi201284u --confirm-remote
smairt reference list
smairt background create
```

Copy the prepared demo synthesis over the generated draft, then read it. It deliberately separates
historical context from evidence about software correctness.

```bash
SMAIRT_SOURCE="$HOME/Documents/GitHub/smairt-template"
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/initial_background.md" \
  background/initial_background.md
smairt background validate
```

Do not continue if the reference ID is not `doi-a04d8aaf11d84cfac807` or validation fails.

Optional orientation: open `smairt menu` → **Literature & references** → **Discover literature**.
Semantic Scholar search works publicly without a key, and a DOI-backed project reference can seed
its recommendation view. OpenAlex adds a second broad index when its free-key profile is connected;
Unpaywall resolves lawful open-access locations after its local contact-email profile is connected.
Discovery candidates are provisional and do not change this demo unless you explicitly select a
DOI result and confirm authoritative Crossref/DataCite import.

## 4. Compare three hypotheses and select one

```bash
smairt hypothesis proposals new
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/proposal_options.md" \
  hypotheses/proposals/PROPOSAL_SET_001.md
smairt hypothesis proposals validate hypotheses/proposals/PROPOSAL_SET_001.md
```

Read all three options. They test a native nonlinear fit, a reciprocal linearization, and a
constant-rate null. Select option A explicitly, replacing the name below with the exact contributor
name you entered during project creation:

```bash
RESEARCHER="Your Registered Name"
smairt hypothesis activate \
  --proposal-set hypotheses/proposals/PROPOSAL_SET_001.md \
  --option A \
  --title "Nonlinear Michaelis-Menten recovery" \
  --statement "Nonlinear fitting recovers the declared Vmax and Km within tolerance." \
  --selected-by "$RESEARCHER" \
  --rationale "It estimates the parameters directly and matches the predeclared correctness test."
```

Open `hypotheses/HYPOTHESIS_001_nonlinear-michaelis-menten-recovery.md`. Preserve its front matter
and replace its unfinished sections with this reviewed content:

```markdown
## Rationale
The native nonlinear relationship directly estimates both declared parameters without reciprocal
error weighting.

## Falsifiable Prediction
Vmax is 119.9–120.1 µmol/min, Km is 2.49–2.51 mM, and absolute blank velocity is at most 0.1.

## Null or Competing Explanation
An implementation, aggregation, or model error causes at least one predeclared check to fail.

## Required Data and Controls
All fixed triplicates, every substrate concentration, and the zero-substrate blank are required.

## Success and Failure Criteria
Success requires every declared range and control check. Any failed check is failure.

## Known Confounders
The synthetic, noise-controlled fixture does not establish performance on biological measurements.

## Human Selection Rationale
It is the most direct bounded test of the demo analysis.
```

## 5. Create the linked experiment and inspect its protocol

Only now create the experiment, inside the project and linked to the selected hypothesis:

```bash
smairt experiment new --title "Enzyme Kinetics" --hypothesis HYPOTHESIS_001 \
  --purpose "Recover independently declared parameters from a deterministic local fixture"

ITERATION="$PWD/experiments/EXPERIMENT_001_enzyme-kinetics/iterations/ITERATION_001"
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/data.csv" "$ITERATION/data.csv"
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/expected-results.json" "$ITERATION/expected-results.json"
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/protocol.yaml" "$ITERATION/protocol.yaml"
cp "$SMAIRT_SOURCE/examples/enzyme-kinetics-demo/analysis.py" \
  "$ITERATION/script_001_enzyme_kinetics.py"
```

Read `protocol.yaml`. It declares inputs, controls, outcomes, uncertainty, failure criteria,
falsifier, stopping rule, and expected output before execution.

## 6. Validate and run locally

```bash
smairt code index
smairt validate
smairt run --experiment EXPERIMENT_001 --iteration ITERATION_001
```

The output must report `vmax_umol_min: 120.0`, `km_mM: 2.5`, and `correct: true`. Save the printed
`RUN_...` ID. If any value differs, stop; do not accept the run.

## 7. Verify, interpret, and accept the evidence

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

smairt paper evidence review --run "$RUN_ID" \
  --purpose "Test deterministic parameter recovery and provenance" \
  --observed-result "Vmax 120.0 and Km 2.5 were recovered; the blank check passed." \
  --limitations "Synthetic deterministic fixture; no claim about biological generalization." \
  --decision ACCEPT
```

The last command prints an evidence filename. Copy its `evidence-run_...` identifier for the next
step.

## 8. Propose and approve one narrow claim

```bash
EVIDENCE_ID=evidence-run_replace_with_your_run_id_in_lowercase
smairt paper claim propose \
  --statement "This demo analysis recovered its independently declared Michaelis-Menten parameters." \
  --evidence "$EVIDENCE_ID"
```

Read the proposed JSON file under `paper/claims/`. Copy its `claim-...` ID, then make the explicit
human decision:

```bash
CLAIM_ID=claim-replace-with-the-printed-id
smairt paper claim approve "$CLAIM_ID"
smairt paper status
smairt validate
smairt status
```

The demo is complete when there is one accepted evidence card, one approved claim, and no validation
error. It intentionally stops before manuscript drafting.

## 9. Confirm the safety boundary

This sends a synthetic request to SMAIRT's hook policy. It does not open a real `.env` file:

```bash
printf '%s' '{"tool_name":"read_file","tool_input":{"path":".env"}}' | \
  smairt harness hook --harness codex --event PreToolUse
```

The result must deny the request. HPC remains available for later large analyses through
**Tools & compute**, but it is outside this local correctness demo.
