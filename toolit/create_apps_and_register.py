"""CLI and optional MCP server for Toolit project."""

from __future__ import annotations

import inspect
import os
import subprocess
from functools import wraps
import typer
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from toolit.constants import MARKER_TOOL, ToolitTypesEnum

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


def register_command(
    command_func: Callable[..., Any],
    name: str | None = None,
    rich_help_panel: str | None = None,
) -> None:
    """Register an external command to the CLI and MCP server if available."""
    if not callable(command_func):
        msg = f"Command function {command_func} is not callable."
        raise TypeError(msg)

    command_to_register = command_func
    if getattr(command_func, MARKER_TOOL, None) == ToolitTypesEnum.CLITOOL:
        command_to_register = _create_clitool_runtime_wrapper(command_func)

    app.command(name=name, rich_help_panel=rich_help_panel)(command_to_register)

    if mcp is not None and getattr(command_func, MARKER_TOOL, None) != ToolitTypesEnum.CLITOOL:
        mcp.tool(name)(command_func)


def _create_clitool_runtime_wrapper(command_func: Callable[..., Any]) -> Callable[..., None]:
    """Wrap a clitool function so its returned command string runs in a shell."""

    @wraps(command_func)
    def _wrapped(*args: Any, **kwargs: Any) -> None:
        command = command_func(*args, **kwargs)
        if not isinstance(command, str):
            typer.secho(
                f"Error: clitool '{command_func.__name__}' must return a string command, got {type(command).__name__}.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)

        command_to_run: str = command.strip()
        if not command_to_run:
            typer.secho(
                f"Error: clitool '{command_func.__name__}' returned an empty command.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)

        if os.name == "nt":
            # Use PowerShell on Windows so command quoting matches interactive pwsh usage.
            result = subprocess.run(["pwsh", "-NoProfile", "-Command", command_to_run], check=False)
        else:
            result = subprocess.run(command_to_run, shell=True, check=False)  # noqa: S602
        if result.returncode != 0:
            raise typer.Exit(code=result.returncode)

    _wrapped.__signature__ = inspect.signature(command_func)
    return _wrapped
