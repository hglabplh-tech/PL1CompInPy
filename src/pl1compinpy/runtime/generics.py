from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field


class GenericRuntimeError(ValueError):
    pass


def pl1_type(value: object) -> str:
    if isinstance(value, str):
        return "CHARACTER"
    if isinstance(value, bytes):
        return "BIT"
    if isinstance(value, float):
        return "FLOAT"
    if isinstance(value, int):
        return "FIXED"
    return type(value).__name__.upper()


@dataclass
class GenericFunction:
    name: str
    alternatives: dict[tuple[str, ...], Callable[..., object]] = field(default_factory=dict)

    def when(self, parameter_types: list[str], implementation: Callable[..., object]) -> "GenericFunction":
        self.alternatives[tuple(type_name.upper() for type_name in parameter_types)] = implementation
        return self

    def __call__(self, *arguments: object) -> object:
        key = tuple(pl1_type(argument) for argument in arguments)
        try:
            implementation = self.alternatives[key]
        except KeyError as exc:
            raise GenericRuntimeError(f"No GENERIC match for {self.name}{key}") from exc
        return implementation(*arguments)


class GenericRuntime:
    def __init__(self) -> None:
        self.functions: dict[str, GenericFunction] = {}

    def define(self, name: str) -> GenericFunction:
        function = self.functions.setdefault(name.upper(), GenericFunction(name.upper()))
        return function

    def call(self, name: str, *arguments: object) -> object:
        try:
            return self.functions[name.upper()](*arguments)
        except KeyError as exc:
            raise GenericRuntimeError(f"Unknown GENERIC function: {name}") from exc


__all__ = ["GenericFunction", "GenericRuntime", "GenericRuntimeError", "pl1_type"]
