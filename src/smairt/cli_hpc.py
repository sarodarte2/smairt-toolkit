"""Compact advanced CLI for optional Slurm execution."""

from __future__ import annotations

from typing import Annotated

import typer

from smairt.cli_shared import emit, project_root
from smairt.hpc import cancel_job, refresh_job, sync_job
from smairt.local_setup import SlurmProfile, configure_slurm_profile, load_user_setup
from smairt.models import ComputeMode

hpc_app = typer.Typer(help="Inspect and reconcile optional Slurm jobs")
setup_hpc_app = typer.Typer(help="Configure an optional user-local Slurm submit host")


@setup_hpc_app.command("configure")
def configure_slurm(
    name: Annotated[str, typer.Argument()] = "default",
    mode: Annotated[ComputeMode, typer.Option()] = ComputeMode.NATIVE,
    remote_root: Annotated[str, typer.Option("--remote-root")] = "/shared/smairt-jobs",
    host: Annotated[str | None, typer.Option("--host")] = None,
) -> None:
    """Configure native Slurm or an existing OpenSSH host alias."""
    profile = configure_slurm_profile(
        name,
        SlurmProfile(mode=mode, remote_root=remote_root, host_alias=host),
    )
    emit({"profile": name, **profile.model_dump(mode="json", exclude_none=True)}, False)


@setup_hpc_app.command("status")
def setup_status(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Show configured profile names without probing a cluster."""
    setup = load_user_setup()
    emit(
        {
            "default": setup.default_compute_profile,
            "profiles": {
                name: profile.model_dump(mode="json", exclude_none=True)
                for name, profile in setup.compute_profiles.items()
            },
            "network_accessed": False,
        },
        as_json,
    )


@hpc_app.command("status")
def job_status(
    run_id: Annotated[str, typer.Argument()],
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Refresh and show one Slurm job state."""
    emit(refresh_job(project_root(), run_id).model_dump(mode="json", exclude_none=True), as_json)


@hpc_app.command("sync")
def job_sync(
    run_id: Annotated[str, typer.Argument()],
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Retrieve terminal outputs and finalize the local run when ready."""
    job, record = sync_job(project_root(), run_id)
    emit(
        {
            "job": job.model_dump(mode="json", exclude_none=True),
            "run": record.model_dump(mode="json", exclude_none=True) if record else None,
        },
        as_json,
    )


@hpc_app.command("cancel")
def job_cancel(
    run_id: Annotated[str, typer.Argument()],
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    """Cancel one explicitly selected Slurm job."""
    if not yes:
        raise typer.BadParameter("cancellation requires --yes")
    emit(cancel_job(project_root(), run_id).model_dump(mode="json", exclude_none=True), False)
