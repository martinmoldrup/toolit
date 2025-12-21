"""Register all tools and plugins to be used by default."""
from toolit.auto_loader import load_tools_from_folder, load_tools_from_plugins
from toolit.config import load_devtools_folder
from toolit.constants import RichHelpPanelNames
from toolit.create_apps_and_register import register_command
from toolit.create_tasks_json import create_vscode_tasks_json


def register_all_tools_from_folder_and_plugin() -> None:
    """Load and register all tools that will be used by default."""
    load_tools_from_folder(load_devtools_folder())
    load_tools_from_plugins()
    register_command(create_vscode_tasks_json, rich_help_panel=RichHelpPanelNames.PLUGINS_COMMANDS_PANEL)
