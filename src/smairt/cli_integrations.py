"""Credential and read-only literature-integration CLI commands."""

from __future__ import annotations

import getpass
from pathlib import Path
from typing import Annotated, cast

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
from smairt.local_setup import (
    ConnectionProfile,
    ProviderName,
    configure_profile,
    delete_profile,
    load_bindings,
    load_user_setup,
    test_profile,
)
from smairt.models import SmairtConfig, ZoteroLibraryType, ZoteroMode
from smairt.zotero import ZoteroProvider

credential_app = typer.Typer(help="Manage credential profiles without storing secrets in files")
integration_app = typer.Typer(help="Configure read-only literature integrations")
setup_connection_app = typer.Typer(help="Manage user-local provider connection profiles")
setup_zotero_app = typer.Typer(help="Configure user-local Zotero profiles")
setup_openalex_app = typer.Typer(help="Configure user-local OpenAlex profiles")
zotero_app = typer.Typer(help="Configure and test read-only Zotero access")
openalex_app = typer.Typer(help="Configure optional OpenAlex supplementation")
integration_app.add_typer(zotero_app, name="zotero")
integration_app.add_typer(openalex_app, name="openalex")
setup_connection_app.add_typer(setup_zotero_app, name="zotero")
setup_connection_app.add_typer(setup_openalex_app, name="openalex")


def _v4_config() -> tuple[Path, SmairtConfig]:
    root = project_root()
    config = SmairtConfig.load(root / "smairt.yaml")
    if config.schema_version < 4:
        raise ValueError("integration settings require schema v4; run 'smairt migrate apply'")
    return root, config


@credential_app.command("list")
def credential_list(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List configured credential references and resolution sources, never values."""
    entries = []
    for name, connection in load_user_setup().profiles.items():
        try:
            _, resolution = resolve_credential(
                connection.provider,
                connection.credential_profile,
                connection.environment_variable,
            )
            source = resolution.source if resolution else "missing"
        except RuntimeError:
            source = "keyring-unavailable"
        entries.append(
            {
                "provider": connection.provider,
                "connection_profile": name,
                "credential_profile": connection.credential_profile,
                "source": source,
            }
        )
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


@setup_connection_app.command("list")
def setup_connection_list(
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List secret-free user-local connection profile summaries."""
    entries = [
        {
            "name": name,
            "provider": profile.provider,
            "mode": profile.mode.value if profile.mode else None,
        }
        for name, profile in load_user_setup().profiles.items()
    ]
    emit(entries, as_json)


@setup_zotero_app.command("configure")
def setup_zotero_configure(
    name: Annotated[str, typer.Argument()] = "default",
    mode: Annotated[ZoteroMode, typer.Option()] = ZoteroMode.LOCAL,
    library_id: Annotated[str | None, typer.Option()] = None,
    library_type: Annotated[ZoteroLibraryType, typer.Option()] = ZoteroLibraryType.USER,
    environment_variable: Annotated[str, typer.Option("--env-var")] = "ZOTERO_API_KEY",
) -> None:
    """Create a secret-free local or Web Zotero connection profile."""
    if mode is ZoteroMode.DISABLED:
        raise typer.BadParameter("setup profiles use local or web mode; remove profiles explicitly")
    profile = configure_profile(
        name,
        ConnectionProfile(
            provider="zotero",
            credential_profile=name,
            environment_variable=environment_variable,
            mode=mode,
            library_id=library_id,
            library_type=library_type if mode is ZoteroMode.WEB else None,
        ),
    )
    emit({"name": name, "provider": profile.provider, "mode": profile.mode}, False)


@setup_zotero_app.command("test")
def setup_zotero_test(name: Annotated[str, typer.Argument()] = "default") -> None:
    """Test one user-local Zotero profile with a bounded request."""
    emit(test_profile(name), False)


@setup_zotero_app.command("remove")
def setup_zotero_remove(name: Annotated[str, typer.Argument()] = "default") -> None:
    """Remove a Zotero profile without deleting its separately stored key."""
    emit({"name": name, "removed": delete_profile(name)}, False)


@setup_openalex_app.command("configure")
def setup_openalex_configure(
    name: Annotated[str, typer.Argument()] = "default",
    environment_variable: Annotated[str, typer.Option("--env-var")] = "OPENALEX_API_KEY",
) -> None:
    """Create a user-local OpenAlex connection profile."""
    profile = configure_profile(
        name,
        ConnectionProfile(
            provider="openalex",
            credential_profile=name,
            environment_variable=environment_variable,
        ),
    )
    emit({"name": name, "provider": profile.provider}, False)


@setup_openalex_app.command("test")
def setup_openalex_test(name: Annotated[str, typer.Argument()] = "default") -> None:
    """Test one OpenAlex key and report secret-free allowance status."""
    emit(test_profile(name), False)


@setup_openalex_app.command("remove")
def setup_openalex_remove(name: Annotated[str, typer.Argument()] = "default") -> None:
    """Remove an OpenAlex profile without deleting its separately stored key."""
    emit({"name": name, "removed": delete_profile(name)}, False)


@integration_app.command("bind")
def integration_bind(
    provider: Annotated[str, typer.Argument()], profile: Annotated[str, typer.Argument()]
) -> None:
    """Bind a user-local profile to the current project checkout."""
    if provider not in {"openalex", "zotero"}:
        raise typer.BadParameter("provider must be openalex or zotero")
    root = project_root()
    selected = load_user_setup().profiles.get(profile)
    if selected is None or selected.provider != provider:
        raise typer.BadParameter(f"no {provider} profile named {profile!r} exists")
    if provider == "openalex":
        result = configure_openalex(
            root,
            enabled=True,
            profile=profile,
            environment_variable=selected.environment_variable or "OPENALEX_API_KEY",
        )
    else:
        result = configure_zotero(
            root,
            mode=selected.mode or ZoteroMode.LOCAL,
            library_id=selected.library_id,
            library_type=selected.library_type or ZoteroLibraryType.USER,
            profile=profile,
        )
    emit({"provider": provider, "profile": profile, "status": result}, False)


@integration_app.command("unbind")
def integration_unbind(provider: Annotated[str, typer.Argument()]) -> None:
    """Remove a checkout-local binding and disable its shared project policy."""
    if provider not in {"openalex", "zotero"}:
        raise typer.BadParameter("provider must be openalex or zotero")
    root = project_root()
    removed = bool(load_bindings(root).providers.get(cast(ProviderName, provider)))
    if provider == "openalex":
        configure_openalex(root, enabled=False, profile="default")
    else:
        configure_zotero(
            root,
            mode=ZoteroMode.DISABLED,
            library_id=None,
            library_type=ZoteroLibraryType.USER,
            profile="default",
        )
    emit({"provider": provider, "unbound": removed}, False)


@integration_app.command("status")
def integration_status(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Show shared policy and local binding readiness for both providers."""
    root = project_root()
    from smairt.integrations import integration_health

    emit(
        {
            "bindings": load_bindings(root).model_dump(mode="json"),
            "health": integration_health(root),
        },
        as_json,
    )


@integration_app.command("test")
def integration_test(
    provider: Annotated[str, typer.Argument()],
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Test the profile bound to this checkout for one provider."""
    if provider not in {"openalex", "zotero"}:
        raise typer.BadParameter("provider must be openalex or zotero")
    name = load_bindings(project_root()).providers.get(cast(ProviderName, provider))
    if not name:
        raise typer.BadParameter(f"{provider} is not bound on this machine")
    emit(test_profile(name), as_json)
