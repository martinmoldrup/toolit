"""Tests for create_tasks_json type annotation handling."""

import inspect
from typing import Any, Optional

import pytest

from toolit.create_tasks_json import TaskJsonBuilder, _annotation_to_string


def _tool_with_pep604_optional(input_dataset_name: str | None = None) -> None:
    """Tool with a PEP 604 optional argument."""


def _tool_with_typing_optional(input_dataset_name: Optional[str] = None) -> None:
    """Tool with a typing.Optional argument."""


def test_create_args_for_tool_handles_pep604_optional() -> None:
    """Ensure str | None annotations do not crash and are rendered in descriptions."""
    builder = TaskJsonBuilder()

    args = builder._create_args_for_tool(_tool_with_pep604_optional)

    assert args == ['"${input:_tool_with_pep604_optional_input_dataset_name}"']
    assert builder.inputs[0]["description"] == "Enter value for input_dataset_name (str | None)"
    assert builder.inputs[0]["default"] is None


def test_create_args_for_tool_handles_typing_optional() -> None:
    """Ensure typing.Optional[str] annotations do not crash and are rendered in descriptions."""
    builder = TaskJsonBuilder()

    args = builder._create_args_for_tool(_tool_with_typing_optional)

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
