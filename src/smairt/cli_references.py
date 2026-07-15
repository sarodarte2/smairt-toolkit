"""Scholarly-reference CLI commands and confirmation flow."""

from pathlib import Path
from typing import Annotated, cast

import typer
from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt

from smairt.cli_shared import emit, project_root
from smairt.models import SmairtConfig
from smairt.references import (
    add_doi_reference,
    add_reference,
    attach_reference,
    copy_zotero_attachment,
    edit_reference,
    enrich_openalex,
    enrich_reference,
    export_references,
    get_reference,
    import_zotero_collection,
    import_zotero_item,
    inspect_pdf,
    load_index,
    organize_pdfs,
    unindexed_pdfs,
    verify_reference,
)
from smairt.utils import atomic_write

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


@reference_app.command("organize-pdfs")
def reference_organize_pdfs(
    apply: Annotated[bool, typer.Option("--apply")] = False,
    yes: Annotated[bool, typer.Option("--yes")] = False,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Preview or apply deterministic names to SMAIRT-managed PDF copies."""
    emit(organize_pdfs(project_root(), apply=apply, confirmed=yes), as_json)


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
    confirm_remote: Annotated[bool, typer.Option("--confirm-remote")] = False,
) -> None:
    """Add OpenAlex metadata using environment-first credential resolution."""
    emit(
        enrich_openalex(project_root(), identifier, confirm_remote=confirm_remote).model_dump(
            mode="json", exclude_none=True
        ),
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
        atomic_write(output, content)
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
    authors = authors or list(cast(list[str], proposed["authors"]))
    doi = doi or cast(str | None, proposed["doi"])
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
        link=link,
    )
    if verified:
        record = verify_reference(project_root(), record.id, _active_contributor())
    emit(record.model_dump(mode="json", exclude_none=True), False)


@reference_app.command("add-doi")
def reference_add_doi(
    doi: Annotated[str, typer.Argument()],
    openalex: Annotated[bool, typer.Option("--openalex")] = False,
    confirm_remote: Annotated[bool, typer.Option("--confirm-remote")] = False,
) -> None:
    """Create a metadata-only reference from authoritative Crossref metadata."""
    record = add_doi_reference(
        project_root(), doi, use_openalex=openalex, confirm_remote=confirm_remote
    )
    emit(record.model_dump(mode="json", exclude_none=True), False)


@reference_app.command("attach")
def reference_attach(
    identifier: Annotated[str, typer.Argument()], pdf: Annotated[Path, typer.Argument()]
) -> None:
    """Attach one explicit local PDF to an existing metadata-only record."""
    emit(
        attach_reference(project_root(), identifier, pdf).model_dump(
            mode="json", exclude_none=True
        ),
        False,
    )


@reference_app.command("import-zotero")
def reference_import_zotero(
    item: Annotated[str | None, typer.Option("--item")] = None,
    collection: Annotated[str | None, typer.Option("--collection")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=1000)] = 500,
    copy_attachment: Annotated[str | None, typer.Option("--copy-attachment")] = None,
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    """Import Zotero metadata, with optional confirmed local attachment copy."""
    if bool(item) == bool(collection):
        raise typer.BadParameter("provide exactly one of --item or --collection")
    if copy_attachment and not item:
        raise typer.BadParameter("--copy-attachment requires --item")
    if item and copy_attachment:
        result: object = copy_zotero_attachment(
            project_root(), item, copy_attachment, confirmed=yes
        ).model_dump(mode="json", exclude_none=True)
    elif item:
        result = import_zotero_item(project_root(), item).model_dump(mode="json", exclude_none=True)
    else:
        result = [
            record.model_dump(mode="json", exclude_none=True)
            for record in import_zotero_collection(project_root(), collection or "", limit=limit)
        ]
    emit(result, False)
