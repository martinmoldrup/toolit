"""CLI entry point for the toolit package."""
from toolit.create_apps_and_register import app
from toolit.register_all_tool_and_plugins import register_all_tools_from_folder_and_plugin

_registration_done: bool = False


def _ensure_tools_registered() -> None:
    """Register tools once for both app and module/script entrypoints."""
    global _registration_done
    if _registration_done:
        return
    register_all_tools_from_folder_and_plugin()
    _registration_done = True


def main() -> None:
    """Register tools and run the Typer application."""
    _ensure_tools_registered()
    app()


# Keep compatibility with existing installed console scripts pointing to `toolit.cli:app`.
_ensure_tools_registered()

if __name__ == "__main__":
    main()
