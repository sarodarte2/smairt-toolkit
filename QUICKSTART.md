# SMAIRT Quickstart

First run `smairt setup` if you want OpenAlex or Zotero, then run `smairt new`. The wizard can
create a new child folder or scaffold the folder you already selected. New Conda environments use
the project slug as their default name.

This journey creates a project, completes the required framing placeholders, selects a hypothesis,
runs an experiment, and records a human decision. Substitute real sources and scientific content;
the example text is deliberately not evidence.

```bash
smairt new quick-study --name "Quick Study" --author "Researcher Name" \
  --confirm-contributor --classification unpublished --no-git
cd quick-study
smairt background create
smairt hypothesis proposals new
```

Open `background/initial_background.md`. Replace the synthesis prompt and complete every section
with indexed source IDs. Open the newest `hypotheses/proposals/PROPOSAL_SET_*.md`; replace every
bracketed placeholder in all three meaningfully distinct options. Validate both:

```bash
smairt background validate
smairt hypothesis proposals validate hypotheses/proposals/PROPOSAL_SET_001.md
```

Record the researcher's selection:

```bash
smairt hypothesis activate \
  --proposal-set hypotheses/proposals/PROPOSAL_SET_001.md \
  --option A --title "Selected direction" \
  --statement "A specific falsifiable statement" \
  --selected-by "Researcher Name" --rationale "Why this option is scientifically preferred"
```

Complete every required section in the new canonical hypothesis, then create and execute its first
experiment:

```bash
smairt experiment new --title "Baseline test" --hypothesis HYPOTHESIS_001
smairt code validate
smairt run --experiment EXPERIMENT_001 --iteration ITERATION_001
smairt verify --json
```

Use the emitted run ID for the explicit interpretation decision:

```bash
smairt decision record --experiment EXPERIMENT_001 --iteration ITERATION_001 \
  --run RUN_<timestamp> --decision ACCEPT \
  --rationale "Observed result met the predefined criterion" --decided-by "Researcher Name"
smairt next --json
```

For a copy/paste-ready agent handoff based on the same project state, run `smairt next --prompt`.
It includes bounded files to read and preserves all human decision gates.

Failed or interrupted runs cannot be accepted. Revise by creating a new iteration rather than
editing an old run.
