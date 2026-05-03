"""CLI and optional MCP server for Toolit project."""

from __future__ import annotations

import os
import enum
import shlex
import typer
import inspect
import subprocess  # noqa: S404
from collections.abc import Callable
from functools import wraps
from toolit.constants import (
    MARKER_TOOL,
    OPTIONAL_STR_SENTINEL,
    ToolitTypesEnum,
)
from toolit.type_utils import unwrap_union_members
from typing import TYPE_CHECKING, get_args, get_origin

OPTIONAL_UNION_MEMBER_COUNT = 2

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    _has_mcp: bool = True
else:
    # Make MCP optional
    try:
        from mcp.server.fastmcp import FastMCP

        _has_mcp = True
    except ImportError:
        FastMCP: object = None  # type: ignore[no-redef]
        _has_mcp = False

# Initialize the Typer app
app: typer.Typer = typer.Typer(no_args_is_help=True)
# Initialize the MCP server with a name, if available
mcp: FastMCP | None = FastMCP("Toolit MCP Server") if _has_mcp else None


@app.callback()
def initialize() -> None:
    """Welcome to the Toolit CLI."""


def register_command(
    command_func: Callable[..., object],
    name: str | None = None,
    rich_help_panel: str | None = None,
) -> None:
    """Register an external command to the CLI and MCP server if available."""
    if not callable(command_func):
        msg = f"Command function {command_func} is not callable."
        raise TypeError(msg)

    command_to_register = _create_type_coercion_wrapper(command_func)
    if getattr(command_func, MARKER_TOOL, None) == ToolitTypesEnum.CLITOOL:
        command_to_register = _create_clitool_runtime_wrapper(command_to_register)

    app.command(name=name, rich_help_panel=rich_help_panel)(command_to_register)

    if mcp is not None and getattr(command_func, MARKER_TOOL, None) != ToolitTypesEnum.CLITOOL:
        mcp.tool(name)(command_func)


def _extract_list_item_type(annotation: object) -> object | None:
    """Return the T for list[T] (including Optional[list[T]]), or None if not a list."""
    for candidate in unwrap_union_members(annotation):
        if candidate is type(None):
            continue
        if get_origin(candidate) is list:
            args = get_args(candidate)
            return args[0] if args else str
    return None


def _is_optional_list(annotation: object) -> bool:
    """Return True when annotation allows None alongside a list type."""
    members = unwrap_union_members(annotation)
    return type(None) in members and any(get_origin(m) is list for m in members)


def _is_optional_str(annotation: object) -> bool:
    """Return True when annotation is exactly str | None."""
    members = unwrap_union_members(annotation)
    return str in members and type(None) in members and len(members) == OPTIONAL_UNION_MEMBER_COUNT


def _is_required_str(annotation: object, default: object) -> bool:
    """Return True when annotation is plain str with no default value."""
    return annotation is str and default is inspect.Parameter.empty


def _contains_bool(annotation: object) -> bool:
    """Return True when annotation is or contains bool."""
    return any(m is bool for m in unwrap_union_members(annotation))


def _coerce_list_value(value: list[object], item_type: object) -> list[object] | None:
    """
    Split a single comma-separated element if needed, then convert to item_type.

    Returns None unchanged (for optional list parameters with no value provided).
    """
    if value is None:
        return None  # type: ignore[return-value]
    if len(value) == 1 and isinstance(value[0], str) and "," in value[0]:
        raw_items: list[str] = [v.strip() for v in value[0].split(",") if v.strip()]
    else:
        raw_items = [str(v) for v in value]

    if item_type is str:
        return raw_items
    if item_type is int:
        return [int(v) for v in raw_items]
    if isinstance(item_type, type) and issubclass(item_type, enum.Enum):
        return [item_type(v) for v in raw_items]
    return raw_items


def _create_type_coercion_wrapper(func: Callable[..., object]) -> Callable[..., object]:  # noqa: C901
    """
    Wrap a function to add CLI type coercions applied before the function is called.

    Handles:
    - list[T]: splits single comma-separated arg; preserves native multi-arg behavior.
    - bool: changes --flag/--no-flag to --flag VALUE accepting 'True'/'False' strings.
    - str | None: converts empty string to None.
    - required str: rejects empty string with a non-zero exit.
    """
    sig = inspect.signature(func)
    new_params: list[inspect.Parameter] = []
    coercions: dict[str, tuple[str, object | None]] = {}

    for param in sig.parameters.values():
        ann = param.annotation

        list_item_type = _extract_list_item_type(ann)
        if list_item_type is not None:
            coercions[param.name] = ("list", list_item_type)
            # Expose list[str] (or list[str] | None) to Typer so it skips type conversion.
            new_ann: object = (list[str] | None) if _is_optional_list(ann) else list[str]
            new_params.append(param.replace(annotation=new_ann))
            continue

        if _contains_bool(ann):
            coercions[param.name] = ("bool", None)
            bool_default = "False" if param.default is inspect.Parameter.empty else str(param.default)
            new_params.append(param.replace(annotation=str, default=bool_default))
            continue

        if _is_optional_str(ann):
            coercions[param.name] = ("optional_str", None)
            new_params.append(param)
            continue

        if _is_required_str(ann, param.default):
            coercions[param.name] = ("required_str", None)
            new_params.append(param)
            continue

        new_params.append(param)

    if not coercions:
        return func

    new_sig = sig.replace(parameters=new_params)

    @wraps(func)
    def _wrapper(*args: object, **kwargs: object) -> object:
        for param_name, (coercion_type, extra) in coercions.items():
            if param_name not in kwargs:
                continue
            value = kwargs[param_name]

            if coercion_type == "list":
                kwargs[param_name] = _coerce_list_value(value, extra)
            elif coercion_type == "bool":
                kwargs[param_name] = str(value).lower() == "true"
            elif coercion_type == "optional_str":
                if isinstance(value, str) and value.startswith(OPTIONAL_STR_SENTINEL):
                    raw_value = value[len(OPTIONAL_STR_SENTINEL) :]
                    kwargs[param_name] = raw_value or None
                elif isinstance(value, str) and not value:
                    kwargs[param_name] = None
            elif coercion_type == "required_str" and isinstance(value, str) and not value:
                typer.secho(f"Error: '{param_name}' cannot be empty.", fg=typer.colors.RED)
                raise typer.Exit(code=1)

        return func(*args, **kwargs)

    _wrapper.__signature__ = new_sig
    # Rebuild __annotations__ to match the new signature so Typer/get_type_hints
    # sees the transformed types rather than the originals copied by @wraps.
    new_annotations: dict[str, object] = {
        p.name: p.annotation for p in new_sig.parameters.values() if p.annotation is not inspect.Parameter.empty
    }
    if sig.return_annotation is not inspect.Parameter.empty:
        new_annotations["return"] = sig.return_annotation
    _wrapper.__annotations__ = new_annotations
    return _wrapper


def _create_clitool_runtime_wrapper(command_func: Callable[..., object]) -> Callable[..., None]:
    """Wrap a clitool function so its returned command string runs in a shell."""

    @wraps(command_func)
    def _wrapped(*args: object, **kwargs: object) -> None:
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

    _wrapped.__signature__ = inspect.signature(command_func)
    return _wrapped
