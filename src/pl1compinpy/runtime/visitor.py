from __future__ import annotations

from typing import Any

from ..core.ast import (
    Assignment,
    AstVisitor,
    Call,
    Declaration,
    DoGroup,
    Expression,
    GotoStatement,
    IfStatement,
    LabelledStatement,
    PreprocessorStatement,
    Program,
    RawStatement,
    SelectStatement,
    Statement,
)
from .calculation import CalculationEngine, PL1Type, PL1Value
from .decimal import CalculationBuiltinRuntime, FixedDecimal
from .function_table import RUNTIME_FUNCTION_TABLE, FunctionTable, FunctionTableError, build_dynamic_function_table, declare_program_builtins


class RuntimeVisitorError(ValueError):
    pass


class RuntimeExecutionVisitor(AstVisitor):
    def __init__(self, variables: dict[str, PL1Value | object] | None = None, max_loop: int = 10000) -> None:
        self.variables: dict[str, PL1Value | object] = variables if variables is not None else {}
        self.max_loop = max_loop
        self.output: list[object] = []
        self.function_table: FunctionTable = RUNTIME_FUNCTION_TABLE
        self.builtins = CalculationBuiltinRuntime()

    def visit_Program(self, node: Program) -> Any:
        self.function_table = RUNTIME_FUNCTION_TABLE.merge(build_dynamic_function_table(node))
        declare_program_builtins(node, self.function_table)
        result = None
        for statement in node.statements:
            result = self.visit(statement)
        return result

    def visit_Declaration(self, node: Declaration) -> None:
        if any(attribute.upper() == "BUILTIN" for attribute in node.attributes):
            return None
        attributes = {attribute.upper() for attribute in node.attributes}
        for name in node.names:
            if name in node.pointer_names or "POINTER" in attributes or "PTR" in attributes:
                self.variables[name] = None
            elif "FLOAT" in attributes:
                self.variables[name] = PL1Value(0.0, PL1Type.FLOAT)
            elif "CHARACTER" in attributes or "CHAR" in attributes:
                self.variables[name] = PL1Value("", PL1Type.CHARACTER)
            elif "BIT" in attributes:
                self.variables[name] = PL1Value(False, PL1Type.BIT)
            elif "DECIMAL" in attributes or "DEC" in attributes:
                self.variables[name] = PL1Value(FixedDecimal.from_int(0, 15, 0), PL1Type.FIXED_DEC)
            else:
                self.variables[name] = PL1Value(0, PL1Type.FIXED_BIN)
        return None

    def visit_Assignment(self, node: Assignment) -> PL1Value:
        value = self.evaluate(node.expression)
        self.variables[node.target] = value
        return value

    def visit_Call(self, node: Call) -> Any:
        try:
            self.function_table.validate_call(node)
        except FunctionTableError as exc:
            raise RuntimeVisitorError(str(exc)) from exc
        arguments = [self._plain(self.evaluate(argument)) for argument in node.arguments]
        return self._dispatch_call(node.name, arguments)

    def visit_DoGroup(self, node: DoGroup) -> Any:
        result = None
        if node.while_condition is None and node.until_condition is None:
            return self._execute_block(node.body)
        count = 0
        while True:
            if node.while_condition is not None and not self.evaluate(node.while_condition).truthy:
                break
            result = self._execute_block(node.body)
            if node.until_condition is not None and self.evaluate(node.until_condition).truthy:
                break
            count += 1
            if count > self.max_loop:
                raise RuntimeVisitorError("Loop exceeded runtime visitor max_loop")
        return result

    def visit_IfStatement(self, node: IfStatement) -> Any:
        if self.evaluate(node.condition).truthy:
            return self.visit(node.then_branch)
        return self.visit(node.else_branch) if node.else_branch else None

    def visit_SelectStatement(self, node: SelectStatement) -> Any:
        selector = self.evaluate(node.expression) if node.expression else None
        for branch in node.when_branches:
            if selector is not None:
                for expression in branch.expressions:
                    if self._plain(selector) == self._plain(self.evaluate(expression)):
                        return self.visit(branch.statement)
            elif any(self.evaluate(expression).truthy for expression in branch.expressions):
                return self.visit(branch.statement)
        return self.visit(node.otherwise) if node.otherwise else None

    def visit_LabelledStatement(self, node: LabelledStatement) -> Any:
        return self.visit(node.statement)

    def visit_GotoStatement(self, node: GotoStatement) -> Any:
        raise RuntimeVisitorError(f"GOTO is parsed for backends but not executed by the direct runtime visitor: {node.label}")

    def visit_PreprocessorStatement(self, node: PreprocessorStatement) -> Any:
        return None

    def visit_RawStatement(self, node: RawStatement) -> Any:
        return None

    def evaluate(self, expression: Expression) -> PL1Value:
        return CalculationEngine(self.variables).evaluate(expression)

    def _execute_block(self, statements: list[Statement]) -> Any:
        result = None
        for statement in statements:
            result = self.visit(statement)
        return result

    def _dispatch_call(self, name: str, arguments: list[object]) -> Any:
        key = name.upper()
        if key in {"DISPLAY", "PRINT", "PUT"}:
            self.output.extend(arguments)
            return None
        handlers = {
            "ABS": self.builtins.ABS,
            "SIGN": self.builtins.SIGN,
            "MIN": self.builtins.MIN,
            "MAX": self.builtins.MAX,
            "MOD": self.builtins.MOD,
            "TRUNC": self.builtins.TRUNC,
            "ROUND": self.builtins.ROUND,
            "CEIL": self.builtins.CEIL,
            "FLOOR": self.builtins.FLOOR,
            "SQRT": self.builtins.SQRT,
            "EXP": self.builtins.EXP,
            "LOG": self.builtins.LOG,
            "SIN": self.builtins.SIN,
            "COS": self.builtins.COS,
            "TAN": self.builtins.TAN,
            "REAL": self.builtins.REAL,
            "IMAG": self.builtins.IMAG,
            "CONJG": self.builtins.CONJG,
            "LENGTH": self.builtins.LENGTH,
            "SUBSTR": self.builtins.SUBSTR,
            "INDEX": self.builtins.INDEX,
            "FIXED_DECIMAL": self.builtins.FIXED_DECIMAL,
            "DECIMAL_TO_PACKED": self.builtins.DECIMAL_TO_PACKED,
            "DECIMAL_FROM_PACKED": self.builtins.DECIMAL_FROM_PACKED,
            "DECIMAL_TO_ZONED": self.builtins.DECIMAL_TO_ZONED,
            "DECIMAL_FROM_ZONED": self.builtins.DECIMAL_FROM_ZONED,
        }
        try:
            return handlers[key](*arguments)
        except KeyError as exc:
            raise RuntimeVisitorError(f"No runtime visitor handler for CALL {name}") from exc

    def _plain(self, value: PL1Value | object) -> object:
        return value.value if isinstance(value, PL1Value) else value

__all__ = ["RuntimeExecutionVisitor", "RuntimeVisitorError"]
