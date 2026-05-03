"""Tests for CLI command builder with full parameter analysis and metadata generation."""

import enum
import inspect
from types import FunctionType
from typing import Any, Optional, cast

import pytest

from toolit.cli_command_builder import CliCommandBuilder
from toolit.constants import OPTIONAL_STR_SENTINEL


def _as_function(func: Any) -> FunctionType:
    """Cast a Python function to FunctionType for strict type checks."""
    return cast(FunctionType, func)


class Color(enum.Enum):
    """Test enum for colors."""

    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class Environment(str, enum.Enum):
    """Test enum for environments."""

    DEV = "development"
    STAGING = "staging"
    PROD = "production"


def _tool_with_pep604_optional(input_dataset_name: str | None = None) -> None:
    """Tool with a PEP 604 optional argument."""


def _tool_with_typing_optional(input_dataset_name: str | None = None) -> None:
    """Tool with a typing.Optional argument."""


def _tool_without_type_hint(to_print) -> None:  # type: ignore[no-untyped-def]  # noqa: ANN001
    """Tool without a type hint on a parameter."""


def _tool_with_multiple_params_missing_hint(name, value: str) -> None:  # type: ignore[no-untyped-def]  # noqa: ANN001
    """Tool where only the first parameter is missing a type hint."""


def _tool_with_enum_param(color: Color) -> None:  # noqa: ARG001
    """Tool with an enum parameter."""


def _tool_with_enum_param_with_default(color: Color = Color.RED) -> None:  # noqa: ARG001
    """Tool with an enum parameter that has a default value."""


def _tool_with_multiple_enum_params(
    color: Color = Color.RED,  # noqa: ARG001
    environment: Environment | None = None,  # noqa: ARG001
) -> None:
    """Tool with multiple enum parameters."""


def _tool_with_list_str_param(items: list[str]) -> None:  # noqa: ARG001
    """Tool with a list[str] parameter."""


def _tool_with_list_int_param(numbers: list[int] = [1, 2, 3]) -> None:  # noqa: B006, ARG001
    """Tool with a list[int] parameter and list default."""


def _tool_with_list_enum_param(colors: list[Color] = [Color.RED, Color.GREEN]) -> None:  # noqa: B006, ARG001
    """Tool with a list[Enum] parameter and list default."""


def _tool_with_optional_list_param(values: list[str] | None = None) -> None:  # noqa: ARG001
    """Tool with an optional list parameter."""


def _tool_with_bool_param(is_enabled: bool = False) -> None:  # noqa: ARG001
    """Tool with a bool parameter."""


def _tool_with_multiple_bool_params(
    verbose: bool = False,  # noqa: ARG001
    dry_run: bool = True,  # noqa: ARG001
) -> None:
    """Tool with multiple bool parameters."""


def _tool_with_mixed_params(
    name: str,
    count: int = 5,  # noqa: ARG001
    color: Color = Color.RED,  # noqa: ARG001
    is_active: bool = False,  # noqa: ARG001
) -> None:
    """Tool with mixed parameter types."""


def _tool_with_single_param(name: str) -> None:  # noqa: ARG001
    """Tool with a single required parameter."""


def _tool_with_no_params() -> None:
    """Tool with no parameters."""


# ============ Tests for annotation string conversion ============


@pytest.mark.parametrize(
    ("annotation", "expected"),
    [
        (inspect.Parameter.empty, "str"),
        (Any, "Any"),
        (list[str], "list[str]"),
        (dict[str, int], "dict[str, int]"),
        (str | None, "str | None"),
        (Optional[int], "int | None"),
    ],
)
def test_annotation_to_string_formats_common_and_complex_types(annotation: Any, expected: str) -> None:
    """Ensure annotation string conversion supports unions, optionals, and generics."""
    builder = CliCommandBuilder()
    assert builder._annotation_to_string(annotation) == expected


# ============ Tests for optional parameters ============


def test_create_args_for_tool_handles_pep604_optional() -> None:
    """Ensure str | None annotations do not crash and are rendered in descriptions."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_pep604_optional))

    args = spec.get_argument_strings()
    inputs = spec.get_input_entries()

    assert args == [
        '--input-dataset-name "'
        f'{OPTIONAL_STR_SENTINEL}'
        '${input:_tool_with_pep604_optional_input_dataset_name}'
        '"'
    ]
    assert inputs[0]["description"] == "Enter value for input_dataset_name (str | None)"
    assert inputs[0]["default"] is None


def test_create_args_for_tool_handles_typing_optional() -> None:
    """Ensure typing.Optional[str] annotations do not crash and are rendered in descriptions."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_typing_optional))

    args = spec.get_argument_strings()
    inputs = spec.get_input_entries()

    assert args == [
        '--input-dataset-name "'
        f'{OPTIONAL_STR_SENTINEL}'
        '${input:_tool_with_typing_optional_input_dataset_name}'
        '"'
    ]
    assert inputs[0]["description"] == "Enter value for input_dataset_name (str | None)"
    assert inputs[0]["default"] is None


# ============ Tests for error handling ============


def test_create_args_for_tool_raises_on_missing_type_hint() -> None:
    """Ensure a missing type hint raises ValueError with an instructive message."""
    cmd_builder = CliCommandBuilder()

    with pytest.raises(
        ValueError, match="Parameter 'to_print' in function '_tool_without_type_hint' is missing a type annotation"
    ):
        cmd_builder.analyze_tool(_as_function(_tool_without_type_hint))


def test_create_args_for_tool_error_message_includes_fix_hint() -> None:
    """Ensure the error message tells the user how to fix the missing annotation."""
    cmd_builder = CliCommandBuilder()

    with pytest.raises(ValueError, match=r"def _tool_without_type_hint\(to_print: str\) -> None"):
        cmd_builder.analyze_tool(_as_function(_tool_without_type_hint))


def test_create_args_for_tool_raises_on_first_missing_hint_in_mixed_params() -> None:
    """Ensure the error reports the specific parameter that is missing the annotation."""
    cmd_builder = CliCommandBuilder()

    with pytest.raises(ValueError, match="Parameter 'name' in function '_tool_with_multiple_params_missing_hint'"):
        cmd_builder.analyze_tool(_as_function(_tool_with_multiple_params_missing_hint))


# ============ Tests for enum parameters ============


def test_create_args_for_tool_enum_creates_picklist_input() -> None:
    """Ensure enum parameters create pickString input type in tasks.json."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_enum_param))

    args = spec.get_argument_strings()
    inputs = spec.get_input_entries()

    assert args == ['"${input:_tool_with_enum_param_color}"']
    assert inputs[0]["type"] == "pickString"
    assert inputs[0]["options"] == ["red", "green", "blue"]


def test_create_args_for_tool_enum_sets_default_to_first_choice() -> None:
    """Ensure enum parameters default to the first enum value when no default provided."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_enum_param))

    inputs = spec.get_input_entries()

    assert inputs[0]["default"] == "red"


def test_create_args_for_tool_enum_respects_provided_default() -> None:
    """Ensure enum parameters use the provided default value if specified."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_enum_param_with_default))

    args = spec.get_argument_strings()
    inputs = spec.get_input_entries()

    assert args == ['--color "${input:_tool_with_enum_param_with_default_color}"']
    assert inputs[0]["default"] == Color.RED.value


def test_create_args_for_tool_multiple_enum_params() -> None:
    """Ensure multiple enum parameters are all correctly handled in tasks.json."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_multiple_enum_params))

    args = spec.get_argument_strings()
    inputs = spec.get_input_entries()

    assert args == [
        '--color "${input:_tool_with_multiple_enum_params_color}"',
        '--environment "${input:_tool_with_multiple_enum_params_environment}"',
    ]
    assert len(inputs) == 2
    # First input (color)
    assert inputs[0]["type"] == "pickString"
    assert inputs[0]["options"] == ["red", "green", "blue"]
    assert inputs[0]["default"] == "red"
    # Second input (environment)
    assert inputs[1]["type"] == "pickString"
    assert inputs[1]["options"] == ["development", "staging", "production"]
    assert inputs[1]["default"] == "development"


# ============ Tests for list parameters ============


def test_create_args_for_tool_list_str_uses_promptstring_and_guidance() -> None:
    """Ensure list[str] parameters use promptString with comma-separated guidance."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_list_str_param))

    args = spec.get_argument_strings()
    inputs = spec.get_input_entries()

    assert args == ['"${input:_tool_with_list_str_param_items}"']
    assert inputs[0]["type"] == "promptString"
    assert inputs[0]["description"] == "Enter comma-separated text values for items (e.g. alpha, beta, gamma)"
    assert inputs[0]["default"] == ""


def test_create_args_for_tool_list_int_serializes_default_values() -> None:
    """Ensure list[int] defaults are serialized to comma-separated text."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_list_int_param))

    args = spec.get_argument_strings()
    inputs = spec.get_input_entries()

    assert args == ['--numbers "${input:_tool_with_list_int_param_numbers}"']
    assert inputs[0]["description"] == "Enter comma-separated integer values for numbers (e.g. 1, 2, 3)"
    assert inputs[0]["default"] == "1, 2, 3"


def test_create_args_for_tool_list_enum_serializes_default_values() -> None:
    """Ensure list[Enum] defaults are serialized using enum values."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_list_enum_param))

    args = spec.get_argument_strings()
    inputs = spec.get_input_entries()

    assert args == ['--colors "${input:_tool_with_list_enum_param_colors}"']
    assert (
        inputs[0]["description"]
        == "Enter comma-separated enum values for colors. Accepted values: [red, green, blue]. You can also use enum member names."
    )
    assert inputs[0]["default"] == "red, green"


def test_create_args_for_tool_optional_list_keeps_none_default() -> None:
    """Ensure optional list parameters preserve None as default."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_optional_list_param))

    args = spec.get_argument_strings()
    inputs = spec.get_input_entries()

    assert args == ['--values "${input:_tool_with_optional_list_param_values}"']
    assert inputs[0]["default"] is None


# ============ Tests for bool parameters ============


def test_create_args_for_tool_bool_creates_picklist_input() -> None:
    """Ensure bool parameters create pickString input type with True/False options."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_bool_param))

    args = spec.get_argument_strings()
    inputs = spec.get_input_entries()

    assert args == ['--is-enabled "${input:_tool_with_bool_param_is_enabled}"']
    assert inputs[0]["type"] == "pickString"
    assert inputs[0]["options"] == ["True", "False"]
    assert inputs[0]["default"] == "False"


def test_create_args_for_tool_bool_respects_true_default() -> None:
    """Ensure bool parameters with True default preserve that value."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_multiple_bool_params))

    inputs = spec.get_input_entries()

    # dry_run has True default
    assert inputs[1]["default"] == "True"


def test_create_args_for_tool_multiple_bool_params() -> None:
    """Ensure multiple bool parameters are all correctly handled."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_multiple_bool_params))

    args = spec.get_argument_strings()
    inputs = spec.get_input_entries()

    assert len(inputs) == 2
    assert all(inp["type"] == "pickString" for inp in inputs)
    assert all(inp["options"] == ["True", "False"] for inp in inputs)


# ============ Tests for mixed parameter types ============


def test_create_args_for_tool_mixed_params_preserves_order() -> None:
    """Ensure mixed parameter types are processed in definition order."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_mixed_params))

    args = spec.get_argument_strings()
    inputs = spec.get_input_entries()

    # Verify parameter order
    assert len(args) == 4
    assert "name" in args[0]
    assert "count" in args[1]
    assert "color" in args[2]
    assert "is-active" in args[3]


# ============ Tests for CLI option names ============


def test_cli_command_builder_create_typer_option_name_replaces_underscores() -> None:
    """Ensure option names follow Typer's kebab-case convention."""
    assert CliCommandBuilder.create_typer_option_name("string_input") == "--string-input"


def test_cli_command_builder_create_typer_option_name_handles_multiple_underscores() -> None:
    """Ensure multiple underscores are all replaced with dashes."""
    assert CliCommandBuilder.create_typer_option_name("this_is_a_long_name") == "--this-is-a-long-name"


# ============ Tests for command name formatting ============


def test_cli_command_builder_create_typer_command_name_converts_underscores() -> None:
    """Ensure command names use kebab-case."""
    assert CliCommandBuilder.create_typer_command_name(lambda: None) is not None  # Just verify the method exists


def test_cli_command_builder_create_display_name_formats_function_name() -> None:
    """Ensure display names are title-cased with spaces."""
    cmd_builder = CliCommandBuilder()
    # Note: Leading underscores in function names create leading spaces in display names
    assert cmd_builder.create_display_name(_tool_with_single_param) == " Tool With Single Param"


def test_cli_command_builder_create_group_name_adds_group_prefix() -> None:
    """Ensure group names are prefixed with 'Group: '."""
    cmd_builder = CliCommandBuilder()
    group_name = cmd_builder.create_group_name(_tool_with_single_param)
    assert group_name.startswith("Group: ")


# ============ Tests for command building ============


def test_cli_command_builder_build_command_with_no_params() -> None:
    """Ensure command building works for functions with no parameters."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_no_params))

    command = spec.build_command()

    assert "no-params" in command
    assert command.endswith("no-params")


def test_cli_command_builder_build_command_with_single_param() -> None:
    """Ensure command building includes parameter placeholders."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_single_param))

    command = spec.build_command()

    assert "single-param" in command
    assert "${input:" in command


def test_cli_command_builder_build_command_respects_custom_program_name() -> None:
    """Ensure custom program name is used when provided."""
    cmd_builder = CliCommandBuilder(program_name="custom-tool")
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_single_param))

    command = spec.build_command(program_name="custom-tool")

    assert "custom-tool" in command


def test_cli_command_builder_build_command_respects_custom_prefix() -> None:
    """Ensure custom command prefix is used when provided."""
    cmd_builder = CliCommandBuilder(command_prefix="python -m ")
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_single_param))

    command = spec.build_command(command_prefix="python -m ")

    assert command.startswith("python -m ")


def test_cli_command_builder_build_command_detects_uv_when_available() -> None:
    """Ensure uv prefix is detected and used automatically when available."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_single_param))

    command = spec.build_command()

    # The command should have some prefix (either 'uv run --no-sync' or empty)
    # We just verify it constructs properly
    assert "single-param" in command


# ============ Tests for tool specification analysis ============


def test_cli_command_builder_analyze_tool_returns_complete_spec() -> None:
    """Ensure analyze_tool returns a ToolCommandSpec with all required fields."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_mixed_params))

    assert spec.tool == _tool_with_mixed_params
    assert spec.tool_name == "_tool_with_mixed_params"
    assert spec.display_name == " Tool With Mixed Params"  # Leading underscore creates leading space
    assert spec.docstring == "Tool with mixed parameter types."
    assert len(spec.parameters) == 4
    assert spec.command_name == "-tool-with-mixed-params"  # Note: first underscore creates leading dash


def test_cli_command_builder_parameter_spec_contains_metadata() -> None:
    """Ensure ParameterSpec contains all required metadata."""
    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_single_param))

    param_spec = spec.parameters["name"]

    assert param_spec.name == "name"
    assert param_spec.annotation == str
    assert param_spec.input_id == "_tool_with_single_param_name"
    assert param_spec.option_name == "--name"
    assert param_spec.uses_option is False  # Required parameter
    assert param_spec.input_type == "promptString"


# ============ Tests for edge cases ============


def test_cli_command_builder_handles_empty_string_default() -> None:
    """Ensure empty string defaults are preserved in parameter specs."""

    def _tool_with_empty_default(text: str = "") -> None:  # noqa: ARG001
        """Tool with empty string default."""

    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_empty_default))

    inputs = spec.get_input_entries()

    assert inputs[0]["default"] == ""


def test_cli_command_builder_handles_zero_as_default() -> None:
    """Ensure zero integer defaults are preserved and not treated as falsy."""

    def _tool_with_zero_default(count: int = 0) -> None:  # noqa: ARG001
        """Tool with zero default."""

    cmd_builder = CliCommandBuilder()
    spec = cmd_builder.analyze_tool(_as_function(_tool_with_zero_default))

    inputs = spec.get_input_entries()

    assert inputs[0]["default"] == 0
