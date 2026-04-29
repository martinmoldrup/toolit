"""CLI and optional MCP server for Toolit project."""

from __future__ import annotations

import enum
import typer
import types
import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Union, get_args, get_origin
from toolit.list_serialization import serialize_list_default

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


def _unwrap_union_annotations(annotation: Any) -> list[Any]:  # noqa: ANN401
    """Return union members for `X | Y` / `Union[X, Y]`, or the annotation itself."""
    origin = get_origin(annotation)
    args = get_args(annotation)
    union_type = getattr(types, "UnionType", None)
    if origin is Union or (union_type is not None and origin is union_type):
        return list(args)
    return [annotation]


def _extract_list_item_type(annotation: Any) -> Any | None:  # noqa: ANN401
    """Extract list item type from an annotation, including optional/union wrappers."""
    for candidate in _unwrap_union_annotations(annotation):
        if candidate in {None, type(None)}:
            continue
        origin = get_origin(candidate)
        if origin is list:
            args = get_args(candidate)
            if args:
                return args[0]
            return str
    return None


def _coerce_enum_item(enum_type: type[enum.Enum], value: str) -> enum.Enum:
    """Convert a token to an enum member by accepting either name or value."""
    if value in enum_type.__members__:
        return enum_type[value]
    for member in enum_type:
        if str(member.value) == value:
            return member
    msg = (
        f"Invalid enum value '{value}' for {enum_type.__name__}. "
        f"Use one of: {', '.join(enum_type.__members__.keys())} or matching enum values."
    )
    raise typer.BadParameter(msg)


def _coerce_list_items(raw_value: str, item_type: Any) -> list[Any]:  # noqa: ANN401
    """Convert a comma-separated string into a typed list for list-annotated parameters."""
    tokens = [token.strip() for token in raw_value.split(",") if token.strip()]
    if item_type is int:
        converted_ints: list[int] = []
        for token in tokens:
            try:
                converted_ints.append(int(token))
            except ValueError as exc:
                msg = f"Invalid integer value '{token}' in list input '{raw_value}'."
                raise typer.BadParameter(msg) from exc
        return converted_ints
    if isinstance(item_type, type) and issubclass(item_type, enum.Enum):
        return [_coerce_enum_item(item_type, token) for token in tokens]
    return tokens


def _build_cli_command(command_func: Callable[..., Any]) -> Callable[..., Any]:
    """Build a CLI callback that accepts list params as comma-separated strings."""
    signature = inspect.signature(command_func)
    list_item_types: dict[str, Any] = {}
    cli_parameters: list[inspect.Parameter] = []

    for parameter in signature.parameters.values():
        list_item_type = _extract_list_item_type(parameter.annotation)
        if list_item_type is None:
            cli_parameters.append(parameter)
            continue

        list_item_types[parameter.name] = list_item_type
        replacement_default = parameter.default
        if isinstance(parameter.default, list):
            replacement_default = serialize_list_default(parameter.default)

        cli_parameters.append(parameter.replace(annotation=str, default=replacement_default))

    if not list_item_types:
        return command_func

    cli_signature = signature.replace(parameters=cli_parameters)

    def _command_wrapper(*args: Any, **kwargs: Any) -> Any:
        bound = cli_signature.bind(*args, **kwargs)
        converted_arguments: dict[str, Any] = dict(bound.arguments)
        for name, item_type in list_item_types.items():
            raw_value = converted_arguments.get(name)
            if raw_value is None:
                # Preserve omitted optional list arguments as None.
                converted_arguments[name] = None
                continue
            converted_arguments[name] = _coerce_list_items(str(raw_value), item_type)
        return command_func(**converted_arguments)

    _command_wrapper.__name__ = command_func.__name__
    _command_wrapper.__doc__ = command_func.__doc__
    _command_wrapper.__signature__ = cli_signature  # type: ignore[attr-defined]
    return _command_wrapper


def register_command(
    command_func: Callable[..., Any],
    name: str | None = None,
    rich_help_panel: str | None = None,
) -> None:
    """Register an external command to the CLI and MCP server if available."""
    if not callable(command_func):
        msg = f"Command function {command_func} is not callable."
        raise TypeError(msg)
    cli_command = _build_cli_command(command_func)
    app.command(name=name, rich_help_panel=rich_help_panel)(cli_command)
    if mcp is not None:
        mcp.tool(name)(command_func)
