"""Validated, versioned records shared by the CLI, TUI, and Codex adapters."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> str:
    """Return a timezone-aware UTC timestamp suitable for durable records."""
    return datetime.now(UTC).isoformat()


class DataClassification(StrEnum):
    """Describe how carefully project data must be handled and shared."""

    PUBLIC = "public"
    UNPUBLISHED = "unpublished"
    PRIVATE = "private"
    CONTROLLED = "controlled"


class EnvironmentMode(StrEnum):
    """Describe whether SMAIRT manages a project-level Conda environment."""

    NEW_CONDA = "new_conda"
    EXISTING_CONDA = "existing_conda"
    NONE = "none"


class Decision(StrEnum):
    """Enumerate the explicit human decisions allowed for research evidence."""

    ACCEPT = "ACCEPT"
    REVISE = "REVISE"
    ABANDON = "ABANDON"
    BLOCKED = "BLOCKED"
    SUPERSEDED = "SUPERSEDED"
    RETRACTED = "RETRACTED"


class ProjectInfo(BaseModel):
    """Store manually supplied project identity and optional initial framing."""

    name: str
    slug: str
    author: str
    description: str | None = None
    question: str | None = None
    created_at: str = Field(default_factory=utc_now)

    @field_validator("name", "slug", "author")
    @classmethod
    def non_empty(cls, value: str) -> str:
        """Reject blank identity fields while preserving intentional text."""
        if not value.strip():
            raise ValueError("must not be empty")
        return value.strip()


class DataPolicy(BaseModel):
    """Store the declared data classification and Git safety contract."""

    classification: DataClassification
    raw_data_in_git: bool = False


class EnvironmentConfig(BaseModel):
    """Identify the environment used to execute project experiments."""

    mode: EnvironmentMode = EnvironmentMode.NONE
    name: str | None = None
    prefix: str | None = None


class GitConfig(BaseModel):
    """Record whether Git and SMAIRT-managed hooks are active."""

    enabled: bool = False
    managed_hooks: bool = False


class Contributor(BaseModel):
    """A manually confirmed person allowed to perform consequential actions."""

    id: str
    name: str
    email: str | None = None
    confirmed_at: str = Field(default_factory=utc_now)
    source: str = "manual"


class RepositoryAttestation(BaseModel):
    """Record the one-time private-repository collaboration acknowledgment."""

    acknowledged: bool = False
    contributor_id: str | None = None
    acknowledged_at: str | None = None


class MigrationEntry(BaseModel):
    """Record one applied schema migration without hiding its provenance."""

    from_version: int
    to_version: int
    applied_at: str = Field(default_factory=utc_now)
    contributor_id: str | None = None


class ActiveState(BaseModel):
    """Point to the current hypothesis, experiment, iteration, and accepted run."""

    hypothesis: str | None = None
    experiment: str | None = None
    iteration: str | None = None
    accepted_run: str | None = None


class SmairtConfig(BaseModel):
    """Define the authoritative, versioned project contract in smairt.yaml."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 2
    smairt_version: str = "0.1.0"
    project: ProjectInfo
    data: DataPolicy
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    safety_mode: str = "standard"
    contributors: list[Contributor] = Field(default_factory=list)
    active_contributor: str | None = None
    repository_attestation: RepositoryAttestation = Field(default_factory=RepositoryAttestation)
    migration_history: list[MigrationEntry] = Field(default_factory=list)
    active: ActiveState = Field(default_factory=ActiveState)

    @field_validator("safety_mode")
    @classmethod
    def valid_safety_mode(cls, value: str) -> str:
        if value not in {"standard", "strict"}:
            raise ValueError("safety_mode must be standard or strict")
        return value

    @classmethod
    def load(cls, path: Path) -> SmairtConfig:
        """Parse and validate a project contract from YAML."""
        return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))

    def dump(self, path: Path) -> None:
        """Serialize the validated contract without implicit null fields."""
        data = self.model_dump(mode="json", exclude_none=True)
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


class ReferenceRecord(BaseModel):
    """Describe one indexed local scholarly reference and its checksum."""

    id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    document_type: str = "article"
    local_path: str
    sha256: str
    metadata_verified: bool = False
    citation_key: str | None = None
    identifiers: dict[str, str] = Field(default_factory=dict)
    publication_date: str | None = None
    venue: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    publisher: str | None = None
    url: str | None = None
    license: str | None = None
    source_provenance: list[dict[str, Any]] = Field(default_factory=list)
    verification_status: str = "unverified"
    edit_history: list[dict[str, Any]] = Field(default_factory=list)
    added_at: str = Field(default_factory=utc_now)


class RunRecord(BaseModel):
    """Capture the immutable execution and provenance metadata for one run."""

    run_id: str
    experiment_id: str
    iteration_id: str
    command: list[str]
    started_at: str
    completed_at: str
    exit_code: int
    working_directory: str
    log_path: str
    results_directory: str
    config_sha256: str | None = None
    git_commit: str | None = None
    git_dirty: bool = False
    environment: dict[str, Any] = Field(default_factory=dict)
    manifest_path: str | None = None


class ProjectEvent(BaseModel):
    id: str
    timestamp: str
    actor: str
    action: str
    artifact_ids: list[str] = Field(default_factory=list)
    hashes: dict[str, str] = Field(default_factory=dict)
    supersedes: str | None = None


class CorrectionRecord(BaseModel):
    id: str
    action: str
    target_run: str | None = None
    replacement_run: str | None = None
    reason: str
    contributor: str
    timestamp: str


class EvidenceCard(BaseModel):
    id: str
    run_id: str
    purpose: str
    observed_result: str
    limitations: str
    decision: str
    contributor: str
    status: str = "current"


class ClaimRecord(BaseModel):
    id: str
    statement: str
    evidence_ids: list[str]
    reference_ids: list[str] = Field(default_factory=list)
    status: str


class SummaryRecord(BaseModel):
    id: str
    contributor: str
    source_id: str
    source_path: str
    source_sha256: str
    content: str
    status: str = "current"


class ContextCapsule(BaseModel):
    task: str
    token_budget: int
    estimated_tokens: int
    read: list[str]
    included: list[dict[str, Any]]
    deferred: list[dict[str, Any]]


class ValidationFinding(BaseModel):
    severity: str
    code: str
    artifact: str
    message: str


class NextAction(BaseModel):
    id: str
    label: str
    kind: str
    requires_human: bool = False


class HumanGate(BaseModel):
    id: str
    action: str
    prompt: str
    contributor_required: bool = True


class PaperBuild(BaseModel):
    format: str
    manuscript_sha256: str
    output_path: str
    output_sha256: str
    built_at: str
