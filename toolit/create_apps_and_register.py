"""CLI and MCP server for Toolit project."""
from collections.abc import Callable
import typer
from mcp.server.fastmcp import FastMCP

# Initialize the Typer app
app = typer.Typer()
# Initialize the MCP server with a name
mcp = FastMCP("Toolit MCP Server")


def register_command(command_func: Callable, name: str | None = None) -> None:
    """Register an external command to the CLI."""
    if not callable(command_func):
        raise ValueError(f"Command function {command_func} is not callable.")
    if name:
        app.command(name=name)(command_func)
        mcp.tool(name)(command_func)
    else:
        app.command()(command_func)
        mcp.tool()(command_func)
