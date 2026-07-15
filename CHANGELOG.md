# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Beta schemas
and interfaces may still break between prereleases.

## [0.2.0-beta.2] - Unreleased

### Added

- One project updater that previews and applies every required schema, managed-guidance, and active
  harness-adapter step from the CLI or **Health & updates** menu.
- Machine-local color themes, a mark-only PNNL-inspired preset, sanitized custom ASCII logos, and
  user-setup schema v4.
- A project-first human-run demo that ends at verified evidence and one approved claim.

### Changed

- Doctor now separates blocking health, recommended maintenance, and sharing readiness.
- Project and global setup menus now use researcher-facing categories and keep provider setup,
  credentials, connection tests, and removal together.
- Responsive menus expose a Back row, Left/Escape one-level navigation, Ctrl-C exit, narrow summary
  rendering, and theme-aware accents without changing terminal font settings.

## [0.2.0-beta.1]

### Added

- Research-to-publication records, corrections, summaries, provenance, and integrity manifests.
- Codex, Zoo Code, Cline, OpenCode, Cursor, and Claude Code adapters with capability metadata.
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
- Six focused research workflows, native read-only adversarial reviewers, a responsive harness
  chooser, and per-harness setup guides.
- Keyless Zotero browsing, DataCite DOI fallback, OpenAlex discovery, explicit Unpaywall access,
  secure PDF retrieval, and previewed deterministic PDF organization.
- Semantic Scholar search, citation traversal, and recommendations with optional user-local keys.
- Fuzzy in-menu command suggestions, standard shell completion, and faster responsive redraws.
- Schema-8 protocol/result contracts, immutable protocol snapshots, and checksum-backed
  interpretation gates.
- Optional typed Slurm submission through native commands or an existing OpenSSH host alias.
- A local enzyme-kinetics installation-to-evidence demo with independently checked correct results.

### Changed

- Incompatible beta project schemas are rejected with a recreate/export message.
- Cline now uses `TaskStart`, `TaskResume`, `PreToolUse`, and `PreCompact` lifecycle hooks.
- Unused `jinja2` was removed.
- Project schema v5 moves integration identity to local state, simplifies health and references,
  and defaults new Conda environment names to the project slug.
- Project schema v6 adds the five-harness vocabulary and a bounded shared hook-policy contract.
- Harness adapter v6 adds native skill, command, mode, hook, permission, and subagent integrations
  while preserving each harness's built-in modes.
- Project schema and harness adapter v7 add Claude Code and merge-safe shared JSON ownership.
- Project schema v8 adds scientific protocol enforcement and optional compute-job records; the
  harness adapter format remains v7.

[0.2.0-beta.2]: https://github.com/PNNL-CompBio/smairt-template/releases/tag/v0.2.0-beta.2
[0.2.0-beta.1]: https://github.com/PNNL-CompBio/smairt-template/releases/tag/v0.2.0-beta.1
