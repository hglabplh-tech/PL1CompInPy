from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, DivisionByZero
from enum import Enum
from typing import Callable

from ..core.ast import BinaryExpression, Expression, FieldReference, FunctionCall, Identifier, NumberLiteral, PointerReference, StringLiteral, UnaryExpression
from .decimal import FixedDecimal


class CalculationError(ValueError):
    pass


class PL1Type(str, Enum):
    FIXED_BIN = "FIXED BIN"
    FIXED_DEC = "FIXED DEC"
    FLOAT = "FLOAT"
    BIT = "BIT"
    CHARACTER = "CHARACTER"


@dataclass(frozen=True)
class PL1Value:
    value: object
    type: PL1Type

    @property
    def truthy(self) -> bool:
        if self.type == PL1Type.BIT:
            return bool(self.value)
        if isinstance(self.value, FixedDecimal):
            return self.value.scaled != 0
        if self.type in {PL1Type.FIXED_BIN, PL1Type.FIXED_DEC, PL1Type.FLOAT}:
            return self.value != 0
        return bool(self.value)


class NumericTower:
    order = {
        PL1Type.BIT: 0,
        PL1Type.FIXED_BIN: 1,
        PL1Type.FIXED_DEC: 2,
        PL1Type.FLOAT: 3,
    }

    def value(self, raw: object, type_name: PL1Type | str | None = None) -> PL1Value:
        if isinstance(raw, PL1Value):
            return raw
        if type_name is not None:
            return self.cast(PL1Value(raw, self._infer(raw)), PL1Type(type_name))
        return PL1Value(raw, self._infer(raw))

    def cast(self, value: PL1Value, target: PL1Type | str) -> PL1Value:
        target = PL1Type(target)
        if target == PL1Type.FIXED_DEC and value.type == PL1Type.FIXED_DEC and not isinstance(value.value, FixedDecimal):
            text = str(value.value)
            return PL1Value(FixedDecimal.from_string(text, max(len(text.replace(".", "").replace("-", "").replace("+", "")), 1), len(text.split(".", 1)[1]) if "." in text else 0), target)
        if value.type == target:
            return value
        if target == PL1Type.CHARACTER:
            if isinstance(value.value, FixedDecimal):
                return PL1Value(value.value.string(), target)
            return PL1Value(str(value.value), target)
        if target == PL1Type.BIT:
            return PL1Value(value.truthy, target)
        if value.type == PL1Type.CHARACTER:
            text = str(value.value).strip()
            if target == PL1Type.FLOAT:
                return PL1Value(float(text), target)
            if target == PL1Type.FIXED_DEC:
                return PL1Value(FixedDecimal.from_string(text, max(len(text.replace(".", "").replace("-", "").replace("+", "")), 1), len(text.split(".", 1)[1]) if "." in text else 0), target)
            if target == PL1Type.FIXED_BIN:
                return PL1Value(int(Decimal(text)), target)
        if target == PL1Type.FLOAT:
            if isinstance(value.value, FixedDecimal):
                return PL1Value(value.value.float(), target)
            return PL1Value(float(value.value), target)
        if target == PL1Type.FIXED_DEC:
            if isinstance(value.value, FixedDecimal):
                return PL1Value(value.value, target)
            text = str(value.value)
            return PL1Value(FixedDecimal.from_string(text, max(len(text.replace(".", "").replace("-", "").replace("+", "")), 1), len(text.split(".", 1)[1]) if "." in text else 0), target)
        if target == PL1Type.FIXED_BIN:
            if isinstance(value.value, FixedDecimal):
                return PL1Value(value.value.int(), target)
            return PL1Value(int(Decimal(str(value.value))), target)
        raise CalculationError(f"Cannot cast {value.type} to {target}")

    def promote(self, left: PL1Value, right: PL1Value) -> tuple[PL1Value, PL1Value, PL1Type]:
        if left.type == PL1Type.CHARACTER or right.type == PL1Type.CHARACTER:
            raise CalculationError("Character values require explicit numeric conversion")
        target = left.type if self.order[left.type] >= self.order[right.type] else right.type
        if target == PL1Type.BIT:
            target = PL1Type.FIXED_BIN
        return self.cast(left, target), self.cast(right, target), target

    def _infer(self, raw: object) -> PL1Type:
        if isinstance(raw, bool):
            return PL1Type.BIT
        if isinstance(raw, int):
            return PL1Type.FIXED_BIN
        if isinstance(raw, (Decimal, FixedDecimal)):
            return PL1Type.FIXED_DEC
        if isinstance(raw, float):
            return PL1Type.FLOAT
        if isinstance(raw, str):
            return PL1Type.CHARACTER
        raise CalculationError(f"Unsupported PL/I value: {raw!r}")


class CalculationEngine:
    def __init__(self, variables: dict[str, PL1Value | object] | None = None, resolver: Callable[[Expression], PL1Value | object] | None = None) -> None:
        self.tower = NumericTower()
        self.variables = variables or {}
        self.resolver = resolver

    def evaluate(self, expression: Expression) -> PL1Value:
        if self.resolver and isinstance(expression, (FieldReference, PointerReference, FunctionCall)):
            return self.tower.value(self.resolver(expression))
        if isinstance(expression, NumberLiteral):
            return self._number(expression.value)
        if isinstance(expression, StringLiteral):
            return PL1Value(expression.value, PL1Type.CHARACTER)
        if isinstance(expression, Identifier):
            if expression.name not in self.variables:
                raise CalculationError(f"Unknown variable: {expression.name}")
            return self.tower.value(self.variables[expression.name])
        if isinstance(expression, FieldReference):
            if self.resolver:
                return self.tower.value(self.resolver(expression))
            if expression.base in self.variables:
                value = self.variables[expression.base]
                if hasattr(value, "get_field"):
                    return self.tower.value(value.get_field(expression.fields))
            dotted = expression.name
            if dotted in self.variables:
                return self.tower.value(self.variables[dotted])
            raise CalculationError(f"Unknown structure field: {dotted}")
        if isinstance(expression, UnaryExpression):
            return self._unary(expression)
        if isinstance(expression, BinaryExpression):
            return self._binary(expression)
        raise CalculationError(f"Unsupported expression: {expression!r}")

    def cast(self, value: PL1Value | object, target: PL1Type | str) -> PL1Value:
        return self.tower.cast(self.tower.value(value), target)

    def _number(self, text: str) -> PL1Value:
        if "." in text:
            return PL1Value(FixedDecimal.from_string(text, len(text.replace(".", "").replace("-", "").replace("+", "")), len(text.split(".", 1)[1])), PL1Type.FIXED_DEC)
        return PL1Value(int(text), PL1Type.FIXED_BIN)

    def _unary(self, expression: UnaryExpression) -> PL1Value:
        value = self.evaluate(expression.operand)
        op = expression.operator.upper()
        if op == "+":
            return value
        if op == "-":
            if value.type == PL1Type.CHARACTER:
                value = self.cast(value, PL1Type.FIXED_DEC)
            return PL1Value(-value.value, value.type)
        if op in {"^", "NOT"}:
            return PL1Value(not value.truthy, PL1Type.BIT)
        raise CalculationError(f"Unsupported unary operator: {expression.operator}")

    def _binary(self, expression: BinaryExpression) -> PL1Value:
        op = expression.operator.upper()
        if op == "||":
            return PL1Value(str(self.evaluate(expression.left).value) + str(self.evaluate(expression.right).value), PL1Type.CHARACTER)
        if op in {"&", "AND", "|", "OR"}:
            left = self.evaluate(expression.left).truthy
            right = self.evaluate(expression.right).truthy
            return PL1Value(left and right if op in {"&", "AND"} else left or right, PL1Type.BIT)
        left = self.evaluate(expression.left)
        right = self.evaluate(expression.right)
        if op in {"=", "^=", "¬=", "~=", "<>", "<", "<=", ">", ">=", "=>"}:
            return PL1Value(self._compare(left, right, op), PL1Type.BIT)
        left, right, target = self.tower.promote(left, right)
        try:
            if op == "+":
                if target == PL1Type.FIXED_DEC and isinstance(left.value, FixedDecimal) and isinstance(right.value, FixedDecimal):
                    return PL1Value(left.value.add(right.value), target)
                return PL1Value(left.value + right.value, target)
            if op == "-":
                if target == PL1Type.FIXED_DEC and isinstance(left.value, FixedDecimal) and isinstance(right.value, FixedDecimal):
                    return PL1Value(left.value.sub(right.value), target)
                return PL1Value(left.value - right.value, target)
            if op == "*":
                if target == PL1Type.FIXED_DEC and isinstance(left.value, FixedDecimal) and isinstance(right.value, FixedDecimal):
                    return PL1Value(left.value.mul(right.value), target)
                return PL1Value(left.value * right.value, target)
            if op == "/":
                if target == PL1Type.FIXED_DEC and isinstance(left.value, FixedDecimal) and isinstance(right.value, FixedDecimal):
                    return PL1Value(left.value.div(right.value), PL1Type.FIXED_DEC)
                return PL1Value(left.value / right.value, PL1Type.FLOAT if target == PL1Type.FLOAT else PL1Type.FIXED_DEC)
            if op == "**":
                return PL1Value(left.value ** right.value, target)
        except DivisionByZero as exc:
            raise CalculationError("Division by zero") from exc
        raise CalculationError(f"Unsupported binary operator: {expression.operator}")

    def _compare(self, left: PL1Value, right: PL1Value, op: str) -> bool:
        if left.type != PL1Type.CHARACTER or right.type != PL1Type.CHARACTER:
            left, right, _ = self.tower.promote(left, right)
        if op == "=":
            return self._comparable(left.value) == self._comparable(right.value)
        if op in {"^=", "¬=", "~=", "<>"}:
            return self._comparable(left.value) != self._comparable(right.value)
        if op == "<":
            return self._comparable(left.value) < self._comparable(right.value)
        if op == "<=":
            return self._comparable(left.value) <= self._comparable(right.value)
        if op == ">":
            return self._comparable(left.value) > self._comparable(right.value)
        if op in {">=", "=>"}:
            return self._comparable(left.value) >= self._comparable(right.value)
        raise CalculationError(f"Unsupported comparison operator: {op}")

    def _comparable(self, value: object) -> object:
        return value.decimal() if isinstance(value, FixedDecimal) else value


__all__ = ["CalculationEngine", "CalculationError", "NumericTower", "PL1Type", "PL1Value"]
