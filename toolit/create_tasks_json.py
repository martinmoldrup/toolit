"""Create a vscode tasks.json file based on the tools discovered in the project."""
from toolit.auto_loader import load_tools_from_folder
import pathlib
from types import FunctionType
from typing import Any, Dict, List
import inspect
import json
import enum

PATH: pathlib.Path = pathlib.Path() / "devtools"
output_file_path: pathlib.Path = pathlib.Path() / ".vscode" / "tasks.json"


def _is_enum(annotation: Any) -> bool:
    """Check if the annotation is an Enum type."""
    return isinstance(annotation, type) and issubclass(annotation, enum.Enum)


def _is_bool(annotation: Any) -> bool:
    """Check if the annotation is a bool type."""
    return annotation is bool


def create_tasks_json(tools: List[FunctionType]) -> None:
    """Create a tasks.json file based on the tools discovered in the project."""
    
    json_builder = TaskJsonBuilder()
    for tool in tools:
        json_builder.process_tool(tool)
    tasks_json: Dict[str, Any] = json_builder.create_tasks_json()

    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(tasks_json, f, indent=4)
    print(f"Tasks JSON created at {output_file_path}")

class TaskJsonBuilder:
    """Class to build tasks.json inputs and argument mappings."""
    def __init__(self) -> None:
        self.inputs: List[Dict[str, Any]] = []
        self.input_id_map: Dict[str, str] = {}
        self.tasks: List[Dict[str, Any]] = []

    def create_args_for_tool(self, tool: FunctionType) -> List[str]:
        """Create argument list and input entries for a given tool."""
        sig = inspect.signature(tool)
        args: List[str] = []
        for param in sig.parameters.values():
            if param.name == "self":
                continue
            input_id: str = f"{tool.__name__}_{param.name}"
            self.input_id_map[(tool.__name__, param.name)] = input_id

            annotation = param.annotation
            input_type: str = "promptString"
            input_options: Dict[str, Any] = {}
            description: str = f"Enter value for {param.name} ({annotation.__name__ if annotation != inspect.Parameter.empty else 'str'})"
            default_value: Any = "" if param.default == inspect.Parameter.empty else param.default

            if _is_enum(annotation):
                input_type = "pickString"
                choices: List[str] = [e.value for e in annotation]  # type: ignore
                input_options["options"] = choices
                default_value = choices[0] if param.default == inspect.Parameter.empty else param.default.value
            elif _is_bool(annotation):
                input_type = "pickString"
                input_options["options"] = ["True", "False"]
                default_value = "False" if param.default == inspect.Parameter.empty else str(param.default)

            input_entry: Dict[str, Any] = {
                "id": input_id,
                "type": input_type,
                "description": description,
                "default": default_value,
            }
            input_entry.update(input_options)
            self.inputs.append(input_entry)
            args.append(f"\"${{input:{input_id}}}\"")
        return args

    def create_task_entry(self, tool: FunctionType, args: List[str]) -> None:
        """Create a task entry for a given tool."""
        name_as_typer_command: str = tool.__name__.replace("_", "-")
        display_name: str = tool.__name__.replace("_", " ").title()
        task: Dict[str, Any] = {
            "label": display_name,
            "type": "shell",
            "command": f"toolit {name_as_typer_command}" + (f" {' '.join(args)}" if args else ""),
            "problemMatcher": [],
        }
        if tool.__doc__:
            task["detail"] = tool.__doc__.strip()
        self.tasks.append(task)

    def process_tool(self, tool: FunctionType) -> None:
        """Process a single tool to create its task entry and inputs."""
        args = self.create_args_for_tool(tool)
        self.create_task_entry(tool, args)

    def create_tasks_json(self) -> dict:
        """Create the final tasks.json structure."""

        tasks_json: Dict[str, Any] = {
            "version": "2.0.0",
            "tasks": self.tasks,
            "inputs": self.inputs,
        }
        return tasks_json

if __name__ == "__main__":
    tools: List[FunctionType] = load_tools_from_folder(PATH)
    print(f"Found {len(tools)} tools in {PATH}.")
    create_tasks_json(tools)