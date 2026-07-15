# Contributing to SMAIRT

SMAIRT is a research preview for traceable, human-gated AI-assisted science. Contributions are
welcome when they make a researcher workflow clearer, safer, more reproducible, or easier to
review.

## Start with an issue

Open a [GitHub Issue](https://github.com/sarodarte2/smairt-toolkit/issues) before substantial code,
schema, harness, safety, or workflow changes. Explain the researcher affected, the current friction,
the desired outcome, and any human-decision or provenance boundary involved. Small documentation
corrections and focused bug fixes may proceed directly to a pull request.

Never include credentials, private PDFs, protected data, identifiable participant information, or
sensitive remote URLs in issues, commits, fixtures, or logs. Use the private route in
[SECURITY.md](SECURITY.md) for vulnerabilities.

## Development setup

```bash
git clone https://github.com/sarodarte2/smairt-toolkit.git
cd smairt-toolkit
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

Create a focused branch. Preserve command names, JSON envelopes, exit codes, scientific decision
gates, immutable records, and user-owned harness configuration unless the issue explicitly changes
that contract.

## Documentation conventions

- Write for the named audience and define SMAIRT-specific terms on first use.
- Prefer plain scientific language, active voice, short paragraphs, and concrete outcomes.
- Separate observation from interpretation, implemented behavior from future work, and technical
  safeguards from compliance claims.
- State whether an operation is offline and read-only, performs remote metadata access, or mutates
  project state.
- Treat executable behavior, tests, and official provider or harness documentation as the source of
  truth. Qualify or remove claims that cannot be verified.
- Update the documentation hub, focused guide, CLI reference, and generated project prose when a
  change affects them. Avoid duplicating the same detailed procedure in multiple files.

## Verification

Run the relevant focused tests while developing, then complete the repository checks:

```bash
ruff format --check src tests scripts
ruff check src tests scripts
mypy src/smairt
python scripts/validate_docs.py
python -m pytest -p no:cacheprovider
python -m build --no-isolation
git diff --check
```

Pull requests should explain the researcher or maintainer outcome, important behavior changes,
verification performed, and any effect on provenance, collaboration, safety, or scientific gates.
