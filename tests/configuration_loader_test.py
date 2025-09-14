"""Tests for configuration loading functions in toolit.config."""

import toml
import pytest
import pathlib
from toolit import config
from toolit.constants import ConfigFileKeys


def create_toml_file(path: pathlib.Path, data: dict) -> None:
    """Helper to create a TOML file with given data."""
    with open(path, "w", encoding="utf-8") as f:
        toml.dump(data, f)


def test_load_ini_config_returns_empty_for_missing_file(tmp_path: pathlib.Path) -> None:
    """Test load_ini_config returns empty dict if file does not exist."""
    file_path: pathlib.Path = tmp_path / "toolit.ini"
    result: dict[str, str] = config.load_ini_config(file_path)
    assert result == {}


def test_load_ini_config_reads_toolit_section(tmp_path: pathlib.Path) -> None:
    """Test load_ini_config reads 'toolit' section from ini file."""
    file_path: pathlib.Path = tmp_path / "toolit.ini"
    data: dict[str, dict[str, str]] = {"toolit": {"foo": "bar"}}
    create_toml_file(file_path, data)
    result: dict[str, str] = config.load_ini_config(file_path)
    assert result == {"foo": "bar"}


def test_load_ini_config_reads_flat_config(tmp_path: pathlib.Path) -> None:
    """Test load_ini_config returns flat config if no 'toolit' section."""
    file_path: pathlib.Path = tmp_path / "toolit.ini"
    data: dict[str, str] = {"foo": "bar"}
    create_toml_file(file_path, data)
    result: dict[str, str] = config.load_ini_config(file_path)
    assert result == {"foo": "bar"}


def test_load_pyproject_config_returns_empty_for_missing_file(tmp_path: pathlib.Path) -> None:
    """Test load_pyproject_config returns empty dict if file does not exist."""
    file_path: pathlib.Path = tmp_path / "pyproject.toml"
    result: dict[str, str] = config.load_pyproject_config(file_path)
    assert result == {}


def test_load_pyproject_config_reads_toolit_section(tmp_path: pathlib.Path) -> None:
    """Test load_pyproject_config reads 'toolit' section from pyproject.toml."""
    file_path: pathlib.Path = tmp_path / "pyproject.toml"
    data: dict[str, dict[str, str]] = {"toolit": {"foo": "bar"}}
    create_toml_file(file_path, data)
    result: dict[str, str] = config.load_pyproject_config(file_path)
    assert result == {"foo": "bar"}


def test_load_pyproject_config_returns_empty_if_no_toolit_section(tmp_path: pathlib.Path) -> None:
    """Test load_pyproject_config returns empty dict if no 'toolit' section."""
    file_path: pathlib.Path = tmp_path / "pyproject.toml"
    data: dict[str, str] = {"foo": "bar"}
    create_toml_file(file_path, data)
    result: dict[str, str] = config.load_pyproject_config(file_path)
    assert result == {}


def test_get_config_value_returns_value(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    """Test get_config_value returns correct value from config."""
    config_data: dict[str, str] = {"mykey": "myvalue"}
    monkeypatch.setattr(config, "_load_config", lambda: config_data)
    result: str | None = config.get_config_value("mykey")
    assert result == "myvalue"


def test_get_config_value_returns_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_config_value returns default if key not found."""
    monkeypatch.setattr(config, "_load_config", lambda: {})
    result: str | None = config.get_config_value("missing", default="defaultval")
    assert result == "defaultval"


def test_load_devtools_folder_returns_configured_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test load_devtools_folder returns configured folder path."""
    folder: str = "custom_tools_folder"
    monkeypatch.setattr(
        config,
        "get_config_value",
        lambda key, default=None: folder if key == ConfigFileKeys.TOOLS_FOLDER else default,
    )
    result: pathlib.Path = config.load_devtools_folder()
    assert str(result) == folder


def test_load_devtools_folder_returns_default_path() -> None:
    """Test load_devtools_folder returns default folder path if not configured."""
    result: pathlib.Path = config.load_devtools_folder()
    assert str(result) == ConfigFileKeys.TOOLS_FOLDER_DEFAULT