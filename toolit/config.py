"""
Load configurations for packages.

The toolit package lets the user change configurations (azure devops pipeline id, folder for tools, etc.).
User can define the configuration by either:
- Creating a `toolit.ini` toml file in the current working directory
- Adding to the `pyproject.toml` file in the current working directory
"""
from __future__ import annotations

import toml
import pathlib
from collections.abc import Callable
from functools import lru_cache
from toolit.constants import ConfigFileKeys
from typing import overload


def load_ini_config(file_path: pathlib.Path) -> dict[str, str]:
    """Load configuration from a toolit.ini file."""
    if not file_path.is_file():
        return {}
    configurations = toml.load(file_path)
    if "toolit" in configurations:
        return configurations["toolit"]
    return configurations


def load_pyproject_config(file_path: pathlib.Path) -> dict[str, str]:
    """Load configuration from a pyproject.toml file."""
    if not file_path.is_file():
        return {}
    config = toml.load(file_path)
    return config.get("toolit", {})


CONFIG_FILENAMES: dict[str, Callable[[pathlib.Path], dict[str, str]]] = {
    "toolit.ini": load_ini_config,
    "pyproject.toml": load_pyproject_config,
}


@lru_cache(maxsize=1)
def _load_config() -> dict[str, str]:
    """Load configuration from toolit.ini or pyproject.toml, only once."""
    config: dict[str, str] = {}
    for filename, loader in CONFIG_FILENAMES.items():
        file_path = pathlib.Path.cwd() / filename
        file_config = loader(file_path)
        config.update(file_config)

    return config


@overload
def get_config_value(key: str, default: None = None) -> str | None: ...

@overload
def get_config_value(key: str, default: str) -> str: ...


def get_config_value(key: str, default: str | None = None) -> str | None:
    """Get a configuration value by key with type-safe default."""
    config: dict[str, str] = _load_config()
    return config.get(key, default)


def load_devtools_folder() -> pathlib.Path:
    """Load the tools folder path from configuration or use default."""
    folder = get_config_value(ConfigFileKeys.TOOLS_FOLDER, ConfigFileKeys.TOOLS_FOLDER_DEFAULT)
    return pathlib.Path(folder)
