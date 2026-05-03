"""
Generate VS Code tasks.json entries from discovered tools.

Scope: this module builds tasks.json structure by consuming rich metadata from
CliCommandBuilder. It delegates all tool inspection and metadata generation to
the command builder.
"""

import json
import typer
import pathlib
from toolit.auto_loader import (
    clitool_strategy,
    get_items_from_folder,
    get_plugin_tools,
    get_toolit_type,
    tool_group_strategy,
    tool_strategy,
)
from toolit.cli_command_builder import CliCommandBuilder, ToolCommandSpec
from toolit.config import load_devtools_folder
from toolit.constants import ToolitTypesEnum
from types import FunctionType
from typing import Any

PATH: pathlib.Path = load_devtools_folder()
output_file_path: pathlib.Path = pathlib.Path() / ".vscode" / "tasks.json"


def create_vscode_tasks_json() -> None:
    """Create a tasks.json file based on the tools discovered in the project."""
    typer.echo(f"Creating tasks.json at {output_file_path}")
    if PATH.exists() and PATH.is_dir():
        tools: list[FunctionType] = get_items_from_folder(PATH, tool_strategy)
        clitools: list[FunctionType] = get_items_from_folder(PATH, clitool_strategy)
        tool_groups: list[FunctionType] = get_items_from_folder(PATH, tool_group_strategy)
        tools.extend(clitools)
        tools.extend(tool_groups)
    else:
        typer.echo(f"The devtools folder does not exist or is not a directory: {PATH.absolute().as_posix()}")
        tools = []

    tools.extend(get_plugin_tools())
    json_builder = _TaskJsonBuilder(CliCommandBuilder())
    for tool in tools:
        json_builder.process_tool(tool)
    tasks_json: dict[str, Any] = json_builder.create_tasks_json()

    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    with output_file_path.open("w", encoding="utf-8") as f:
        json.dump(tasks_json, f, indent=4)


class _TaskJsonBuilder:
    """Build tasks.json payloads from tool command specs."""

    def __init__(self, cli_command_builder: CliCommandBuilder) -> None:
        """Initialize the object."""
        self.cli_command_builder = cli_command_builder
        self.inputs: list[dict[str, Any]] = []
        self.tasks: list[dict[str, Any]] = []

    def _create_task_entry(self, spec: ToolCommandSpec) -> None:
        """Create a task entry from a tool command spec."""
        command: str = spec.build_command(
            self.cli_command_builder.program_name, self.cli_command_builder.command_prefix,
        )
        task: dict[str, Any] = {
            "label": spec.display_name,
            "type": "shell",
            "command": command,
            "problemMatcher": [],
        }
        if spec.docstring:
            task["detail"] = spec.docstring.strip()
        self.tasks.append(task)

    def _create_task_group_entry(self, tool: FunctionType, tool_type: ToolitTypesEnum) -> None:
        """Create a task group entry for a given tool."""
        group_name: str = self.cli_command_builder.create_group_name(tool)
        tools: list[FunctionType] = tool()  # Call the tool to get the list of tools in the group
        task: dict[str, Any] = {
            "label": group_name,
            "dependsOn": [self.cli_command_builder.create_display_name(t) for t in tools],
            "problemMatcher": [],
        }
        if tool_type == ToolitTypesEnum.SEQUENTIAL_GROUP:
            task["dependsOrder"] = "sequence"
        if tool.__doc__:
            task["detail"] = tool.__doc__.strip()
        self.tasks.append(task)

    def process_tool(self, tool: FunctionType) -> None:
        """Process a single tool to create its task entry and inputs."""
        tool_type = get_toolit_type(tool)
        if tool_type in {ToolitTypesEnum.TOOL, ToolitTypesEnum.CLITOOL}:
            spec = self.cli_command_builder.analyze_tool(tool)
            self._create_task_entry(spec)
            self.inputs.extend(spec.get_input_entries())
        elif tool_type in {ToolitTypesEnum.SEQUENTIAL_GROUP, ToolitTypesEnum.PARALLEL_GROUP}:
            self._create_task_group_entry(tool, tool_type)

    def create_tasks_json(self) -> dict[str, Any]:
        """Create the final tasks.json structure."""
        return {
            "version": "2.0.0",
            "tasks": self.tasks,
            "inputs": self.inputs,
        }


if __name__ == "__main__":
    create_vscode_tasks_json()
