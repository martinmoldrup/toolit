"""CLI entry point for the toolit package."""
from toolit.auto_loader import load_tools_from_folder, load_tools_from_plugins, register_command
from toolit.config import load_devtools_folder
from toolit.constants import RichHelpPanelNames
from toolit.create_apps_and_register import app
from toolit.create_tasks_json import create_vscode_tasks_json

load_tools_from_folder(load_devtools_folder())
load_tools_from_plugins()
register_command(create_vscode_tasks_json, rich_help_panel=RichHelpPanelNames.PLUGINS_COMMANDS_PANEL)


if __name__ == "__main__":
    # Run the typer app
    app()
