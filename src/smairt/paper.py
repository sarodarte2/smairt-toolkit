"""Paper-element provenance validation."""

from __future__ import annotations

import html
import json
import zipfile
from pathlib import Path

import yaml

from smairt.integrity import verify_run
from smairt.models import utc_now
from smairt.provenance import record_event, require_contributor
from smairt.references import load_index
from smairt.utils import sha256_file, slugify


def accepted_runs(root: Path) -> dict[str, dict[str, object]]:
    """Return accepted, current run selections keyed by immutable run ID."""
    accepted: dict[str, dict[str, object]] = {}
    for selection in (root / "analysis").glob("*/selection.yaml"):
        payload = yaml.safe_load(selection.read_text()) or {}
        if payload.get("status") == "ACCEPTED" and payload.get("run_id"):
            accepted[str(payload["run_id"])] = payload
    return accepted


def validate_paper(root: Path) -> list[str]:
    """Ensure every paper element points to unique, currently accepted evidence."""
    manifest = root / "paper/manifest.yaml"
    payload = yaml.safe_load(manifest.read_text()) or {}
    elements = payload.get("elements", [])
    if not isinstance(elements, list):
        return ["paper manifest elements must be a list"]
    accepted = accepted_runs(root)
    errors: list[str] = []
    identifiers: set[str] = set()
    for index, element in enumerate(elements, start=1):
        if not isinstance(element, dict):
            errors.append(f"paper element {index} must be a mapping")
            continue
        identifier = str(element.get("id", ""))
        if not identifier:
            errors.append(f"paper element {index} is missing id")
        elif identifier in identifiers:
            errors.append(f"duplicate paper element id: {identifier}")
        identifiers.add(identifier)
        run_id = str(element.get("run_id", ""))
        if run_id not in accepted:
            display_run = run_id or "[missing]"
            errors.append(f"{identifier or index} references non-accepted run {display_run}")
    for claim_path in sorted((root / "paper/claims").glob("*.json")):
        claim = json.loads(claim_path.read_text())
        if claim.get("status") != "approved":
            continue
        for evidence_id in claim.get("evidence_ids", []):
            evidence_path = root / "paper/evidence" / f"{evidence_id}.json"
            if not evidence_path.exists():
                errors.append(f"approved claim {claim['id']} has missing evidence {evidence_id}")
                continue
            evidence = json.loads(evidence_path.read_text())
            if evidence.get("status") != "current" or evidence.get("run_id") not in accepted:
                errors.append(f"approved claim {claim['id']} has stale evidence {evidence_id}")
        references = {item.id: item for item in load_index(root)}
        for reference_id in claim.get("reference_ids", []):
            if (
                reference_id not in references
                or references[reference_id].verification_status != "verified"
            ):
                errors.append(
                    f"approved claim {claim['id']} has unverified citation {reference_id}"
                )
    return errors


def create_evidence_card(
    root: Path,
    run_id: str,
    *,
    purpose: str,
    observed_result: str,
    limitations: str,
    decision: str,
    relevance: str = "",
) -> Path:
    """Freeze one accepted run into a contributor-attributed evidence card."""
    contributor = require_contributor(root)
    accepted = accepted_runs(root)
    if run_id not in accepted:
        raise ValueError("evidence cards require a currently accepted run")
    verification = verify_run(root, run_id)
    if not verification["ok"]:
        raise ValueError("run integrity verification failed")
    run_path = next((root / "results").glob(f"EXPERIMENT_*/ITERATION_*/{run_id}/run.json"))
    payload = {
        "schema_version": 1,
        "id": f"evidence-{run_id.lower()}",
        "run_id": run_id,
        "purpose": purpose,
        "observed_result": observed_result,
        "limitations": limitations,
        "decision": decision,
        "possible_paper_relevance": relevance,
        "contributor": contributor.id,
        "created_at": utc_now(),
        "run_record_sha256": sha256_file(run_path),
        "status": "current",
    }
    path = root / "paper/evidence" / f"{payload['id']}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n")
    record_event(
        root,
        "paper.evidence.created",
        artifact_ids=[payload["id"]],
        hashes={str(path.relative_to(root)): sha256_file(path)},
    )
    return path


def create_claim(
    root: Path, statement: str, evidence_ids: list[str], reference_ids: list[str] | None = None
) -> Path:
    contributor = require_contributor(root)
    for identifier in evidence_ids:
        if not (root / "paper/evidence" / f"{identifier}.json").exists():
            raise ValueError(f"unknown evidence card: {identifier}")
    identifier = f"claim-{slugify(statement)[:48]}"
    payload = {
        "schema_version": 1,
        "id": identifier,
        "statement": statement,
        "evidence_ids": evidence_ids,
        "reference_ids": reference_ids or [],
        "status": "proposed",
        "proposed_by": contributor.id,
        "created_at": utc_now(),
    }
    path = root / "paper/claims" / f"{identifier}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n")
    record_event(root, "paper.claim.proposed", artifact_ids=[identifier])
    return path


def review_claim(root: Path, identifier: str, status: str) -> dict[str, object]:
    if status not in {"approved", "rejected", "retracted", "superseded"}:
        raise ValueError("invalid claim state")
    contributor = require_contributor(root)
    path = root / "paper/claims" / f"{identifier}.json"
    payload = json.loads(path.read_text())
    payload.update(status=status, reviewed_by=contributor.id, reviewed_at=utc_now())
    path.write_text(json.dumps(payload, indent=2) + "\n")
    record_event(root, f"paper.claim.{status}", artifact_ids=[identifier])
    return payload


def begin_paper(root: Path, title: str) -> Path:
    """Create the authoritative manuscript only after approved claims exist."""
    approved = [
        json.loads(path.read_text())
        for path in (root / "paper/claims").glob("*.json")
        if json.loads(path.read_text()).get("status") == "approved"
    ]
    if not approved:
        raise ValueError("paper drafting requires at least one approved claim")
    path = root / "paper/manuscript.md"
    if path.exists():
        raise FileExistsError(path)
    path.write_text(
        f"# {title}\n\n## Abstract\n\n## Introduction\n\n## Methods\n\n"
        "## Results\n\n## Discussion\n\n## References\n",
        encoding="utf-8",
    )
    (root / "paper/sections.yaml").write_text(
        yaml.safe_dump(
            {
                "sections": {
                    name: {"status": "draft", "claim_ids": []}
                    for name in (
                        "Abstract",
                        "Introduction",
                        "Methods",
                        "Results",
                        "Discussion",
                        "References",
                    )
                }
            },
            sort_keys=False,
        )
    )
    record_event(root, "paper.begun", artifact_ids=["paper/manuscript.md"])
    return path


def review_section(root: Path, section: str, claim_ids: list[str]) -> dict[str, object]:
    require_contributor(root)
    claims = {p.stem: json.loads(p.read_text()) for p in (root / "paper/claims").glob("*.json")}
    invalid = [
        identifier
        for identifier in claim_ids
        if identifier not in claims or claims[identifier].get("status") != "approved"
    ]
    if invalid:
        raise ValueError("section references non-approved claims: " + ", ".join(invalid))
    path = root / "paper/sections.yaml"
    payload = yaml.safe_load(path.read_text()) or {"sections": {}}
    payload.setdefault("sections", {}).setdefault(section, {})
    payload["sections"][section].update(
        status="reviewed", claim_ids=claim_ids, reviewed_at=utc_now()
    )
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    record_event(root, "paper.section.reviewed", artifact_ids=[section])
    return payload["sections"][section]


def build_paper(root: Path, format_name: str) -> Path:
    """Create a versioned snapshot from canonical Markdown after provenance validation."""
    errors = validate_paper(root)
    if errors:
        raise ValueError("paper validation failed: " + "; ".join(errors))
    manuscript = root / "paper/manuscript.md"
    if not manuscript.exists():
        raise ValueError("paper has not begun")
    stamp = utc_now().replace(":", "").replace("+", "_")
    if format_name == "md":
        target = root / "paper/builds" / f"manuscript-{stamp}.md"
        target.write_text(manuscript.read_text(), encoding="utf-8")
    elif format_name == "docx":
        target = root / "paper/builds" / f"manuscript-{stamp}.docx"
        _write_docx(target, manuscript.read_text())
    else:
        raise ValueError("format must be md or docx")
    record_event(
        root,
        "paper.built",
        artifact_ids=[str(target.relative_to(root))],
        hashes={str(target.relative_to(root)): sha256_file(target)},
    )
    return target


def _write_docx(path: Path, markdown: str) -> None:
    """Write a compact, standards-compliant journal-neutral DOCX snapshot."""
    paragraphs = []
    for line in markdown.splitlines():
        if not line.strip():
            continue
        level = len(line) - len(line.lstrip("#")) if line.startswith("#") else 0
        text = line[level:].strip() if level else line
        style = f'<w:pStyle w:val="Heading{min(level, 3)}"/>' if level else ""
        paragraphs.append(
            f"<w:p><w:pPr>{style}</w:pPr><w:r><w:t>{html.escape(text)}</w:t></w:r></w:p>"
        )
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(paragraphs)}<w:sectPr/></w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
        'relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-'
        'officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    relationships = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
        'relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("word/document.xml", document)
