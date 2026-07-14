# Literature integrations

SMAIRT keeps its reference index authoritative and treats external services as attributed inputs.
Raw metadata responses are bounded, saved under `references/provenance/`, and never marked
human-verified automatically.

## The simple setup model

Run `smairt setup` once per machine. It stores API keys in the OS keyring (or reads the documented
environment variable) and stores connection details in the operating system's user config
directory. Then, inside a project, use Project setup → Integrations or:

```bash
smairt setup openalex configure default
smairt setup zotero configure default
smairt integration bind openalex default
smairt integration bind zotero default
smairt integration status
smairt integration test zotero
```

The shared `smairt.yaml` records only whether a provider is enabled and whether metadata-only
agent access was explicitly allowed. Account IDs, Zotero library IDs, profile names, and keys are
not written there. A checkout-local binding lives under `.smairt/local/`, which is ignored by Git.
Normal status and test output never prints secret values or account/library identifiers.

## DOI metadata

```bash
smairt reference add-doi 10.1000/example --confirm-remote
smairt reference attach doi-REFERENCE-ID ~/Downloads/paper.pdf
```

Crossref supplies the primary record. `--openalex` requests optional missing-field supplementation
using `OPENALEX_API_KEY` or the configured OS-keyring profile. Existing verified or manually edited
fields are not silently replaced. Crossref and the requested OpenAlex supplement are both fetched
and validated before the index or either raw snapshot is committed. Existing slug-based reference
IDs remain unchanged; only a newly created DOI record receives an opaque `doi-...` ID.

## Zotero

Local Zotero 7 access uses its read-only loopback API and needs no key. Zotero must be running and
its local API enabled. A 403 means Zotero's local API is disabled; a connection failure normally
means the desktop app is not running:

```bash
smairt setup zotero configure default --mode local
smairt integration bind zotero default
smairt integration test zotero
smairt reference import-zotero --item ITEMKEY
smairt reference import-zotero --collection COLLECTIONKEY --limit 500
smairt reference import-zotero --item ITEMKEY --copy-attachment ATTACHMENTKEY --yes
```

Web user or group libraries require a library ID and a read-only API key stored in the OS keyring
or `ZOTERO_API_KEY`. Guided setup validates the key and lets the user choose My Library or a group
without exposing its identifier in shared project files. Collection imports consume paginated
API-v3 responses directly, default to a 500-item bound, and reject limits above 1000. Web
attachment downloads are not implemented. A local PDF copy requires one named attachment and
`--yes`; SMAIRT retrieves it through Zotero's loopback API, validates the PDF and 100 MiB bound,
and commits its snapshots, metadata, checksum, file, and index together.

Metadata import changes the reference index and saves a sanitized provenance snapshot; it does not
copy or expose a PDF. PDF copy is always a separate, explicit action. The terminal receipt names
the changed reference, index/provenance paths, and copied PDF when applicable.

## Read-only MCP

“Agent access” means read-only metadata tools for the selected harness. It never grants PDF,
full-text, filesystem, secret, or write access. Enable it only for the active adapter, for example:

```bash
smairt mcp enable --harness opencode
smairt mcp status --json
```

The server exposes `reference_search`, `reference_get`, `zotero_search`, `zotero_get_item`, and
`zotero_list_collections`. It has no mutation, arbitrary-path, PDF, or full-text tool. Zotero MCP
access is separately opt-in; controlled projects cannot enable it and private projects require an
active contributor plus attributed confirmation.

Enabling or disabling the current state is a no-op. Disable removes only SMAIRT's managed MCP
entry while retaining lifecycle hooks, rules, permissions, and unrelated server definitions.

Third-party Zotero MCP servers may expose write operations. SMAIRT does not install, configure, or
represent them as read-only.

## Upgrading older projects

Schema-v4 projects may contain profile or library identifiers in tracked `smairt.yaml` history.
The guided v5 migration moves current connection identity into user-local setup and checkout-local
bindings, creates the normal SMAIRT migration backup, and removes those fields from the current
shared file. Migration cannot erase old Git commits; review repository history before publishing a
repository that previously contained sensitive identifiers.
