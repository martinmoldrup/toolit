"""CLI and optional MCP server for Toolit project."""

from __future__ import annotations

import os
import shlex
import typer
import inspect
import subprocess  # noqa: S404
from collections.abc import Callable
from functools import wraps
from toolit.constants import (
    MARKER_TOOL,
    ToolitTypesEnum,
)
from toolit.type_coersion_wrapper import create_type_coercion_wrapper
from typing import TYPE_CHECKING, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP  # type: ignore[import-not-found]

    _has_mcp: bool = True
else:
    # Make MCP optional
    try:
        from mcp.server.fastmcp import FastMCP

        _has_mcp = True
    except ImportError:
        FastMCP = None  # type: ignore[assignment,no-redef]
        _has_mcp = False

# Initialize the Typer app
app: typer.Typer = typer.Typer(no_args_is_help=True)
# Initialize the MCP server with a name, if available
mcp: FastMCP | None = FastMCP("Toolit MCP Server") if _has_mcp else None


@app.callback()
def initialize() -> None:
    """Welcome to the Toolit CLI."""


def register_command(
    command_func: Callable[..., R],
    name: str | None = None,
    rich_help_panel: str | None = None,
) -> None:
    """Register an external command to the CLI and MCP server if available."""
    if not callable(command_func):
        msg = f"Command function {command_func} is not callable."
        raise TypeError(msg)

    command_to_register = create_type_coercion_wrapper(command_func)
    if getattr(command_func, MARKER_TOOL, None) == ToolitTypesEnum.CLITOOL:
        app.command(name=name, rich_help_panel=rich_help_panel)(
            create_clitool_runtime_wrapper(command_to_register),
        )
    else:
        app.command(name=name, rich_help_panel=rich_help_panel)(command_to_register)

    if mcp is not None and getattr(command_func, MARKER_TOOL, None) != ToolitTypesEnum.CLITOOL:
        mcp.tool(name)(command_func)


def create_clitool_runtime_wrapper(command_func: Callable[P, R]) -> Callable[P, None]:
    """Wrap a clitool function so its returned command string runs in a shell."""

    @wraps(command_func)
    def _wrapped(*args: P.args, **kwargs: P.kwargs) -> None:
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
            result = subprocess.run(["pwsh", "-NoProfile", "-Command", command_to_run], check=False)  # noqa: S603, S607
        else:
            # For non-Windows: try to split the command safely to avoid shell injection.
            # If the command contains shell metacharacters (pipes, redirects, etc.),
            # fall back to shell=True which is necessary for those features.
            shell_metacharacters = set("|&;<>()$`\\\"'")
            if any(char in command_to_run for char in shell_metacharacters):
                # Contains shell syntax - must use shell=True
                result = subprocess.run(command_to_run, shell=True, check=False)  # noqa: S602
            else:
                # Simple command - safe to split and execute without shell
                try:
                    cmd_args = shlex.split(command_to_run)
                    result = subprocess.run(cmd_args, check=False)  # noqa: S603
                except ValueError:
                    # If shlex.split fails, fall back to shell=True
                    result = subprocess.run(command_to_run, shell=True, check=False)  # noqa: S602
        if result.returncode != 0:
            raise typer.Exit(code=result.returncode)

    setattr(_wrapped, "__signature__", inspect.signature(command_func))  # noqa: B010
    return _wrapped
