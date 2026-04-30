"""Tests for load_tools_from_folder in auto_loader."""

import os
import pathlib
import types

import pytest

from toolit import auto_loader
from toolit.auto_loader import load_tools_from_folder


class DummyToolitTypesEnum:
    """Dummy enum for tool types."""

    TOOL = "TOOL"
    CLITOOL = "CLITOOL"
    SEQUENTIAL_GROUP = "SEQUENTIAL_GROUP"
    PARALLEL_GROUP = "PARALLEL_GROUP"


@pytest.fixture
def temp_tools_folder(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture to create a temporary folder with tool files."""
    folder: pathlib.Path = tmp_path / "tools"
    folder.mkdir()

    tool_file: pathlib.Path = folder / "my_tool.py"
    tool_file.write_text(
        "def dummy():\n"
        "    pass\n"
        "dummy.toolit_type = 'TOOL'\n"
        "\n"
        "def group():\n"
        "    pass\n"
        "group.toolit_type = 'SEQUENTIAL_GROUP'\n"
        "\n"
        "def cli_command():\n"
        "    pass\n"
        "cli_command.toolit_type = 'CLITOOL'\n"
    )

    nontool_file: pathlib.Path = folder / "not_a_tool.py"
    nontool_file.write_text(
        "def not_a_tool():\n"
        "    pass\n"
    )
    return folder


def patch_auto_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch auto_loader internals for isolated testing."""
    monkeypatch.setattr(auto_loader, "ToolitTypesEnum", DummyToolitTypesEnum)
    monkeypatch.setattr(auto_loader, "MARKER_TOOL", "toolit_type")
    monkeypatch.setattr(auto_loader, "register_command", lambda *args, **kwargs: None)

    def import_module(file: pathlib.Path) -> types.ModuleType:
        module = types.ModuleType(file.stem)
        code = file.read_text()
        exec(code, module.__dict__)
        return module

    monkeypatch.setattr(auto_loader, "import_module", import_module)


@pytest.mark.usefixtures("temp_tools_folder")
def test_load_tools_from_folder_loads_tools_and_groups(
    temp_tools_folder: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test load_tools_from_folder loads tools and tool groups."""
    patch_auto_loader(monkeypatch)
    loaded = load_tools_from_folder(temp_tools_folder)
    loaded_names: set[str] = {f.__name__ for f in loaded}
    assert "dummy" in loaded_names
    assert "group" in loaded_names
    assert "cli_command" in loaded_names
    assert "not_a_tool" not in loaded_names


def test_load_tools_from_folder_empty_folder(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test load_tools_from_folder returns empty list for empty folder."""
    patch_auto_loader(monkeypatch)
    empty_folder: pathlib.Path = tmp_path / "empty"
    empty_folder.mkdir()
    loaded = load_tools_from_folder(empty_folder)
    assert loaded == []


def test_load_tools_from_folder_relative_path(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    """Test load_tools_from_folder works with relative paths."""
    patch_auto_loader(monkeypatch)
    folder: pathlib.Path = tmp_path / "reltools"
    folder.mkdir()
    tool_file: pathlib.Path = folder / "toolx.py"
    tool_file.write_text(
        "def toolx():\n"
        "    pass\n"
        "toolx.toolit_type = 'TOOL'\n"
    )
    cwd = pathlib.Path.cwd()
    try:
        os.chdir(tmp_path)
        loaded = load_tools_from_folder(pathlib.Path("reltools"))
        loaded_names: set[str] = {f.__name__ for f in loaded}
        assert "toolx" in loaded_names
    finally:
        os.chdir(cwd)