from toolit.auto_loader import load_tools_from_folder
import pathlib
from toolit.create_apps_and_register import mcp

PATH = pathlib.Path() / "devtools"
load_tools_from_folder(PATH)

if __name__ == "__main__":
    # Run the typer app
    mcp.run()