from __future__ import annotations

from dataclasses import dataclass
import cmath
from decimal import Decimal, ROUND_CEILING, ROUND_DOWN, ROUND_FLOOR, ROUND_HALF_UP, getcontext
import math
from typing import Any

from .complex import ComplexRuntime, ComplexValue
from .strings import StringValue

getcontext().prec = max(getcontext().prec, 80)


@dataclass(frozen=True)
class FixedDecimal:
    scaled: int
    precision: int
    scale: int = 0

    @classmethod
    def from_decimal(cls, value: Decimal, precision: int, scale: int = 0) -> "FixedDecimal":
        factor = Decimal(10) ** scale
        scaled = int((value * factor).to_integral_value(rounding=ROUND_HALF_UP))
        result = cls(scaled, precision, scale)
        result.check()
        return result

    @classmethod
    def from_string(cls, text: str, precision: int, scale: int = 0) -> "FixedDecimal":
        return cls.from_decimal(Decimal(text.strip()), precision, scale)

    @classmethod
    def from_int(cls, value: int, precision: int, scale: int = 0) -> "FixedDecimal":
        return cls.from_decimal(Decimal(value), precision, scale)

    @classmethod
    def from_float(cls, value: float, precision: int, scale: int = 0) -> "FixedDecimal":
        return cls.from_decimal(Decimal(str(value)), precision, scale)

    def decimal(self) -> Decimal:
        return Decimal(self.scaled) / (Decimal(10) ** self.scale)

    def string(self) -> str:
        quantum = Decimal(1) / (Decimal(10) ** self.scale)
        return str(self.decimal().quantize(quantum))

    def __str__(self) -> str:
        return self.string()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FixedDecimal):
            return self.decimal() == other.decimal()
        if isinstance(other, Decimal):
            return self.decimal() == other
        return False

    def int(self) -> int:
        return int(self.decimal())

    def float(self) -> float:
        return float(self.decimal())

    def check(self) -> None:
        digits = len(str(abs(self.scaled)).lstrip("0")) or 1
        if digits > self.precision:
            raise OverflowError(f"FIXED DECIMAL({self.precision},{self.scale}) overflow")

    def rescale(self, precision: int, scale: int) -> "FixedDecimal":
        return FixedDecimal.from_decimal(self.decimal(), precision, scale)

    def add(self, other: "FixedDecimal") -> "FixedDecimal":
        scale = max(self.scale, other.scale)
        precision = max(self.precision - self.scale, other.precision - other.scale) + scale + 1
        left = self.rescale(precision, scale)
        right = other.rescale(precision, scale)
        return FixedDecimal(left.scaled + right.scaled, precision, scale)

    def sub(self, other: "FixedDecimal") -> "FixedDecimal":
        scale = max(self.scale, other.scale)
        precision = max(self.precision - self.scale, other.precision - other.scale) + scale + 1
        left = self.rescale(precision, scale)
        right = other.rescale(precision, scale)
        return FixedDecimal(left.scaled - right.scaled, precision, scale)

    def mul(self, other: "FixedDecimal") -> "FixedDecimal":
        return FixedDecimal(self.scaled * other.scaled, self.precision + other.precision, self.scale + other.scale)

    def div(self, other: "FixedDecimal", precision: int | None = None, scale: int | None = None) -> "FixedDecimal":
        if other.scaled == 0:
            raise ZeroDivisionError("decimal division by zero")
        precision = precision or max(self.precision, other.precision) + 8
        scale = scale if scale is not None else max(self.scale, other.scale) + 8
        return FixedDecimal.from_decimal(self.decimal() / other.decimal(), precision, scale)


POS_OVERPUNCH = {"0": "{", "1": "A", "2": "B", "3": "C", "4": "D", "5": "E", "6": "F", "7": "G", "8": "H", "9": "I"}
NEG_OVERPUNCH = {"0": "}", "1": "J", "2": "K", "3": "L", "4": "M", "5": "N", "6": "O", "7": "P", "8": "Q", "9": "R"}
REV_OVERPUNCH = {value: (key, 1) for key, value in POS_OVERPUNCH.items()}
REV_OVERPUNCH.update({value: (key, -1) for key, value in NEG_OVERPUNCH.items()})


class ZonedDecimalCodec:
    @staticmethod
    def encode(value: FixedDecimal, signed: bool = True, overpunch: bool = True) -> str:
        digits = str(abs(value.scaled)).rjust(value.precision, "0")
        if not signed:
            return digits
        if overpunch:
            table = POS_OVERPUNCH if value.scaled >= 0 else NEG_OVERPUNCH
            return digits[:-1] + table[digits[-1]]
        return ("+" if value.scaled >= 0 else "-") + digits

    @staticmethod
    def decode(text: str, precision: int, scale: int = 0) -> FixedDecimal:
        value = text.strip()
        sign = 1
        if value and value[0] in "+-":
            sign = -1 if value[0] == "-" else 1
            digits = value[1:]
        elif value and value[-1] in REV_OVERPUNCH:
            last_digit, sign = REV_OVERPUNCH[value[-1]]
            digits = value[:-1] + last_digit
        else:
            digits = value
        if not digits.isdigit():
            raise ValueError(f"Invalid zoned decimal: {text!r}")
        return FixedDecimal(sign * int(digits), precision, scale)


class PackedDecimalCodec:
    POS_SIGNS = {0xA, 0xC, 0xE, 0xF}
    NEG_SIGNS = {0xB, 0xD}

    @staticmethod
    def encode(value: FixedDecimal) -> bytes:
        digits = str(abs(value.scaled)).rjust(value.precision, "0")
        sign = 0xC if value.scaled >= 0 else 0xD
        nibbles = [int(digit) for digit in digits] + [sign]
        if len(nibbles) % 2:
            nibbles.insert(0, 0)
        return bytes((nibbles[index] << 4) | nibbles[index + 1] for index in range(0, len(nibbles), 2))

    @staticmethod
    def decode(data: bytes | bytearray, precision: int, scale: int = 0) -> FixedDecimal:
        nibbles: list[int] = []
        for byte in bytes(data):
            nibbles.append((byte >> 4) & 0xF)
            nibbles.append(byte & 0xF)
        sign_nibble = nibbles.pop()
        if sign_nibble in PackedDecimalCodec.NEG_SIGNS:
            sign = -1
        elif sign_nibble in PackedDecimalCodec.POS_SIGNS:
            sign = 1
        else:
            raise ValueError(f"Invalid packed sign nibble {sign_nibble:X}")
        digits = nibbles[-precision:]
        if any(digit > 9 for digit in digits):
            raise ValueError("Invalid packed decimal digit")
        return FixedDecimal(sign * int("".join(str(digit) for digit in digits)), precision, scale)


class DecimalRuntime:
    @staticmethod
    def fixed_decimal(value: Decimal | str | int | float | FixedDecimal, precision: int, scale: int = 0) -> FixedDecimal:
        if isinstance(value, FixedDecimal):
            return value.rescale(precision, scale)
        if isinstance(value, Decimal):
            return FixedDecimal.from_decimal(value, precision, scale)
        if isinstance(value, int):
            return FixedDecimal.from_int(value, precision, scale)
        if isinstance(value, float):
            return FixedDecimal.from_float(value, precision, scale)
        return FixedDecimal.from_string(str(value), precision, scale)

    @staticmethod
    def convert(value: Any, source: str, target: str, *, precision: int, scale: int = 0) -> Any:
        fixed = DecimalRuntime.to_fixed_decimal(value, source, precision, scale)
        target = target.upper().replace(" ", "_")
        if target in {"FIXED_DEC", "FIXED_DECIMAL"}:
            return fixed
        if target == "STRING":
            return fixed.string()
        if target in {"FIXED_BIN", "FIXED_BINARY"}:
            return fixed.int()
        if target in {"FLOAT", "FLOAT_BINARY"}:
            return fixed.float()
        if target == "FLOAT_DECIMAL":
            return fixed.decimal()
        if target == "ZONED":
            return ZonedDecimalCodec.encode(fixed)
        if target == "PACKED":
            return PackedDecimalCodec.encode(fixed)
        raise ValueError(f"Unknown decimal conversion target: {target}")

    @staticmethod
    def to_fixed_decimal(value: Any, source: str, precision: int, scale: int = 0) -> FixedDecimal:
        source = source.upper().replace(" ", "_")
        if source in {"FIXED_DEC", "FIXED_DECIMAL"}:
            return DecimalRuntime.fixed_decimal(value, precision, scale)
        if source == "STRING":
            return FixedDecimal.from_string(str(value), precision, scale)
        if source in {"FIXED_BIN", "FIXED_BINARY"}:
            return FixedDecimal.from_int(int(value), precision, scale)
        if source in {"FLOAT", "FLOAT_BINARY"}:
            return FixedDecimal.from_float(float(value), precision, scale)
        if source == "FLOAT_DECIMAL":
            return FixedDecimal.from_decimal(Decimal(value), precision, scale)
        if source == "ZONED":
            return ZonedDecimalCodec.decode(str(value), precision, scale)
        if source == "PACKED":
            return PackedDecimalCodec.decode(value, precision, scale)
        raise ValueError(f"Unknown decimal conversion source: {source}")


def to_decimal(value: Any) -> Decimal:
    if isinstance(value, FixedDecimal):
        return value.decimal()
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return Decimal(int(value))
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, (ComplexValue, complex)):
        raise TypeError("Cannot convert complex value to Decimal without REAL/IMAG/ABS")
    if isinstance(value, StringValue):
        return Decimal(value.text())
    return Decimal(str(value))


def to_python_float(value: Any) -> float:
    if isinstance(value, FixedDecimal):
        return value.float()
    return float(to_decimal(value))


class CalculationBuiltinRuntime:
    def ABS(self, value: Any) -> Any:
        if isinstance(value, (ComplexValue, complex)):
            return ComplexRuntime().abs(value)
        if isinstance(value, FixedDecimal):
            return FixedDecimal(abs(value.scaled), value.precision, value.scale)
        return abs(value)

    def SIGN(self, value: Any) -> int:
        decimal = to_decimal(value)
        return -1 if decimal < 0 else 1 if decimal > 0 else 0

    def MIN(self, *args: Any) -> Any:
        return min(args, key=to_decimal)

    def MAX(self, *args: Any) -> Any:
        return max(args, key=to_decimal)

    def MOD(self, left: Any, right: Any) -> int:
        return int(to_decimal(left)) % int(to_decimal(right))

    def TRUNC(self, value: Any, scale: Any = 0) -> FixedDecimal:
        places = int(to_decimal(scale))
        quantum = Decimal(1) / (Decimal(10) ** places)
        return FixedDecimal.from_decimal(to_decimal(value).quantize(quantum, rounding=ROUND_DOWN), 31, places)

    def ROUND(self, value: Any, scale: Any = 0) -> FixedDecimal:
        places = int(to_decimal(scale))
        quantum = Decimal(1) / (Decimal(10) ** places)
        return FixedDecimal.from_decimal(to_decimal(value).quantize(quantum, rounding=ROUND_HALF_UP), 31, places)

    def CEIL(self, value: Any) -> int:
        return int(to_decimal(value).to_integral_value(rounding=ROUND_CEILING))

    def FLOOR(self, value: Any) -> int:
        return int(to_decimal(value).to_integral_value(rounding=ROUND_FLOOR))

    def COMPLEX(self, real: Any = 0, imag: Any = 0) -> ComplexValue:
        return ComplexRuntime().value(real, imag)

    def SQRT(self, value: Any) -> Any:
        if isinstance(value, (ComplexValue, complex)):
            return ComplexRuntime().sqrt(value)
        return math.sqrt(to_python_float(value))

    def EXP(self, value: Any) -> Any:
        if isinstance(value, (ComplexValue, complex)):
            return ComplexRuntime().exp(value)
        return math.exp(to_python_float(value))

    def LOG(self, value: Any) -> Any:
        if isinstance(value, (ComplexValue, complex)):
            return ComplexRuntime().log(value)
        return math.log(to_python_float(value))

    def SIN(self, value: Any) -> Any:
        if isinstance(value, (ComplexValue, complex)):
            return ComplexRuntime().sin(value)
        return math.sin(to_python_float(value))

    def COS(self, value: Any) -> Any:
        if isinstance(value, (ComplexValue, complex)):
            return ComplexRuntime().cos(value)
        return math.cos(to_python_float(value))

    def TAN(self, value: Any) -> Any:
        if isinstance(value, (ComplexValue, complex)):
            return ComplexRuntime().tan(value)
        return math.tan(to_python_float(value))

    def REAL(self, value: Any) -> Any:
        return ComplexRuntime().real(value)

    def IMAG(self, value: Any) -> Any:
        return ComplexRuntime().imag(value)

    def CONJG(self, value: Any) -> ComplexValue:
        return ComplexRuntime().conjg(value)

    def LENGTH(self, value: Any) -> int:
        if isinstance(value, StringValue):
            return value.length
        if isinstance(value, bytes):
            return len(value)
        return len(str(value))

    def SUBSTR(self, value: Any, start: Any, count: Any | None = None) -> str:
        text = value.text() if isinstance(value, StringValue) else str(value)
        index = max(int(to_decimal(start)) - 1, 0)
        return text[index:] if count is None else text[index : index + max(int(to_decimal(count)), 0)]

    def INDEX(self, value: Any, needle: Any) -> int:
        text = value.text() if isinstance(value, StringValue) else str(value)
        search = needle.text() if isinstance(needle, StringValue) else str(needle)
        index = text.find(search)
        return 0 if index < 0 else index + 1

    def FIXED_DECIMAL(self, value: Any, precision: Any, scale: Any = 0) -> FixedDecimal:
        return DecimalRuntime.fixed_decimal(value, int(to_decimal(precision)), int(to_decimal(scale)))

    def DECIMAL_TO_PACKED(self, value: Any, precision: Any, scale: Any = 0) -> bytes:
        fixed = DecimalRuntime.fixed_decimal(value, int(to_decimal(precision)), int(to_decimal(scale)))
        return PackedDecimalCodec.encode(fixed)

    def DECIMAL_FROM_PACKED(self, value: Any, precision: Any, scale: Any = 0) -> FixedDecimal:
        return PackedDecimalCodec.decode(value, int(to_decimal(precision)), int(to_decimal(scale)))

    def DECIMAL_TO_ZONED(self, value: Any, precision: Any, scale: Any = 0) -> str:
        fixed = DecimalRuntime.fixed_decimal(value, int(to_decimal(precision)), int(to_decimal(scale)))
        return ZonedDecimalCodec.encode(fixed)

    def DECIMAL_FROM_ZONED(self, value: Any, precision: Any, scale: Any = 0) -> FixedDecimal:
        return ZonedDecimalCodec.decode(str(value), int(to_decimal(precision)), int(to_decimal(scale)))


__all__ = [
    "ComplexRuntime",
    "ComplexValue",
    "CalculationBuiltinRuntime",
    "DecimalRuntime",
    "FixedDecimal",
    "PackedDecimalCodec",
    "ZonedDecimalCodec",
    "to_decimal",
    "to_python_float",
]
