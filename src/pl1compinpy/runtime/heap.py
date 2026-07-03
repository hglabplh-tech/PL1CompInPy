from __future__ import annotations

from dataclasses import dataclass


class HeapRuntimeError(ValueError):
    pass


@dataclass
class HeapBlock:
    handle: int
    storage: bytearray

    @property
    def size(self) -> int:
        return len(self.storage)


class HeapRuntime:
    def __init__(self) -> None:
        self._next_handle = 1
        self._blocks: dict[int, HeapBlock] = {}

    def allocate(self, size: int) -> int:
        if size < 0:
            raise HeapRuntimeError("Cannot allocate a negative number of bytes")
        handle = self._next_handle
        self._next_handle += 1
        self._blocks[handle] = HeapBlock(handle, bytearray(size))
        return handle

    def free(self, handle: int) -> None:
        if handle not in self._blocks:
            raise HeapRuntimeError(f"Unknown heap handle: {handle}")
        del self._blocks[handle]

    def block(self, handle: int) -> HeapBlock:
        try:
            return self._blocks[handle]
        except KeyError as exc:
            raise HeapRuntimeError(f"Unknown heap handle: {handle}") from exc


__all__ = ["HeapBlock", "HeapRuntime", "HeapRuntimeError"]

