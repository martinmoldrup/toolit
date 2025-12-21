"""Decorator to tell if a function is a tool."""

from collections.abc import Callable
from toolit.constants import MARKER_TOOL, ToolitTypesEnum
from typing import Any, TypeVar

T = TypeVar("T", bound=Callable[..., Any])


def tool(func: T) -> T:
    """Decorate function as a tool by setting a marker."""
    setattr(func, MARKER_TOOL, ToolitTypesEnum.TOOL)
    return func


def sequential_group_of_tools(func: T) -> T:
    """Decorate a function that returns a list of callable tools."""
    setattr(func, MARKER_TOOL, ToolitTypesEnum.SEQUENTIAL_GROUP)
    return func


def parallel_group_of_tools(func: T) -> T:
    """Decorate a function that returns a list of callable tools."""
    setattr(func, MARKER_TOOL, ToolitTypesEnum.PARALLEL_GROUP)
    return func
