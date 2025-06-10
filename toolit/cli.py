"""CLI entry point for the toolit package."""
import pathlib
from .auto_loader import load_tools_from_folder
from .create_apps_and_register import app

PATH = pathlib.Path() / "devtools"
load_tools_from_folder(PATH)

if __name__ == "__main__":
    # Run the typer app
    app()
