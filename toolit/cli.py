"""CLI entry point for the toolit package."""

from toolit.create_apps_and_register import app
from toolit.register_all_tool_and_plugins import register_all_tools_from_folder_and_plugin

register_all_tools_from_folder_and_plugin()


def main() -> None:
    """Register tools and run the Typer application."""
    app()


if __name__ == "__main__":
    main()
