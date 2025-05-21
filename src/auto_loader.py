"""
A folder is defined. 
Everything that has the @decorators.tool decorator will be loaded and added as CLI and MCP commands.
The folder is defined in the config file.

Example of a tool:
@decorators.tool
def my_tool():
    pass


"""
import os
import importlib
import inspect
import sys
from types import FunctionType
from typing import List
from .create_apps_and_register import register_command
import pathlib
from .constants import MARKER_TOOL

def load_tools_from_folder(folder_path: pathlib.Path) -> List[FunctionType]:
    """Load all tools from a given folder (relative to the project's working directory) and register them as commands."""
    # If folder_path is relative, compute its absolute path using the current working directory.
    if not folder_path.is_absolute():
        folder_path = pathlib.Path.cwd() / folder_path

    tools: List[FunctionType] = []
    project_root: str = str(pathlib.Path.cwd())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    # Iterate over each .py file in the folder
    for file in folder_path.iterdir():
        if not (file.is_file() and file.suffix == ".py" and not file.name.startswith("__")):
            continue
        tools_for_file: List[FunctionType] = load_tool_from_file(file)
        tools.extend(tools_for_file)
    return tools

def load_tool_from_file(file: pathlib.Path) -> List[FunctionType]:
    """Load a tool from a given file and register it as a command."""
    tools = []
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
    for name, obj in inspect.getmembers(module):
        is_tool: bool = isinstance(obj, FunctionType) and getattr(obj, MARKER_TOOL, False)
        if inspect.isfunction(obj) and is_tool:
            tools.append(obj)
                # Register the tool with the CLI and MCP commands.
            register_command(obj, name=name)
    return tools