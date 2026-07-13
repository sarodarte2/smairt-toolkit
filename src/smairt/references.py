"""Local reference-library indexing with explicit human metadata verification."""

from __future__ import annotations

import json
import os
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml
from pypdf import PdfReader

from smairt.models import ReferenceRecord, utc_now
from smairt.utils import sha256_file, slugify

DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)


def normalize_doi(value: str) -> str:
    """Normalize and validate DOI strings from common URL and label forms."""
    normalized = value.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        normalized = normalized.removeprefix(prefix)
    if not DOI_PATTERN.fullmatch(normalized):
        raise ValueError(f"invalid DOI: {value}")
    return normalized


def load_index(root: Path) -> list[ReferenceRecord]:
    """Load and validate all reference records from the project index."""
    payload = yaml.safe_load((root / "references/index.yaml").read_text(encoding="utf-8")) or {}
    return [ReferenceRecord.model_validate(item) for item in payload.get("references", [])]


def save_index(root: Path, records: list[ReferenceRecord]) -> None:
    """Persist validated reference records in a stable YAML representation."""
    payload = {
        "references": [record.model_dump(mode="json", exclude_none=True) for record in records]
    }
    (root / "references/index.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )


def inspect_pdf(source: Path) -> dict[str, object]:
    """Extract best-effort PDF metadata for explicit researcher confirmation."""
    reader = PdfReader(str(source))
    metadata = reader.metadata or {}
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


def add_reference(
    root: Path,
    source: Path,
    *,
    title: str,
    authors: list[str] | None = None,
    year: int | None = None,
    doi: str | None = None,
    verified: bool = False,
    link: bool = False,
) -> ReferenceRecord:
    """Copy or link a PDF locally and append its verified metadata to the index."""
    source = source.expanduser().resolve()
    if source.suffix.lower() != ".pdf" or not source.exists():
        raise ValueError("reference must be an existing PDF")
    records = load_index(root)
    digest = sha256_file(source)
    if any(record.sha256 == digest for record in records):
        raise ValueError("this PDF is already indexed")
    record_id = slugify(f"{year or 'undated'}-{title}")[:80]
    destination = root / "references/pdfs" / f"{record_id}.pdf"
    if link:
        destination.symlink_to(source)
    else:
        shutil.copy2(source, destination)
    record = ReferenceRecord(
        id=record_id,
        title=title,
        authors=authors or [],
        year=year,
        doi=normalize_doi(doi) if doi else None,
        local_path=str(destination.relative_to(root / "references")),
        sha256=digest,
        metadata_verified=verified,
        citation_key=slugify(
            f"{(authors or ['anon'])[0].split()[-1]}-{year or 'nd'}-{title.split()[0]}"
        )
        if title.split()
        else record_id,
        identifiers={"doi": normalize_doi(doi)} if doi else {},
        verification_status="verified" if verified else "unverified",
        source_provenance=[{"source": "local_pdf", "captured_at": utc_now(), "sha256": digest}],
    )
    records.append(record)
    save_index(root, records)
    return record


def get_reference(root: Path, identifier: str) -> ReferenceRecord:
    """Return one indexed reference by stable identifier."""
    record = next((item for item in load_index(root) if item.id == identifier), None)
    if record is None:
        raise ValueError(f"unknown reference: {identifier}")
    return record


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
    record.verification_status = "unverified"
    record.metadata_verified = False
    save_index(root, records)
    return record


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
    if record.pages and not re.fullmatch(r"[A-Za-z]?\d+(?:[-–][A-Za-z]?\d+)?", record.pages):
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
    record.verification_status = "verified"
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
    request = urllib.request.Request(url, headers={"User-Agent": "SMAIRT/0.1 (mailto:unknown)"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Crossref unavailable; local metadata preserved: {exc}") from exc
    snapshot = (
        root / "references/provenance" / identifier / f"crossref-{utc_now().replace(':', '')}.json"
    )
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(json.dumps(raw, indent=2) + "\n")
    message = raw.get("message", {})
    record.title = (message.get("title") or [record.title])[0]
    record.authors = [
        " ".join(filter(None, (a.get("given"), a.get("family")))) for a in message.get("author", [])
    ] or record.authors
    record.venue = (message.get("container-title") or [record.venue])[0]
    record.volume = message.get("volume") or record.volume
    record.issue = message.get("issue") or record.issue
    record.pages = message.get("page") or record.pages
    record.publisher = message.get("publisher") or record.publisher
    record.url = message.get("URL") or record.url
    record.source_provenance.append(
        {
            "source": "crossref",
            "captured_at": utc_now(),
            "snapshot": str(snapshot.relative_to(root)),
        }
    )
    record.verification_status = "enriched_unverified"
    save_index(root, records)
    return record


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
    request = urllib.request.Request(url, headers={"User-Agent": "SMAIRT/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"OpenAlex unavailable; existing metadata preserved: {exc}") from exc
    snapshot = (
        root / "references/provenance" / identifier / f"openalex-{utc_now().replace(':', '')}.json"
    )
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(json.dumps(raw, indent=2) + "\n")
    location = raw.get("primary_location") or {}
    source = location.get("source") or {}
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
    record.verification_status = "enriched_unverified"
    save_index(root, records)
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
