"""Constants for the toolit package."""

import enum

MARKER_TOOL = "__toolit_tool_type__"


class RichHelpPanelNames:
    """Namespace for the different rich help panel names."""

    NAME_OF_THE_RICH_GROUP_HELP_PANEL_PROJECT = "Commands from Project"
    NAME_OF_THE_RICH_GROUP_HELP_PANEL_PLUGINS = "Commands from Plugins"


class ConfigFileKeys:
    """Namespace for the different configuration file keys for user configuration."""

    TOOLS_FOLDER: str = "tools_folder"
    TOOLS_FOLDER_DEFAULT: str = "devtools"


class ToolitTypesEnum(enum.Enum):
    """Enum for the different types of toolit tools."""

    TOOL = "tool"
    SEQUENTIAL_GROUP = "sequential_group"
    PARALLEL_GROUP = "parallel_group"
