# Literature integrations

SMAIRT keeps its own reference index authoritative and treats external services as attributed
inputs. Remote metadata snapshots are bounded and are not marked human-verified automatically.

## Connection model

There are three separate layers:

1. `smairt setup` creates a user-local provider profile and stores any secret in the OS keyring.
2. A project binds to a named local profile under ignored `.smairt/local/` state.
3. A researcher explicitly invokes a remote lookup, import, or download.

Shared `smairt.yaml` policy never contains API keys, account IDs, library IDs, or local profile
names.

```bash
smairt setup openalex configure default
smairt setup semantic-scholar configure default
smairt setup zotero configure default
smairt setup unpaywall configure default --email you@example.org
smairt integration bind openalex default
smairt integration bind semantic_scholar default
smairt integration bind zotero default
smairt integration bind unpaywall default
smairt integration status
```

## Provider responsibilities

| Provider | Purpose | Network and mutation boundary |
| --- | --- | --- |
| Crossref | Primary DOI metadata | Explicit DOI import; saves attributed metadata |
| DataCite | DOI fallback | Used only after a typed Crossref not-found response |
| Zotero | Search a local or Web library and import selected metadata | Read-only provider access; a local PDF copy is separate and confirmed |
| OpenAlex | Broad discovery and citation graph context | Explicit remote search; results remain provisional |
| Semantic Scholar | Relevance search, citation trails, and recommendations | Explicit remote search; public calls may work without a key |
| Unpaywall | Resolve lawful open-access locations | Explicit lookup; download requires a separate confirmation |

Timeouts, rate limits, and provider failures do not silently change authority or trigger broad
fallback behavior.

## DOI metadata and local PDFs

```bash
smairt reference add-doi 10.1000/example --confirm-remote
smairt reference attach doi-REFERENCE-ID ~/Downloads/paper.pdf
smairt reference inspect doi-REFERENCE-ID
```

Crossref supplies the primary DOI record. Existing human-verified or manually corrected fields are
not silently replaced. A metadata-only record may later receive one explicit local attachment;
attachment path and checksum are stored together.

## Zotero

Zotero Desktop 7 local access uses its read-only loopback API and needs no API key. Zotero must be
running with the local API enabled.

```bash
smairt setup zotero configure default --mode local
smairt integration bind zotero default
smairt integration test zotero
smairt reference import-zotero --item ITEMKEY
smairt reference import-zotero --collection COLLECTIONKEY --limit 500
```

Web user or group libraries need a library ID and read-only API key stored outside the project.
Collection import is bounded. Metadata import changes the reference index and stores a sanitized
provenance snapshot; it does not expose or copy a PDF.

A local attachment copy is a distinct confirmed action:

```bash
smairt reference import-zotero --item ITEMKEY \
  --copy-attachment ATTACHMENTKEY --yes
```

SMAIRT validates the PDF, enforces a 100 MiB bound, and commits metadata, snapshots, checksum, and
file atomically. Web attachment download is not implemented.

## Literature discovery and access

```bash
smairt literature search "topic" --provider all --limit 20 --json
smairt literature related REFERENCE_ID --direction references
smairt literature recommend REFERENCE_ID --limit 20 --json
smairt literature access REFERENCE_ID --confirm-remote
```

Discovery abstracts, citation counts, and landing URLs are context, not verified project metadata.
Only selected DOI-bearing candidates can be imported automatically, and import returns to the DOI
authority path.

Before a PDF download, SMAIRT shows the domain, license, version, and access status. Downloads use
HTTPS, bounded redirects, address checks at each hop, a timeout and size limit, PDF validation, and
an atomic project update. The user still decides whether the source and license are appropriate.

## Metadata-only MCP

Optional agent access exposes reference metadata, not the project filesystem:

```bash
smairt mcp enable --harness codex
smairt mcp status --json
```

The server provides five bounded tools: `reference_search`, `reference_get`, `zotero_search`,
`zotero_get_item`, and `zotero_list_collections`. It has no mutation, arbitrary-path, PDF,
full-text, or credential tool. Zotero MCP access is separately opt-in and unavailable for
controlled projects.

Third-party Zotero MCP servers may have different permissions. SMAIRT does not install or describe
them as part of its read-only boundary.

## Privacy and older projects

Normal project status, validation, doctor, and menu refreshes do not contact these services.
Provider tests and research queries are explicit.

Older schema-v4 projects may have stored connection identity in tracked history. Migration removes
those fields from the current file but cannot erase prior Git commits. Review repository history
before publishing an older project.
