from pathlib import Path

from pypdf import PdfWriter

from smairt.models import DataClassification, EnvironmentMode
from smairt.references import add_reference, inspect_pdf, load_index
from smairt.scaffold import create_project


def test_local_pdf_is_copied_ignored_and_indexed(tmp_path: Path) -> None:
    root = tmp_path / "project"
    create_project(
        root,
        name="References",
        author="Researcher",
        classification=DataClassification.PRIVATE,
        initialize_git=False,
        environment_mode=EnvironmentMode.NONE,
    )
    source = tmp_path / "paper.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_metadata({"/Title": "Test Paper", "/Author": "A. Researcher"})
    with source.open("wb") as stream:
        writer.write(stream)
    proposed = inspect_pdf(source)
    assert proposed["title"] == "Test Paper"
    record = add_reference(
        root,
        source,
        title="Test Paper",
        authors=["A. Researcher"],
        year=2026,
        verified=True,
    )
    assert (root / "references" / record.local_path).exists()
    assert load_index(root)[0].metadata_verified
