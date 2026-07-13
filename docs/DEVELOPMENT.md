# Development and readability

SMAIRT code should explain the research invariant it protects without narrating ordinary Python
syntax. Readability is enforced by Ruff for module, class, method, and function docstrings across
the runtime package.

## Writing conventions

- Give public functions an imperative one-line docstring describing their observable contract.
- Add detail when a function mutates persistent state, performs remote I/O, or enforces a human
  gate. Document failure conditions that callers are expected to handle.
- Use comments for provenance, safety, scientific intent, and non-obvious ordering constraints.
  Remove comments that merely restate the next line.
- Prefer domain names such as `replacement_run` and `active_contributor` over generic names such
  as `item`, `data`, or `value` when the scope is not already obvious.
- Keep command presentation in `cli_*.py`; put state transitions and validation in domain modules.
- Keep adapters as translations of shared state. Harness modules must not create parallel research
  truth or silently overwrite user-owned files.

## CLI module boundaries

`cli.py` owns the root command tree and cross-domain project lifecycle. Focused modules own
cohesive command groups and use `cli_shared.py` for project resolution and output rendering.
Command extraction must preserve command names, option names, exit codes, JSON shapes, and safety
confirmations.

Run `ruff check src tests`, `pytest`, and `git diff --check` after readability refactors.
