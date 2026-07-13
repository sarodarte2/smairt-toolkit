# Literature integrations

SMAIRT keeps its reference index authoritative and treats external services as attributed inputs.
Raw metadata responses are bounded, saved under `references/provenance/`, and never marked
human-verified automatically.

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

Local Zotero 7 access uses its read-only loopback API and needs no key:

```bash
smairt integration zotero configure --mode local
smairt integration zotero test
smairt reference import-zotero --item ITEMKEY
smairt reference import-zotero --collection COLLECTIONKEY --limit 500
smairt reference import-zotero --item ITEMKEY --copy-attachment ATTACHMENTKEY --yes
```

Web user or group libraries require a library ID and a read-only API key stored in the OS keyring
or `ZOTERO_API_KEY`. Collection imports consume paginated API-v3 responses directly, default to a
500-item bound, and reject limits above 1000. Web attachment downloads are not implemented. A
local PDF copy requires one named attachment and `--yes`; SMAIRT retrieves it through Zotero's
loopback API, validates the PDF and 100 MiB bound, and commits its snapshots, metadata, checksum,
file, and index together.

## Read-only MCP

`smairt mcp enable --harness codex` or `--harness zoo` changes only the active managed adapter.
The server exposes `reference_search`, `reference_get`, `zotero_search`, `zotero_get_item`, and
`zotero_list_collections`. It has no mutation, arbitrary-path, PDF, or full-text tool. Zotero MCP
access is separately opt-in; controlled projects cannot enable it and private projects require an
active contributor plus attributed confirmation.

Enabling or disabling the current state is a no-op. Disable removes SMAIRT's Codex server table or
Zoo server entry completely while retaining Codex hooks and unrelated Zoo MCP servers.

Third-party Zotero MCP servers may expose write operations. SMAIRT does not install, configure, or
represent them as read-only.
