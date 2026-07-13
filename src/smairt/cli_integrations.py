"""Credential and read-only literature-integration CLI commands."""

from __future__ import annotations

import getpass
from pathlib import Path
from typing import Annotated

import typer

from smairt.cli_shared import emit, project_root
from smairt.credentials import (
    SUPPORTED_PROVIDERS,
    delete_credential,
    keyring_health,
    resolve_credential,
    set_credential,
)
from smairt.integrations import (
    configure_openalex,
    configure_zotero,
    openalex_status,
)
from smairt.integrations import (
    zotero_status as get_zotero_status,
)
from smairt.models import SmairtConfig, ZoteroLibraryType, ZoteroMode
from smairt.zotero import ZoteroProvider

credential_app = typer.Typer(help="Manage credential profiles without storing secrets in files")
integration_app = typer.Typer(help="Configure read-only literature integrations")
zotero_app = typer.Typer(help="Configure and test read-only Zotero access")
openalex_app = typer.Typer(help="Configure optional OpenAlex supplementation")
integration_app.add_typer(zotero_app, name="zotero")
integration_app.add_typer(openalex_app, name="openalex")


def _v4_config() -> tuple[Path, SmairtConfig]:
    root = project_root()
    config = SmairtConfig.load(root / "smairt.yaml")
    if config.schema_version < 4:
        raise ValueError("integration settings require schema v4; run 'smairt migrate apply'")
    return root, config


@credential_app.command("list")
def credential_list(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List configured credential references and resolution sources, never values."""
    _, config = _v4_config()
    entries = []
    for provider, reference in (
        ("openalex", config.integrations.openalex.credential),
        ("zotero", config.integrations.zotero.credential),
    ):
        try:
            _, resolution = resolve_credential(
                provider, reference.profile, reference.environment_variable
            )
            source = resolution.source if resolution else "missing"
        except RuntimeError:
            source = "keyring-unavailable"
        entries.append({"provider": provider, "profile": reference.profile, "source": source})
    emit(entries, as_json)


@credential_app.command("set")
def credential_set(
    provider: Annotated[str, typer.Argument()],
    profile: Annotated[str, typer.Option()] = "default",
) -> None:
    """Prompt invisibly and store one credential in the OS keyring."""
    if provider not in SUPPORTED_PROVIDERS:
        raise typer.BadParameter("provider must be openalex or zotero")
    value = getpass.getpass(f"{provider} credential: ")
    set_credential(provider, profile, value)
    emit({"provider": provider, "profile": profile, "stored": True}, False)


@credential_app.command("delete")
def credential_delete(
    provider: Annotated[str, typer.Argument()],
    profile: Annotated[str, typer.Option()] = "default",
) -> None:
    """Delete a named OS-keyring credential."""
    emit(
        {"provider": provider, "profile": profile, "deleted": delete_credential(provider, profile)},
        False,
    )


@credential_app.command("doctor")
def credential_doctor(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Report keyring backend health without reading credentials."""
    emit(keyring_health(), as_json)


@openalex_app.command("configure")
def openalex_configure(
    enabled: Annotated[bool, typer.Option("--enabled/--disabled")] = True,
    profile: Annotated[str, typer.Option()] = "default",
    environment_variable: Annotated[str, typer.Option("--env-var")] = "OPENALEX_API_KEY",
) -> None:
    """Configure a non-secret OpenAlex credential reference."""
    emit(
        configure_openalex(
            project_root(),
            enabled=enabled,
            profile=profile,
            environment_variable=environment_variable,
        ),
        False,
    )


@openalex_app.command("status")
def openalex_status_command(
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show non-secret OpenAlex configuration without contacting it."""
    emit(openalex_status(project_root()), as_json)


@zotero_app.command("configure")
def zotero_configure(
    mode: Annotated[ZoteroMode, typer.Option()],
    library_id: Annotated[str | None, typer.Option()] = None,
    library_type: Annotated[ZoteroLibraryType, typer.Option()] = ZoteroLibraryType.USER,
    profile: Annotated[str, typer.Option()] = "default",
    environment_variable: Annotated[str, typer.Option("--env-var")] = "ZOTERO_API_KEY",
    enable_mcp: Annotated[bool, typer.Option("--enable-mcp")] = False,
    confirm_agent_access: Annotated[bool, typer.Option("--confirm-agent-access")] = False,
) -> None:
    """Configure local or Web read-only Zotero access without a secret value."""
    emit(
        configure_zotero(
            project_root(),
            mode=mode,
            library_id=library_id,
            library_type=library_type,
            profile=profile,
            environment_variable=environment_variable,
            mcp_access_enabled=enable_mcp,
            confirm_agent_access=confirm_agent_access,
        ),
        False,
    )


@zotero_app.command("status")
def zotero_status(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Show non-secret Zotero configuration and credential availability."""
    emit(get_zotero_status(project_root()), as_json)


@zotero_app.command("test")
def zotero_test(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Explicitly contact the configured Zotero endpoint with a bounded request."""
    provider = ZoteroProvider(project_root())
    collections = provider.collections(1)
    emit({"ok": True, "collections_returned": len(collections), "network_accessed": True}, as_json)
