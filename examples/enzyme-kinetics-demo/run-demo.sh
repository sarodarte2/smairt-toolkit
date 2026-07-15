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
"$SMAIRT" new "$PROJECT" --name "Enzyme Kinetics Preview" --author "Demo Researcher" \
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
cp "$HERE/ANALYSIS_ITERATION_001.md" \
  "$PROJECT/analysis/EXPERIMENT_001/ANALYSIS_ITERATION_001.md"
test -n "$RUN_JSON"

HOOK_RESULT=$(printf '%s' '{"tool_name":"read_file","tool_input":{"path":".env"}}' | \
  "$SMAIRT" harness hook --harness codex --event PreToolUse)
printf '%s' "$HOOK_RESULT" | grep -q 'deny'

"$SMAIRT" status --json
printf '\nCompleted non-validating smoke example: %s\n' "$PROJECT"
printf '%s\n' 'No verification or research decision was recorded.'
