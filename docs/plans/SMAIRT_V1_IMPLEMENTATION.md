# SMAIRT v1 Implementation

## Milestones

1. Package governance: Python package, MIT license, citation metadata, PNNL acknowledgment.
2. Project core: schemas, atomic writes, scaffold, Textual wizard/dashboard, status and context.
3. Safety and environment: Git policy, hooks, validation, Conda creation/selection/execution.
4. Grounding: local PDF index, checksums, initial background, retained proposal sets.
5. Research execution: hypotheses, experiments, iterations, recorded runs, decisions, amendments.
6. Scholarly output: unified paper scaffold and accepted-evidence provenance.
7. Distribution: macOS/Linux CI, wheel/sdist, pipx/uv documentation, PhD dogfood workflow.

## Release Gates

- Clean package installation on Python 3.11 and 3.12.
- All automated tests pass on macOS and Linux.
- TUI creation and cancellation are non-destructive.
- Protected files cannot be staged.
- A complete question-to-paper-evidence smoke workflow passes.
- The PyPI name is rechecked before publishing.
