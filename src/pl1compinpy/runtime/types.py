from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass(frozen=True)
class PliType:
    kind: str
    precision: tuple[int, int | None] | None = None
    length: int | None = None
    varying: bool = False
    picture: str | None = None
    signed: bool = True
    attributes: tuple[str, ...] = ()

    def canonical(self) -> str:
        suffix = ""
        if self.precision:
            values = [str(self.precision[0])]
            if self.precision[1] is not None:
                values.append(str(self.precision[1]))
            suffix = "(" + ",".join(values) + ")"
        elif self.length is not None:
            suffix = f"({self.length})"
        elif self.picture:
            suffix = f"({self.picture})"
        varying = " VARYING" if self.varying else ""
        return f"{self.kind}{suffix}{varying}".strip()

    @property
    def arithmetic(self) -> bool:
        return self.kind in {"FIXED BINARY", "FIXED DECIMAL", "FLOAT BINARY", "FLOAT DECIMAL"}

    @property
    def locator(self) -> bool:
        return self.kind in {"POINTER", "OFFSET", "ENTRY"}


@dataclass(frozen=True)
class TypeMapping:
    python: str
    jvm: str
    dotnet: str
    x86_64: str
    arm64_apple: str
    notes: str = ""


TYPE_MAPPINGS: dict[str, TypeMapping] = {
    "BIT": TypeMapping("bool | int", "boolean / BitSet", "bool / BitArray", "bitfield / byte", "bitfield / byte", "BIT(n) needs packed bit storage when n > 1."),
    "CHARACTER": TypeMapping("str or two-byte-length payload", "String / byte[]", "string / byte[]", "char* + length", "char* + length", "CHARACTER VARYING maps naturally to the existing two-byte length string runtime."),
    "FIXED BINARY": TypeMapping("int", "int/long/BigInteger", "short/int/long/BigInteger", "int16/int32/int64", "wN/xN integer register", "Precision decides storage width and overflow checks."),
    "FIXED DECIMAL": TypeMapping("decimal.Decimal / FixedDecimal", "BigDecimal", "decimal / runtime", "packed/zoned decimal runtime", "packed/zoned decimal runtime", "Decimal arithmetic stays in runtime helpers, not CPU integer registers."),
    "FLOAT BINARY": TypeMapping("float", "float/double", "float/double", "xmm float/double", "sN/dN FP register", "BINARY FLOAT follows target floating-point support."),
    "FLOAT DECIMAL": TypeMapping("decimal.Decimal", "BigDecimal", "decimal", "decimal FP runtime", "decimal FP runtime", "Decimal float needs runtime or target decimal FP support."),
    "PICTURE": TypeMapping("str + decimal codec", "String + BigDecimal codec", "string + decimal codec", "zoned/packed buffer", "zoned/packed buffer", "PICTURE is both storage/display format and conversion policy."),
    "POINTER": TypeMapping("PointerValue", "handle/reference", "IntPtr / managed handle", "uint64 pointer", "uint64 pointer", "Safe targets should use runtime handles rather than raw host addresses."),
    "OFFSET": TypeMapping("int offset", "int offset", "int offset", "relative offset", "relative offset", "OFFSET is relative to an AREA or locator base."),
    "ENTRY": TypeMapping("Callable / descriptor", "FunctionalInterface", "delegate", "function pointer + descriptor", "function pointer + descriptor", "ENTRY carries parameter and return descriptors for call checking."),
    "STRUCTURE": TypeMapping("StructureValue", "class/record", "struct/class", "flattened storage", "flattened storage", "Level-numbered members should keep offsets for debugger lookup."),
}


class PliTypeParser:
    def parse(self, text: str | list[str] | tuple[str, ...] | None) -> PliType | None:
        if text is None:
            return None
        source = " ".join(text) if isinstance(text, (list, tuple)) else str(text)
        normalized = self._normalize(source)
        if not normalized:
            return None
        if "ENTRY" in normalized:
            return PliType("ENTRY", attributes=self._attributes(normalized))
        if "POINTER" in normalized or re.search(r"\bPTR\b", normalized):
            return PliType("POINTER", attributes=self._attributes(normalized))
        if "OFFSET" in normalized:
            return PliType("OFFSET", attributes=self._attributes(normalized))
        if "PICTURE" in normalized or re.search(r"\bPIC\b", normalized):
            return PliType("PICTURE", picture=self._picture(source), attributes=self._attributes(normalized))
        if "CHARACTER" in normalized or re.search(r"\bCHAR\b", normalized):
            return PliType("CHARACTER", length=self._first_int_paren(source), varying=("VARYING" in normalized or "VAR" in normalized), attributes=self._attributes(normalized))
        if "BIT" in normalized:
            return PliType("BIT", length=self._first_int_paren(source), attributes=self._attributes(normalized))
        if "FIXED" in normalized and ("DECIMAL" in normalized or re.search(r"\bDEC\b", normalized)):
            return PliType("FIXED DECIMAL", precision=self._precision(source), attributes=self._attributes(normalized))
        if "FIXED" in normalized or "BINARY" in normalized or re.search(r"\bBIN\b", normalized):
            return PliType("FIXED BINARY", precision=self._precision(source), attributes=self._attributes(normalized))
        if "FLOAT" in normalized and ("DECIMAL" in normalized or re.search(r"\bDEC\b", normalized)):
            return PliType("FLOAT DECIMAL", precision=self._precision(source), attributes=self._attributes(normalized))
        if "FLOAT" in normalized:
            return PliType("FLOAT BINARY", precision=self._precision(source), attributes=self._attributes(normalized))
        if "FILE" in normalized:
            return PliType("FILE", attributes=self._attributes(normalized))
        return None

    def mapping_for(self, pli_type: PliType | str | None) -> TypeMapping | None:
        if pli_type is None:
            return None
        key = pli_type.kind if isinstance(pli_type, PliType) else str(pli_type).upper()
        return TYPE_MAPPINGS.get(key)

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip()).upper()

    def _attributes(self, normalized: str) -> tuple[str, ...]:
        return tuple(part for part in normalized.replace(",", " ").split() if part)

    def _first_int_paren(self, text: str) -> int | None:
        match = re.search(r"\((\d+)\)", text)
        return int(match.group(1)) if match else None

    def _precision(self, text: str) -> tuple[int, int | None] | None:
        match = re.search(r"\((\d+)(?:\s*,\s*(\d+))?\)", text)
        if not match:
            return None
        return int(match.group(1)), int(match.group(2)) if match.group(2) else None

    def _picture(self, text: str) -> str | None:
        match = re.search(r"(?:PICTURE|PIC)\s*'?([^';]+)'?", text, flags=re.IGNORECASE)
        return match.group(1).strip() if match else None


def parse_pli_type(text: str | list[str] | tuple[str, ...] | None) -> PliType | None:
    return PliTypeParser().parse(text)


__all__ = ["PliType", "PliTypeParser", "TYPE_MAPPINGS", "TypeMapping", "parse_pli_type"]
