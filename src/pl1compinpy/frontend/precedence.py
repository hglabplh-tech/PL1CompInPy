from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .lexer import Token, TokenType


class Associativity(str, Enum):
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True)
class OperatorInfo:
    symbol: str
    precedence: int
    associativity: Associativity = Associativity.LEFT
    category: str = "binary"


# Higher numbers bind tighter. The order follows the PL/I shape used by IBM
# Enterprise PL/I references: exponentiation, prefix signs/not, multiply/divide,
# add/subtract, concatenation, comparison, logical AND, logical OR.
BINARY_OPERATORS: dict[str, OperatorInfo] = {
    "|": OperatorInfo("|", 1, category="logical-or"),
    "OR": OperatorInfo("OR", 1, category="logical-or"),
    "&": OperatorInfo("&", 2, category="logical-and"),
    "AND": OperatorInfo("AND", 2, category="logical-and"),
    "=": OperatorInfo("=", 3, category="comparison"),
    "^=": OperatorInfo("^=", 3, category="comparison"),
    "¬=": OperatorInfo("¬=", 3, category="comparison"),
    "~=": OperatorInfo("~=", 3, category="comparison"),
    "<>": OperatorInfo("<>", 3, category="comparison"),
    "<": OperatorInfo("<", 3, category="comparison"),
    "<=": OperatorInfo("<=", 3, category="comparison"),
    ">": OperatorInfo(">", 3, category="comparison"),
    ">=": OperatorInfo(">=", 3, category="comparison"),
    "=>": OperatorInfo("=>", 3, category="comparison"),
    "||": OperatorInfo("||", 4, category="concatenation"),
    "+": OperatorInfo("+", 5, category="additive"),
    "-": OperatorInfo("-", 5, category="additive"),
    "*": OperatorInfo("*", 6, category="multiplicative"),
    "/": OperatorInfo("/", 6, category="multiplicative"),
    "**": OperatorInfo("**", 8, Associativity.RIGHT, "power"),
}

PREFIX_OPERATORS: dict[str, OperatorInfo] = {
    "+": OperatorInfo("+", 7, Associativity.RIGHT, "prefix"),
    "-": OperatorInfo("-", 7, Associativity.RIGHT, "prefix"),
    "^": OperatorInfo("^", 7, Associativity.RIGHT, "prefix"),
    "NOT": OperatorInfo("NOT", 7, Associativity.RIGHT, "prefix"),
}

_TOKEN_OPERATORS = {
    TokenType.OR: "|",
    TokenType.AND: "&",
    TokenType.EQ: "=",
    TokenType.ASSIGN: "=",
    TokenType.NE: "^=",
    TokenType.LT: "<",
    TokenType.LE: "<=",
    TokenType.GT: ">",
    TokenType.GE: ">=",
    TokenType.CONCAT: "||",
    TokenType.PLUS: "+",
    TokenType.MINUS: "-",
    TokenType.STAR: "*",
    TokenType.SLASH: "/",
    TokenType.POWER: "**",
}


def binary_operator(token: Token) -> OperatorInfo | None:
    if token.type in _TOKEN_OPERATORS:
        symbol = token.lexeme if token.type in {TokenType.NE, TokenType.GE} else _TOKEN_OPERATORS[token.type]
        return BINARY_OPERATORS.get(symbol) or BINARY_OPERATORS.get(_TOKEN_OPERATORS[token.type])
    if token.keyword and token.keyword.word in {"AND", "OR"}:
        return BINARY_OPERATORS[token.keyword.word]
    return None


def prefix_operator(token: Token) -> OperatorInfo | None:
    if token.type in {TokenType.PLUS, TokenType.MINUS, TokenType.NOT}:
        return PREFIX_OPERATORS[token.lexeme]
    if token.keyword and token.keyword.word == "NOT":
        return PREFIX_OPERATORS["NOT"]
    return None


def operator_precedence_table() -> list[OperatorInfo]:
    seen: dict[tuple[str, str], OperatorInfo] = {}
    for info in list(BINARY_OPERATORS.values()) + list(PREFIX_OPERATORS.values()):
        seen[(info.symbol, info.category)] = info
    return sorted(seen.values(), key=lambda item: (item.precedence, item.symbol))


__all__ = [
    "Associativity",
    "BINARY_OPERATORS",
    "OperatorInfo",
    "PREFIX_OPERATORS",
    "binary_operator",
    "operator_precedence_table",
    "prefix_operator",
]
