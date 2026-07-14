# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Beta schemas
and interfaces may still break between prereleases.

## [0.2.0-beta.1] - Unreleased

### Added

- Research-to-publication records, corrections, summaries, provenance, and integrity manifests.
- Codex, Zoo Code, Cline, OpenCode, and Cursor adapters with truthful capability metadata.
- Checkout mutation locks and recoverable multi-file transaction journals.
- Terminal-state run capture for completion, failure, launch failure, and interruption.
- Explicit cached visibility refresh and experimental Standard/Strict safety modes.
- Responsive anchored terminal workspace, offline doctor, versioned JSON, production CI, and
  attested releases.
- Separate global setup, project creation, and project dashboard experiences with circular menu
  navigation and context-aware suggested prompts.
- User-local OpenAlex/Zotero profiles and checkout-local bindings that keep account and library
  identifiers out of shared project configuration.
- Responsive anchored terminal frames, original SMAIRT ASCII branding, reduced-motion controls,
  and maintained OpenCode and Cursor adapters.

### Changed

- Incompatible beta project schemas are rejected with a recreate/export message.
- Cline now uses `TaskStart`, `TaskResume`, `PreToolUse`, and `PreCompact` lifecycle hooks.
- Unused `jinja2` was removed.
- Project schema v5 moves integration identity to local state, simplifies health and references,
  and defaults new Conda environment names to the project slug.
- Project schema v6 adds the five-harness vocabulary and a bounded shared hook-policy contract.

[0.2.0-beta.1]: https://github.com/PNNL-CompBio/smairt-template/releases/tag/v0.2.0-beta.1
