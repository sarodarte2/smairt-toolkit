# SMAIRT documentation

This documentation explains the SMAIRT research preview from first installation through technical
architecture and maintenance. Start with the shortest path that matches your role.

## Getting started

- [Installation](getting-started/installation.md) — install the source preview, run setup checks,
  and understand optional local connections.
- [Quickstart](getting-started/quickstart.md) — create a project, inspect its state, and learn what
  SMAIRT records without making a scientific decision.

## Research guides

- [Research workflow](guides/research-workflow.md) — move from sources and proposals through runs,
  evidence, claims, correction, and collaboration.
- [Literature integrations](guides/integrations.md) — configure and use Zotero, Crossref, OpenAlex,
  Semantic Scholar, DataCite, Unpaywall, and metadata-only MCP access.
- [Optional HPC execution](guides/hpc.md) — submit declared work to Slurm after it runs locally.
- [Troubleshooting](guides/troubleshooting.md) — recover from locks, transactions, failed runs,
  adapter conflicts, and terminal problems.

## Concepts

- [Scientific workflow](concepts/scientific-workflow.md) — understand human gates, evidence states,
  corrections, and the durable provenance model.
- [Architecture](concepts/architecture.md) — review domain boundaries, trust boundaries,
  concurrency, storage, context, and extension surfaces.
- [Safety model](concepts/safety.md) — understand classifications, Standard and Strict modes,
  remote operations, enforcement maturity, and non-compliance boundaries.

## Reference

- [CLI reference](reference/cli.md) — common command groups, workflows, JSON output, exit codes, and
  completion.
- [Harness guide](reference/harnesses.md) — compare supported coding harnesses and open their
  focused setup guides.

## Development

- [Contributing](../CONTRIBUTING.md) — issue-first contribution process and writing conventions.
- [Developer guide](development/developer-guide.md) — code structure, contracts, tests, and harness
  extension requirements.
- [Release process](development/release.md) — automated and manual gates for a future release.

## Project status and origin

SMAIRT is an unreleased research preview. The enzyme-kinetics example is explicitly unverified, and
there is no current citation recommendation. See the root [README](../README.md),
[Acknowledgments](../ACKNOWLEDGMENTS.md), [Changelog](../CHANGELOG.md), and
[Security policy](../SECURITY.md) for the corresponding public statements.
