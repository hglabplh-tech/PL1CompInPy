from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Program:
    statements: list["Statement"]


class Statement:
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


@dataclass(frozen=True)
class GenericAlternative:
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


@dataclass(frozen=True)
class IfStatement(Statement):
    condition: "Expression"
    then_branch: Statement
    else_branch: Statement | None


@dataclass(frozen=True)
class LabelledStatement(Statement):
    label: str
    statement: Statement


@dataclass(frozen=True)
class RawStatement(Statement):
    keyword: str
    tokens: list[str]


class Expression:
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
