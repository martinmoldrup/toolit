"""CLI and optional MCP server for Toolit project."""

from __future__ import annotations

import typer
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP
    _has_mcp: bool = True
else:
    # Make MCP optional
    try:
        from mcp.server.fastmcp import FastMCP
        _has_mcp = True
    except ImportError:
        FastMCP: Any = None  # type: ignore[no-redef]
        _has_mcp = False

# Initialize the Typer app
app: typer.Typer = typer.Typer(no_args_is_help=True)
# Initialize the MCP server with a name, if available
mcp: FastMCP | None = FastMCP("Toolit MCP Server") if _has_mcp else None


@app.callback()
def initialize() -> None:
    """Welcome to the Toolit CLI."""


def register_command(command_func: Callable[..., Any], name: str | None = None) -> None:
    """Register an external command to the CLI and MCP server if available."""
    if not callable(command_func):
        msg = f"Command function {command_func} is not callable."
        raise TypeError(msg)
    app.command(name=name)(command_func)
    if mcp is not None:
        mcp.tool(name)(command_func)
