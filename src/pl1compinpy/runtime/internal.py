from __future__ import annotations

from decimal import Decimal
from typing import Any

from .based import PointerValue
from .calculation import PL1Value
from .decimal import FixedDecimal
from .heap import HeapRuntime, HeapRuntimeError


class InternalRuntimeError(ValueError):
    pass


class InternalRuntimeBuiltins:
    def __init__(self, heap: HeapRuntime | None = None) -> None:
        self.heap = heap or HeapRuntime()

    def PL1RT_ALLOC(self, size: Any) -> PointerValue:
        return PointerValue(self.heap.allocate(self._integer(size)), 0)

    def PL1RT_FREE(self, pointer: Any) -> None:
        value = self._pointer(pointer)
        if value.handle is None:
            raise InternalRuntimeError("Cannot free a NULL runtime pointer")
        self.heap.free(value.handle)

    def PL1RT_REALLOC(self, pointer: Any, size: Any) -> PointerValue:
        value = self._pointer(pointer)
        new_size = self._integer(size)
        if value.handle is None:
            return self.PL1RT_ALLOC(new_size)
        old_block = self.heap.block(value.handle)
        new_handle = self.heap.allocate(new_size)
        new_block = self.heap.block(new_handle)
        new_block.storage[: min(old_block.size, new_size)] = old_block.storage[: min(old_block.size, new_size)]
        self.heap.free(value.handle)
        return PointerValue(new_handle, 0)

    def PL1RT_SIZE(self, pointer: Any) -> int:
        value = self._pointer(pointer)
        if value.handle is None:
            return 0
        block = self.heap.block(value.handle)
        return max(block.size - value.offset, 0)

    def PL1RT_PEEK(self, pointer: Any, size: Any = 1, offset: Any = 0) -> bytes:
        value = self._pointer(pointer)
        block, start = self._block_slice(value, self._integer(offset), self._integer(size))
        return bytes(block.storage[start : start + self._integer(size)])

    def PL1RT_POKE(self, pointer: Any, data: Any, offset: Any = 0) -> int:
        payload = self._bytes(data)
        value = self._pointer(pointer)
        block, start = self._block_slice(value, self._integer(offset), len(payload))
        block.storage[start : start + len(payload)] = payload
        return len(payload)

    def PL1RT_FILL(self, pointer: Any, byte_value: Any, size: Any, offset: Any = 0) -> int:
        count = self._integer(size)
        fill = self._integer(byte_value) & 0xFF
        value = self._pointer(pointer)
        block, start = self._block_slice(value, self._integer(offset), count)
        block.storage[start : start + count] = bytes([fill]) * count
        return count

    def _block_slice(self, pointer: PointerValue, extra_offset: int, size: int):
        if pointer.handle is None:
            raise InternalRuntimeError("Runtime pointer is NULL")
        if extra_offset < 0 or size < 0:
            raise InternalRuntimeError("Runtime memory offset and size must be non-negative")
        try:
            block = self.heap.block(pointer.handle)
        except HeapRuntimeError as exc:
            raise InternalRuntimeError(str(exc)) from exc
        start = pointer.offset + extra_offset
        end = start + size
        if start < 0 or end > block.size:
            raise InternalRuntimeError("Runtime memory access exceeds allocated block")
        return block, start

    def _pointer(self, value: Any) -> PointerValue:
        if isinstance(value, PL1Value):
            value = value.value
        if isinstance(value, PointerValue):
            return value
        if value is None:
            return PointerValue()
        return PointerValue(self._integer(value), 0)

    def _bytes(self, value: Any) -> bytes:
        if isinstance(value, PL1Value):
            value = value.value
        if isinstance(value, bytes):
            return value
        if isinstance(value, bytearray):
            return bytes(value)
        if isinstance(value, str):
            return value.encode("utf-8")
        if isinstance(value, int):
            return bytes([value & 0xFF])
        return str(value).encode("utf-8")

    def _integer(self, value: Any) -> int:
        if isinstance(value, PL1Value):
            value = value.value
        if isinstance(value, FixedDecimal):
            return value.int()
        if isinstance(value, Decimal):
            return int(value)
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str) and value.strip():
            return int(Decimal(value.strip()))
        raise InternalRuntimeError(f"Cannot convert {value!r} to an integer runtime size")


__all__ = ["InternalRuntimeBuiltins", "InternalRuntimeError"]
