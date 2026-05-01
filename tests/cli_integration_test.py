"""Integration tests for CLI command builder with actual typer command execution.

This module tests that commands built by CliCommandBuilder can actually be
executed through a real Typer CLI application. It validates parameter parsing,
type conversions, and handling of edge cases like empty strings and multiple values.
"""

import enum
import subprocess
import sys
from typing import Any

import pytest
import typer

from toolit.cli_command_builder import CliCommandBuilder


# ============ Test enums and types ============


class Priority(str, enum.Enum):
    """Test priority enum."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Mode(enum.Enum):
    """Test mode enum."""

    DEVELOPMENT = "dev"
    PRODUCTION = "prod"


# ============ Test CLI app setup ============


def _create_test_cli_app() -> tuple[typer.Typer, dict[str, Any]]:
    """Create a test CLI app with various tool functions.

    Returns:
        Tuple of (app, results_dict) where results_dict stores command outputs
        for assertion in tests.
    """
    app = typer.Typer()
    results: dict[str, Any] = {}

    @app.command()
    def simple_string(text: str) -> None:
        """Simple string parameter."""
        results["simple_string"] = text

    @app.command()
    def with_default(name: str = "default") -> None:
        """Parameter with default value."""
        results["with_default"] = name

    @app.command()
    def with_integer(count: int) -> None:
        """Integer parameter."""
        results["with_integer"] = count

    @app.command()
    def with_bool(enabled: bool = False) -> None:
        """Boolean parameter."""
        results["with_bool"] = enabled

    @app.command()
    def with_priority(priority: Priority = Priority.MEDIUM) -> None:
        """Enum parameter."""
        results["with_priority"] = priority.value

    @app.command()
    def with_list_str(items: list[str]) -> None:
        """List of strings parameter."""
        results["with_list_str"] = items

    @app.command()
    def with_list_int(numbers: list[int]) -> None:
        """List of integers parameter."""
        results["with_list_int"] = numbers

    @app.command()
    def multiple_params(name: str, count: int = 1, verbose: bool = False) -> None:
        """Multiple parameters of different types."""
        results["multiple_params"] = {"name": name, "count": count, "verbose": verbose}

    return app, results


# ============ Tests for basic parameter types ============


class TestBasicParameterExecution:
    """Tests for basic parameter types through CLI execution."""

    def test_simple_string_parameter_passes_correctly(self) -> None:
        """Ensure simple string parameters are passed and received correctly."""
        cmd_builder = CliCommandBuilder()

        def simple_string(text: str) -> None:  # noqa: ARG001
            """Simple string parameter."""

        spec = cmd_builder.analyze_tool(simple_string)
        
        # Verify the spec is correctly generated for a simple string parameter
        assert "text" in spec.parameters
        assert spec.parameters["text"].annotation == str
        assert spec.parameters["text"].uses_option is False  # Required parameter

    def test_parameter_with_default_value(self) -> None:
        """Ensure parameters with defaults work correctly."""

        def with_default(name: str = "default") -> None:  # noqa: ARG001
            """Parameter with default."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(with_default)

        param = spec.parameters["name"]
        assert param.uses_option is True
        assert param.option_name == "--name"
        inputs = spec.get_input_entries()
        assert inputs[0]["default"] == "default"

    def test_integer_parameter_conversion(self) -> None:
        """Ensure integer parameters are handled correctly."""

        def with_integer(count: int) -> None:  # noqa: ARG001
            """Integer parameter."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(with_integer)

        param = spec.parameters["count"]
        assert param.annotation == int
        assert param.uses_option is False


# ============ Tests for boolean parameters ============


class TestBooleanParameterExecution:
    """Tests for boolean parameter handling through CLI."""

    def test_bool_parameter_defaults_to_false(self) -> None:
        """Ensure bool parameters default to False when not specified."""

        def with_bool(enabled: bool = False) -> None:  # noqa: ARG001
            """Boolean parameter."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(with_bool)

        inputs = spec.get_input_entries()
        assert inputs[0]["type"] == "pickString"
        assert inputs[0]["options"] == ["True", "False"]
        assert inputs[0]["default"] == "False"

    def test_bool_parameter_with_true_default(self) -> None:
        """Ensure bool parameters with True default preserve it."""

        def with_bool_true(enabled: bool = True) -> None:  # noqa: ARG001
            """Boolean parameter with True default."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(with_bool_true)

        inputs = spec.get_input_entries()
        assert inputs[0]["default"] == "True"

    def test_bool_command_with_true_string(self) -> None:
        """Ensure 'True' string is correctly converted to bool True."""
        cmd = CliCommandBuilder().create_typer_option_name("enabled")
        assert cmd == "--enabled"


# ============ Tests for enum parameters ============


class TestEnumParameterExecution:
    """Tests for enum parameter handling through CLI."""

    def test_enum_parameter_creates_picklist(self) -> None:
        """Ensure enum parameters create pickString input."""

        def with_priority(priority: Priority = Priority.MEDIUM) -> None:  # noqa: ARG001
            """Enum parameter."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(with_priority)

        inputs = spec.get_input_entries()
        assert inputs[0]["type"] == "pickString"
        assert "low" in inputs[0]["options"]
        assert "medium" in inputs[0]["options"]
        assert "high" in inputs[0]["options"]
        assert inputs[0]["default"] == "medium"

    def test_enum_with_no_default_uses_first_value(self) -> None:
        """Ensure enum parameters without default use first enum value."""

        def with_mode(mode: Mode) -> None:  # noqa: ARG001
            """Mode parameter without default."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(with_mode)

        inputs = spec.get_input_entries()
        assert inputs[0]["default"] == "dev"  # First enum value


# ============ Tests for list parameters ============


class TestListParameterExecution:
    """Tests for list parameter handling through CLI."""

    def test_list_string_parameter_description(self) -> None:
        """Ensure list[str] parameters provide comma-separated guidance."""

        def with_list_str(items: list[str]) -> None:  # noqa: ARG001
            """List of strings."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(with_list_str)

        inputs = spec.get_input_entries()
        assert inputs[0]["type"] == "promptString"
        assert "comma-separated" in inputs[0]["description"].lower()
        assert "alpha, beta, gamma" in inputs[0]["description"]

    def test_list_int_parameter_description(self) -> None:
        """Ensure list[int] parameters provide integer-specific guidance."""

        def with_list_int(numbers: list[int]) -> None:  # noqa: ARG001
            """List of integers."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(with_list_int)

        inputs = spec.get_input_entries()
        assert "integer" in inputs[0]["description"].lower()
        assert "1, 2, 3" in inputs[0]["description"]

    def test_list_with_defaults_serializes_correctly(self) -> None:
        """Ensure list defaults are serialized to comma-separated strings."""

        def with_list_default(values: list[int] = [10, 20, 30]) -> None:  # noqa: ARG001, B006
            """List with default."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(with_list_default)

        inputs = spec.get_input_entries()
        assert inputs[0]["default"] == "10, 20, 30"


# ============ Tests for edge cases ============


class TestEdgeCases:
    """Tests for edge cases in parameter handling."""

    def test_empty_string_default_is_preserved(self) -> None:
        """Ensure empty string defaults are preserved."""

        def with_empty_default(text: str = "") -> None:  # noqa: ARG001
            """Tool with empty string default."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(with_empty_default)

        inputs = spec.get_input_entries()
        assert inputs[0]["default"] == ""
        assert inputs[0]["type"] == "promptString"

    def test_zero_integer_default_is_not_falsy(self) -> None:
        """Ensure zero integer defaults are preserved and not treated as falsy."""

        def with_zero(count: int = 0) -> None:  # noqa: ARG001
            """Tool with zero default."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(with_zero)

        inputs = spec.get_input_entries()
        assert inputs[0]["default"] == 0

    def test_none_default_for_optional_string(self) -> None:
        """Ensure None defaults for optional strings are preserved."""

        def with_optional(text: str | None = None) -> None:  # noqa: ARG001
            """Tool with optional parameter."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(with_optional)

        inputs = spec.get_input_entries()
        assert inputs[0]["default"] is None

    def test_empty_list_default(self) -> None:
        """Ensure empty list defaults are handled correctly."""

        def with_empty_list(items: list[str] = []) -> None:  # noqa: ARG001, B006
            """Tool with empty list default."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(with_empty_list)

        inputs = spec.get_input_entries()
        assert inputs[0]["default"] == ""

    def test_parameter_with_special_characters_in_default(self) -> None:
        """Ensure defaults with special characters are preserved."""

        def with_special_chars(text: str = "hello,world!") -> None:  # noqa: ARG001
            """Tool with special characters in default."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(with_special_chars)

        inputs = spec.get_input_entries()
        assert inputs[0]["default"] == "hello,world!"


# ============ Tests for command building ============


class TestCommandBuilding:
    """Tests for building complete commands from tool specs."""

    def test_command_includes_all_parameters_in_order(self) -> None:
        """Ensure command includes all parameters in the correct order."""

        def multi_param(name: str, count: int = 1, verbose: bool = False) -> None:  # noqa: ARG001
            """Multiple parameters."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(multi_param)

        command = spec.build_command()
        
        # Verify all parameters are in the command
        assert "--count" in command or "count" in command
        assert "--verbose" in command or "verbose" in command
        assert "${input:multi_param_name}" in command

    def test_command_with_no_parameters(self) -> None:
        """Ensure commands with no parameters are built correctly."""

        def no_params() -> None:
            """Tool with no parameters."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(no_params)

        command = spec.build_command()
        assert "no-params" in command
        assert "${input:" not in command  # No input placeholders

    def test_command_with_custom_program_name(self) -> None:
        """Ensure custom program names are used in commands."""

        def example(name: str) -> None:  # noqa: ARG001
            """Example tool."""

        cmd_builder = CliCommandBuilder(program_name="mytool")
        spec = cmd_builder.analyze_tool(example)

        command = spec.build_command(program_name="mytool")
        assert "mytool" in command

    def test_command_with_custom_prefix(self) -> None:
        """Ensure custom command prefixes are used."""

        def example(name: str) -> None:  # noqa: ARG001
            """Example tool."""

        cmd_builder = CliCommandBuilder(command_prefix="python -m ")
        spec = cmd_builder.analyze_tool(example)

        command = spec.build_command(command_prefix="python -m ")
        assert command.startswith("python -m ")


# ============ Tests for potential issues ============


class TestPotentialIssues:
    """Tests highlighting potential issues with current implementation.

    These tests identify areas where the generated commands might not work
    correctly when executed through the actual CLI.
    """

    @pytest.mark.xfail(reason="Empty string from tasks.json might not parse correctly in Typer")
    def test_empty_string_input_execution(self) -> None:
        """
        Test whether empty strings from task inputs are correctly passed to the CLI.

        POTENTIAL ISSUE: When a user provides an empty string in a tasks.json input,
        it's unclear if Typer will correctly receive and parse an empty string versus
        treating it as a missing argument. This needs verification.
        """

        def process_text(text: str) -> None:  # noqa: ARG001
            """Process text input."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(process_text)

        # The generated command would look like:
        # toolit process-text ""
        # Question: Does Typer handle the empty string correctly?
        args = spec.get_argument_strings()
        assert args[0] == '"${input:process_text_text}"'

    @pytest.mark.xfail(reason="Comma-separated list parsing needs Typer configuration")
    def test_comma_separated_list_input_execution(self) -> None:
        """
        Test whether comma-separated list inputs are correctly parsed by Typer.

        POTENTIAL ISSUE: The tasks.json input provides "item1, item2, item3",
        but Typer expects list[str] to be specified multiple times as:
        --items item1 --items item2 --items item3

        The current implementation doesn't handle the conversion from comma-separated
        strings to repeated option flags. This needs a custom Typer callback or parser.
        """

        def process_items(items: list[str]) -> None:  # noqa: ARG001
            """Process list of items."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(process_items)

        inputs = spec.get_input_entries()
        description = inputs[0]["description"]
        assert "comma-separated" in description.lower()

        # The generated command would be:
        # toolit process-items "item1, item2, item3"
        # But Typer might not correctly parse this as a list without custom handling.

    @pytest.mark.xfail(reason="Boolean string conversion needs Typer configuration")
    def test_bool_string_conversion_in_typer(self) -> None:
        """
        Test whether string "True"/"False" from tasks.json are converted to bool by Typer.

        POTENTIAL ISSUE: The tasks.json input provides "True" or "False" as strings,
        but Typer needs to convert these to actual boolean values. Typer's default
        behavior might not handle this conversion without custom configuration.
        """

        def set_flag(enabled: bool = False) -> None:  # noqa: ARG001
            """Set a boolean flag."""

        cmd_builder = CliCommandBuilder()
        spec = cmd_builder.analyze_tool(set_flag)

        inputs = spec.get_input_entries()
        assert inputs[0]["options"] == ["True", "False"]

        # The generated command would be:
        # toolit set-flag --enabled True
        # Question: Does Typer correctly convert the string "True" to bool True?


# ============ Question for design discussion ============


class TestDesignQuestions:
    """Tests and questions about the overall design.

    These highlight areas where design decisions need to be made.
    """

    def test_how_should_list_parameters_be_handled_in_tasks_json(self) -> None:
        """
        Question: How should list parameters be input through tasks.json?

        Current approach:
        - Input: "item1, item2, item3" (user types comma-separated values)
        - Command: toolit process-items "item1, item2, item3"
        - Typer expectation: --items item1 --items item2 --items item3

        Alternative approaches:
        1. Use a custom separator character (e.g., semicolon or pipe)
        2. Use a Typer callback to parse comma-separated strings
        3. Require quoted JSON format: '["item1", "item2"]'
        4. Use a different input mechanism entirely
        """
        pass

    def test_how_should_empty_strings_be_handled(self) -> None:
        """
        Question: How should empty string values be handled in tasks.json inputs?

        Current approach:
        - User leaves input blank or types nothing
        - Input default is empty string ""
        - Generated command: toolit command-name ""

        Issues:
        - Unclear if shell will pass empty string to Typer
        - Unclear if Typer will treat it as None vs empty string
        - Might conflict with required string parameters

        Should empty strings be:
        1. Not allowed for required parameters?
        2. Converted to None for optional parameters?
        3. Treated as a special marker?
        """
        pass
