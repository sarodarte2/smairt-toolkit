import asyncio
from pathlib import Path

from smairt.tui import NewProjectApp, ProjectMenuApp


def test_new_project_tui_mounts(tmp_path: Path) -> None:
    async def exercise() -> None:
        app = NewProjectApp(tmp_path / "tui-project")
        async with app.run_test(size=(100, 50)) as pilot:
            await pilot.pause()
            assert app.query_one("#name")
            assert app.query_one("#author")
            assert app.query_one("#classification")
            assert app.query_one("#environment")

    asyncio.run(exercise())

def test_project_menu_mounts(tmp_path: Path) -> None:
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
        app = ProjectMenuApp(root)
        async with app.run_test(size=(100, 50)) as pilot:
            await pilot.pause()
            assert "TUI" in str(app.query_one(".title").render())

    asyncio.run(exercise())
