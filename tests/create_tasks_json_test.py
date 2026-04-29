"""Tests for create_tasks_json type annotation handling."""

import enum
import inspect
from typing import Any, Optional

import pytest

from toolit.create_tasks_json import TaskJsonBuilder, _annotation_to_string  # noqa: PLC2701


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


def test_create_args_for_tool_handles_pep604_optional() -> None:
    """Ensure str | None annotations do not crash and are rendered in descriptions."""
    builder = TaskJsonBuilder()

    args = builder._create_args_for_tool(_tool_with_pep604_optional)  # noqa: SLF001

    assert args == ['"${input:_tool_with_pep604_optional_input_dataset_name}"']
    assert builder.inputs[0]["description"] == "Enter value for input_dataset_name (str | None)"
    assert builder.inputs[0]["default"] is None


def test_create_args_for_tool_handles_typing_optional() -> None:
    """Ensure typing.Optional[str] annotations do not crash and are rendered in descriptions."""
    builder = TaskJsonBuilder()

    args = builder._create_args_for_tool(_tool_with_typing_optional)  # noqa: SLF001

    assert args == ['"${input:_tool_with_typing_optional_input_dataset_name}"']
    assert builder.inputs[0]["description"] == "Enter value for input_dataset_name (str | None)"
    assert builder.inputs[0]["default"] is None


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
    assert _annotation_to_string(annotation) == expected


def test_create_args_for_tool_raises_on_missing_type_hint() -> None:
    """Ensure a missing type hint raises ValueError with an instructive message."""
    builder = TaskJsonBuilder()

    with pytest.raises(
        ValueError, match="Parameter 'to_print' in function '_tool_without_type_hint' is missing a type annotation"
    ):
        builder._create_args_for_tool(_tool_without_type_hint)


def test_create_args_for_tool_error_message_includes_fix_hint() -> None:
    """Ensure the error message tells the user how to fix the missing annotation."""
    builder = TaskJsonBuilder()

    with pytest.raises(ValueError, match=r"def _tool_without_type_hint\(to_print: str\) -> None"):
        builder._create_args_for_tool(_tool_without_type_hint)


def test_create_args_for_tool_raises_on_first_missing_hint_in_mixed_params() -> None:
    """Ensure the error reports the specific parameter that is missing the annotation."""
    builder = TaskJsonBuilder()

    with pytest.raises(ValueError, match="Parameter 'name' in function '_tool_with_multiple_params_missing_hint'"):
        builder._create_args_for_tool(_tool_with_multiple_params_missing_hint)


def test_create_args_for_tool_enum_creates_picklist_input() -> None:
    """Ensure enum parameters create pickString input type in tasks.json."""
    builder = TaskJsonBuilder()

    args = builder._create_args_for_tool(_tool_with_enum_param)  # noqa: SLF001

    assert args == ['"${input:_tool_with_enum_param_color}"']
    assert builder.inputs[0]["type"] == "pickString"
    assert builder.inputs[0]["options"] == ["red", "green", "blue"]


def test_create_args_for_tool_enum_sets_default_to_first_choice() -> None:
    """Ensure enum parameters default to the first enum value when no default provided."""
    builder = TaskJsonBuilder()

    args = builder._create_args_for_tool(_tool_with_enum_param)  # noqa: SLF001

    assert builder.inputs[0]["default"] == "red"


def test_create_args_for_tool_enum_respects_provided_default() -> None:
    """Ensure enum parameters use the provided default value if specified."""
    builder = TaskJsonBuilder()

    args = builder._create_args_for_tool(_tool_with_enum_param_with_default)  # noqa: SLF001

    assert builder.inputs[0]["default"] == Color.RED.value


def test_create_args_for_tool_multiple_enum_params() -> None:
    """Ensure multiple enum parameters are all correctly handled in tasks.json."""
    builder = TaskJsonBuilder()

    args = builder._create_args_for_tool(_tool_with_multiple_enum_params)  # noqa: SLF001

    assert len(builder.inputs) == 2
    # First input (color)
    assert builder.inputs[0]["type"] == "pickString"
    assert builder.inputs[0]["options"] == ["red", "green", "blue"]
    assert builder.inputs[0]["default"] == "red"
    # Second input (environment)
    assert builder.inputs[1]["type"] == "pickString"
    assert builder.inputs[1]["options"] == ["development", "staging", "production"]
    assert builder.inputs[1]["default"] == "development"
