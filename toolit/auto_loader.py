"""
Load tools automatically from a folder and register them as commands.

A folder is defined. Everything that has the @decorators.tool decorator will be loaded
and added as CLI and MCP commands.
"""
from __future__ import annotations

import os
import sys
import inspect
import pathlib
import importlib
from toolit.constants import MARKER_TOOL, ToolitTypesEnum
from toolit.create_apps_and_register import register_command
from types import FunctionType, ModuleType


def load_tools_from_folder(folder_path: pathlib.Path) -> list[FunctionType]:
    """
    Load all tools from a given folder and register them as commands.

    Folder is relative to the project's working directory.
    """
    # If folder_path is relative, compute its absolute path using the current working directory.
    if not folder_path.is_absolute():
        folder_path = pathlib.Path.cwd() / folder_path

    tools: list[FunctionType] = []
    tool_groups: list[FunctionType] = []
    project_root: str = str(pathlib.Path.cwd())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    # Iterate over each .py file in the folder
    for file in folder_path.iterdir():
        if not (file.is_file() and file.suffix == ".py" and not file.name.startswith("__")):
            continue
        module = import_module(file)
        tools_for_file: list[FunctionType] = load_tools_from_file(module, ToolitTypesEnum.TOOL)
        tools.extend(tools_for_file)
        tool_groups.extend(load_tools_from_file(module, ToolitTypesEnum.SEQUENTIAL_GROUP))
        tool_groups.extend(load_tools_from_file(module, ToolitTypesEnum.PARALLEL_GROUP))
    # Register each tool as a command
    for tool in tools:
        register_command(tool)
    return tools + tool_groups


def get_toolit_type(tool: FunctionType) -> ToolitTypesEnum | None:
    """Get the type of a tool based on its marker."""
    if hasattr(tool, MARKER_TOOL):
        return getattr(tool, MARKER_TOOL)
    return None


def load_tools_from_file(module: ModuleType, tool_type: ToolitTypesEnum) -> list[FunctionType]:
    """Load a tool from a given file and register it as a command."""
    tools = []
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
