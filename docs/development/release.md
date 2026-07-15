# Release process

SMAIRT has no verified release yet. This document defines the gates that must pass before creating
one; it is not evidence that they have already passed.

## Automated gates

A release candidate must pass:

- Ruff format and lint checks, strict mypy, documentation validation, and the functional test suite;
- Python 3.11–3.13 on Linux and macOS plus minimum/latest dependency resolution;
- source distribution and wheel builds followed by clean-environment smoke tests;
- CodeQL, dependency audit and review, and secret scanning;
- README commands, local links, external links, metadata consistency, and package/version checks.

## Manual gates

- Run the WSL clean-wheel orientation journey.
- Verify compact, medium, and wide terminal layouts, resizing, reduced motion, and custom ASCII
  marks without built-in institutional marks.
- Install, switch, inspect, and toggle metadata-only MCP for every maintained harness.
- Confirm ordinary status, validation, doctor, and menu refreshes use no network.
- Review safety wording and controlled-data refusal with appropriate project stakeholders.
- Keep the enzyme-kinetics walkthrough outside release acceptance criteria; it remains unverified
  preview material until a reviewer completes and documents the human walkthrough.
- Review repository About text, topics, social preview, support routes, branch protection, and
  required checks.
- Confirm there is no unresolved high- or critical-severity validated security finding.

## Attribution gates

Before the first public release:

- confirm the existing MIT copyright line and derivative-work licensing with the appropriate PNNL
  contact;
- decide software authorship and create a reviewed `CITATION.cff`;
- establish a private conduct-reporting route before restoring a Code of Conduct;
- confirm that acknowledgments do not imply PNNL or UTEP endorsement.

## Publishing a future release

Only after the gates pass should maintainers update the changelog, synchronize version metadata,
create a reviewed tag, and invoke the GitHub release workflow. The workflow builds wheel and source
artifacts once, tests them, produces checksums and an SBOM, creates provenance attestations, and
publishes a GitHub prerelease. PyPI publication remains a separate decision.
