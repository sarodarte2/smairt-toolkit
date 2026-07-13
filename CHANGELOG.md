# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Beta schemas
and interfaces may still break between prereleases.

## [0.2.0-beta.1] - Unreleased

### Added

- Research-to-publication records, corrections, summaries, provenance, and integrity manifests.
- Codex, Zoo Code, and Cline adapters with truthful capability metadata.
- Checkout mutation locks and recoverable multi-file transaction journals.
- Terminal-state run capture for completion, failure, launch failure, and interruption.
- Explicit cached visibility refresh and experimental Standard/Strict safety modes.
- Responsive TUI, offline doctor, versioned JSON, production CI, and attested releases.

### Changed

- Incompatible beta project schemas are rejected with a recreate/export message.
- Cline `PreCompact` was replaced by implemented `TaskStart` and `TaskResume` hooks.
- Unused `jinja2` was removed.

[0.2.0-beta.1]: https://github.com/PNNL-CompBio/smairt-template/releases/tag/v0.2.0-beta.1
