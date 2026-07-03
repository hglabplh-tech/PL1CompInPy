from __future__ import annotations

from dataclasses import dataclass

from .heap import HeapRuntime, HeapRuntimeError


class BasedRuntimeError(ValueError):
    pass


@dataclass
class PointerValue:
    handle: int | None = None
    offset: int = 0

    @property
    def is_null(self) -> bool:
        return self.handle is None


@dataclass(frozen=True)
class BasedRecord:
    name: str
    pointer_name: str | None
    size: int


class BasedRuntime:
    def __init__(self, heap: HeapRuntime | None = None) -> None:
        self.heap = heap or HeapRuntime()
        self.pointers: dict[str, PointerValue] = {}
        self.records: dict[str, BasedRecord] = {}

    def declare_pointer(self, name: str) -> PointerValue:
        pointer = self.pointers.setdefault(name, PointerValue())
        return pointer

    def declare_based_record(self, name: str, size: int, pointer_name: str | None = None) -> BasedRecord:
        if size < 0:
            raise BasedRuntimeError("BASED record size cannot be negative")
        if pointer_name is not None:
            self.declare_pointer(pointer_name)
        record = BasedRecord(name, pointer_name, size)
        self.records[name] = record
        return record

    def allocate_based(self, record_name: str, pointer_name: str | None = None) -> PointerValue:
        record = self._record(record_name)
        locator = pointer_name or record.pointer_name
        if locator is None:
            raise BasedRuntimeError(f"BASED record {record_name} has no pointer locator")
        handle = self.heap.allocate(record.size)
        pointer = self.declare_pointer(locator)
        pointer.handle = handle
        pointer.offset = 0
        return pointer

    def set_pointer(self, pointer_name: str, handle: int, offset: int = 0) -> PointerValue:
        if offset < 0:
            raise BasedRuntimeError("Pointer offset cannot be negative")
        try:
            self.heap.block(handle)
        except HeapRuntimeError as exc:
            raise BasedRuntimeError(f"Cannot set pointer {pointer_name} to unknown handle {handle}") from exc
        pointer = self.declare_pointer(pointer_name)
        pointer.handle = handle
        pointer.offset = offset
        return pointer

    def set_pointer_to_record(self, pointer_name: str, record_name: str, source_pointer: str | None = None) -> PointerValue:
        source = self.pointer_for_record(record_name, source_pointer)
        if source.handle is None:
            raise BasedRuntimeError(f"Record {record_name} is not currently based on allocated storage")
        return self.set_pointer(pointer_name, source.handle, source.offset)

    def pointer_for_record(self, record_name: str, pointer_name: str | None = None) -> PointerValue:
        record = self._record(record_name)
        locator = pointer_name or record.pointer_name
        if locator is None:
            raise BasedRuntimeError(f"BASED record {record_name} has no pointer locator")
        pointer = self.declare_pointer(locator)
        if pointer.handle is None:
            raise BasedRuntimeError(f"Pointer {locator} is NULL for BASED record {record_name}")
        return pointer

    def storage_for(self, record_name: str, pointer_name: str | None = None) -> memoryview:
        record = self._record(record_name)
        pointer = self.pointer_for_record(record_name, pointer_name)
        block = self.heap.block(pointer.handle or 0)
        end = pointer.offset + record.size
        if end > block.size:
            raise BasedRuntimeError(f"BASED record {record_name} exceeds target storage")
        return memoryview(block.storage)[pointer.offset:end]

    def write_record(self, record_name: str, data: bytes, pointer_name: str | None = None) -> None:
        storage = self.storage_for(record_name, pointer_name)
        if len(data) > len(storage):
            raise BasedRuntimeError(f"Data does not fit BASED record {record_name}")
        storage[: len(data)] = data
        if len(data) < len(storage):
            storage[len(data) :] = b"\0" * (len(storage) - len(data))

    def read_record(self, record_name: str, pointer_name: str | None = None) -> bytes:
        return bytes(self.storage_for(record_name, pointer_name))

    def _record(self, name: str) -> BasedRecord:
        try:
            return self.records[name]
        except KeyError as exc:
            raise BasedRuntimeError(f"Unknown BASED record: {name}") from exc


__all__ = ["BasedRecord", "BasedRuntime", "BasedRuntimeError", "PointerValue"]
