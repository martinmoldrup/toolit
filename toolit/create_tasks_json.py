"""Create a vscode tasks.json file based on the tools discovered in the project."""

import enum
import json
import typer
import inspect
import pathlib
from toolit.auto_loader import (
    get_items_from_folder,
    get_plugin_tools,
    get_toolit_type,
    tool_group_strategy,
    tool_strategy,
)
from toolit.constants import ToolitTypesEnum
from types import FunctionType
from typing import Any

PATH: pathlib.Path = pathlib.Path() / "devtools"
output_file_path: pathlib.Path = pathlib.Path() / ".vscode" / "tasks.json"


def create_vscode_tasks_json() -> None:
    """Create a tasks.json file based on the tools discovered in the project."""
    typer.echo(f"Creating tasks.json at {output_file_path}")
    if PATH.exists() and PATH.is_dir():
        tools: list[FunctionType] = get_items_from_folder(PATH, tool_strategy)
        tool_groups: list[FunctionType] = get_items_from_folder(PATH, tool_group_strategy)
        tools.extend(tool_groups)
    else:
        typer.echo(f"The devtools folder does not exist or is not a directory: {PATH.absolute().as_posix()}")
        tools = []

    tools.extend(get_plugin_tools())
    json_builder = TaskJsonBuilder()
    for tool in tools:
        json_builder.process_tool(tool)
    tasks_json: dict[str, Any] = json_builder.create_tasks_json()

    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    with output_file_path.open("w", encoding="utf-8") as f:
        json.dump(tasks_json, f, indent=4)


def _is_enum(annotation: Any) -> bool:  # noqa: ANN401
    """Check if the annotation is an Enum type."""
    return isinstance(annotation, type) and issubclass(annotation, enum.Enum)


def _is_bool(annotation: Any) -> bool:  # noqa: ANN401
    """Check if the annotation is a bool type."""
    return annotation is bool


def _create_typer_command_name(tool: FunctionType) -> str:
    """Create a Typer command name from a tool function name."""
    return tool.__name__.replace("_", "-").lower()


def _create_display_name(tool: FunctionType) -> str:
    """Create a display name from a tool function name."""
    return tool.__name__.replace("_", " ").title()


class TaskJsonBuilder:
    """Class to build tasks.json inputs and argument mappings."""

    def __init__(self) -> None:
        """Initialize the object."""
        self.inputs: list[dict[str, Any]] = []
        self.input_id_map: dict[tuple[str, str], str] = {}
        self.tasks: list[dict[str, Any]] = []

    def _create_args_for_tool(self, tool: FunctionType) -> list[str]:
        """Create argument list and input entries for a given tool."""
        sig = inspect.signature(tool)
        args: list[str] = []
        for param in sig.parameters.values():
            if param.name == "self":
                continue
            input_id: str = f"{tool.__name__}_{param.name}"
            self.input_id_map[tool.__name__, param.name] = input_id

            annotation = param.annotation
            input_type: str = "promptString"
            input_options: dict[str, Any] = {}
            description: str = "Enter value for {param_name} ({type})".format(
                param_name=param.name,
                type=annotation.__name__ if annotation != inspect.Parameter.empty else "str",
            )
            default_value: Any = "" if param.default == inspect.Parameter.empty else param.default

            if _is_enum(annotation):
                input_type = "pickString"
                choices: list[str] = [e.value for e in annotation]  # type: ignore[misc]
                input_options["options"] = choices
                default_value = choices[0] if param.default == inspect.Parameter.empty else param.default.value
            elif _is_bool(annotation):
                input_type = "pickString"
                input_options["options"] = ["True", "False"]
                default_value = "False" if param.default == inspect.Parameter.empty else str(param.default)

            input_entry: dict[str, Any] = {
                "id": input_id,
                "type": input_type,
                "description": description,
                "default": default_value,
            }
            input_entry.update(input_options)
            self.inputs.append(input_entry)
            args.append(f'"${{input:{input_id}}}"')
        return args

    def _create_task_entry(self, tool: FunctionType, args: list[str]) -> None:
        """Create a task entry for a given tool."""
        name_as_typer_command: str = _create_typer_command_name(tool)
        display_name: str = _create_display_name(tool)
        task: dict[str, Any] = {
            "label": display_name,
            "type": "shell",
            "command": f"toolit {name_as_typer_command}" + (f" {' '.join(args)}" if args else ""),
            "problemMatcher": [],
        }
        if tool.__doc__:
            task["detail"] = tool.__doc__.strip()
        self.tasks.append(task)

    def _create_task_group_entry(self, tool: FunctionType, tool_type: ToolitTypesEnum) -> None:
        """Create a task group entry for a given tool."""
        group_name: str = "Group: " + tool.__name__.replace("_", " ").title()
        tools: list[FunctionType] = tool()  # Call the tool to get the list of tools in the group
        task: dict[str, Any] = {
            "label": group_name,
            "dependsOn": [f"{_create_display_name(t)}" for t in tools],
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
        if tool_type == ToolitTypesEnum.TOOL:
            args = self._create_args_for_tool(tool)
            self._create_task_entry(tool, args)
        elif tool_type in {ToolitTypesEnum.SEQUENTIAL_GROUP, ToolitTypesEnum.PARALLEL_GROUP}:
            self._create_task_group_entry(tool, tool_type)

    def create_tasks_json(self) -> dict:
        """Create the final tasks.json structure."""
        tasks_json: dict[str, Any] = {
            "version": "2.0.0",
            "tasks": self.tasks,
            "inputs": self.inputs,
        }
        return tasks_json


if __name__ == "__main__":
    create_vscode_tasks_json()
