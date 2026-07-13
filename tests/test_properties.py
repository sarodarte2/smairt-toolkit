"""Property checks for path, identifier, normalization, and managed-state invariants."""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from smairt.harnesses import BEGIN_MARKER, END_MARKER, _merge_agents
from smairt.models import RunRecord, RunStatus
from smairt.references import normalize_doi
from smairt.utils import ensure_within, validate_identifier


@given(st.from_regex(r"[A-Za-z0-9][A-Za-z0-9._-]{0,40}", fullmatch=True))
def test_valid_identifier_property(identifier: str) -> None:
    """Accept every portable identifier generated from the documented grammar."""
    assert validate_identifier(identifier) == identifier


@given(st.sampled_from(["../x", "a/b", "*", "[abc]", "", ".", "a" * 129]))
def test_invalid_identifier_property(identifier: str) -> None:
    """Reject traversal, glob syntax, emptiness, and overlong identifier values."""
    with pytest.raises(ValueError):
        validate_identifier(identifier)


@given(
    prefix=st.sampled_from(["", "doi:", "https://doi.org/", "http://doi.org/"]),
    suffix=st.from_regex(r"[A-Za-z0-9._;()/:-]{1,24}", fullmatch=True),
)
def test_doi_normalization_property(prefix: str, suffix: str) -> None:
    """Normalize every supported DOI prefix without changing identifier semantics."""
    value = f"{prefix}10.1234/{suffix}"
    assert normalize_doi(value) == f"10.1234/{suffix}".lower()


@given(
    before=st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=80),
    after=st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=80),
)
def test_managed_block_merge_is_idempotent(before: str, after: str) -> None:
    """Replace only the managed block and converge after one merge."""
    existing = f"{before}\n{BEGIN_MARKER}\nold\n{END_MARKER}\n{after}"
    merged = _merge_agents(existing)
    assert _merge_agents(merged) == merged
    assert merged.count(BEGIN_MARKER) == 1
    assert merged.count(END_MARKER) == 1


def test_path_containment_resolves_symlinks(tmp_path: Path) -> None:
    """Reject both lexical traversal and symlinks that leave the project root."""
    root = tmp_path / "root"
    root.mkdir()
    inside = root / "inside"
    inside.mkdir()
    assert ensure_within(root, inside) == inside.resolve()
    with pytest.raises(ValueError):
        ensure_within(root, root / ".." / "outside")
    link = root / "escape"
    link.symlink_to(tmp_path)
    with pytest.raises(ValueError):
        ensure_within(root, link / "outside")


@given(
    status=st.sampled_from(list(RunStatus)),
    exit_code=st.one_of(st.none(), st.integers(min_value=-255, max_value=255)),
    completed_at=st.one_of(st.none(), st.just("2026-01-01T00:00:00Z")),
)
def test_run_lifecycle_state_invariant(
    status: RunStatus, exit_code: int | None, completed_at: str | None
) -> None:
    """Accept exactly the started or terminal field combinations allowed by status."""
    valid = (
        (status is RunStatus.STARTED and exit_code is None and completed_at is None)
        or (status is RunStatus.COMPLETED and exit_code == 0 and completed_at is not None)
        or (status is RunStatus.FAILED and exit_code not in {None, 0} and completed_at is not None)
        or (status is RunStatus.INTERRUPTED and exit_code is not None and completed_at is not None)
    )
    payload = {
        "run_id": "RUN_001",
        "experiment_id": "EXPERIMENT_001",
        "iteration_id": "ITERATION_001",
        "status": status,
        "command": ["python", "analysis.py"],
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": completed_at,
        "exit_code": exit_code,
        "working_directory": "experiments/EXPERIMENT_001/iterations/ITERATION_001",
        "log_path": "results/EXPERIMENT_001/ITERATION_001/RUN_001/run.log",
        "results_directory": "results/EXPERIMENT_001/ITERATION_001/RUN_001",
    }
    if valid:
        assert RunRecord.model_validate(payload).status is status
    else:
        with pytest.raises(ValidationError):
            RunRecord.model_validate(payload)
