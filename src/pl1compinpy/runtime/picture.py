from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


class PictureRuntimeError(ValueError):
    pass


@dataclass(frozen=True)
class PictureSpec:
    pattern: str

    @property
    def scale(self) -> int:
        upper = self.pattern.upper()
        if "V" in upper:
            return self._digit_count(upper.split("V", 1)[1])
        if "." in upper:
            return self._digit_count(upper.split(".", 1)[1])
        return 0

    @property
    def integer_digits(self) -> int:
        upper = self.pattern.upper()
        integer = upper.split("V", 1)[0].split(".", 1)[0]
        return self._digit_count(integer)

    @property
    def storage_width(self) -> int:
        return len(self.pattern.replace("V", "").replace("v", ""))

    def format(self, value: int | float | Decimal | str) -> str:
        decimal = Decimal(str(value)).quantize(Decimal(1).scaleb(-self.scale), rounding=ROUND_HALF_UP)
        if decimal < 0:
            raise PictureRuntimeError("Signed PICTURE output is not implemented yet")
        digits = f"{decimal:.{self.scale}f}".replace(".", "")
        needed = self.integer_digits + self.scale
        if len(digits) > needed:
            raise PictureRuntimeError(f"Value {value!r} does not fit PICTURE {self.pattern!r}")
        digits = digits.rjust(needed, "0")
        digit_index = 0
        first_required = self._first_required_integer_index()
        suppressing = True
        output: list[str] = []

        for pattern_index, char in enumerate(self.pattern):
            upper = char.upper()
            if upper == "V":
                continue
            if upper in {"9", "Z"}:
                digit = digits[digit_index]
                digit_index += 1
                if upper == "Z" and suppressing and digit == "0" and pattern_index < first_required:
                    output.append(" ")
                else:
                    output.append(digit)
                    if digit != "0" or upper == "9":
                        suppressing = False
            else:
                output.append(char)
                if char == ".":
                    suppressing = False
        return "".join(output)

    def parse(self, text: str) -> Decimal:
        cleaned = "".join(char for char in text if char.isdigit())
        needed = self.integer_digits + self.scale
        if len(cleaned) > needed:
            raise PictureRuntimeError(f"Picture text {text!r} does not fit PICTURE {self.pattern!r}")
        cleaned = cleaned.rjust(needed, "0")
        if self.scale:
            integer = cleaned[:-self.scale] or "0"
            fraction = cleaned[-self.scale :]
            return Decimal(f"{integer}.{fraction}")
        return Decimal(cleaned or "0")

    def _first_required_integer_index(self) -> int:
        for index, char in enumerate(self.pattern):
            if char == "." or char.upper() == "V":
                break
            if char.upper() == "9":
                return index
        return len(self.pattern)

    def _digit_count(self, text: str) -> int:
        return sum(1 for char in text if char.upper() in {"9", "Z"})


class PictureRuntime:
    def compile(self, pattern: str) -> PictureSpec:
        if not pattern:
            raise PictureRuntimeError("PICTURE pattern cannot be empty")
        if not any(char.upper() in {"9", "Z"} for char in pattern):
            raise PictureRuntimeError(f"PICTURE pattern has no digit positions: {pattern!r}")
        return PictureSpec(pattern)

    def fixed_to_picture(self, value: int | Decimal, pattern: str) -> str:
        return self.compile(pattern).format(value)

    def float_to_picture(self, value: float, pattern: str) -> str:
        return self.compile(pattern).format(value)

    def picture_to_fixed(self, text: str, pattern: str) -> Decimal:
        return self.compile(pattern).parse(text)

    def picture_to_float(self, text: str, pattern: str) -> float:
        return float(self.picture_to_fixed(text, pattern))


__all__ = ["PictureRuntime", "PictureRuntimeError", "PictureSpec"]
