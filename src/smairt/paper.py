"""Paper-element provenance validation."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import yaml

from smairt.integrity import verify_run
from smairt.models import utc_now
from smairt.provenance import record_event, require_contributor
from smairt.references import load_index
from smairt.utils import atomic_write, sha256_file, slugify, write_json


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
    if path.exists():
        raise ValueError(f"evidence card already exists for {run_id}")
    write_json(path, payload)
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
    """Propose a uniquely identified claim linked to existing evidence cards."""
    contributor = require_contributor(root)
    for identifier in evidence_ids:
        if not (root / "paper/evidence" / f"{identifier}.json").exists():
            raise ValueError(f"unknown evidence card: {identifier}")
    identifier = f"claim-{slugify(statement)[:40]}-{uuid4().hex[:8]}"
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
    write_json(path, payload)
    record_event(root, "paper.claim.proposed", artifact_ids=[identifier])
    return path


def review_claim(root: Path, identifier: str, status: str) -> dict[str, object]:
    """Record a human claim decision after validating approval dependencies."""
    if status not in {"approved", "rejected", "retracted", "superseded"}:
        raise ValueError("invalid claim state")
    contributor = require_contributor(root)
    path = root / "paper/claims" / f"{identifier}.json"
    payload = json.loads(path.read_text())
    if status == "approved":
        errors = _validate_claim(root, payload)
        if errors:
            raise ValueError("claim cannot be approved: " + "; ".join(errors))
    payload.update(status=status, reviewed_by=contributor.id, reviewed_at=utc_now())
    write_json(path, payload)
    record_event(root, f"paper.claim.{status}", artifact_ids=[identifier])
    return payload


def begin_paper(root: Path, title: str) -> Path:
    """Create the authoritative manuscript only after approved claims exist."""
    claims = [json.loads(path.read_text()) for path in (root / "paper/claims").glob("*.json")]
    approved = [claim for claim in claims if claim.get("status") == "approved"]
    if not approved:
        raise ValueError("paper drafting requires at least one approved claim")
    path = root / "paper/manuscript.md"
    if path.exists():
        raise FileExistsError(path)
    atomic_write(
        path,
        f"# {title}\n\n## Abstract\n\n## Introduction\n\n## Methods\n\n"
        "## Results\n\n## Discussion\n\n## References\n",
    )
    atomic_write(
        root / "paper/sections.yaml",
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
        ),
    )
    record_event(root, "paper.begun", artifact_ids=["paper/manuscript.md"])
    return path


def create_outline(root: Path) -> Path:
    """Create a claim-linked outline from approved claims without drafting prose."""
    claims = [json.loads(path.read_text()) for path in (root / "paper/claims").glob("*.json")]
    approved = [claim for claim in claims if claim.get("status") == "approved"]
    if not approved:
        raise ValueError("an outline requires at least one approved claim")
    lines = ["# Manuscript Outline", ""]
    for section in ("Introduction", "Methods", "Results", "Discussion"):
        lines.extend([f"## {section}", ""])
        lines.extend(f"- [{claim['id']}] {claim['statement']}" for claim in approved)
        lines.append("")
    path = root / "paper/outline.md"
    atomic_write(path, "\n".join(lines))
    record_event(root, "paper.outline.created", artifact_ids=["paper/outline.md"])
    return path


def draft_section(root: Path, section: str, text: str, claim_ids: list[str]) -> Path:
    """Replace one canonical Markdown section with prose linked to approved claims."""
    manuscript = root / "paper/manuscript.md"
    if not manuscript.exists():
        raise ValueError("paper has not begun")
    claims = {p.stem: json.loads(p.read_text()) for p in (root / "paper/claims").glob("*.json")}
    invalid = [
        identifier
        for identifier in claim_ids
        if identifier not in claims or claims[identifier].get("status") != "approved"
    ]
    if invalid:
        raise ValueError("section references non-approved claims: " + ", ".join(invalid))
    content = manuscript.read_text()
    heading = f"## {section}"
    if heading not in content:
        raise ValueError(f"unknown manuscript section: {section}")
    before, remainder = content.split(heading, 1)
    next_heading = remainder.find("\n## ")
    after = remainder[next_heading:] if next_heading >= 0 else "\n"
    linked = " ".join(f"[{identifier}]" for identifier in claim_ids)
    atomic_write(
        manuscript, f"{before}{heading}\n\n{text.strip()}\n\nClaims: {linked}\n{after.lstrip()}"
    )
    sections_path = root / "paper/sections.yaml"
    payload = yaml.safe_load(sections_path.read_text()) or {"sections": {}}
    payload.setdefault("sections", {}).setdefault(section, {})
    payload["sections"][section].update(status="draft", claim_ids=claim_ids, drafted_at=utc_now())
    atomic_write(sections_path, yaml.safe_dump(payload, sort_keys=False))
    record_event(root, "paper.section.drafted", artifact_ids=[section])
    return manuscript


def review_section(root: Path, section: str, claim_ids: list[str]) -> dict[str, object]:
    """Mark a manuscript section reviewed against approved supporting claims."""
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


def build_paper(
    root: Path,
    format_name: str,
    *,
    template: Path | None = None,
    line_numbering: bool = False,
) -> Path:
    """Create a versioned snapshot from canonical Markdown after provenance validation."""
    errors = validate_paper(root)
    if errors:
        raise ValueError("paper validation failed: " + "; ".join(errors))
    manuscript = root / "paper/manuscript.md"
    if not manuscript.exists():
        raise ValueError("paper has not begun")
    sections_path = root / "paper/sections.yaml"
    sections = (yaml.safe_load(sections_path.read_text()) or {}).get("sections", {})
    unreviewed = [name for name, value in sections.items() if value.get("status") != "reviewed"]
    if not sections or unreviewed:
        raise ValueError("paper sections require explicit review: " + ", ".join(unreviewed))
    stamp = utc_now().replace(":", "").replace("+", "_")
    if format_name == "md":
        target = root / "paper/builds" / f"manuscript-{stamp}.md"
        atomic_write(target, manuscript.read_text())
    elif format_name == "docx":
        target = root / "paper/builds" / f"manuscript-{stamp}.docx"
        _write_docx(
            target, manuscript.read_text(), template=template, line_numbering=line_numbering
        )
    else:
        raise ValueError("format must be md or docx")
    record_event(
        root,
        "paper.built",
        artifact_ids=[str(target.relative_to(root))],
        hashes={str(target.relative_to(root)): sha256_file(target)},
    )
    return target


def _write_docx(
    path: Path,
    markdown: str,
    *,
    template: Path | None = None,
    line_numbering: bool = False,
) -> None:
    """Write a journal-neutral DOCX using Word-native styles and page structure."""
    from docx import Document
    from docx.enum.section import WD_SECTION
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.shared import Inches, Pt

    document = Document(str(template)) if template else Document()
    normal = document.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    lines = markdown.splitlines()
    title = next((line[2:].strip() for line in lines if line.startswith("# ")), "Manuscript")
    title_paragraph = document.add_paragraph()
    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_paragraph.add_run(title)
    run.bold = True
    run.font.size = Pt(18)
    document.add_paragraph("Authors and affiliations: complete manually")
    document.add_paragraph("Corresponding author: complete manually")
    document.add_section(WD_SECTION.NEW_PAGE)
    if line_numbering:
        for section in document.sections:
            line_numbers = OxmlElement("w:lnNumType")
            line_numbers.set(
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}countBy", "1"
            )
            section._sectPr.append(line_numbers)
    for line in lines:
        if not line.strip() or line.startswith("# "):
            continue
        if line.startswith("## "):
            document.add_heading(line[3:].strip(), level=1)
        elif line.startswith("### "):
            document.add_heading(line[4:].strip(), level=2)
        elif line.startswith("![") and "](" in line:
            alt, source = line[2:].split("](", 1)
            image = path.parent.parent / source.rstrip(")")
            if image.exists():
                document.add_picture(str(image), width=Inches(6))
                document.add_paragraph(alt, style="Caption")
        else:
            document.add_paragraph(line)
    path.parent.mkdir(parents=True, exist_ok=True)
    document.save(path)


def _validate_claim(root: Path, claim: dict[str, object]) -> list[str]:
    """Return evidence and citation errors that prevent claim approval."""
    errors: list[str] = []
    accepted = accepted_runs(root)
    for evidence_id in claim.get("evidence_ids", []):
        path = root / "paper/evidence" / f"{evidence_id}.json"
        if not path.exists():
            errors.append(f"missing evidence {evidence_id}")
            continue
        evidence = json.loads(path.read_text())
        if evidence.get("status") != "current" or evidence.get("run_id") not in accepted:
            errors.append(f"stale evidence {evidence_id}")
    references = {item.id: item for item in load_index(root)}
    for reference_id in claim.get("reference_ids", []):
        if (
            reference_id not in references
            or references[reference_id].verification_status != "verified"
        ):
            errors.append(f"unverified citation {reference_id}")
    return errors
