from pathlib import Path

from smairt.models import DataClassification, EnvironmentMode, SmairtConfig
from smairt.project import context, is_prohibited, status, validate_project
from smairt.scaffold import create_project


def make_project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    create_project(
        root,
        name="RNA Research",
        author="Manual Author",
        question="What can the data support?",
        description=None,
        classification=DataClassification.UNPUBLISHED,
        initialize_git=False,
        environment_mode=EnvironmentMode.NONE,
    )
    return root


def test_scaffold_is_safe_and_complete(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    config = SmairtConfig.load(root / "smairt.yaml")
    assert config.project.author == "Manual Author"
    assert not config.git.enabled
    assert (root / "hypotheses/HYPOTHESIS_TEMPLATE.md").exists()
    assert (root / "paper/working").is_dir()
    assert "references/pdfs/*" in (root / ".gitignore").read_text()
    assert validate_project(root).ok


def test_status_and_context_are_compact(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    payload = status(root)
    assert payload["counts"]["hypotheses"] == 0
    selected = context(root, "code")
    assert "prompts/CODE_CONVENTIONS.md" in selected["read"]
    assert "references/pdfs" not in str(selected)


def test_protected_paths_are_recognized() -> None:
    for path in (
        ".env",
        "credentials.json",
        "references/pdfs/article.pdf",
        "data/raw/reads.csv",
        "sample.fast5",
        "alignment.bam",
    ):
        assert is_prohibited(path)
