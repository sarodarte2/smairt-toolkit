"""Local reference-library indexing with explicit human metadata verification."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import yaml
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from smairt import __version__
from smairt.errors import ExternalServiceError
from smairt.locking import mutating
from smairt.models import ReferenceRecord, VerificationStatus, utc_now
from smairt.transactions import FileTransaction
from smairt.utils import (
    atomic_write,
    ensure_within,
    sha256_file,
    slugify,
    validate_identifier,
)

DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
MAX_METADATA_BYTES = 10 * 1024 * 1024


def _index_yaml(records: list[ReferenceRecord]) -> str:
    """Render a validated deterministic reference index for atomic transactions."""
    payload = {
        "references": [record.model_dump(mode="json", exclude_none=True) for record in records]
    }
    return yaml.safe_dump(payload, sort_keys=False)


def normalize_doi(value: str) -> str:
    """Normalize and validate DOI strings from common URL and label forms."""
    normalized = value.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        normalized = normalized.removeprefix(prefix)
    if not DOI_PATTERN.fullmatch(normalized):
        raise ValueError(f"invalid DOI: {value}")
    return normalized


def _read_metadata_response(response: Any, service: str) -> object:
    """Decode one bounded metadata response without trusting server size claims."""
    headers = getattr(response, "headers", None)
    length = headers.get("Content-Length") if headers is not None else None
    if length is not None:
        try:
            if int(length) > MAX_METADATA_BYTES:
                raise ExternalServiceError(f"{service} response exceeded the size limit")
        except ValueError as exc:
            raise ExternalServiceError(f"{service} returned an invalid Content-Length") from exc
    try:
        body = response.read(MAX_METADATA_BYTES + 1)
    except TypeError:  # Simple test doubles and older file-like implementations.
        body = response.read()
    if not isinstance(body, bytes) or len(body) > MAX_METADATA_BYTES:
        raise ExternalServiceError(f"{service} response exceeded the size limit")
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
        raise ExternalServiceError(f"{service} returned malformed JSON") from exc


def _first_string(value: object, fallback: str | None = None) -> str | None:
    """Return a scalar or first-list string from a metadata service field."""
    if isinstance(value, str):
        return value
    if isinstance(value, list) and value and isinstance(value[0], str):
        return value[0]
    return fallback


def load_index(root: Path) -> list[ReferenceRecord]:
    """Load and validate all reference records from the project index."""
    payload = yaml.safe_load((root / "references/index.yaml").read_text(encoding="utf-8")) or {}
    return [ReferenceRecord.model_validate(item) for item in payload.get("references", [])]


@mutating("reference index save")
def save_index(root: Path, records: list[ReferenceRecord]) -> None:
    """Persist validated reference records in a stable YAML representation."""
    atomic_write(root / "references/index.yaml", _index_yaml(records))


def inspect_pdf(source: Path) -> dict[str, Any]:
    """Extract best-effort PDF metadata for explicit researcher confirmation."""
    if source.stat().st_size == 0:
        raise ValueError("PDF is empty")
    if source.stat().st_size > 100 * 1024 * 1024:
        raise ValueError("PDF exceeds the 100 MiB local inspection limit")
    try:
        reader = PdfReader(str(source), strict=False)
    except (PdfReadError, OSError) as exc:
        raise ValueError("PDF is corrupt or unreadable") from exc
    if reader.is_encrypted:
        raise ValueError("encrypted PDFs are not supported")
    if not reader.pages:
        raise ValueError("PDF contains no pages")
    metadata: Any = reader.metadata or {}
    title = str(metadata.get("/Title") or source.stem).strip()
    author = str(metadata.get("/Author") or "").strip()
    text = "\n".join((page.extract_text() or "")[:5000] for page in reader.pages[:5])
    match = DOI_PATTERN.search(text)
    return {
        "title": title,
        "authors": [item.strip() for item in author.split(";") if item.strip()],
        "doi": match.group(0).rstrip(".,;)") if match else None,
        "pages": len(reader.pages),
    }


@mutating("reference add")
def add_reference(
    root: Path,
    source: Path,
    *,
    title: str,
    authors: list[str] | None = None,
    year: int | None = None,
    doi: str | None = None,
    link: bool = False,
) -> ReferenceRecord:
    """Copy a PDF and append unverified metadata through one transaction."""
    root = root.resolve()
    source = source.expanduser().absolute()
    if source.is_symlink() or any(parent.is_symlink() for parent in source.parents):
        raise ValueError("reference source must not traverse a symlink")
    source = source.resolve()
    if source.suffix.lower() != ".pdf" or not source.exists():
        raise ValueError("reference must be an existing PDF")
    if link:
        raise ValueError("linked references are not supported by the recoverable beta index")
    records = load_index(root)
    digest = sha256_file(source)
    if any(record.sha256 == digest for record in records):
        raise ValueError("this PDF is already indexed")
    record_id = slugify(f"{year or 'undated'}-{title}")[:80]
    destination = root / "references/pdfs" / f"{record_id}.pdf"
    ensure_within(root, destination)
    parent = destination.parent
    while parent != root.resolve():
        if parent.is_symlink():
            raise ValueError("reference destination must not traverse a symlink")
        parent = parent.parent
    citation_key = (
        slugify(f"{(authors or ['anon'])[0].split()[-1]}-{year or 'nd'}-{title.split()[0]}")
        if title.split()
        else record_id
    )
    normalized_doi = normalize_doi(doi) if doi else None
    if any(item.id == record_id for item in records):
        raise ValueError(f"duplicate reference ID: {record_id}")
    if any(item.citation_key == citation_key for item in records):
        raise ValueError(f"duplicate citation key: {citation_key}")
    if normalized_doi and any(item.doi == normalized_doi for item in records):
        raise ValueError(f"duplicate DOI: {normalized_doi}")
    if os.path.lexists(destination):
        raise ValueError(f"reference destination already exists: {destination.name}")
    record = ReferenceRecord(
        id=record_id,
        title=title,
        authors=authors or [],
        year=year,
        doi=normalized_doi,
        local_path=str(destination.relative_to(root / "references")),
        sha256=digest,
        metadata_verified=False,
        citation_key=citation_key,
        identifiers={"doi": normalized_doi} if normalized_doi else {},
        verification_status=VerificationStatus.UNVERIFIED,
        source_provenance=[{"source": "local_pdf", "captured_at": utc_now(), "sha256": digest}],
    )
    records.append(record)
    transaction = FileTransaction(root, "reference add")
    transaction.stage_bytes(destination, source.read_bytes(), mode=0o644)
    transaction.stage_text(root / "references/index.yaml", _index_yaml(records))
    transaction.commit()
    return record


def get_reference(root: Path, identifier: str) -> ReferenceRecord:
    """Return one indexed reference by stable identifier."""
    validate_identifier(identifier, label="reference ID")
    record = next((item for item in load_index(root) if item.id == identifier), None)
    if record is None:
        raise ValueError(f"unknown reference: {identifier}")
    return record


@mutating("reference edit")
def edit_reference(
    root: Path, identifier: str, field: str, value: str, contributor: str
) -> ReferenceRecord:
    """Edit an allowed metadata field and append field-level provenance."""
    records = load_index(root)
    record = next((item for item in records if item.id == identifier), None)
    if record is None:
        raise ValueError(f"unknown reference: {identifier}")
    if field not in ReferenceRecord.model_fields or field in {"id", "sha256", "local_path"}:
        raise ValueError(f"field cannot be edited: {field}")
    previous = getattr(record, field)
    if field == "doi":
        value = normalize_doi(value)
    parsed: object = int(value) if field == "year" else value
    setattr(record, field, parsed)
    record.edit_history.append(
        {
            "field": field,
            "previous": previous,
            "value": parsed,
            "contributor": contributor,
            "edited_at": utc_now(),
        }
    )
    record.verification_status = VerificationStatus.UNVERIFIED
    record.metadata_verified = False
    save_index(root, records)
    return record


@mutating("reference verify")
def verify_reference(root: Path, identifier: str, contributor: str) -> ReferenceRecord:
    """Validate required metadata, DOI, pages, and duplicates before verification."""
    records = load_index(root)
    record = next((item for item in records if item.id == identifier), None)
    if record is None:
        raise ValueError(f"unknown reference: {identifier}")
    if not record.title.strip() or not record.authors:
        raise ValueError("reference requires title and authors before verification")
    if record.doi:
        record.doi = normalize_doi(record.doi)
    if record.pages and not re.fullmatch(r"[A-Za-z]?\d+(?:[-\u2013][A-Za-z]?\d+)?", record.pages):
        raise ValueError("invalid page range")
    duplicate_keys = [
        r.id for r in records if r.id != record.id and r.citation_key == record.citation_key
    ]
    duplicate_dois = [
        r.id for r in records if r.id != record.id and record.doi and r.doi == record.doi
    ]
    if duplicate_keys or duplicate_dois:
        raise ValueError("duplicate citation key or DOI")
    record.metadata_verified = True
    record.verification_status = VerificationStatus.VERIFIED
    record.edit_history.append(
        {
            "field": "verification_status",
            "value": "verified",
            "contributor": contributor,
            "edited_at": utc_now(),
        }
    )
    save_index(root, records)
    return record


@mutating("reference enrich crossref")
def enrich_reference(
    root: Path, identifier: str, *, confirm_remote: bool = False
) -> ReferenceRecord:
    """Merge deterministic Crossref DOI metadata and preserve the raw response."""
    records = load_index(root)
    _require_remote_permission(root, confirm_remote)
    record = next((item for item in records if item.id == identifier), None)
    if record is None or not record.doi:
        raise ValueError("reference enrichment requires a DOI")
    url = "https://api.crossref.org/works/" + urllib.parse.quote(normalize_doi(record.doi))
    request = urllib.request.Request(  # noqa: S310 - URL is constructed from HTTPS literal
        url, headers={"User-Agent": f"SMAIRT/{__version__}"}
    )
    try:
        with urllib.request.urlopen(  # noqa: S310 - Request URL is HTTPS-only above
            request, timeout=15
        ) as response:
            if getattr(response, "status", 200) != 200:
                raise ExternalServiceError("Crossref returned an unsuccessful response")
            raw = _read_metadata_response(response, "Crossref")
    except urllib.error.HTTPError as exc:
        raise ExternalServiceError(f"Crossref request failed with HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError):
        raise ExternalServiceError(
            "Crossref is unavailable; local metadata was preserved"
        ) from None
    if not isinstance(raw, dict) or not isinstance(raw.get("message"), dict):
        raise ExternalServiceError("Crossref returned an unexpected record shape")
    snapshot = (
        root / "references/provenance" / identifier / f"crossref-{utc_now().replace(':', '')}.json"
    )
    message = raw.get("message", {})
    authors = message.get("author", [])
    if not isinstance(authors, list) or not all(isinstance(author, dict) for author in authors):
        raise ExternalServiceError("Crossref returned malformed author metadata")
    record.title = _first_string(message.get("title"), record.title) or record.title
    record.authors = [
        " ".join(
            part
            for part in (author.get("given"), author.get("family"))
            if isinstance(part, str) and part
        )
        for author in authors
    ] or record.authors
    record.venue = _first_string(message.get("container-title"), record.venue)
    for field, key in (
        ("volume", "volume"),
        ("issue", "issue"),
        ("pages", "page"),
        ("publisher", "publisher"),
        ("url", "URL"),
    ):
        value = message.get(key)
        if value is not None and not isinstance(value, str):
            raise ExternalServiceError(f"Crossref returned malformed {key} metadata")
        if value:
            setattr(record, field, value)
    record.source_provenance.append(
        {
            "source": "crossref",
            "captured_at": utc_now(),
            "snapshot": str(snapshot.relative_to(root)),
        }
    )
    record.verification_status = VerificationStatus.ENRICHED_UNVERIFIED
    transaction = FileTransaction(root, "reference enrich crossref")
    transaction.stage_text(snapshot, json.dumps(raw, indent=2, sort_keys=True) + "\n")
    transaction.stage_text(root / "references/index.yaml", _index_yaml(records))
    transaction.commit()
    return record


@mutating("reference enrich openalex")
def enrich_openalex(
    root: Path,
    identifier: str,
    api_key: str | None = None,
    *,
    confirm_remote: bool = False,
) -> ReferenceRecord:
    """Optionally enrich a DOI record from OpenAlex without replacing Crossref authority."""
    records = load_index(root)
    _require_remote_permission(root, confirm_remote)
    record = next((item for item in records if item.id == identifier), None)
    if record is None or not record.doi:
        raise ValueError("OpenAlex enrichment requires a DOI")
    key = api_key or os.environ.get("OPENALEX_API_KEY")
    if not key:
        raise ValueError("OpenAlex enrichment requires OPENALEX_API_KEY")
    external_id = urllib.parse.quote(f"doi:{normalize_doi(record.doi)}", safe=":")
    url = f"https://api.openalex.org/works/{external_id}?" + urllib.parse.urlencode(
        {"api_key": key}
    )
    request = urllib.request.Request(  # noqa: S310 - URL is constructed from HTTPS literal
        url, headers={"User-Agent": f"SMAIRT/{__version__}"}
    )
    try:
        with urllib.request.urlopen(  # noqa: S310 - Request URL is HTTPS-only above
            request, timeout=15
        ) as response:
            if getattr(response, "status", 200) != 200:
                raise ExternalServiceError("OpenAlex returned an unsuccessful response")
            raw = _read_metadata_response(response, "OpenAlex")
    except urllib.error.HTTPError as exc:
        raise ExternalServiceError(f"OpenAlex request failed with HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError):
        raise ExternalServiceError(
            "OpenAlex is unavailable; local metadata was preserved"
        ) from None
    if not isinstance(raw, dict) or not raw.get("id"):
        raise ExternalServiceError("OpenAlex returned an unexpected or empty record")
    snapshot = (
        root / "references/provenance" / identifier / f"openalex-{utc_now().replace(':', '')}.json"
    )
    location = raw.get("primary_location") or {}
    if not isinstance(location, dict):
        raise ExternalServiceError("OpenAlex returned malformed location metadata")
    source = location.get("source") or {}
    if not isinstance(source, dict):
        raise ExternalServiceError("OpenAlex returned malformed source metadata")
    # OpenAlex supplements missing fields. Crossref-derived values remain authoritative.
    record.publication_date = record.publication_date or raw.get("publication_date")
    record.venue = record.venue or source.get("display_name")
    record.url = record.url or location.get("landing_page_url")
    record.license = record.license or location.get("license")
    record.identifiers["openalex"] = str(raw.get("id", ""))
    record.source_provenance.append(
        {
            "source": "openalex",
            "captured_at": utc_now(),
            "snapshot": str(snapshot.relative_to(root)),
        }
    )
    record.verification_status = VerificationStatus.ENRICHED_UNVERIFIED
    transaction = FileTransaction(root, "reference enrich openalex")
    transaction.stage_text(snapshot, json.dumps(raw, indent=2, sort_keys=True) + "\n")
    transaction.stage_text(root / "references/index.yaml", _index_yaml(records))
    transaction.commit()
    return record


def _require_remote_permission(root: Path, confirmed: bool) -> None:
    """Require explicit consent before Strict protected-project metadata queries."""
    from smairt.models import SmairtConfig

    config = SmairtConfig.load(root / "smairt.yaml")
    protected = config.data.classification.value in {"private", "controlled"}
    if config.safety_mode == "strict" and protected and not confirmed:
        raise ValueError("Strict protected projects require --confirm-remote for metadata queries")


def export_references(root: Path, format_name: str) -> str:
    """Export verified structured records for citation tooling."""
    records = load_index(root)
    unverified = [record.id for record in records if record.verification_status != "verified"]
    if unverified:
        raise ValueError("reference export requires verified records: " + ", ".join(unverified))
    if format_name == "csl-json":
        import json

        items = [
            {
                "id": r.citation_key or r.id,
                "type": r.document_type,
                "title": r.title,
                "author": [{"literal": a} for a in r.authors],
                "issued": {"date-parts": [[r.year]]} if r.year else None,
                "DOI": r.doi,
                "container-title": r.venue,
                "volume": r.volume,
                "issue": r.issue,
                "page": r.pages,
                "URL": r.url,
            }
            for r in records
        ]
        return json.dumps(items, indent=2, ensure_ascii=False) + "\n"
    if format_name != "bibtex":
        raise ValueError("format must be bibtex or csl-json")
    entries = []
    for r in records:
        fields = {
            "title": r.title,
            "author": " and ".join(r.authors),
            "year": str(r.year) if r.year else None,
            "doi": r.doi,
            "journal": r.venue,
            "volume": r.volume,
            "number": r.issue,
            "pages": r.pages,
            "url": r.url,
        }
        body = ",\n".join(f"  {key} = {{{value}}}" for key, value in fields.items() if value)
        entries.append(f"@article{{{r.citation_key or r.id},\n{body}\n}}")
    return "\n\n".join(entries) + ("\n" if entries else "")


def unindexed_pdfs(root: Path) -> list[Path]:
    """List local reference PDFs whose checksums are absent from the index."""
    records = load_index(root)
    known = {record.sha256 for record in records}
    return [
        path
        for path in sorted((root / "references/pdfs").glob("*.pdf"))
        if sha256_file(path) not in known
    ]
