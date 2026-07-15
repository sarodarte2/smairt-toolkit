"""Project scaffold, progressive context, and Git safety integration tests."""

import os
import subprocess
import sys
from pathlib import Path

import yaml

from smairt.models import DataClassification, EnvironmentMode, SmairtConfig
from smairt.project import context, is_prohibited, status, validate_project
from smairt.scaffold import create_project
from smairt.upgrade import managed_files
from smairt.utils import sha256_text


def make_project(tmp_path: Path) -> Path:
    """Create a representative unpublished project for scaffold checks."""
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
    """Verify required files, manual author identity, and local-data safeguards."""
    root = make_project(tmp_path)
    config = SmairtConfig.load(root / "smairt.yaml")
    assert config.project.author == "Manual Author"
    assert not config.git.enabled
    assert (root / "hypotheses/HYPOTHESIS_TEMPLATE.md").exists()
    assert (root / "paper/working").is_dir()
    assert "references/pdfs/*" in (root / ".gitignore").read_text()
    assert validate_project(root).ok


def test_generated_documentation_paths_and_managed_hashes_are_stable(tmp_path: Path) -> None:
    """Keep readable project guidance at compatible paths with authoritative hashes."""
    root = make_project(tmp_path)
    expected_documents = {
        "AGENTS.md",
        "docs/ACKNOWLEDGMENTS.md",
        "docs/GIT_AND_COLLABORATION.md",
        "docs/PHILOSOPHY.md",
        "docs/WORKFLOW.md",
        "prompts/CODE_CONVENTIONS.md",
        "prompts/INTERPRETATION_CONVENTIONS.md",
        "prompts/KNOWN_PATTERNS.md",
        "prompts/RESEARCH_CONVENTIONS.md",
        "prompts/intellectual_contribution.md",
        "plans/README.md",
        "hypotheses/README.md",
        "experiments/README.md",
        "scripts/README.md",
        "scripts/shared/README.md",
        "analysis/README.md",
        "references/README.md",
        "paper/README.md",
        "paper/contribution_statement.md",
    }
    assert all((root / relative).is_file() for relative in expected_documents)
    assert all(
        (root / relative).read_text().lstrip().startswith(("#", "<!--"))
        for relative in expected_documents
    )

    manifest = yaml.safe_load((root / ".smairt/framework.yaml").read_text())
    expected_managed = managed_files()
    assert set(manifest["managed_files"]) == set(expected_managed)
    assert manifest["managed_files"] == {
        relative: sha256_text(content.rstrip() + "\n")
        for relative, content in expected_managed.items()
    }


def test_status_and_context_are_compact(tmp_path: Path) -> None:
    """Ensure progressive context does not load PDFs or unrelated project state."""
    root = make_project(tmp_path)
    payload = status(root)
    assert payload["counts"]["hypotheses"] == 0
    selected = context(root, "code")
    assert "prompts/CODE_CONVENTIONS.md" in selected["read"]
    assert "references/pdfs" not in str(selected)


def test_protected_paths_are_recognized() -> None:
    """Recognize representative secrets, raw data, and local reference paths."""
    for path in (
        ".env",
        "credentials.json",
        "references/pdfs/article.pdf",
        "data/raw/reads.csv",
        "sample.fast5",
        "alignment.bam",
    ):
        assert is_prohibited(path)


def test_init_can_add_smairt_to_reviewed_nonempty_directory(tmp_path: Path) -> None:
    """Ensure explicit initialization preserves existing non-Git research work."""
    root = tmp_path / "existing"
    root.mkdir()
    existing = root / "research-notes.md"
    existing.write_text("Keep this work.\n")
    create_project(
        root,
        name="Existing Research",
        author="Manual Author",
        classification=DataClassification.UNPUBLISHED,
        initialize_git=False,
        allow_existing=True,
    )
    assert existing.read_text() == "Keep this work.\n"
    assert (root / "smairt.yaml").exists()


def test_staged_protected_file_fails_validation(tmp_path: Path) -> None:
    """Ensure force-staged secrets are rejected by validation and the Git hook."""
    root = tmp_path / "git-project"
    create_project(
        root,
        name="Protected Research",
        author="Manual Author",
        classification=DataClassification.PRIVATE,
        initialize_git=True,
    )
    secret = root / ".env"
    secret.write_text("API_KEY=do-not-commit\n")
    subprocess.run(["git", "add", "-f", ".env"], cwd=root, check=True)
    report = validate_project(root, staged=True)
    assert not report.ok
    assert report.checks["git_safety"] is False
    assert any(".env" in error for error in report.errors)
    hook = subprocess.run(
        [str(root / ".githooks/pre-commit")],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            "PATH": f"{Path(sys.executable).parent}:{os.environ['PATH']}",
            "PYTHONPATH": str(Path(__file__).parents[1] / "src"),
        },
    )
    assert hook.returncode == 1
    assert "Protected files" in hook.stdout
