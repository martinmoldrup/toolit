"""CLI entry point for the toolit package."""
from .auto_loader import load_tools_from_folder, load_tools_from_plugins, register_command
from .config import load_devtools_folder
from .create_apps_and_register import app
from .create_tasks_json import create_vscode_tasks_json

load_tools_from_folder(load_devtools_folder())
load_tools_from_plugins()
register_command(create_vscode_tasks_json)


if __name__ == "__main__":
    # Run the typer app
    app()
