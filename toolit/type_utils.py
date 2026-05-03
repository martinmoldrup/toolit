"""Shared utilities for type annotation handling."""

from __future__ import annotations

import types
from typing import Any, Union, get_args, get_origin


def is_union_type(annotation: Any) -> bool:
    """
    Check if annotation is a Union type (Union[X, Y] or X | Y).

    Handles both:
    - typing.Union[X, Y] (Python 3.9+)
    - X | Y (PEP 604, Python 3.10+)
    """
    origin = get_origin(annotation)
    union_type = getattr(types, "UnionType", None)
    return origin is Union or (union_type is not None and origin is union_type)


def unwrap_union_members(annotation: Any) -> list[Any]:
    """Return members for X | Y / Union[X, Y], or a single-element list otherwise."""
    if is_union_type(annotation):
        return list(get_args(annotation))
    return [annotation]
