"""CLI entry point for the toolit package."""
import pathlib
from .auto_loader import load_tools_from_folder, load_tools_from_plugins, register_command
from .create_apps_and_register import app
from .create_tasks_json import create_vscode_tasks_json

PATH = pathlib.Path() / "devtools"
load_tools_from_folder(PATH)
load_tools_from_plugins()
register_command(create_vscode_tasks_json)


if __name__ == "__main__":
    # Run the typer app
    app()
