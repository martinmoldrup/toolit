"""Tests for tasks.json generation and structure.

This module tests the _TaskJsonBuilder class and ensures that tasks.json
is properly structured with correct task entries and input metadata.
"""

from types import FunctionType
from typing import Any, cast

import pytest

from toolit import clitool
from toolit.cli_command_builder import CliCommandBuilder
from toolit.create_tasks_json import _TaskJsonBuilder


def _as_function(func: Any) -> FunctionType:
    """Cast a Python function to FunctionType for strict type checks."""
    return cast(FunctionType, func)


# ============ Tests for task entry creation ============


def test_task_json_builder_creates_task_entry_from_spec() -> None:
    """Ensure _TaskJsonBuilder creates properly formatted task entries."""

    @clitool
    def run_script(name: str) -> str:
        """Run a shell script."""
        return f"echo {name}"

    cmd_builder = CliCommandBuilder()
    builder = _TaskJsonBuilder(cmd_builder)
    spec = cmd_builder.analyze_tool(_as_function(run_script))

    builder._create_task_entry(spec)

    assert len(builder.tasks) == 1
    task = builder.tasks[0]

    assert task["label"] == "Run Script"
    assert task["type"] == "shell"
    assert task["command"].endswith('toolit run-script "${input:run_script_name}"')
    assert task["detail"] == "Run a shell script."
    assert task["problemMatcher"] == []


def test_task_json_builder_omits_detail_when_no_docstring() -> None:
    """Ensure detail field is omitted when tool has no docstring."""

    @clitool
    def run_without_docstring(name: str) -> str:  # type: ignore[no-untyped-def]
        pass

    cmd_builder = CliCommandBuilder()
    builder = _TaskJsonBuilder(cmd_builder)
    spec = cmd_builder.analyze_tool(_as_function(run_without_docstring))

    # Docstring is None, so we'll set it explicitly to test
    spec.docstring = None
    builder._create_task_entry(spec)

    task = builder.tasks[0]
    assert "detail" not in task


def test_task_json_builder_collects_input_entries() -> None:
    """Ensure all input entries are collected during processing."""

    @clitool
    def multi_param(name: str, count: int = 5) -> None:  # noqa: ARG001
        """Tool with multiple parameters."""

    cmd_builder = CliCommandBuilder()
    builder = _TaskJsonBuilder(cmd_builder)
    spec = cmd_builder.analyze_tool(_as_function(multi_param))

    builder._create_task_entry(spec)
    builder.inputs.extend(spec.get_input_entries())

    assert len(builder.inputs) == 2
    assert builder.inputs[0]["id"] == "multi_param_name"
    assert builder.inputs[1]["id"] == "multi_param_count"


def test_task_json_builder_create_tasks_json_returns_proper_structure() -> None:
    """Ensure create_tasks_json returns properly formatted output."""

    @clitool
    def simple_tool(text: str) -> None:  # noqa: ARG001
        """A simple tool."""

    cmd_builder = CliCommandBuilder()
    builder = _TaskJsonBuilder(cmd_builder)
    spec = cmd_builder.analyze_tool(_as_function(simple_tool))
    builder.process_tool(simple_tool)

    tasks_json = builder.create_tasks_json()

    assert "version" in tasks_json
    assert tasks_json["version"] == "2.0.0"
    assert "tasks" in tasks_json
    assert "inputs" in tasks_json
    assert isinstance(tasks_json["tasks"], list)
    assert isinstance(tasks_json["inputs"], list)


def test_task_json_builder_final_json_structure() -> None:
    """Ensure the final tasks.json has correct structure with tasks and inputs."""

    @clitool
    def example_tool(name: str, enabled: bool = False) -> None:  # noqa: ARG001
        """Example tool."""

    cmd_builder = CliCommandBuilder()
    builder = _TaskJsonBuilder(cmd_builder)
    spec = cmd_builder.analyze_tool(_as_function(example_tool))
    builder.process_tool(example_tool)

    tasks_json = builder.create_tasks_json()

    assert len(tasks_json["tasks"]) == 1
    assert len(tasks_json["inputs"]) >= 2
    
    task = tasks_json["tasks"][0]
    assert task["label"] == "Example Tool"
    assert "example-tool" in task["command"]
