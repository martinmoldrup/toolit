"""MCP server for the toolit package."""
import pathlib
from toolit.auto_loader import load_tools_from_folder
from toolit.create_apps_and_register import mcp

PATH = pathlib.Path() / "devtools"
load_tools_from_folder(PATH)

if __name__ == "__main__":
    # Run the typer app
    if mcp is None:
        msg = (
            "FastMCP is not available. "
            "Please install it to use the MCP server. Use `pip install mcp[cli]` to install it."
        )
        raise ImportError(
            msg,
        )
    mcp.run()
