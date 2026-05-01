"""Build complete CLI commands with rich metadata for tool functions.

Scope: this module handles complete tool inspection including parameter analysis,
VS Code input metadata generation, command-line name formatting, and shell command
assembly. The command builder is self-contained and returns rich domain objects.
"""

import enum
import inspect
import shutil
import types
from dataclasses import dataclass
from typing import Any, Callable, Union, get_args, get_origin


@dataclass
class ParameterSpec:
    """Complete specification for a single tool parameter.

    Includes both CLI-specific information (option names, argument building)
    and VS Code input metadata (type, description, default, options).
    """

    name: str
    annotation: Any
    default: Any

    # CLI metadata
    input_id: str
    option_name: str  # e.g., '--param-name'
    uses_option: bool  # whether parameter has a default (uses option flag)

    # VS Code input metadata
    input_type: str  # 'promptString', 'pickString', etc.
    input_options: dict[str, Any]  # options for pickString, etc.
    input_description: str
    input_default: Any

    def get_argument_string(self) -> str:
        """Get this parameter's argument string for command building."""
        input_ref: str = f'"${{input:{self.input_id}}}"'
        if self.uses_option:
            return f"{self.option_name} {input_ref}"
        return input_ref

    def to_input_entry(self) -> dict[str, Any]:
        """Convert to VS Code input entry for tasks.json."""
        entry: dict[str, Any] = {
            "id": self.input_id,
            "type": self.input_type,
            "description": self.input_description,
            "default": self.input_default,
        }
        entry.update(self.input_options)
        return entry


@dataclass
class ToolCommandSpec:
    """Rich specification for building a tool command with full metadata."""

    tool: Callable[..., Any]
    tool_name: str
    display_name: str
    docstring: str | None
    parameters: dict[str, ParameterSpec]  # param_name -> spec

    def get_argument_strings(self) -> list[str]:
        """Get all argument strings in parameter order."""
        return [param.get_argument_string() for param in self.parameters.values()]

    def get_input_entries(self) -> list[dict[str, Any]]:
        """Get all VS Code input entries for tasks.json."""
        return [param.to_input_entry() for param in self.parameters.values()]

    def iter_parameters(self) -> list[ParameterSpec]:
        """Iterate parameters in order."""
        return list(self.parameters.values())

    @property
    def command_name(self) -> str:
        """Get the Typer command name derived from tool name."""
        return self.tool_name.replace("_", "-").lower()

    def build_command(self, program_name: str = "toolit", command_prefix: str | None = None) -> str:
        """Build the complete shell command string for this tool spec.

        Args:
            program_name: The program/command name (default: 'toolit').
            command_prefix: Optional prefix like 'uv run --no-sync '. If None, auto-detects uv.

        Returns:
            Complete shell command string ready for execution.
        """
        if command_prefix is None:
            command_prefix = "uv run --no-sync " if shutil.which("uv") else ""

        args: list[str] = self.get_argument_strings()
        rendered_args: str = f" {' '.join(args)}" if args else ""
        return f"{command_prefix}{program_name} {self.command_name}{rendered_args}"


class CliCommandBuilder:
    """Expert analyzer for tool commands with rich metadata generation."""

    def __init__(self, program_name: str = "toolit", command_prefix: str | None = None) -> None:
        """Initialize command builder settings.

        When command_prefix is omitted, uv is used when available.
        """
        self.program_name: str = program_name
        self.command_prefix: str = command_prefix if command_prefix is not None else self._detect_command_prefix()

    @staticmethod
    def create_typer_command_name(tool: Callable[..., Any]) -> str:
        """Create a Typer command name from a tool function name."""
        return tool.__name__.replace("_", "-").lower()

    @staticmethod
    def create_typer_option_name(param_name: str) -> str:
        """Create a Typer option name from a function parameter name."""
        return f"--{param_name.replace('_', '-')}"

    @staticmethod
    def create_display_name(tool: Callable[..., Any]) -> str:
        """Create a user-facing display name from a tool function name."""
        return tool.__name__.replace("_", " ").title()

    @staticmethod
    def create_group_name(tool: Callable[..., Any]) -> str:
        """Create a user-facing group label for grouped tools."""
        return "Group: " + tool.__name__.replace("_", " ").title()

    @staticmethod
    def _detect_command_prefix() -> str:
        """Detect command prefix, preferring uv when available."""
        return "uv run --no-sync " if shutil.which("uv") else ""

    @staticmethod
    def _is_enum(annotation: Any) -> bool:
        """Check if annotation is an Enum type."""
        return isinstance(annotation, type) and issubclass(annotation, enum.Enum)

    @staticmethod
    def _is_bool(annotation: Any) -> bool:
        """Check if annotation is a bool type."""
        return annotation is bool

    @staticmethod
    def _unwrap_union_annotations(annotation: Any) -> list[Any]:
        """Return union members for X | Y or Union[X, Y], or the annotation itself."""
        origin = get_origin(annotation)
        args = get_args(annotation)
        union_type = getattr(types, "UnionType", None)
        if origin is Union or (union_type is not None and origin is union_type):
            return list(args)
        return [annotation]

    @staticmethod
    def _extract_enum_type(annotation: Any) -> type[enum.Enum] | None:
        """Extract enum type from annotation, including optional/union wrappers."""
        for candidate in CliCommandBuilder._unwrap_union_annotations(annotation):
            if candidate in {None, type(None)}:
                continue
            if CliCommandBuilder._is_enum(candidate):
                return candidate
        return None

    @staticmethod
    def _contains_bool(annotation: Any) -> bool:
        """Check whether annotation contains bool directly or via union/optional."""
        return any(
            CliCommandBuilder._is_bool(candidate)
            for candidate in CliCommandBuilder._unwrap_union_annotations(annotation)
        )

    @staticmethod
    def _extract_list_item_type(annotation: Any) -> Any | None:
        """Extract list item type from annotation, including optional/union wrappers."""
        for candidate in CliCommandBuilder._unwrap_union_annotations(annotation):
            if candidate in {None, type(None)}:
                continue
            origin = get_origin(candidate)
            if origin is list:
                args = get_args(candidate)
                if args:
                    return args[0]
                return str
        return None

    @staticmethod
    def _annotation_to_string(annotation: Any) -> str:
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
                result = " | ".join(CliCommandBuilder._annotation_to_string(arg) for arg in args)
            elif origin is not None:
                origin_name = getattr(origin, "__name__", str(origin).replace("typing.", ""))
                if args:
                    args_repr = ", ".join(CliCommandBuilder._annotation_to_string(arg) for arg in args)
                    result = f"{origin_name}[{args_repr}]"
                else:
                    result = origin_name
            elif hasattr(annotation, "__name__"):
                result = annotation.__name__
            else:
                result = str(annotation).replace("typing.", "")

        return result

    @staticmethod
    def _build_list_description(param_name: str, list_item_type: Any) -> str:
        """Build type-specific description for list prompt inputs."""
        if list_item_type is str:
            return f"Enter comma-separated text values for {param_name} (e.g. alpha, beta, gamma)"
        if list_item_type is int:
            return f"Enter comma-separated integer values for {param_name} (e.g. 1, 2, 3)"
        if CliCommandBuilder._is_enum(list_item_type):
            accepted_values = ", ".join(str(member.value) for member in list_item_type)
            return (
                f"Enter comma-separated enum values for {param_name}. "
                f"Accepted values: [{accepted_values}]. You can also use enum member names."
            )
        item_type_name = CliCommandBuilder._annotation_to_string(list_item_type)
        return f"Enter comma-separated values for {param_name} ({item_type_name})"

    def _build_input_metadata(self, param: inspect.Parameter) -> tuple[str, dict[str, Any], str, Any]:
        """Build VS Code input metadata for a single parameter.

        Returns: (input_type, input_options, description, default_value)
        """
        annotation = param.annotation
        input_type: str = "promptString"
        input_options: dict[str, Any] = {}
        description: str = f"Enter value for {param.name} ({self._annotation_to_string(annotation)})"
        default_value: Any = "" if param.default == inspect.Parameter.empty else param.default

        list_item_type = self._extract_list_item_type(annotation)
        if list_item_type is not None:
            description = self._build_list_description(param.name, list_item_type)
            if param.default == inspect.Parameter.empty or param.default is None:
                default_value = "" if param.default == inspect.Parameter.empty else None
            else:
                # Serialize list defaults
                rendered_items: list[str] = []
                for item in param.default:
                    if isinstance(item, enum.Enum):
                        rendered_items.append(str(item.value))
                    else:
                        rendered_items.append(str(item))
                default_value = ", ".join(rendered_items)
            return input_type, input_options, description, default_value

        enum_type = self._extract_enum_type(annotation)
        if enum_type is not None:
            input_type = "pickString"
            choices: list[str] = [e.value for e in enum_type]
            input_options["options"] = choices
            if param.default == inspect.Parameter.empty or param.default is None:
                default_value = choices[0]
            else:
                default_value = param.default.value
            return input_type, input_options, description, default_value

        if self._contains_bool(annotation):
            input_type = "pickString"
            input_options["options"] = ["True", "False"]
            if param.default == inspect.Parameter.empty or param.default is None:
                default_value = "False"
            else:
                default_value = str(param.default)

        return input_type, input_options, description, default_value

    def analyze_tool(self, tool: Callable[..., Any]) -> ToolCommandSpec:
        """Analyze tool and return complete specification for building command and inputs.

        Args:
            tool: The tool function to analyze.

        Returns:
            ToolCommandSpec with all metadata needed for command and input generation.

        Raises:
            ValueError: If a parameter lacks a type annotation.
        """
        sig = inspect.signature(tool)
        parameters: dict[str, ParameterSpec] = {}

        for param in sig.parameters.values():
            if param.name == "self":
                continue

            annotation = param.annotation
            if annotation is inspect.Parameter.empty:
                msg = (
                    f"Parameter '{param.name}' in function '{tool.__name__}' is missing a type annotation. "
                    f"Please add a type hint, e.g.: def {tool.__name__}({param.name}: str) -> None"
                )
                raise ValueError(msg)

            # Build CLI metadata
            input_id: str = f"{tool.__name__}_{param.name}"
            option_name: str = self.create_typer_option_name(param.name)
            uses_option: bool = param.default is not inspect.Parameter.empty

            # Build VS Code input metadata
            input_type, input_options, description, default_value = self._build_input_metadata(param)

            parameters[param.name] = ParameterSpec(
                name=param.name,
                annotation=annotation,
                default=param.default,
                input_id=input_id,
                option_name=option_name,
                uses_option=uses_option,
                input_type=input_type,
                input_options=input_options,
                input_description=description,
                input_default=default_value,
            )

        return ToolCommandSpec(
            tool=tool,
            tool_name=tool.__name__,
            display_name=self.create_display_name(tool),
            docstring=tool.__doc__,
            parameters=parameters,
        )
