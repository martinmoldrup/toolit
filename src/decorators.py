"""
Decorator to tell if a function is a tool.
"""
from typing import Callable, TypeVar, Any
from .constants import MARKER_TOOL


T = TypeVar("T", bound=Callable[..., Any])

def tool(func: T) -> T:
    """Decorator marking a function as a tool."""
    setattr(func, MARKER_TOOL, True)
    return func