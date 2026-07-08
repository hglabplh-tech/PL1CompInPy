from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import cmath
from typing import Any


class ComplexRuntimeError(ValueError):
    pass


@dataclass(frozen=True)
class ComplexValue:
    real: Any = 0.0
    imag: Any = 0.0

    @classmethod
    def from_python(cls, value: complex) -> "ComplexValue":
        return cls(_clean_float(value.real), _clean_float(value.imag))

    def as_complex(self) -> complex:
        return complex(_to_float(self.real), _to_float(self.imag))

    def __complex__(self) -> complex:
        return self.as_complex()

    def __str__(self) -> str:
        sign = "+" if _to_float(self.imag) >= 0 else "-"
        return f"{self.real}{sign}{abs(_to_float(self.imag))}i"


def _clean_float(value: float) -> int | float:
    return int(value) if value.is_integer() else value


def _to_float(value: Any) -> float:
    if isinstance(value, ComplexValue):
        complex_value = value.as_complex()
        if abs(complex_value.imag) > 0:
            raise ComplexRuntimeError("Cannot coerce non-real complex value to float")
        return float(complex_value.real)
    if isinstance(value, complex):
        if abs(value.imag) > 0:
            raise ComplexRuntimeError("Cannot coerce non-real complex value to float")
        return float(value.real)
    if hasattr(value, "float") and callable(value.float):
        return float(value.float())
    if hasattr(value, "decimal") and callable(value.decimal):
        return float(value.decimal())
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


class ComplexRuntime:
    def value(self, real: Any = 0.0, imag: Any = 0.0) -> ComplexValue:
        if isinstance(real, ComplexValue) and _to_float(imag) == 0:
            return real
        if isinstance(real, complex) and _to_float(imag) == 0:
            return ComplexValue.from_python(real)
        return ComplexValue(real, imag)

    def normalize(self, value: Any) -> ComplexValue:
        if isinstance(value, ComplexValue):
            return value
        if isinstance(value, complex):
            return ComplexValue.from_python(value)
        return ComplexValue(value, 0.0)

    def add(self, left: Any, right: Any) -> ComplexValue:
        return ComplexValue.from_python(self.normalize(left).as_complex() + self.normalize(right).as_complex())

    def sub(self, left: Any, right: Any) -> ComplexValue:
        return ComplexValue.from_python(self.normalize(left).as_complex() - self.normalize(right).as_complex())

    def mul(self, left: Any, right: Any) -> ComplexValue:
        return ComplexValue.from_python(self.normalize(left).as_complex() * self.normalize(right).as_complex())

    def div(self, left: Any, right: Any) -> ComplexValue:
        divisor = self.normalize(right).as_complex()
        if divisor == 0:
            raise ComplexRuntimeError("complex division by zero")
        return ComplexValue.from_python(self.normalize(left).as_complex() / divisor)

    def power(self, left: Any, right: Any) -> ComplexValue:
        return ComplexValue.from_python(self.normalize(left).as_complex() ** self.normalize(right).as_complex())

    def neg(self, value: Any) -> ComplexValue:
        return ComplexValue.from_python(-self.normalize(value).as_complex())

    def real(self, value: Any) -> Any:
        return self.normalize(value).real if _is_complex_like(value) else value

    def imag(self, value: Any) -> Any:
        return self.normalize(value).imag if _is_complex_like(value) else 0

    def conjg(self, value: Any) -> ComplexValue:
        return ComplexValue.from_python(self.normalize(value).as_complex().conjugate())

    def abs(self, value: Any) -> float:
        return abs(self.normalize(value).as_complex())

    def sqrt(self, value: Any) -> ComplexValue:
        return ComplexValue.from_python(cmath.sqrt(self.normalize(value).as_complex()))

    def exp(self, value: Any) -> ComplexValue:
        return ComplexValue.from_python(cmath.exp(self.normalize(value).as_complex()))

    def log(self, value: Any) -> ComplexValue:
        return ComplexValue.from_python(cmath.log(self.normalize(value).as_complex()))

    def sin(self, value: Any) -> ComplexValue:
        return ComplexValue.from_python(cmath.sin(self.normalize(value).as_complex()))

    def cos(self, value: Any) -> ComplexValue:
        return ComplexValue.from_python(cmath.cos(self.normalize(value).as_complex()))

    def tan(self, value: Any) -> ComplexValue:
        return ComplexValue.from_python(cmath.tan(self.normalize(value).as_complex()))


def _is_complex_like(value: Any) -> bool:
    return isinstance(value, (ComplexValue, complex))


__all__ = ["ComplexRuntime", "ComplexRuntimeError", "ComplexValue"]
