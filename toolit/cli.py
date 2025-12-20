"""CLI entry point for the toolit package."""
from toolit.auto_loader import register_all_tools_from_folder_and_plugin
from toolit.create_apps_and_register import app

register_all_tools_from_folder_and_plugin()

if __name__ == "__main__":
    # Run the typer app
    app()
