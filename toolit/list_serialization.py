"""Utilities for serializing list defaults for CLI/task inputs."""

from __future__ import annotations

import enum
from typing import Any


def serialize_list_default(default_value: Any) -> str:  # noqa: ANN401
    """Serialize list defaults to comma-separated text using enum values when needed."""
    if default_value is None:
        return ""
    if isinstance(default_value, list):
        rendered_items: list[str] = []
        for item in default_value:
            if isinstance(item, enum.Enum):
                rendered_items.append(str(item.value))
            else:
                rendered_items.append(str(item))
        return ", ".join(rendered_items)
    return str(default_value)