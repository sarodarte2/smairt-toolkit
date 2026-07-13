"""Scholarly-reference CLI commands and confirmation flow."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt

from smairt.cli_shared import emit, project_root
from smairt.models import SmairtConfig
from smairt.references import (
    add_reference,
    edit_reference,
    enrich_openalex,
    enrich_reference,
    export_references,
    get_reference,
    inspect_pdf,
    load_index,
    unindexed_pdfs,
    verify_reference,
)

reference_app = typer.Typer(help="Manage local scholarly references")
console = Console()


def _active_contributor() -> str:
    """Return the active contributor required for attributed metadata changes."""
    contributor = SmairtConfig.load(project_root() / "smairt.yaml").active_contributor
    if not contributor:
        raise typer.BadParameter("select an active contributor first")
    return contributor


@reference_app.command("list")
def reference_list(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List indexed references without loading full PDF content."""
    records = [
        record.model_dump(mode="json", exclude_none=True) for record in load_index(project_root())
    ]
    emit(records, as_json)


@reference_app.command("scan")
def reference_scan(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Report local PDFs that have not been indexed by checksum."""
    emit({"unindexed": [str(path) for path in unindexed_pdfs(project_root())]}, as_json)


@reference_app.command("inspect")
def reference_inspect(identifier: Annotated[str, typer.Argument()]) -> None:
    """Show one indexed reference and its provenance metadata."""
    emit(
        get_reference(project_root(), identifier).model_dump(mode="json", exclude_none=True), False
    )


@reference_app.command("enrich")
def reference_enrich(
    identifier: Annotated[str, typer.Argument()],
    confirm_remote: Annotated[bool, typer.Option("--confirm-remote")] = False,
) -> None:
    """Enrich a reference from Crossref after applicable safety confirmation."""
    emit(
        enrich_reference(project_root(), identifier, confirm_remote=confirm_remote).model_dump(
            mode="json", exclude_none=True
        ),
        False,
    )


@reference_app.command("enrich-openalex")
def reference_enrich_openalex(
    identifier: Annotated[str, typer.Argument()],
    api_key: Annotated[str | None, typer.Option(envvar="OPENALEX_API_KEY", hidden=True)] = None,
    confirm_remote: Annotated[bool, typer.Option("--confirm-remote")] = False,
) -> None:
    """Add optional OpenAlex metadata without persisting the API key."""
    emit(
        enrich_openalex(
            project_root(), identifier, api_key, confirm_remote=confirm_remote
        ).model_dump(mode="json", exclude_none=True),
        False,
    )


@reference_app.command("edit")
def reference_edit(
    identifier: Annotated[str, typer.Argument()],
    field: Annotated[str, typer.Option()],
    value: Annotated[str, typer.Option()],
) -> None:
    """Append an attributed manual metadata correction."""
    emit(
        edit_reference(project_root(), identifier, field, value, _active_contributor()).model_dump(
            mode="json", exclude_none=True
        ),
        False,
    )


@reference_app.command("verify")
def reference_verify(identifier: Annotated[str, typer.Argument()]) -> None:
    """Record human verification of current reference metadata."""
    emit(
        verify_reference(project_root(), identifier, _active_contributor()).model_dump(
            mode="json", exclude_none=True
        ),
        False,
    )


@reference_app.command("export")
def reference_export(
    format_name: Annotated[str, typer.Option("--format")],
    output: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Export the reference index as BibTeX or CSL JSON."""
    content = export_references(project_root(), format_name)
    if output:
        output.write_text(content, encoding="utf-8")
        console.print(output)
    else:
        console.print(content, markup=False)


@reference_app.command("add")
def reference_add(
    source: Annotated[Path, typer.Argument()],
    title: Annotated[str | None, typer.Option()] = None,
    authors: Annotated[list[str] | None, typer.Option()] = None,
    year: Annotated[int | None, typer.Option()] = None,
    doi: Annotated[str | None, typer.Option()] = None,
    verified: Annotated[bool, typer.Option("--verified")] = False,
    link: Annotated[bool, typer.Option("--link")] = False,
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    """Inspect, confirm, and index one local scholarly PDF."""
    proposed = inspect_pdf(source)
    title = title or str(proposed["title"])
    authors = authors or list(proposed["authors"])
    doi = doi or proposed["doi"]
    if not yes:
        console.print({"title": title, "authors": authors, "year": year, "doi": doi})
        title = Prompt.ask("Confirmed title", default=title)
        if year is None:
            year = IntPrompt.ask("Year (0 if unknown)", default=0) or None
        verified = Confirm.ask("Have you verified this metadata?", default=False)
        if not Confirm.ask("Add this local reference?", default=True):
            raise typer.Exit()
    record = add_reference(
        project_root(),
        source,
        title=title,
        authors=authors,
        year=year,
        doi=doi,
        verified=verified,
        link=link,
    )
    emit(record.model_dump(mode="json", exclude_none=True), False)
