"""
Load tools automatically from a folder and register them as commands.

A folder is defined. Everything that has the @decorators.tool decorator will be loaded
and added as CLI and MCP commands.
"""

from __future__ import annotations

import os
import sys
import typer
import inspect
import pathlib
import importlib
import importlib.metadata
from collections.abc import Callable
from toolit.constants import MARKER_TOOL, RichHelpPanelNames, ToolitTypesEnum
from toolit.create_apps_and_register import register_command
from types import FunctionType, ModuleType
from typing import Any


def get_items_from_folder(
    folder_path: pathlib.Path,
    strategy: Callable[[ModuleType], list[FunctionType]],
) -> list[FunctionType]:
    """Get items from a given folder using a strategy function."""
    if not folder_path.is_absolute():
        folder_path = pathlib.Path.cwd() / folder_path

    items: list[FunctionType] = []
    project_root: str = str(pathlib.Path.cwd())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    for file in folder_path.iterdir():
        if not (file.is_file() and file.suffix == ".py" and not file.name.startswith("__")):
            continue
        module = import_module(file)
        items.extend(strategy(module))
    return items


def tool_strategy(module: ModuleType) -> list[FunctionType]:
    """Strategy to get tools from a module."""
    return load_tools_from_file(module, ToolitTypesEnum.TOOL)


def tool_group_strategy(module: ModuleType) -> list[FunctionType]:
    """Strategy to get tool groups from a module."""
    groups: list[FunctionType] = []
    groups.extend(load_tools_from_file(module, ToolitTypesEnum.SEQUENTIAL_GROUP))
    groups.extend(load_tools_from_file(module, ToolitTypesEnum.PARALLEL_GROUP))
    return groups


def load_tools_from_plugins() -> list[FunctionType]:
    """Discover and return plugin commands via entry points."""
    plugins = get_plugin_tools()
    for plugin in plugins:
        register_command(plugin, rich_help_panel=RichHelpPanelNames.PLUGINS_COMMANDS_PANEL)
    return plugins


def load_tools_from_folder(folder_path: pathlib.Path) -> list[FunctionType]:
    """
    Load all tools from a given folder and register them as commands.

    Folder is relative to the project's working directory.
    """
    if not folder_path.exists() or not folder_path.is_dir():
        msg = (
            "No tools loaded.\n"
            "The folder selected for devtools does not exist or is not a directory.\n"
            f"{folder_path.absolute().as_posix()}\n"
            "Please create it and add your tools there."
        )
        typer.secho(f"\n{'=' * 60}\nERROR: {msg}\n{'=' * 60}\n", fg=typer.colors.RED, bold=True)
        return []
    # If folder_path is relative, compute its absolute path using the current working directory.
    if not folder_path.is_absolute():
        folder_path = pathlib.Path.cwd() / folder_path

    tools: list[FunctionType] = get_items_from_folder(folder_path, tool_strategy)
    tool_groups: list[FunctionType] = get_items_from_folder(folder_path, tool_group_strategy)
    # Register each tool as a command
    for tool in tools:
        register_command(tool, rich_help_panel=RichHelpPanelNames.PROJECT_COMMANDS_PANEL)
    return tools + tool_groups


def get_toolit_type(tool: FunctionType) -> ToolitTypesEnum | None:
    """Get the type of a tool based on its marker."""
    if hasattr(tool, MARKER_TOOL):
        return getattr(tool, MARKER_TOOL)
    return None


def load_tools_from_file(module: ModuleType, tool_type: ToolitTypesEnum) -> list[FunctionType]:
    """Load a tool from a given file and register it as a command."""
    tools: list[FunctionType] = []
    for _name, obj in inspect.getmembers(module):
        is_tool: bool = get_toolit_type(obj) == tool_type
        if inspect.isfunction(obj) and is_tool:
            tools.append(obj)
    return tools


def import_module(file: pathlib.Path) -> ModuleType:
    """Import a module from a given file path."""
    module_name: str = file.stem
    try:
        # Compute module import name relative to the project's working directory.
        # For example, if file is "experimentation/tools/tool.py", it becomes "experimentation.tools.tool".
        rel_module: pathlib.Path = file.relative_to(pathlib.Path.cwd())
        module_import_name: str = str(rel_module.with_suffix("")).replace(os.sep, ".")
    except ValueError:
        # Fallback to the module name if relative path cannot be determined.
        module_import_name = module_name
    module = importlib.import_module(module_import_name)
    return module


def get_entry_points(name: str) -> importlib.metadata.EntryPoints:
    """Get entry points by group name."""
    entry_points = importlib.metadata.entry_points()
    return entry_points.select(group=name)


def get_plugin_tools() -> list[FunctionType]:
    """Discover and return plugin commands via entry points."""
    plugins: list[FunctionType] = []
    entry_points = get_entry_points("toolit_plugins")
    for entry_point in entry_points:
        plugin_func: Any = entry_point.load()
        plugin_func.__name__ = entry_point.name
        plugins.append(plugin_func)
    return plugins
