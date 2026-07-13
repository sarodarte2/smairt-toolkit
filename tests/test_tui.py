"""Textual interface tests for safe creation and existing-project dashboards."""

import asyncio
from pathlib import Path

from textual.widgets import Button, Input, Static

from smairt.tui import NewProjectApp, ProjectMenuApp


def test_new_project_tui_mounts(tmp_path: Path) -> None:
    """Verify the creation wizard exposes every required low-friction field."""

    async def exercise() -> None:
        """Mount the wizard in Textual's isolated test driver."""
        app = NewProjectApp(tmp_path / "tui-project")
        async with app.run_test(size=(100, 50)) as pilot:
            await pilot.pause()
            assert app.query_one("#name")
            assert app.query_one("#author")
            assert app.query_one("#classification")
            assert app.query_one("#environment")

    asyncio.run(exercise())


def test_new_project_preflights_nonempty_destination(tmp_path: Path) -> None:
    """Explain non-empty destinations before creation can leave partial output."""
    destination = tmp_path / "partial"
    destination.mkdir()
    (destination / "leftover").mkdir()

    async def exercise() -> None:
        """Submit the preview action and inspect its non-destructive warning."""
        app = NewProjectApp(destination)
        async with app.run_test(size=(100, 50)) as pilot:
            app.query_one("#name", Input).value = "Test Project"
            app.query_one("#author", Input).value = "Manual Researcher"
            app.query_one("#submit", Button).press()
            await pilot.pause()
            message = str(app.query_one("#message", Static).render())
            assert "Choose a new empty folder" in message
            assert not app.previewing
            assert not (destination / "smairt.yaml").exists()

    asyncio.run(exercise())


def test_project_menu_mounts(tmp_path: Path) -> None:
    """Verify the existing-project dashboard renders project identity."""
    from smairt.models import DataClassification, EnvironmentMode
    from smairt.scaffold import create_project

    root = tmp_path / "project"
    create_project(
        root,
        name="TUI",
        author="Researcher",
        classification=DataClassification.PUBLIC,
        initialize_git=False,
        environment_mode=EnvironmentMode.NONE,
    )

    async def exercise() -> None:
        """Mount the project dashboard and inspect its visible title."""
        app = ProjectMenuApp(root)
        async with app.run_test(size=(100, 50)) as pilot:
            await pilot.pause()
            assert "TUI" in str(app.query_one(".title").render())

    asyncio.run(exercise())
