#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPOSITORY=$(CDPATH= cd -- "$HERE/../.." && pwd)
WORK=${1:-"$HERE/.demo-work"}
VENV="$WORK/venv"
PROJECT="$WORK/project"

if [ -e "$WORK" ]; then
  printf '%s\n' "Demo destination already exists: $WORK" >&2
  exit 2
fi

if [ -n "${SMAIRT_BIN:-}" ]; then
  SMAIRT=$SMAIRT_BIN
else
  python3 -m venv "$VENV"
  "$VENV/bin/python" -m pip install --quiet "$REPOSITORY"
  SMAIRT="$VENV/bin/smairt"
fi

"$SMAIRT" --version
"$SMAIRT" new "$PROJECT" --name "Verified Enzyme Kinetics" --author "Demo Researcher" \
  --question "Can the workflow recover known Michaelis-Menten parameters?" \
  --confirm-contributor --no-git

cd "$PROJECT"
"$SMAIRT" doctor --json >/dev/null
"$SMAIRT" experiment new --title "Enzyme Kinetics" \
  --purpose "Recover known parameters from a deterministic local fixture"

ITERATION="$PROJECT/experiments/EXPERIMENT_001_enzyme-kinetics/iterations/ITERATION_001"
cp "$HERE/data.csv" "$HERE/expected-results.json" "$ITERATION/"
cp "$HERE/protocol.yaml" "$ITERATION/protocol.yaml"
cp "$HERE/analysis.py" "$ITERATION/script_001_enzyme_kinetics.py"
"$SMAIRT" code index >/dev/null
"$SMAIRT" validate --json >/dev/null
"$SMAIRT" run --experiment EXPERIMENT_001 --iteration ITERATION_001

RUN_JSON=$(find "$PROJECT/results/EXPERIMENT_001/ITERATION_001" -name run.json -print | head -n 1)
RUN_ID=$(basename "$(dirname "$RUN_JSON")")
cp "$HERE/ANALYSIS_ITERATION_001.md" \
  "$PROJECT/analysis/EXPERIMENT_001/ANALYSIS_ITERATION_001.md"
"$SMAIRT" verify --run "$RUN_ID" --json >/dev/null
"$SMAIRT" decision record --experiment EXPERIMENT_001 --iteration ITERATION_001 \
  --run "$RUN_ID" --decision ACCEPT --rationale "Independent recovery checks passed." \
  --decided-by "Demo Researcher"

HOOK_RESULT=$(printf '%s' '{"tool_name":"read_file","tool_input":{"path":".env"}}' | \
  "$SMAIRT" harness hook --harness codex --event PreToolUse)
printf '%s' "$HOOK_RESULT" | grep -q 'deny'

"$SMAIRT" status --json
printf '\nCompleted local demo: %s\n' "$PROJECT"
