from __future__ import annotations

from dataclasses import dataclass, field
from functools import reduce
from operator import mul

from .heap import HeapRuntime


class ArrayRuntimeError(ValueError):
    pass


@dataclass
class ArrayValue:
    name: str
    dimensions: list[int]
    heap_handle: int
    element_size: int = 4
    values: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        total = self.element_count
        if not self.values:
            self.values = [0] * total

    @property
    def element_count(self) -> int:
        return reduce(mul, self.dimensions, 1)

    def index(self, *subscripts: int) -> int:
        if len(subscripts) != len(self.dimensions):
            raise ArrayRuntimeError(f"{self.name} expects {len(self.dimensions)} subscripts")
        offset = 0
        stride = 1
        for subscript, bound in zip(reversed(subscripts), reversed(self.dimensions)):
            if subscript < 1 or subscript > bound:
                raise ArrayRuntimeError(f"{self.name} subscript {subscript} outside 1..{bound}")
            offset += (subscript - 1) * stride
            stride *= bound
        return offset

    def get(self, *subscripts: int) -> int:
        return self.values[self.index(*subscripts)]

    def set(self, value: int, *subscripts: int) -> None:
        self.values[self.index(*subscripts)] = value


class ArrayRuntime:
    def __init__(self, heap: HeapRuntime | None = None) -> None:
        self.heap = heap or HeapRuntime()
        self.arrays: dict[str, ArrayValue] = {}

    def allocate_array(self, name: str, dimensions: list[int], element_size: int = 4) -> ArrayValue:
        if not dimensions or any(dimension <= 0 for dimension in dimensions):
            raise ArrayRuntimeError(f"Invalid dimensions for {name}: {dimensions}")
        element_count = reduce(mul, dimensions, 1)
        handle = self.heap.allocate(element_count * element_size)
        value = ArrayValue(name, dimensions, handle, element_size)
        self.arrays[name] = value
        return value

    def free_array(self, name: str) -> None:
        array = self.arrays.pop(name)
        self.heap.free(array.heap_handle)


__all__ = ["ArrayRuntime", "ArrayRuntimeError", "ArrayValue"]

