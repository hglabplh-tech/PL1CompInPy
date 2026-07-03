from __future__ import annotations

from dataclasses import dataclass

from .heap import HeapRuntime


class StringRuntimeError(ValueError):
    pass


@dataclass
class StringValue:
    heap: HeapRuntime
    handle: int

    @property
    def storage(self) -> bytearray:
        return self.heap.block(self.handle).storage

    @property
    def length(self) -> int:
        return int.from_bytes(self.storage[:2], "big")

    @property
    def payload(self) -> bytes:
        return bytes(self.storage[2 : 2 + self.length])

    def text(self, encoding: str = "utf-8") -> str:
        return self.payload.decode(encoding)


class StringRuntime:
    def __init__(self, heap: HeapRuntime | None = None) -> None:
        self.heap = heap or HeapRuntime()

    def allocate(self, data: bytes | str, encoding: str = "utf-8") -> StringValue:
        payload = data.encode(encoding) if isinstance(data, str) else data
        if len(payload) > 0xFFFF:
            raise StringRuntimeError("String payload exceeds two-byte length field")
        handle = self.heap.allocate(2 + len(payload))
        storage = self.heap.block(handle).storage
        storage[:2] = len(payload).to_bytes(2, "big")
        storage[2:] = payload
        return StringValue(self.heap, handle)

    def substr(self, value: StringValue, start: int, count: int | None = None) -> StringValue:
        if start < 1:
            raise StringRuntimeError("SUBSTR start position is one-based")
        payload = value.payload
        index = start - 1
        if index >= len(payload):
            return self.allocate(b"")
        end = None if count is None else index + max(count, 0)
        return self.allocate(payload[index:end])


__all__ = ["StringRuntime", "StringRuntimeError", "StringValue"]

