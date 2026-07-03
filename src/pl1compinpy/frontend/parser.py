from __future__ import annotations

from ..ast import (
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
    Statement,
    StringLiteral,
)
from .lexer import Token, TokenType


class ParserError(ValueError):
    pass


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Program:
        statements: list[Statement] = []
        while not self._check(TokenType.EOF):
            if self._match_semicolon():
                continue
            statements.append(self._statement())
        return Program(statements)

    def _statement(self) -> Statement:
        if self._looks_like_label():
            label = self._advance().lexeme
            self._consume(TokenType.COLON, "Expected ':' after label")
            return LabelledStatement(label, self._statement())

        if self._check(TokenType.IDENTIFIER) and self._check_next(TokenType.ASSIGN):
            statement = self._assignment()
            self._consume(TokenType.SEMICOLON, "Expected ';' after assignment")
            return statement
        if self._match_keyword("DECLARE", "DCL"):
            return self._declaration()
        if self._match_keyword("PROCEDURE", "PROC"):
            return self._procedure(None)
        if self._check(TokenType.IDENTIFIER) and self._check_next_keyword("PROCEDURE", "PROC"):
            name = self._advance().lexeme
            self._advance()
            return self._procedure(name)
        if self._match_keyword("DO"):
            return self._do_group()
        if self._match_keyword("IF"):
            return self._if_statement()
        if self._match_keyword("CALL"):
            statement = self._call_statement()
            self._consume(TokenType.SEMICOLON, "Expected ';' after CALL statement")
            return statement
        if self._starts_raw_statement():
            return self._raw_statement()

        statement = self._assignment()
        self._consume(TokenType.SEMICOLON, "Expected ';' after assignment")
        return statement

    def _declaration(self) -> Declaration:
        tokens = self._collect_until_semicolon()
        names: list[str] = []
        attributes: list[str] = []
        before_attribute = True

        for token in tokens:
            if token.type == TokenType.COMMA:
                before_attribute = True
                continue
            if token.type != TokenType.IDENTIFIER:
                before_attribute = False
                continue
            if before_attribute and not token.is_keyword:
                names.append(token.lexeme)
            else:
                attributes.append(token.lexeme)
                before_attribute = False

        return Declaration(names, attributes)

    def _procedure(self, name: str | None) -> Procedure:
        parameters: list[str] = []
        options: list[str] = []

        if self._match(TokenType.LPAREN):
            parameters = self._identifier_list_until(TokenType.RPAREN)
        if self._match_keyword("OPTIONS"):
            self._consume(TokenType.LPAREN, "Expected '(' after OPTIONS")
            options = self._identifier_list_until(TokenType.RPAREN)
        self._consume(TokenType.SEMICOLON, "Expected ';' after PROCEDURE header")

        body: list[Statement] = []
        while not self._check(TokenType.EOF) and not self._match_keyword("END"):
            if self._match_semicolon():
                continue
            body.append(self._statement())

        if not self._previous_keyword("END"):
            raise self._error(self._peek(), "Expected END for PROCEDURE")
        if self._check(TokenType.IDENTIFIER):
            self._advance()
        self._consume(TokenType.SEMICOLON, "Expected ';' after END")
        return Procedure(name, parameters, options, body)

    def _do_group(self) -> DoGroup:
        control = [token.lexeme for token in self._collect_until_semicolon()]
        body: list[Statement] = []

        while not self._check(TokenType.EOF) and not self._match_keyword("END"):
            if self._match_semicolon():
                continue
            body.append(self._statement())

        if not self._previous_keyword("END"):
            raise self._error(self._peek(), "Expected END for DO group")
        self._consume(TokenType.SEMICOLON, "Expected ';' after END")
        return DoGroup(control, body)

    def _if_statement(self) -> IfStatement:
        condition_tokens = self._collect_until_keyword("THEN")
        condition = self._expression_from_tokens(condition_tokens)
        then_branch = self._statement()
        else_branch = self._statement() if self._match_keyword("ELSE") else None
        return IfStatement(condition, then_branch, else_branch)

    def _call_statement(self) -> Call:
        name = self._consume_identifier("Expected procedure name after CALL")
        arguments: list[Expression] = []
        mode = "reference"
        if self._match(TokenType.LPAREN):
            if not self._check(TokenType.RPAREN):
                arguments.append(self._expression())
                while self._match(TokenType.COMMA):
                    arguments.append(self._expression())
            self._consume(TokenType.RPAREN, "Expected ')' after CALL arguments")
        if self._match_keyword("BY"):
            if self._match_keyword("NAME"):
                mode = "name"
            elif self._match_keyword("REFERENCE", "REF"):
                mode = "reference"
            else:
                raise self._error(self._peek(), "Expected NAME or REFERENCE after BY")
        return Call(name.lexeme, arguments, mode)

    def _assignment(self) -> Assignment:
        target = self._consume_identifier("Expected assignment target")
        self._consume(TokenType.ASSIGN, "Expected '=' after assignment target")
        return Assignment(target.lexeme, self._expression())

    def _raw_statement(self) -> RawStatement:
        keyword = self._advance().lexeme
        tokens = [token.lexeme for token in self._collect_until_semicolon()]
        return RawStatement(keyword, tokens)

    def _expression(self) -> Expression:
        return self._comparison()

    def _comparison(self) -> Expression:
        expression = self._term()
        while self._match(TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE):
            operator = self._previous().lexeme
            right = self._term()
            expression = BinaryExpression(expression, operator, right)
        return expression

    def _term(self) -> Expression:
        expression = self._factor()
        while self._match(TokenType.PLUS, TokenType.MINUS, TokenType.CONCAT, TokenType.OR):
            operator = self._previous().lexeme
            right = self._factor()
            expression = BinaryExpression(expression, operator, right)
        return expression

    def _factor(self) -> Expression:
        expression = self._power()
        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.AND):
            operator = self._previous().lexeme
            right = self._power()
            expression = BinaryExpression(expression, operator, right)
        return expression

    def _power(self) -> Expression:
        expression = self._primary()
        if self._match(TokenType.POWER):
            operator = self._previous().lexeme
            right = self._power()
            return BinaryExpression(expression, operator, right)
        return expression

    def _primary(self) -> Expression:
        if self._match(TokenType.NUMBER):
            return NumberLiteral(self._previous().lexeme)
        if self._match(TokenType.STRING):
            return StringLiteral(self._previous().lexeme)
        if self._match(TokenType.IDENTIFIER):
            return Identifier(self._previous().lexeme)
        if self._match(TokenType.LPAREN):
            expression = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return expression
        raise self._error(self._peek(), "Expected expression")

    def _expression_from_tokens(self, tokens: list[Token]) -> Expression:
        parser = Parser(tokens + [Token(TokenType.EOF, "", self._peek().line, self._peek().column)])
        return parser._expression()

    def _identifier_list_until(self, end: TokenType) -> list[str]:
        values: list[str] = []
        while not self._check(TokenType.EOF) and not self._check(end):
            if self._check(TokenType.IDENTIFIER):
                values.append(self._advance().lexeme)
            else:
                self._advance()
        self._consume(end, f"Expected {end.value!r}")
        return values

    def _collect_until_semicolon(self) -> list[Token]:
        tokens: list[Token] = []
        depth = 0
        while not self._check(TokenType.EOF):
            if depth == 0 and self._check(TokenType.SEMICOLON):
                self._advance()
                return tokens
            if self._check(TokenType.LPAREN):
                depth += 1
            elif self._check(TokenType.RPAREN):
                depth -= 1
            tokens.append(self._advance())
        raise self._error(self._peek(), "Expected ';'")

    def _collect_until_keyword(self, *keywords: str) -> list[Token]:
        tokens: list[Token] = []
        depth = 0
        while not self._check(TokenType.EOF):
            if depth == 0 and self._check_keyword(*keywords):
                self._advance()
                return tokens
            if self._check(TokenType.LPAREN):
                depth += 1
            elif self._check(TokenType.RPAREN):
                depth -= 1
            tokens.append(self._advance())
        raise self._error(self._peek(), f"Expected one of: {', '.join(keywords)}")

    def _looks_like_label(self) -> bool:
        return self._check(TokenType.IDENTIFIER) and self._check_next(TokenType.COLON)

    def _starts_raw_statement(self) -> bool:
        return self._check_keyword(
            "ALLOCATE",
            "ALLOC",
            "BEGIN",
            "CLOSE",
            "DEFAULT",
            "DFT",
            "DELETE",
            "ENTRY",
            "FORMAT",
            "FREE",
            "GET",
            "GO",
            "GOTO",
            "LOCATE",
            "ON",
            "OPEN",
            "PUT",
            "READ",
            "RETURN",
            "REVERT",
            "REWRITE",
            "SELECT",
            "SIGNAL",
            "STOP",
            "WRITE",
        )

    def _match(self, *types: TokenType) -> bool:
        if not any(self._check(token_type) for token_type in types):
            return False
        self._advance()
        return True

    def _match_semicolon(self) -> bool:
        return self._match(TokenType.SEMICOLON)

    def _match_keyword(self, *keywords: str) -> bool:
        if not self._check_keyword(*keywords):
            return False
        self._advance()
        return True

    def _previous_keyword(self, keyword: str) -> bool:
        return self._previous().lexeme.upper() == keyword

    def _check(self, token_type: TokenType) -> bool:
        return self._peek().type == token_type

    def _check_next(self, token_type: TokenType) -> bool:
        if self.current + 1 >= len(self.tokens):
            return False
        return self.tokens[self.current + 1].type == token_type

    def _check_keyword(self, *keywords: str) -> bool:
        token = self._peek()
        return token.type == TokenType.IDENTIFIER and token.lexeme.upper() in keywords

    def _check_next_keyword(self, *keywords: str) -> bool:
        if self.current + 1 >= len(self.tokens):
            return False
        token = self.tokens[self.current + 1]
        return token.type == TokenType.IDENTIFIER and token.lexeme.upper() in keywords

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise self._error(self._peek(), message)

    def _consume_identifier(self, message: str) -> Token:
        if self._check(TokenType.IDENTIFIER):
            return self._advance()
        raise self._error(self._peek(), message)

    def _advance(self) -> Token:
        if not self._check(TokenType.EOF):
            self.current += 1
        return self._previous()

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _error(self, token: Token, message: str) -> ParserError:
        return ParserError(f"{message} at {token.line}:{token.column}")
