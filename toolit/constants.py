"""Constants for the toolit package."""

import enum
import pathlib

MARKER_TOOL = "__toolit_tool_type__"


class ConfigFileKeysEnum:
    """Namespace for the different configuration file keys for user configuration."""

    TOOLS_FOLDER: str = "tools_folder"
    TOOLS_FOLDER_DEFAULT: pathlib.Path = pathlib.Path() / "devtools"

class ToolitTypesEnum(enum.Enum):
    """Enum for the different types of toolit tools."""

    TOOL = "tool"
    SEQUENTIAL_GROUP = "sequential_group"
    PARALLEL_GROUP = "parallel_group"
