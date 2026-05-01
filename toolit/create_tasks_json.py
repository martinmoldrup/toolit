"""Create a vscode tasks.json file based on the tools discovered in the project."""

import enum
import json
import shutil
import typer
import types
import inspect
import pathlib
from toolit.auto_loader import (
    clitool_strategy,
    get_items_from_folder,
    get_plugin_tools,
    get_toolit_type,
    tool_group_strategy,
    tool_strategy,
)
from toolit.config import load_devtools_folder
from toolit.constants import ToolitTypesEnum
from types import FunctionType
from typing import Any, Union, get_args, get_origin

PATH: pathlib.Path = load_devtools_folder()
output_file_path: pathlib.Path = pathlib.Path() / ".vscode" / "tasks.json"


def serialize_list_default(default_value: Any) -> str | None:  # noqa: ANN401
    """Serialize list defaults to comma-separated text using enum values when needed."""
    if default_value is None:
        return None
    if isinstance(default_value, list):
        rendered_items: list[str] = []
        for item in default_value:
            if isinstance(item, enum.Enum):
                rendered_items.append(str(item.value))
            else:
                rendered_items.append(str(item))
        return ", ".join(rendered_items)
    return str(default_value)


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


def _unwrap_union_annotations(annotation: Any) -> list[Any]:  # noqa: ANN401
    """Return union members for `X | Y` / `Union[X, Y]`, or the annotation itself."""
    origin = get_origin(annotation)
    args = get_args(annotation)
    union_type = getattr(types, "UnionType", None)
    if origin is Union or (union_type is not None and origin is union_type):
        return list(args)
    return [annotation]


def _extract_enum_type(annotation: Any) -> type[enum.Enum] | None:  # noqa: ANN401
    """Extract enum type from an annotation, including optional/union wrappers."""
    for candidate in _unwrap_union_annotations(annotation):
        if candidate in {None, type(None)}:
            continue
        if _is_enum(candidate):
            return candidate
    return None


def _contains_bool(annotation: Any) -> bool:  # noqa: ANN401
    """Check whether an annotation contains bool directly or via union/optional."""
    return any(_is_bool(candidate) for candidate in _unwrap_union_annotations(annotation))


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


def _build_list_description(param_name: str, list_item_type: Any) -> str:  # noqa: ANN401
    """Build a type-specific description for list prompt inputs."""
    if list_item_type is str:
        return f"Enter comma-separated text values for {param_name} (e.g. alpha, beta, gamma)"
    if list_item_type is int:
        return f"Enter comma-separated integer values for {param_name} (e.g. 1, 2, 3)"
    if _is_enum(list_item_type):
        accepted_values = ", ".join(str(member.value) for member in list_item_type)
        return (
            f"Enter comma-separated enum values for {param_name}. "
            f"Accepted values: [{accepted_values}]. You can also use enum member names."
        )
    item_type_name = _annotation_to_string(list_item_type)
    return f"Enter comma-separated values for {param_name} ({item_type_name})"


def _annotation_to_string(annotation: Any) -> str:  # noqa: ANN401
    """Convert Python type annotations to readable strings."""
    result: str = ""

    if annotation == inspect.Parameter.empty:
        result = "str"
    elif annotation is Any:
        result = "Any"
    elif annotation is None or annotation is type(None):
        result = "None"
    else:
        origin = get_origin(annotation)
        args = get_args(annotation)

        union_type = getattr(types, "UnionType", None)
        if origin is Union or (union_type is not None and origin is union_type):
            result = " | ".join(_annotation_to_string(arg) for arg in args)
        elif origin is not None:
            origin_name = getattr(origin, "__name__", str(origin).replace("typing.", ""))
            if args:
                args_repr = ", ".join(_annotation_to_string(arg) for arg in args)
                result = f"{origin_name}[{args_repr}]"
            else:
                result = origin_name
        elif hasattr(annotation, "__name__"):
            result = annotation.__name__
        else:
            result = str(annotation).replace("typing.", "")

    return result


def _create_typer_command_name(tool: FunctionType) -> str:
    """Create a Typer command name from a tool function name."""
    return tool.__name__.replace("_", "-").lower()


def _create_display_name(tool: FunctionType) -> str:
    """Create a display name from a tool function name."""
    return tool.__name__.replace("_", " ").title()


def _create_typer_option_name(param_name: str) -> str:
    """Create a Typer option name from a function parameter name."""
    return f"--{param_name.replace('_', '-')}"


class TaskJsonBuilder:
    """Class to build tasks.json inputs and argument mappings."""

    def __init__(self) -> None:
        """Initialize the object."""
        self.inputs: list[dict[str, Any]] = []
        self.input_id_map: dict[tuple[str, str], str] = {}
        self.tasks: list[dict[str, Any]] = []

    @staticmethod
    def _build_command_prefix() -> str:
        """Build command prefix for task commands based on uv availability."""
        return "uv run --no-sync " if shutil.which("uv") else ""

    def _build_input_metadata(self, param: inspect.Parameter) -> tuple[str, dict[str, Any], str, Any]:
        """Build VS Code input metadata for a function parameter."""
        annotation = param.annotation
        input_type: str = "promptString"
        input_options: dict[str, Any] = {}
        description: str = f"Enter value for {param.name} ({_annotation_to_string(annotation)})"
        default_value: Any = "" if param.default == inspect.Parameter.empty else param.default

        list_item_type = _extract_list_item_type(annotation)
        if list_item_type is not None:
            description = _build_list_description(param.name, list_item_type)
            default_value = "" if param.default == inspect.Parameter.empty else serialize_list_default(param.default)
            return input_type, input_options, description, default_value

        enum_type = _extract_enum_type(annotation)
        if enum_type is not None:
            input_type = "pickString"
            choices: list[str] = [e.value for e in enum_type]
            input_options["options"] = choices
            if param.default == inspect.Parameter.empty or param.default is None:
                default_value = choices[0]
            else:
                default_value = param.default.value
            return input_type, input_options, description, default_value

        if _contains_bool(annotation):
            input_type = "pickString"
            input_options["options"] = ["True", "False"]
            if param.default == inspect.Parameter.empty or param.default is None:
                default_value = "False"
            else:
                default_value = str(param.default)

        return input_type, input_options, description, default_value

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
            if annotation is inspect.Parameter.empty:
                msg = (
                    f"Parameter '{param.name}' in function '{tool.__name__}' is missing a type annotation. "
                    f"Please add a type hint, e.g.: def {tool.__name__}({param.name}: str) -> None"
                )
                raise ValueError(
                    msg,
                )
            input_type, input_options, description, default_value = self._build_input_metadata(param)

            input_entry: dict[str, Any] = {
                "id": input_id,
                "type": input_type,
                "description": description,
                "default": default_value,
            }
            input_entry.update(input_options)
            self.inputs.append(input_entry)
            input_value_ref = f'"${{input:{input_id}}}"'
            if param.default is inspect.Parameter.empty:
                args.append(input_value_ref)
            else:
                args.append(f"{_create_typer_option_name(param.name)} {input_value_ref}")
        return args

    def _create_task_entry(self, tool: FunctionType, args: list[str]) -> None:
        """Create a task entry for a given tool."""
        name_as_typer_command: str = _create_typer_command_name(tool)
        display_name: str = _create_display_name(tool)
        command_prefix: str = self._build_command_prefix()
        task: dict[str, Any] = {
            "label": display_name,
            "type": "shell",
            "command": f"{command_prefix}toolit {name_as_typer_command}" + (f" {' '.join(args)}" if args else ""),
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
        if tool_type in {ToolitTypesEnum.TOOL, ToolitTypesEnum.CLITOOL}:
            args = self._create_args_for_tool(tool)
            self._create_task_entry(tool, args)
        elif tool_type in {ToolitTypesEnum.SEQUENTIAL_GROUP, ToolitTypesEnum.PARALLEL_GROUP}:
            self._create_task_group_entry(tool, tool_type)

    def create_tasks_json(self) -> dict[str, Any]:
        """Create the final tasks.json structure."""
        tasks_json: dict[str, Any] = {
            "version": "2.0.0",
            "tasks": self.tasks,
            "inputs": self.inputs,
        }
        return tasks_json


if __name__ == "__main__":
    create_vscode_tasks_json()
