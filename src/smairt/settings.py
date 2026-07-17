"""Transactional researcher-facing project and environment settings."""

from __future__ import annotations

from pathlib import Path

import yaml

from smairt.licenses import license_manifest, render_license, verify_managed_license
from smairt.local_setup import normalize_fields_of_study
from smairt.locking import mutating
from smairt.models import EnvironmentConfig, EnvironmentMode, ProjectLicense, SmairtConfig
from smairt.provenance import require_contributor, stage_event
from smairt.scaffold import create_conda_environment
from smairt.transactions import FileTransaction


def _config_text(config: SmairtConfig) -> str:
    """Render one already-validated project contract deterministically."""
    rendered = config.to_yaml()
    SmairtConfig.model_validate(yaml.safe_load(rendered))
    return rendered


@mutating("project settings update")
def update_project_settings(
    root: Path,
    *,
    name: str,
    author: str,
    question: str | None,
    description: str | None,
    fields_of_study: list[str],
    license_name: ProjectLicense,
) -> SmairtConfig:
    """Update project metadata and its managed license through one transaction."""
    contributor = require_contributor(root)
    config = SmairtConfig.load(root / "smairt.yaml").model_copy(deep=True)
    if config.schema_version < 3:
        raise ValueError("project settings require schema v3; run 'smairt migrate apply'")
    previous_license = config.project.license
    if license_name != previous_license:
        verify_managed_license(root)
    config.project.name = name
    config.project.author = author
    config.project.question = question
    config.project.description = description
    config.project.fields_of_study = normalize_fields_of_study(fields_of_study)
    config.project.license = license_name
    transaction = FileTransaction(root, "project settings update")
    transaction.stage_text(root / "smairt.yaml", _config_text(config))
    if license_name != previous_license:
        content = render_license(license_name, author)
        if content is None:
            transaction.stage_delete(root / "LICENSE")
            transaction.stage_delete(root / ".smairt/license.json")
        else:
            transaction.stage_text(root / "LICENSE", content)
            transaction.stage_text(
                root / ".smairt/license.json", license_manifest(license_name, content)
            )
    stage_event(
        root,
        transaction,
        "project.settings.updated",
        artifact_ids=["smairt.yaml", "LICENSE"],
        details={"contributor": contributor.id, "license": license_name.value},
    )
    transaction.commit()
    return config


@mutating("environment select")
def select_environment(
    root: Path,
    *,
    mode: EnvironmentMode,
    name: str | None = None,
    prefix: str | None = None,
    create: bool = False,
) -> EnvironmentConfig:
    """Select a validated Conda environment after optional successful creation."""
    contributor = require_contributor(root)
    if create:
        if mode is not EnvironmentMode.NEW_CONDA or not name:
            raise ValueError("environment creation requires new_conda mode and a name")
        create_conda_environment(name)
    environment = EnvironmentConfig(mode=mode, name=name, prefix=prefix)
    config = SmairtConfig.load(root / "smairt.yaml").model_copy(deep=True)
    config.environment = environment
    transaction = FileTransaction(root, "environment select")
    transaction.stage_text(root / "smairt.yaml", _config_text(config))
    stage_event(
        root,
        transaction,
        "environment.selected",
        artifact_ids=["smairt.yaml"],
        details={"contributor": contributor.id, "mode": mode.value},
    )
    transaction.commit()
    return environment
