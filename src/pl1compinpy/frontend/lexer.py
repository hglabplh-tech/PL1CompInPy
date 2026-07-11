from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .keywords import KeywordInfo, keyword_info


class TokenType(str, Enum):
    COMMENT = "COMMENT"
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    STRING = "STRING"
    ASSIGN = "="
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    POWER = "**"
    CONCAT = "||"
    AND = "&"
    OR = "|"
    NOT = "^"
    EQ = "="
    NE = "^="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    ARROW = "->"
    LPAREN = "("
    RPAREN = ")"
    COMMA = ","
    COLON = ":"
    PERCENT = "%"
    DOT = "."
    SEMICOLON = ";"
    EOF = "EOF"


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int
    keyword: KeywordInfo | None = None

    @property
    def is_keyword(self) -> bool:
        return self.keyword is not None


class LexerError(ValueError):
    pass


class Lexer:
    def __init__(self, source: str, preserve_comments: bool = False) -> None:
        self.source = source
        self.preserve_comments = preserve_comments
        self.index = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while not self._at_end:
            char = self._peek()
            if char in " \t\r":
                self._advance()
            elif char == "\n":
                self._advance_line()
            elif char == "/" and self._peek_next() == "*":
                comment = self._comment()
                if self.preserve_comments:
                    tokens.append(comment)
            elif char.isalpha() or char == "_":
                tokens.append(self._identifier())
            elif char.isdigit():
                tokens.append(self._number())
            elif char in "'\"":
                tokens.append(self._string())
            else:
                tokens.append(self._symbol())

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens

    @property
    def _at_end(self) -> bool:
        return self.index >= len(self.source)

    def _peek(self) -> str:
        return self.source[self.index]

    def _peek_next(self) -> str:
        next_index = self.index + 1
        if next_index >= len(self.source):
            return "\0"
        return self.source[next_index]

    def _advance(self) -> str:
        char = self.source[self.index]
        self.index += 1
        self.column += 1
        return char

    def _advance_line(self) -> None:
        self.index += 1
        self.line += 1
        self.column = 1

    def _identifier(self) -> Token:
        start = self.index
        line = self.line
        column = self.column
        while not self._at_end and (self._peek().isalnum() or self._peek() in "_$#@"):
            self._advance()
        lexeme = self.source[start:self.index]
        return Token(TokenType.IDENTIFIER, lexeme, line, column, keyword_info(lexeme))

    def _number(self) -> Token:
        start = self.index
        line = self.line
        column = self.column
        while not self._at_end and self._peek().isdigit():
            self._advance()
        if not self._at_end and self._peek() == ".":
            self._advance()
            while not self._at_end and self._peek().isdigit():
                self._advance()
        return Token(TokenType.NUMBER, self.source[start:self.index], line, column)

    def _string(self) -> Token:
        quote = self._advance()
        start = self.index
        line = self.line
        column = self.column - 1
        while not self._at_end and self._peek() != quote:
            if self._peek() == "\n":
                raise LexerError(f"Unterminated string at {line}:{column}")
            self._advance()
        if self._at_end:
            raise LexerError(f"Unterminated string at {line}:{column}")
        value = self.source[start:self.index]
        self._advance()
        return Token(TokenType.STRING, value, line, column)

    def _comment(self) -> Token:
        line = self.line
        column = self.column
        start = self.index
        self._advance()
        self._advance()
        content_start = self.index
        while not self._at_end:
            if self._peek() == "*" and self._peek_next() == "/":
                text = self.source[content_start:self.index]
                self._advance()
                self._advance()
                return Token(TokenType.COMMENT, text, line, column)
            if self._peek() == "\n":
                self._advance_line()
            else:
                self._advance()
        raw = self.source[start:self.index]
        raise LexerError(f"Unterminated comment at {line}:{column}: {raw!r}")

    def _symbol(self) -> Token:
        line = self.line
        column = self.column
        char = self._advance()
        two_char_symbols = {
            "**": TokenType.POWER,
            "||": TokenType.CONCAT,
            "^=": TokenType.NE,
            "¬=": TokenType.NE,
            "~=": TokenType.NE,
            "<>": TokenType.NE,
            "<=": TokenType.LE,
            ">=": TokenType.GE,
            "=>": TokenType.GE,
            "->": TokenType.ARROW,
        }
        pair = char + self._peek() if not self._at_end else char
        if pair in two_char_symbols:
            self._advance()
            return Token(two_char_symbols[pair], pair, line, column)

        symbols = {
            "=": TokenType.ASSIGN,
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "&": TokenType.AND,
            "|": TokenType.OR,
            "^": TokenType.NOT,
            "<": TokenType.LT,
            ">": TokenType.GT,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            ",": TokenType.COMMA,
            ":": TokenType.COLON,
            "%": TokenType.PERCENT,
            ".": TokenType.DOT,
            ";": TokenType.SEMICOLON,
        }
        if char not in symbols:
            raise LexerError(f"Unexpected character {char!r} at {line}:{column}")
        return Token(symbols[char], char, line, column)
