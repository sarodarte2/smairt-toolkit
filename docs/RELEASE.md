# Maintainer Release Guide

## Automated gates

A release candidate must pass CI on Python 3.11–3.13 for Linux and macOS, minimum/latest dependency
resolution, source-scoped branch coverage at or above 90%, strict mypy, Ruff, clean-wheel user
journeys, CodeQL, pip-audit, dependency review, gitleaks, and the formal repository security scan.

## Manual gates

- Run the WSL clean-wheel smoke journey.
- Confirm the TUI first paint and 80×24 wizard/dashboard behavior.
- Confirm ordinary status, validation, doctor, and TUI refresh have no network access.
- Review experimental safety wording and controlled-data refusal with the team.
- Verify README commands, links, badges, changelog, and installation instructions.
- Confirm no high/critical validated security or dependency finding is open.

## Tag release

Update `CHANGELOG.md` and version metadata, then tag `v0.2.0-beta.1`. The tag workflow builds wheel
and sdist once, installs the wheel in a clean environment, generates a CycloneDX SBOM and SHA-256
checksums, creates provenance attestations, and publishes a prerelease on GitHub. It never uploads
to PyPI.

## GitHub repository settings checklist

- About text: "Local-first scientific workflow and provenance for coding-agent research."
- Topics: `research-software`, `reproducibility`, `scientific-method`, `provenance`, `ai-agents`.
- Upload `docs/assets/social-preview.svg` (or an approved raster export) as the social preview.
- Protect the default branch and require CI and Security checks.
- Route questions through Discussions or `SUPPORT.md`; keep security reports private.
- Review the proposed repository rename from `smairt-template` to `smairt`; do not perform it
  without organization approval.
