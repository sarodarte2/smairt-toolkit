"""Paper provenance, manuscript, and summary CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.prompt import Confirm

from smairt.cli_shared import emit, project_root
from smairt.models import ClaimRecord, EvidenceCard
from smairt.paper import (
    begin_paper,
    build_paper,
    create_claim,
    create_evidence_card,
    create_outline,
    draft_section,
    review_claim,
    review_section,
    validate_paper,
)
from smairt.summaries import create_summary, list_summaries, promote_summary, supersede_summary

console = Console()
paper_app = typer.Typer(help="Manage paper evidence provenance")
paper_section_app = typer.Typer(help="Draft and review manuscript sections")
paper_evidence_app = typer.Typer(help="Manage immutable paper evidence cards")
paper_claim_app = typer.Typer(help="Manage human-reviewed manuscript claims")
summary_app = typer.Typer(help="Manage contributor-scoped source summaries")

paper_app.add_typer(paper_evidence_app, name="evidence")
paper_app.add_typer(paper_claim_app, name="claim")
paper_app.add_typer(paper_section_app, name="section")


@paper_app.command("validate")
def paper_validate() -> None:
    """Reject manuscript elements not backed by current accepted evidence."""
    errors = validate_paper(project_root())
    emit({"ok": not errors, "errors": errors}, False)
    if errors:
        raise typer.Exit(1)


@paper_app.command("status")
def paper_status(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Summarize evidence, claim-review, and manuscript state."""
    root = project_root()
    claims: list[ClaimRecord] = []
    corrupt: list[str] = []
    seen: set[str] = set()
    for path in sorted((root / "paper/claims").glob("*.json")):
        try:
            claim = ClaimRecord.model_validate_json(path.read_text())
        except (OSError, ValueError, ValidationError):
            corrupt.append(path.name)
            continue
        if claim.id in seen:
            corrupt.append(path.name)
            continue
        seen.add(claim.id)
        claims.append(claim)
    payload = {
        "evidence_cards": len(list((root / "paper/evidence").glob("*.json"))),
        "claims": {
            state: sum(claim.status == state for claim in claims)
            for state in ("proposed", "approved", "rejected", "superseded", "retracted")
        },
        "manuscript_started": (root / "paper/manuscript.md").exists(),
        "corrupt_records": corrupt,
    }
    emit(payload, as_json)


@paper_evidence_app.command("list")
def paper_evidence_list(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List immutable manuscript evidence cards."""
    items: list[dict[str, object]] = []
    corrupt: list[str] = []
    seen: set[str] = set()
    for path in sorted((project_root() / "paper/evidence").glob("*.json")):
        try:
            card = EvidenceCard.model_validate_json(path.read_text())
        except (OSError, ValueError, ValidationError):
            corrupt.append(path.name)
            continue
        if card.id in seen:
            corrupt.append(path.name)
            continue
        seen.add(card.id)
        items.append(card.model_dump(mode="json", exclude_none=True))
    emit({"items": items, "corrupt_records": corrupt}, as_json)


@paper_evidence_app.command("review")
def paper_evidence_review(
    run: Annotated[str, typer.Option()],
    purpose: Annotated[str, typer.Option()],
    observed_result: Annotated[str, typer.Option()],
    limitations: Annotated[str, typer.Option()],
    decision: Annotated[str, typer.Option()],
    relevance: Annotated[str, typer.Option()] = "",
) -> None:
    """Create an immutable evidence card from a verified research run."""
    console.print(
        create_evidence_card(
            project_root(),
            run,
            purpose=purpose,
            observed_result=observed_result,
            limitations=limitations,
            decision=decision,
            relevance=relevance,
        )
    )


@paper_claim_app.command("propose")
def paper_claim_propose(
    statement: Annotated[str, typer.Option()],
    evidence: Annotated[list[str], typer.Option()],
    reference: Annotated[list[str] | None, typer.Option()] = None,
) -> None:
    """Propose a claim linked to project evidence and references."""
    console.print(create_claim(project_root(), statement, evidence, reference))


def _review_claim(identifier: str, status: str, confirmed: bool) -> None:
    """Apply a human-confirmed claim decision through the domain review gate."""
    if not confirmed and not Confirm.ask(f"Mark {identifier} {status}?", default=False):
        raise typer.Exit()
    emit(review_claim(project_root(), identifier, status), False)


@paper_claim_app.command("approve")
def paper_claim_approve(
    identifier: Annotated[str, typer.Argument()],
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    """Approve a currently supported manuscript claim."""
    _review_claim(identifier, "approved", yes)


@paper_claim_app.command("reject")
def paper_claim_reject(
    identifier: Annotated[str, typer.Argument()],
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    """Reject a proposed manuscript claim with human confirmation."""
    _review_claim(identifier, "rejected", yes)


@paper_app.command("begin")
def paper_begin(title: Annotated[str, typer.Option()]) -> None:
    """Initialize canonical manuscript files."""
    console.print(begin_paper(project_root(), title))


@paper_app.command("outline")
def paper_outline() -> None:
    """Create a claim-linked manuscript outline."""
    console.print(create_outline(project_root()))


@paper_section_app.command("draft")
def paper_section_draft(
    section: Annotated[str, typer.Argument()],
    text: Annotated[str, typer.Option()],
    claim: Annotated[list[str], typer.Option()],
) -> None:
    """Draft one canonical section from approved claims."""
    console.print(draft_section(project_root(), section, text, claim))


@paper_section_app.command("review")
def paper_section_review(
    section: Annotated[str, typer.Argument()],
    claim: Annotated[list[str], typer.Option()],
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    """Mark a drafted section reviewed against approved claims."""
    if not yes and not Confirm.ask(f"Mark {section} reviewed?", default=False):
        raise typer.Exit()
    emit(review_section(project_root(), section, claim), False)


@paper_app.command("build")
def paper_build(
    format_name: Annotated[str, typer.Option("--format")],
    template: Annotated[Path | None, typer.Option()] = None,
    line_numbering: Annotated[bool, typer.Option("--line-numbering")] = False,
) -> None:
    """Build a versioned manuscript after evidence validation."""
    console.print(
        build_paper(project_root(), format_name, template=template, line_numbering=line_numbering)
    )


@summary_app.command("create")
def summary_create(
    source: Annotated[Path, typer.Argument()],
    content: Annotated[str, typer.Option()],
    shareable: Annotated[bool, typer.Option("--shareable")] = False,
    redaction_confirmed: Annotated[bool, typer.Option("--redaction-confirmed")] = False,
) -> None:
    """Create an immutable contributor-scoped source summary."""
    console.print(
        create_summary(
            project_root(),
            source,
            content,
            shareable=shareable,
            redaction_confirmed=redaction_confirmed,
        )
    )


@summary_app.command("list")
def summary_list(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List current summary records and canonical state."""
    emit(list_summaries(project_root()), as_json)


@summary_app.command("compare")
def summary_compare(source_id: Annotated[str, typer.Argument()]) -> None:
    """Compare contributor summaries for one source."""
    emit([item for item in list_summaries(project_root()) if item["source_id"] == source_id], False)


@summary_app.command("promote")
def summary_promote(identifier: Annotated[str, typer.Argument()]) -> None:
    """Promote a fresh summary to the shared canonical pointer."""
    console.print(promote_summary(project_root(), identifier))


@summary_app.command("supersede")
def summary_supersede(
    previous: Annotated[str, typer.Argument()], replacement: Annotated[str, typer.Argument()]
) -> None:
    """Link an older summary to its fresh replacement."""
    console.print(supersede_summary(project_root(), previous, replacement))
