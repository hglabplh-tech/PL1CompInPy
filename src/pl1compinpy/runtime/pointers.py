from __future__ import annotations

from decimal import Decimal
from typing import Any

from .based import PointerValue
from .calculation import PL1Value
from .decimal import FixedDecimal


class PointerBuiltinRuntimeError(ValueError):
    pass


class PointerBuiltinRuntime:
    def POINTER(self, value: Any = None, offset: Any = 0) -> PointerValue:
        pointer_offset = self._integer(offset)
        if pointer_offset < 0:
            raise PointerBuiltinRuntimeError("POINTER offset cannot be negative")
        if isinstance(value, PL1Value):
            value = value.value
        if isinstance(value, PointerValue):
            return PointerValue(value.handle, value.offset + pointer_offset)
        if value is None:
            return PointerValue(None, pointer_offset)
        return PointerValue(self._integer(value), pointer_offset)

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
        raise PointerBuiltinRuntimeError(f"Cannot convert {value!r} to POINTER handle or offset")


__all__ = ["PointerBuiltinRuntime", "PointerBuiltinRuntimeError"]
