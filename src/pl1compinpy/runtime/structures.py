from __future__ import annotations

from dataclasses import dataclass, field
from functools import reduce
from operator import mul
from typing import Any

from ..core.ast import StructureField
from .calculation import PL1Type, PL1Value


class StructureRuntimeError(ValueError):
    pass


@dataclass(frozen=True)
class StructureFieldLayout:
    name: str
    path: tuple[str, ...]
    attributes: tuple[str, ...] = ()
    dimensions: tuple[int, ...] = ()
    offset: int = 0
    size: int = 4
    children: tuple["StructureFieldLayout", ...] = ()

    @property
    def qualified_name(self) -> str:
        return ".".join(self.path)


@dataclass
class StructureValue:
    name: str
    layout: StructureFieldLayout
    values: dict[str, Any] = field(default_factory=dict)

    def get_field(self, path: str | list[str] | tuple[str, ...]) -> Any:
        parts = _path_parts(path)
        current: Any = self.values
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                raise StructureRuntimeError(f"Unknown structure field {self.name}.{'.'.join(parts)}")
            current = current[part]
        return current

    def set_field(self, path: str | list[str] | tuple[str, ...], value: Any) -> None:
        parts = _path_parts(path)
        current: Any = self.values
        for part in parts[:-1]:
            if not isinstance(current, dict) or part not in current:
                raise StructureRuntimeError(f"Unknown structure field {self.name}.{'.'.join(parts)}")
            current = current[part]
        if not parts or not isinstance(current, dict) or parts[-1] not in current:
            raise StructureRuntimeError(f"Unknown structure field {self.name}.{'.'.join(parts)}")
        current[parts[-1]] = value

    def flattened(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        self._flatten_values(self.values, [self.name], values)
        return values

    def _flatten_values(self, current: dict[str, Any], prefix: list[str], values: dict[str, Any]) -> None:
        for name, value in current.items():
            path = [*prefix, name]
            if isinstance(value, dict):
                self._flatten_values(value, path, values)
            else:
                values[".".join(path)] = value


class StructureRuntime:
    def __init__(self) -> None:
        self.structures: dict[str, StructureValue] = {}

    def declare_structure(self, field: StructureField) -> StructureValue:
        layout, _ = self._layout(field, (field.name,), 0)
        value = StructureValue(field.name, layout, self._initial_values(layout))
        self.structures[field.name] = value
        return value

    def set_field(self, structure_name: str, field_path: str | list[str] | tuple[str, ...], value: Any) -> None:
        self._structure(structure_name).set_field(field_path, value)

    def get_field(self, structure_name: str, field_path: str | list[str] | tuple[str, ...]) -> Any:
        return self._structure(structure_name).get_field(field_path)

    def flattened_offsets(self, structure_name: str) -> dict[str, int]:
        values: dict[str, int] = {}
        self._flatten_offsets(self._structure(structure_name).layout, values)
        return values

    def _structure(self, name: str) -> StructureValue:
        try:
            return self.structures[name]
        except KeyError as exc:
            raise StructureRuntimeError(f"Unknown structure: {name}") from exc

    def _layout(self, field: StructureField, path: tuple[str, ...], offset: int) -> tuple[StructureFieldLayout, int]:
        child_offset = offset
        children: list[StructureFieldLayout] = []
        for child in field.children:
            child_layout, child_offset = self._layout(child, (*path, child.name), child_offset)
            children.append(child_layout)
        own_size = sum(child.size for child in children) if children else self._field_size(field)
        return (
            StructureFieldLayout(
                field.name,
                path,
                tuple(field.attributes),
                tuple(field.dimensions),
                offset,
                own_size,
                tuple(children),
            ),
            offset + own_size,
        )

    def _field_size(self, field: StructureField) -> int:
        attributes = {attribute.upper() for attribute in field.attributes}
        if "CHARACTER" in attributes or "CHAR" in attributes:
            size = self._first_numeric_attribute(field.attributes) or 1
        elif "FLOAT" in attributes:
            size = 8
        elif "POINTER" in attributes or "PTR" in attributes:
            size = 8
        elif "BIT" in attributes:
            size = 1
        else:
            size = 4
        if field.dimensions:
            size *= reduce(mul, field.dimensions, 1)
        return size

    def _first_numeric_attribute(self, attributes: list[str]) -> int | None:
        for attribute in attributes:
            try:
                return int(float(attribute))
            except ValueError:
                continue
        return None

    def _initial_values(self, layout: StructureFieldLayout) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for child in layout.children:
            if child.children:
                values[child.name] = self._initial_values(child)
            else:
                values[child.name] = self._default_value(child)
        return values

    def _default_value(self, layout: StructureFieldLayout) -> PL1Value:
        attributes = {attribute.upper() for attribute in layout.attributes}
        if "CHARACTER" in attributes or "CHAR" in attributes:
            return PL1Value("", PL1Type.CHARACTER)
        if "FLOAT" in attributes:
            return PL1Value(0.0, PL1Type.FLOAT)
        if "BIT" in attributes:
            return PL1Value(False, PL1Type.BIT)
        return PL1Value(0, PL1Type.FIXED_BIN)

    def _flatten_offsets(self, layout: StructureFieldLayout, values: dict[str, int]) -> None:
        if not layout.children:
            values[layout.qualified_name] = layout.offset
            return
        for child in layout.children:
            self._flatten_offsets(child, values)


def flattened_structure_fields(field: StructureField) -> list[str]:
    runtime = StructureRuntime()
    value = runtime.declare_structure(field)
    return sorted(value.flattened())


def _path_parts(path: str | list[str] | tuple[str, ...]) -> list[str]:
    if isinstance(path, str):
        return [part for part in path.split(".") if part]
    return [str(part) for part in path]


__all__ = [
    "StructureFieldLayout",
    "StructureRuntime",
    "StructureRuntimeError",
    "StructureValue",
    "flattened_structure_fields",
]
