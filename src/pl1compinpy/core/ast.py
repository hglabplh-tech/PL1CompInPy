from __future__ import annotations

from dataclasses import dataclass, fields, field
from typing import Any


class AstNode:
    def accept(self, visitor: "AstVisitor") -> Any:
        return visitor.visit(self)


class AstVisitor:
    def visit(self, node: AstNode | None) -> Any:
        if node is None:
            return None
        method = getattr(self, f"visit_{node.__class__.__name__}", self.generic_visit)
        return method(node)

    def visit_children(self, node: AstNode) -> list[Any]:
        results: list[Any] = []
        for item in fields(node):
            value = getattr(node, item.name)
            results.extend(self._visit_value(value))
        return results

    def generic_visit(self, node: AstNode) -> Any:
        return self.visit_children(node)

    def _visit_value(self, value: object) -> list[Any]:
        if isinstance(value, AstNode):
            return [self.visit(value)]
        if isinstance(value, list):
            results: list[Any] = []
            for item in value:
                results.extend(self._visit_value(item))
            return results
        if isinstance(value, dict):
            results: list[Any] = []
            for item in value.values():
                results.extend(self._visit_value(item))
            return results
        return []


@dataclass(frozen=True)
class Program(AstNode):
    statements: list["Statement"]


class Statement(AstNode):
    pass


@dataclass(frozen=True)
class Assignment(Statement):
    target: str
    expression: "Expression"


@dataclass(frozen=True)
class Declaration(Statement):
    names: list[str]
    attributes: list[str]
    dimensions: dict[str, list[int]] = field(default_factory=dict)
    file_options: dict[str, str] = field(default_factory=dict)
    generic_options: dict[str, list["GenericAlternative"]] = field(default_factory=dict)
    picture_options: dict[str, str] = field(default_factory=dict)
    based_options: dict[str, str | None] = field(default_factory=dict)
    pointer_names: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GenericAlternative(AstNode):
    procedure: str
    parameter_types: list[str]


@dataclass(frozen=True)
class Call(Statement):
    name: str
    arguments: list["Expression"]
    mode: str = "reference"


@dataclass(frozen=True)
class Procedure(Statement):
    name: str | None
    parameters: list[str]
    options: list[str]
    body: list["Statement"]
    returns: str | None = None
    recursive: bool = False


@dataclass(frozen=True)
class DoGroup(Statement):
    control: list[str]
    body: list["Statement"]
    while_condition: "Expression | None" = None
    until_condition: "Expression | None" = None


@dataclass(frozen=True)
class IfStatement(Statement):
    condition: "Expression"
    then_branch: Statement
    else_branch: Statement | None


@dataclass(frozen=True)
class IOStatement(Statement):
    operation: str
    file_name: str | None = None
    target: str | None = None
    source: "Expression | None" = None
    options: dict[str, "Expression"] = field(default_factory=dict)


@dataclass(frozen=True)
class SelectStatement(Statement):
    expression: "Expression | None"
    when_branches: list["WhenBranch"]
    otherwise: Statement | None = None


@dataclass(frozen=True)
class WhenBranch(AstNode):
    expressions: list["Expression"]
    statement: Statement


@dataclass(frozen=True)
class LabelledStatement(Statement):
    label: str
    statement: Statement


@dataclass(frozen=True)
class GotoStatement(Statement):
    label: str


@dataclass(frozen=True)
class PreprocessorStatement(Statement):
    command: str
    arguments: list[str] = field(default_factory=list)
    raw: str = ""


@dataclass(frozen=True)
class RawStatement(Statement):
    keyword: str
    tokens: list[str]


class Expression(AstNode):
    pass


@dataclass(frozen=True)
class Identifier(Expression):
    name: str


@dataclass(frozen=True)
class NumberLiteral(Expression):
    value: str


@dataclass(frozen=True)
class StringLiteral(Expression):
    value: str


@dataclass(frozen=True)
class BinaryExpression(Expression):
    left: Expression
    operator: str
    right: Expression


@dataclass(frozen=True)
class UnaryExpression(Expression):
    operator: str
    operand: Expression
