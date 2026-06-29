"""Module provides a decorator to wrap a function and apply type coercions to its parameters before calling it."""

from __future__ import annotations

import enum
import typer
import inspect
from collections.abc import Callable
from functools import wraps
from toolit.constants import (
    OPTIONAL_STR_SENTINEL,
)
from toolit.type_utils import unwrap_union_members
from typing import Literal, ParamSpec, TypeAlias, TypeVar, cast, get_args, get_origin

OPTIONAL_UNION_MEMBER_COUNT = 2

P = ParamSpec("P")
R = TypeVar("R")
AnnotationT = TypeVar("AnnotationT")
DefaultT = TypeVar("DefaultT")
RawListItem: TypeAlias = str | int | bool | float | enum.Enum | None
RawCliValue: TypeAlias = RawListItem | list[RawListItem]
CoercedListValue: TypeAlias = list[str] | list[int] | list[enum.Enum] | None
CoercedCliValue: TypeAlias = RawCliValue | CoercedListValue | bool
ListItemType: TypeAlias = type[str] | type[int] | type[enum.Enum]
CoercionKind: TypeAlias = Literal["list", "bool", "optional_str", "required_str"]


def create_type_coercion_wrapper(func: Callable[P, R]) -> Callable[P, R]:
    """
    Wrap a function to add CLI type coercions applied before the function is called.

    Handles:
    - list[T]: splits single comma-separated arg; preserves native multi-arg behavior.
    - bool: changes --flag/--no-flag to --flag VALUE accepting 'True'/'False' strings.
    - str | None: converts empty string to None.
    - required str: rejects empty string with a non-zero exit.
    """
    sig = inspect.signature(func)
    new_params: list[inspect.Parameter] = []
    coercions: dict[str, tuple[CoercionKind, ListItemType | None]] = {}

    for param in sig.parameters.values():
        rewritten_param, coercion = _parameter_coercion_spec(param)
        new_params.append(rewritten_param)
        if coercion is not None:
            coercions[param.name] = coercion

    if not coercions:
        return func

    new_sig = sig.replace(parameters=new_params)

    @wraps(func)
    def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        coerced_kwargs = cast("dict[str, object]", kwargs)
        for param_name, (coercion_type, extra) in coercions.items():
            if param_name not in coerced_kwargs:
                continue
            coerced_kwargs[param_name] = _apply_single_coercion(
                param_name,
                coercion_type,
                extra,
                cast("RawCliValue", coerced_kwargs[param_name]),
            )

        return func(*args, **kwargs)

    setattr(_wrapper, "__signature__", new_sig)  # noqa: B010
    # Rebuild __annotations__ to match the new signature so Typer/get_type_hints
    # sees the transformed types rather than the originals copied by @wraps.
    new_annotations = {
        p.name: p.annotation for p in new_sig.parameters.values() if p.annotation is not inspect.Parameter.empty
    }
    if sig.return_annotation is not inspect.Parameter.empty:
        new_annotations["return"] = sig.return_annotation
    _wrapper.__annotations__ = new_annotations
    return _wrapper


def _extract_list_item_type(annotation: AnnotationT) -> ListItemType | None:
    """Return the T for list[T] (including Optional[list[T]]), or None if not a list."""
    for candidate in unwrap_union_members(annotation):
        if candidate is type(None):
            continue
        if get_origin(candidate) is list:
            args = get_args(candidate)
            if not args:
                return str

            list_item = args[0]
            if list_item is str or list_item is int:
                return list_item
            if isinstance(list_item, type) and issubclass(list_item, enum.Enum):
                return cast("type[enum.Enum]", list_item)
            return str
    return None


def _is_optional_list(annotation: AnnotationT) -> bool:
    """Return True when annotation allows None alongside a list type."""
    members = unwrap_union_members(annotation)
    return type(None) in members and any(get_origin(m) is list for m in members)


def _is_optional_str(annotation: AnnotationT) -> bool:
    """Return True when annotation is exactly str | None."""
    members = unwrap_union_members(annotation)
    return str in members and type(None) in members and len(members) == OPTIONAL_UNION_MEMBER_COUNT


def _is_required_str(annotation: AnnotationT, default: DefaultT) -> bool:
    """Return True when annotation is plain str with no default value."""
    return annotation is str and default is inspect.Parameter.empty


def _contains_bool(annotation: AnnotationT) -> bool:
    """Return True when annotation is or contains bool."""
    return any(m is bool for m in unwrap_union_members(annotation))


def _parameter_coercion_spec(
    param: inspect.Parameter,
) -> tuple[inspect.Parameter, tuple[CoercionKind, ListItemType | None] | None]:
    """Return rewritten parameter and optional coercion metadata for runtime conversion."""
    ann = param.annotation

    list_item_type = _extract_list_item_type(ann)
    if list_item_type is not None:
        new_ann = (list[str] | None) if _is_optional_list(ann) else list[str]
        return param.replace(annotation=new_ann), ("list", list_item_type)

    if _contains_bool(ann):
        if param.default is inspect.Parameter.empty:
            return param.replace(annotation=str), ("bool", None)
        return param.replace(annotation=str, default=str(param.default)), ("bool", None)

    if _is_optional_str(ann):
        return param, ("optional_str", None)

    if _is_required_str(ann, param.default):
        return param, ("required_str", None)

    return param, None


def _coerce_list_value(value: list[RawListItem] | None, item_type: ListItemType) -> CoercedListValue:
    """
    Split a single comma-separated element if needed, then convert to item_type.

    Returns None unchanged (for optional list parameters with no value provided).
    """
    if value is None:
        return None
    if len(value) == 1 and isinstance(value[0], str) and "," in value[0]:
        raw_items: list[str] = [v.strip() for v in value[0].split(",") if v.strip()]
    else:
        raw_items = [str(v) for v in value]

    if item_type is str:
        return raw_items
    if item_type is int:
        return [int(v) for v in raw_items]
    if isinstance(item_type, type) and issubclass(item_type, enum.Enum):
        return [item_type(v) for v in raw_items]
    return raw_items


def _apply_single_coercion(
    param_name: str,
    coercion_type: CoercionKind,
    extra: ListItemType | None,
    value: RawCliValue,
) -> CoercedCliValue:
    """Apply a single coercion strategy to one parameter value."""
    if coercion_type == "list":
        assert extra is not None
        return _coerce_list_value(_normalize_list_input(value), extra)

    if coercion_type == "bool":
        return str(value).lower() == "true"

    if coercion_type == "optional_str":
        if isinstance(value, str) and value.startswith(OPTIONAL_STR_SENTINEL):
            raw_value = value[len(OPTIONAL_STR_SENTINEL) :]
            return cast("CoercedCliValue", raw_value or None)
        if isinstance(value, str) and not value:
            return None
        return cast("CoercedCliValue", value)

    if coercion_type == "required_str" and isinstance(value, str) and not value:
        typer.secho(f"Error: '{param_name}' cannot be empty.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    return cast("CoercedCliValue", value)


def _normalize_list_input(value: RawCliValue) -> list[RawListItem] | None:
    """Normalize Typer list input into a list or None before list coercion."""
    if value is None:
        return None
    if isinstance(value, list):
        return value
    return [value]
