"""Constants for the toolit package."""
import enum
MARKER_TOOL = "__toolit_tool_type__"

class ToolitTypesEnum(enum.Enum):
    """Enum for the different types of toolit tools."""
    TOOL = "tool"
    SEQUENCIAL_GROUP = "sequencial_group"
    PARALLEL_GROUP = "parallel_group"
