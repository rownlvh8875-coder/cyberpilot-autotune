"""Strict value validation at construction; processing recovery belongs to runtime."""

import math
from collections.abc import Mapping
from types import MappingProxyType


class ValidationError(ValueError):
    """Invalid contract or configuration supplied by a caller."""


class NonFiniteError(ValidationError):
    """A numeric value is not finite or cannot be represented as a float."""


def finite(value: object, name: str) -> float:
    if type(value) not in (int, float):
        raise ValidationError(f"{name} must be a finite number")
    try:
        number = float(value)  # type: ignore[arg-type]
    except OverflowError as exc:
        raise NonFiniteError(f"{name} is not representable") from exc
    if not math.isfinite(number):
        raise NonFiniteError(f"{name} must be finite")
    return number


def nonnegative(value: object, name: str) -> float:
    number = finite(value, name)
    if number < 0:
        raise ValidationError(f"{name} must be nonnegative")
    return number


def count(value: object, name: str) -> None:
    if type(value) is not int or value < 0:
        raise ValidationError(f"{name} must be a nonnegative integer")


def text(value: object, name: str) -> None:
    if type(value) is not str or not value or value.strip() != value or not value.isprintable():
        raise ValidationError(f"{name} must be nonempty printable text without edge whitespace")


def boolean(value: object, name: str, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if type(value) is not bool:
        raise ValidationError(f"{name} must be a bool")


def parameters(value: Mapping[str, float]) -> Mapping[str, float]:
    if not isinstance(value, Mapping):
        raise ValidationError("parameters must be a mapping")
    copied: dict[str, float] = {}
    for key, number in value.items():
        text(key, "parameter_id")
        copied[key] = finite(number, "parameter value")
    return MappingProxyType(copied)


def typed_tuple[T](value: tuple[T, ...], item_type: type[T]) -> tuple[T, ...]:
    if not isinstance(value, (tuple, list)) or any(type(item) is not item_type for item in value):
        raise ValidationError("invalid collection element")
    return tuple(value)


def strings(value: tuple[str, ...]) -> tuple[str, ...]:
    result = typed_tuple(value, str)
    for item in result:
        text(item, "diagnostic text")
    return result
