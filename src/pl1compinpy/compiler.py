from __future__ import annotations

from .ast import (
    Assignment,
    BinaryExpression,
    Call,
    Declaration,
    DoGroup,
    Expression,
    Identifier,
    IfStatement,
    LabelledStatement,
    NumberLiteral,
    Procedure,
    Program,
    RawStatement,
    StringLiteral,
)
from .backends import TARGETS, emit_assembly
from .binary_formats import BINARY_FORMATS, emit_binary
from .lexer import Lexer
from .parser import Parser


class Compiler:
    def compile(self, source: str, target: str = "python") -> str:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        if target != "python":
            return emit_assembly(program, target)
        return PythonEmitter().emit(program)


def compile_source(source: str, target: str = "python") -> str:
    return Compiler().compile(source, target)


def available_targets() -> tuple[str, ...]:
    return tuple(TARGETS)


def available_binary_formats() -> tuple[str, ...]:
    return BINARY_FORMATS


def compile_binary(format_name: str, source: str | None = None) -> bytes:
    program = Parser(Lexer(source).tokenize()).parse() if source is not None else None
    return emit_binary(format_name, program)


class PythonEmitter:
    def emit(self, program: Program) -> str:
        lines: list[str] = []
        for statement in program.statements:
            lines.extend(self._statement(statement))
        return "\n".join(lines) + ("\n" if lines else "")

    def _statement(self, statement: object, indent: int = 0) -> list[str]:
        prefix = " " * indent
        if isinstance(statement, Assignment):
            return [f"{prefix}{statement.target} = {self._expression(statement.expression)}"]
        if isinstance(statement, Declaration):
            names = ", ".join(statement.names) if statement.names else "<anonymous>"
            attributes = " ".join(statement.attributes)
            return [f"{prefix}# declare {names} {attributes}".rstrip()]
        if isinstance(statement, Call):
            arguments = ", ".join(self._expression(argument) for argument in statement.arguments)
            return [f"{prefix}{statement.name}({arguments})"]
        if isinstance(statement, Procedure):
            name = statement.name or "anonymous_procedure"
            parameters = ", ".join(statement.parameters)
            lines = [f"{prefix}def {name}({parameters}):"]
            if not statement.body:
                lines.append(f"{prefix}    pass")
            for child in statement.body:
                lines.extend(self._statement(child, indent + 4))
            return lines
        if isinstance(statement, DoGroup):
            lines = [f"{prefix}while True:"]
            if not statement.body:
                lines.append(f"{prefix}    pass")
            for child in statement.body:
                lines.extend(self._statement(child, indent + 4))
            return lines
        if isinstance(statement, IfStatement):
            lines = [f"{prefix}if {self._expression(statement.condition)}:"]
            lines.extend(self._statement(statement.then_branch, indent + 4))
            if statement.else_branch:
                lines.append(f"{prefix}else:")
                lines.extend(self._statement(statement.else_branch, indent + 4))
            return lines
        if isinstance(statement, LabelledStatement):
            lines = [f"{prefix}# label {statement.label}"]
            lines.extend(self._statement(statement.statement, indent))
            return lines
        if isinstance(statement, RawStatement):
            rest = " ".join(statement.tokens)
            return [f"{prefix}# {statement.keyword} {rest}".rstrip()]
        raise TypeError(f"Unsupported statement: {statement!r}")

    def _expression(self, expression: Expression) -> str:
        if isinstance(expression, Identifier):
            return expression.name
        if isinstance(expression, NumberLiteral):
            return expression.value
        if isinstance(expression, StringLiteral):
            return repr(expression.value)
        if isinstance(expression, BinaryExpression):
            left = self._expression(expression.left)
            right = self._expression(expression.right)
            operator = self._operator(expression.operator)
            return f"({left} {operator} {right})"
        raise TypeError(f"Unsupported expression: {expression!r}")

    def _operator(self, operator: str) -> str:
        return {
            "^=": "!=",
            "<>": "!=",
            "||": "+",
            "&": "and",
            "|": "or",
            "**": "**",
        }.get(operator, operator)
