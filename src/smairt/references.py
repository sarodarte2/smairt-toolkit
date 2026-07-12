"""Local reference-library indexing with explicit human metadata verification."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import yaml
from pypdf import PdfReader

from smairt.models import ReferenceRecord
from smairt.utils import sha256_file, slugify

DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)


def load_index(root: Path) -> list[ReferenceRecord]:
    payload = yaml.safe_load((root / "references/index.yaml").read_text(encoding="utf-8")) or {}
    return [ReferenceRecord.model_validate(item) for item in payload.get("references", [])]


def save_index(root: Path, records: list[ReferenceRecord]) -> None:
    payload = {
        "references": [
            record.model_dump(mode="json", exclude_none=True) for record in records
        ]
    }
    (root / "references/index.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )


def inspect_pdf(source: Path) -> dict[str, object]:
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
        doi=doi,
        local_path=str(destination.relative_to(root / "references")),
        sha256=digest,
        metadata_verified=verified,
    )
    records.append(record)
    save_index(root, records)
    return record


def unindexed_pdfs(root: Path) -> list[Path]:
    records = load_index(root)
    known = {record.sha256 for record in records}
    return [
        path
        for path in sorted((root / "references/pdfs").glob("*.pdf"))
        if sha256_file(path) not in known
    ]
