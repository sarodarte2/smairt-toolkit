"""Validated, versioned records shared by the CLI, TUI, and Codex adapters."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from smairt import __version__
from smairt.utils import atomic_write

IDENTIFIER_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"


class DurableModel(BaseModel):
    """Reject unknown durable fields so schema drift is never silent."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


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


class HarnessName(StrEnum):
    """Enumerate coding harnesses with maintained SMAIRT adapters."""

    CODEX = "codex"
    ZOO = "zoo"
    CLINE = "cline"
    OPENCODE = "opencode"
    CURSOR = "cursor"


class ZoteroMode(StrEnum):
    """Describe the configured read-only Zotero connection."""

    DISABLED = "disabled"
    LOCAL = "local"
    WEB = "web"


class ZoteroLibraryType(StrEnum):
    """Enumerate Zotero Web API library namespaces."""

    USER = "user"
    GROUP = "group"


class ProjectLicense(StrEnum):
    """Enumerate the project-level licenses SMAIRT can generate safely."""

    UNSPECIFIED = "unspecified"
    MIT = "MIT"
    BSD_3_CLAUSE = "BSD-3-Clause"
    APACHE_2_0 = "Apache-2.0"
    GPL_3_0_ONLY = "GPL-3.0-only"
    PROPRIETARY = "proprietary"


class Decision(StrEnum):
    """Enumerate the explicit human decisions allowed for research evidence."""

    ACCEPT = "ACCEPT"
    REVISE = "REVISE"
    ABANDON = "ABANDON"
    BLOCKED = "BLOCKED"
    SUPERSEDED = "SUPERSEDED"
    RETRACTED = "RETRACTED"


class SafetyMode(StrEnum):
    """Control how conservatively uncertain policy state is handled."""

    STANDARD = "standard"
    STRICT = "strict"


class RunStatus(StrEnum):
    """Describe the terminal or in-progress state of an execution attempt."""

    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class EvidenceStatus(StrEnum):
    """Describe whether evidence remains usable by current claims."""

    CURRENT = "current"
    RETRACTED = "retracted"
    SUPERSEDED = "superseded"


class ClaimStatus(StrEnum):
    """Describe the human review state of a publication claim."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETRACTED = "retracted"
    SUPERSEDED = "superseded"


class VerificationStatus(StrEnum):
    """Describe the degree of human confirmation for reference metadata."""

    UNVERIFIED = "unverified"
    ENRICHED_UNVERIFIED = "enriched_unverified"
    VERIFIED = "verified"


class RepositoryVisibility(StrEnum):
    """Enumerate repository visibility states returned or attested by Git hosts."""

    UNKNOWN = "unknown"
    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"


class ProjectInfo(DurableModel):
    """Store manually supplied project identity and optional initial framing."""

    name: str
    slug: str
    author: str
    description: str | None = None
    question: str | None = None
    fields_of_study: list[str] = Field(default_factory=list)
    license: ProjectLicense = ProjectLicense.UNSPECIFIED
    created_at: str = Field(default_factory=utc_now)

    @field_validator("name", "slug", "author")
    @classmethod
    def non_empty(cls, value: str) -> str:
        """Reject blank identity fields while preserving intentional text."""
        if not value.strip():
            raise ValueError("must not be empty")
        return value.strip()

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str) -> str:
        """Require the project slug to remain path-safe."""
        return _validated_identifier(value, "project slug")

    @field_validator("fields_of_study")
    @classmethod
    def valid_fields_of_study(cls, values: list[str]) -> list[str]:
        """Trim fields and remove case-insensitive duplicates without reordering."""
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            field = value.strip()
            if not field:
                raise ValueError("fields of study must not contain blank values")
            key = field.casefold()
            if key not in seen:
                normalized.append(field)
                seen.add(key)
        return normalized


class DataPolicy(DurableModel):
    """Store the declared data classification and Git safety contract."""

    classification: DataClassification
    raw_data_in_git: bool = False


class EnvironmentConfig(DurableModel):
    """Identify the environment used to execute project experiments."""

    mode: EnvironmentMode = EnvironmentMode.NONE
    name: str | None = None
    prefix: str | None = None

    @model_validator(mode="after")
    def coherent_environment(self) -> EnvironmentConfig:
        """Require the selector needed by each managed environment mode."""
        if self.mode is EnvironmentMode.NEW_CONDA and not self.name:
            raise ValueError("new_conda environment requires a name")
        if self.mode is EnvironmentMode.EXISTING_CONDA and not (self.name or self.prefix):
            raise ValueError("existing_conda environment requires a name or prefix")
        return self


class GitConfig(DurableModel):
    """Record whether Git and SMAIRT-managed hooks are active."""

    enabled: bool = False
    managed_hooks: bool = False


class Contributor(DurableModel):
    """A manually confirmed person allowed to perform consequential actions."""

    id: str
    name: str
    email: str | None = None
    confirmed_at: str = Field(default_factory=utc_now)
    source: str = "manual"

    @field_validator("id")
    @classmethod
    def valid_id(cls, value: str) -> str:
        """Reject contributor IDs that could alter path or glob semantics."""
        import re

        if not re.fullmatch(IDENTIFIER_PATTERN, value):
            raise ValueError("invalid contributor identifier")
        return value


class RepositoryAttestation(DurableModel):
    """Record the one-time private-repository collaboration acknowledgment."""

    acknowledged: bool = False
    contributor_id: str | None = None
    acknowledged_at: str | None = None
    visibility: RepositoryVisibility = RepositoryVisibility.UNKNOWN


class MigrationEntry(DurableModel):
    """Record one applied schema migration without hiding its provenance."""

    from_version: int
    to_version: int
    applied_at: str = Field(default_factory=utc_now)
    contributor_id: str | None = None


class HarnessConfig(DurableModel):
    """Identify the one active coding harness and installed adapter version."""

    active: HarnessName = HarnessName.CODEX
    adapter_version: int = 1
    activated_at: str = Field(default_factory=utc_now)


class CredentialProfile(DurableModel):
    """Reference a secret without storing its value in project files."""

    profile: str = "default"
    environment_variable: str | None = None

    @field_validator("profile")
    @classmethod
    def valid_profile(cls, value: str) -> str:
        """Require a path-safe portable profile name."""
        return _validated_identifier(value, "credential profile")

    @field_validator("environment_variable")
    @classmethod
    def valid_environment_variable(cls, value: str | None) -> str | None:
        """Accept only portable environment-variable names, never shell expressions."""
        if value is not None and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
            raise ValueError("invalid credential environment-variable name")
        return value


class OpenAlexIntegration(DurableModel):
    """Configure optional OpenAlex supplementation."""

    enabled: bool = False
    credential: CredentialProfile = Field(
        default_factory=lambda: CredentialProfile(environment_variable="OPENALEX_API_KEY")
    )


class ZoteroIntegration(DurableModel):
    """Configure read-only local or Web Zotero access."""

    enabled: bool = False
    mode: ZoteroMode = ZoteroMode.DISABLED
    library_id: str | None = None
    library_type: ZoteroLibraryType = ZoteroLibraryType.USER
    credential: CredentialProfile = Field(
        default_factory=lambda: CredentialProfile(environment_variable="ZOTERO_API_KEY")
    )
    mcp_access_enabled: bool = False
    mcp_confirmed_by: str | None = None
    mcp_confirmed_at: str | None = None


class McpIntegration(DurableModel):
    """Record which maintained harnesses may start SMAIRT's read-only MCP."""

    enabled_harnesses: list[HarnessName] = Field(default_factory=list)

    @field_validator("enabled_harnesses")
    @classmethod
    def unique_supported_harnesses(cls, values: list[HarnessName]) -> list[HarnessName]:
        """Remove duplicate maintained harness entries."""
        return list(dict.fromkeys(values))


class IntegrationConfig(DurableModel):
    """Store non-secret literature and agent integration settings."""

    openalex: OpenAlexIntegration = Field(default_factory=OpenAlexIntegration)
    zotero: ZoteroIntegration = Field(default_factory=ZoteroIntegration)
    mcp: McpIntegration = Field(default_factory=McpIntegration)


class ActiveState(DurableModel):
    """Point to the current hypothesis, experiment, iteration, and accepted run."""

    hypothesis: str | None = None
    experiment: str | None = None
    iteration: str | None = None
    accepted_run: str | None = None

    @field_validator("hypothesis", "experiment", "iteration", "accepted_run")
    @classmethod
    def valid_ids(cls, value: str | None) -> str | None:
        """Reject active pointers that could alter path and glob resolution."""
        return _validated_identifier(value, "active artifact ID") if value else None


class SmairtConfig(DurableModel):
    """Define the authoritative, versioned project contract in smairt.yaml."""

    schema_version: int = 6
    smairt_version: str = Field(default_factory=lambda: __version__)
    project: ProjectInfo
    data: DataPolicy
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    harness: HarnessConfig = Field(default_factory=HarnessConfig)
    integrations: IntegrationConfig = Field(default_factory=IntegrationConfig)
    safety_mode: SafetyMode = SafetyMode.STANDARD
    contributors: list[Contributor] = Field(default_factory=list)
    active_contributor: str | None = None
    repository_attestation: RepositoryAttestation = Field(default_factory=RepositoryAttestation)
    migration_history: list[MigrationEntry] = Field(default_factory=list)
    active: ActiveState = Field(default_factory=ActiveState)

    @field_validator("schema_version")
    @classmethod
    def supported_schema(cls, value: int) -> int:
        """Reject beta schemas that this release cannot safely interpret."""
        if value not in {2, 3, 4, 5, 6}:
            raise ValueError(
                "incompatible project schema; migrate through a supported SMAIRT release"
            )
        return value

    @field_validator("active_contributor")
    @classmethod
    def valid_active_contributor(cls, value: str | None) -> str | None:
        """Validate the active contributor before it is used in event paths."""
        if value is not None:
            Contributor.valid_id(value)
        return value

    @model_validator(mode="after")
    def valid_relationships(self) -> SmairtConfig:
        """Ensure contributor pointers resolve inside the same durable record."""
        contributor_ids = {item.id for item in self.contributors}
        if len(contributor_ids) != len(self.contributors):
            raise ValueError("contributor IDs must be unique")
        if self.active_contributor and self.active_contributor not in contributor_ids:
            raise ValueError("active_contributor does not identify a registered contributor")
        attested_by = self.repository_attestation.contributor_id
        if attested_by and attested_by not in contributor_ids:
            raise ValueError("repository attestation contributor is not registered")
        zotero = self.integrations.zotero
        if bool(zotero.mcp_confirmed_by) != bool(zotero.mcp_confirmed_at):
            raise ValueError("Zotero MCP confirmation contributor and timestamp must be paired")
        if zotero.mcp_confirmed_by and zotero.mcp_confirmed_by not in contributor_ids:
            raise ValueError("Zotero MCP confirmation contributor is not registered")
        if self.data.classification is DataClassification.CONTROLLED and zotero.mcp_access_enabled:
            raise ValueError("controlled projects cannot enable Zotero MCP access")
        if (
            self.data.classification is DataClassification.PRIVATE
            and zotero.mcp_access_enabled
            and not zotero.mcp_confirmed_by
        ):
            raise ValueError("private projects require attributed Zotero MCP confirmation")
        return self

    def durable_dict(self) -> dict[str, Any]:
        """Return only fields defined by the project's declared schema version."""
        data = self.model_dump(mode="json", exclude_none=True)
        if self.schema_version < 4:
            data.pop("integrations", None)
        elif self.schema_version < 5:
            integrations = data.get("integrations")
            if isinstance(integrations, dict):
                zotero = integrations.get("zotero")
                if isinstance(zotero, dict):
                    zotero.pop("enabled", None)
        else:
            integrations = data.get("integrations")
            if isinstance(integrations, dict):
                openalex = integrations.get("openalex")
                if isinstance(openalex, dict):
                    openalex.pop("credential", None)
                zotero = integrations.get("zotero")
                if isinstance(zotero, dict):
                    for field in ("mode", "library_id", "library_type", "credential"):
                        zotero.pop(field, None)
        if self.schema_version < 3:
            project = data.get("project")
            if isinstance(project, dict):
                project.pop("fields_of_study", None)
                project.pop("license", None)
        return data

    def to_yaml(self) -> str:
        """Render version-aware durable YAML for transactions and managed writers."""
        return yaml.safe_dump(self.durable_dict(), sort_keys=False)

    @classmethod
    def load(cls, path: Path) -> SmairtConfig:
        """Parse and validate a project contract from YAML."""
        return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))

    def dump(self, path: Path) -> None:
        """Serialize the validated contract without implicit null fields."""
        atomic_write(path, self.to_yaml())


class ReferenceRecord(DurableModel):
    """Describe one indexed local scholarly reference and its checksum."""

    id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    document_type: str = "article"
    local_path: str | None = None
    sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
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
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    edit_history: list[dict[str, Any]] = Field(default_factory=list)
    added_at: str = Field(default_factory=utc_now)

    @field_validator("id", "citation_key")
    @classmethod
    def valid_identifier(cls, value: str | None) -> str | None:
        """Reject reference keys with path or glob metacharacters."""
        import re

        if value is not None and not re.fullmatch(IDENTIFIER_PATTERN, value):
            raise ValueError("invalid reference identifier")
        return value

    @field_validator("local_path")
    @classmethod
    def safe_local_path(cls, value: str | None) -> str | None:
        """Require a portable relative path contained by the project."""
        if value is None:
            return None
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("reference path must be project-relative")
        return value

    @model_validator(mode="after")
    def coherent_attachment(self) -> ReferenceRecord:
        """Require a path and checksum together when an attachment exists."""
        if (self.local_path is None) != (self.sha256 is None):
            raise ValueError("reference attachment path and checksum must be provided together")
        return self


class RunRecord(DurableModel):
    """Capture the immutable execution and provenance metadata for one run."""

    run_id: str
    experiment_id: str
    iteration_id: str
    status: RunStatus
    command: list[str]
    started_at: str
    completed_at: str | None = None
    exit_code: int | None = None
    working_directory: str
    log_path: str
    results_directory: str
    config_sha256: str | None = None
    git_commit: str | None = None
    git_dirty: bool = False
    environment: dict[str, Any] = Field(default_factory=dict)
    manifest_path: str | None = None

    @field_validator("run_id", "experiment_id", "iteration_id")
    @classmethod
    def valid_identifier(cls, value: str) -> str:
        """Reject execution IDs that could escape directories or broaden globs."""
        import re

        if not re.fullmatch(IDENTIFIER_PATTERN, value):
            raise ValueError("invalid run relationship identifier")
        return value

    @field_validator("working_directory", "log_path", "results_directory", "manifest_path")
    @classmethod
    def valid_relative_path(cls, value: str | None) -> str | None:
        """Require run paths to be portable and project-relative."""
        if value is None:
            return None
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("run path must be project-relative")
        return value

    @model_validator(mode="after")
    def coherent_lifecycle(self) -> RunRecord:
        """Require in-progress and terminal run fields to agree with status."""
        if self.status is RunStatus.STARTED:
            if self.completed_at is not None or self.exit_code is not None:
                raise ValueError("started runs cannot contain terminal fields")
        elif self.completed_at is None or self.exit_code is None:
            raise ValueError("terminal runs require completion time and exit code")
        if self.status is RunStatus.COMPLETED and self.exit_code != 0:
            raise ValueError("completed runs require exit code zero")
        if self.status is RunStatus.FAILED and self.exit_code == 0:
            raise ValueError("failed runs require a nonzero exit code")
        return self


class ProjectEvent(DurableModel):
    """Describe one immutable contributor-scoped consequential action."""

    schema_version: int = Field(default=1, ge=1, le=1)
    id: str
    timestamp: str
    actor: str
    action: str
    artifact_ids: list[str] = Field(default_factory=list)
    hashes: dict[str, str] = Field(default_factory=dict)
    git: dict[str, Any] = Field(default_factory=dict)
    supersedes: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id", "actor", "supersedes")
    @classmethod
    def valid_ids(cls, value: str | None) -> str | None:
        """Validate event identifiers before contributor-path use."""
        return _validated_identifier(value, "event identifier") if value else None


class CorrectionRecord(DurableModel):
    """Describe an amendment, retraction, or explicit run supersession."""

    id: str
    action: str
    target_run: str | None = None
    replacement_run: str | None = None
    reason: str
    contributor: str
    timestamp: str

    @field_validator("id", "target_run", "replacement_run", "contributor")
    @classmethod
    def valid_ids(cls, value: str | None) -> str | None:
        """Validate correction relationships before path lookup."""
        return _validated_identifier(value, "correction identifier") if value else None


class EvidenceCard(DurableModel):
    """Freeze an accepted run's result, limitations, and paper relevance."""

    schema_version: int = Field(default=1, ge=1, le=1)
    id: str
    run_id: str
    purpose: str
    observed_result: str
    limitations: str
    decision: str
    contributor: str
    status: EvidenceStatus = EvidenceStatus.CURRENT
    possible_paper_relevance: str = ""
    created_at: str
    run_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    replacement_run: str | None = None
    correction_id: str | None = None

    @field_validator("id", "run_id", "contributor", "replacement_run", "correction_id")
    @classmethod
    def valid_ids(cls, value: str | None) -> str | None:
        """Validate evidence relationships before file lookup."""
        return _validated_identifier(value, "evidence identifier") if value else None


class ClaimRecord(DurableModel):
    """Represent a human-reviewed claim linked to evidence and references."""

    schema_version: int = Field(default=1, ge=1, le=1)
    id: str
    statement: str
    evidence_ids: list[str]
    reference_ids: list[str] = Field(default_factory=list)
    status: ClaimStatus
    proposed_by: str
    created_at: str
    reviewed_by: str | None = None
    reviewed_at: str | None = None

    @field_validator("id", "proposed_by", "reviewed_by")
    @classmethod
    def valid_id(cls, value: str | None) -> str | None:
        """Validate the claim filename identifier."""
        return _validated_identifier(value, "claim identifier") if value else None

    @field_validator("evidence_ids", "reference_ids")
    @classmethod
    def valid_relationship_ids(cls, values: list[str]) -> list[str]:
        """Validate and deduplicate every evidence and reference relationship."""
        validated = [_validated_identifier(value, "claim relationship") for value in values]
        if len(set(validated)) != len(validated):
            raise ValueError("claim relationships must be unique")
        return validated


class SummaryRecord(DurableModel):
    """Represent an immutable contributor summary of one source hash."""

    schema_version: int = Field(default=1, ge=1, le=1)
    id: str
    contributor: str
    source_id: str
    source_path: str
    source_sha256: str
    content: str
    shareable: bool = False
    redaction_confirmed: bool = False
    tracked: bool = True
    status: EvidenceStatus = EvidenceStatus.CURRENT
    created_at: str

    @field_validator("source_sha256")
    @classmethod
    def valid_source_hash(cls, value: str) -> str:
        """Require an exact lowercase SHA-256 digest for the summarized source."""
        import re

        if not re.fullmatch(r"[a-f0-9]{64}", value):
            raise ValueError("summary source hash must be a SHA-256 digest")
        return value

    @field_validator("id", "contributor", "source_id")
    @classmethod
    def valid_ids(cls, value: str) -> str:
        """Validate summary identifiers before path lookup."""
        return _validated_identifier(value, "summary identifier")

    @field_validator("source_path")
    @classmethod
    def valid_source_path(cls, value: str) -> str:
        """Require summary sources to remain inside the project."""
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("summary source path must be project-relative")
        return value


class ContextCapsule(DurableModel):
    """Describe a token-budgeted set of selected and deferred context files."""

    task: str
    token_budget: int
    estimated_tokens: int
    read: list[str]
    included: list[dict[str, Any]]
    deferred: list[dict[str, Any]]


class ValidationFinding(DurableModel):
    """Represent a stable machine-readable validation finding."""

    severity: str
    code: str
    artifact: str
    message: str


class NextAction(DurableModel):
    """Describe one state-aware action offered by `smairt next`."""

    id: str
    label: str
    kind: str
    requires_human: bool = False


class HumanGate(DurableModel):
    """Describe an action that cannot proceed without explicit human input."""

    id: str
    action: str
    prompt: str
    contributor_required: bool = True


class PaperBuild(DurableModel):
    """Record one versioned manuscript build and its checksums."""

    format: str
    manuscript_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    output_path: str
    output_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    built_at: str

    @field_validator("output_path")
    @classmethod
    def valid_output_path(cls, value: str) -> str:
        """Require build outputs to remain portable project-relative paths."""
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("paper output path must be project-relative")
        return value


def _validated_identifier(value: str, label: str) -> str:
    """Validate a durable identifier without importing filesystem helpers."""
    import re

    if not re.fullmatch(IDENTIFIER_PATTERN, value):
        raise ValueError(f"invalid {label}")
    return value
