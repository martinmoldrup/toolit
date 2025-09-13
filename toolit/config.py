"""
Load configurations for packages.

The toolit package lets the user change configurations (azure devops pipeline id, folder for tools, etc.).
User can define the configuration by either:
- Creating a `toolit.ini` toml file in the current working directory
- Adding to the `pyproject.toml` file in the current working directory
"""
import os
import toml
from typing import Any, Callable, Dict, Optional
import pathlib
from .constants import ConfigFileKeysEnum

_config_cache: Optional[Dict[str, Any]] = None  # Lazy-loaded config cache

def load_ini_config(file_path: pathlib.Path) -> Dict[str, Any]:
    """Load configuration from a toolit.ini file."""
    if not file_path.is_file():
        return {}
    configurations = toml.load(file_path)
    if "toolit" in configurations:
        return configurations["toolit"]
    return configurations

def load_pyproject_config(file_path: pathlib.Path) -> Dict[str, Any]:
    """Load configuration from a pyproject.toml file."""
    if not file_path.is_file():
        return {}
    config = toml.load(file_path)
    return config.get("toolit", {})


CONFIG_FILENAMES: Dict[str, Callable[[pathlib.Path], Dict[str, Any]]] = {
    "toolit.ini": load_ini_config,
    "pyproject.toml": load_pyproject_config,
}


def _load_config() -> Dict[str, Any]:
    """Load configuration from toolit.ini or pyproject.toml, only once."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    config: Dict[str, Any] = {}

    for filename, loader in CONFIG_FILENAMES.items():
        file_path = pathlib.Path.cwd() / filename
        file_config = loader(file_path)
        config.update(file_config)

    _config_cache = config
    return config


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value by key."""
    config: Dict[str, Any] = _load_config()
    return config.get(key, default)

def load_devtools_folder() -> pathlib.Path:
    """Load the tools folder path from configuration or use default."""
    folder = get_config_value(ConfigFileKeysEnum.TOOLS_FOLDER, ConfigFileKeysEnum.TOOLS_FOLDER_DEFAULT)
    return pathlib.Path(folder) if isinstance(folder, str) else ConfigFileKeysEnum.TOOLS_FOLDER_DEFAULT
