"""CLI entry point for the toolit package."""
import pathlib
import importlib.metadata
from .auto_loader import load_tools_from_folder, register_command
from .create_apps_and_register import app
from .create_tasks_json import create_vscode_tasks_json
from typing import Any


def register_plugins() -> None:
    """Discover and register plugin commands via entry points."""
    for entry_point in importlib.metadata.entry_points().get("toolit_plugins", []):
        plugin_func: Any = entry_point.load()
        register_command(plugin_func)


PATH = pathlib.Path() / "devtools"
load_tools_from_folder(PATH)
register_command(create_vscode_tasks_json)
register_plugins()

if __name__ == "__main__":
    # Run the typer app
    app()
