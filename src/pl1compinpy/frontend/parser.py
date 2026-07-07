from __future__ import annotations

from ..core.ast import (
    Assignment,
    BinaryExpression,
    Call,
    Declaration,
    DoGroup,
    Expression,
    FieldReference,
    GenericAlternative,
    GotoStatement,
    Identifier,
    IfStatement,
    IOStatement,
    LabelledStatement,
    NumberLiteral,
    PreprocessorStatement,
    Procedure,
    Program,
    RawStatement,
    SelectStatement,
    Statement,
    StringLiteral,
    StructureField,
    UnaryExpression,
    WhenBranch,
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
        if self._match(TokenType.PERCENT):
            return self._preprocessor_statement()

        if self._looks_like_label():
            label = self._advance().lexeme
            self._consume(TokenType.COLON, "Expected ':' after label")
            return LabelledStatement(label, self._statement())

        if self._looks_like_assignment_target():
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
        if self._check_keyword("OPEN", "CLOSE", "READ", "WRITE"):
            return self._io_statement()
        if self._match_keyword("SELECT"):
            return self._select_statement()
        if self._match_keyword("GOTO"):
            return self._goto_statement()
        if self._match_keyword("GO"):
            if not self._match_keyword("TO"):
                raise self._error(self._peek(), "Expected TO after GO")
            return self._goto_statement()
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
        dimensions: dict[str, list[int]] = {}
        file_options: dict[str, str] = {}
        generic_options: dict[str, list[GenericAlternative]] = {}
        picture_options: dict[str, str] = {}
        based_options: dict[str, str | None] = {}
        pointer_names: list[str] = []
        structures: dict[str, StructureField] = {}
        before_attribute = True
        index = 0
        depth = 0

        while index < len(tokens):
            token = tokens[index]
            if token.type == TokenType.LPAREN:
                depth += 1
                index += 1
                continue
            if token.type == TokenType.RPAREN:
                depth = max(depth - 1, 0)
                index += 1
                continue
            if token.type == TokenType.COMMA:
                if depth == 0:
                    before_attribute = True
                index += 1
                continue
            if depth == 0 and token.type == TokenType.NUMBER and index + 1 < len(tokens):
                level = int(float(token.lexeme))
                if level == 1 and tokens[index + 1].type == TokenType.IDENTIFIER:
                    names.append(tokens[index + 1].lexeme)
                    before_attribute = False
                    index += 2
                    continue
                if level > 1:
                    before_attribute = False
                    index += 2 if tokens[index + 1].type == TokenType.IDENTIFIER else 1
                    continue
            if token.type != TokenType.IDENTIFIER:
                before_attribute = False
                index += 1
                continue
            if depth == 0 and before_attribute and not token.is_keyword:
                names.append(token.lexeme)
                if index + 1 < len(tokens) and tokens[index + 1].type == TokenType.LPAREN:
                    dims, index = self._dimensions_from_tokens(tokens, index + 2)
                    dimensions[token.lexeme] = dims
                    continue
            elif depth == 0:
                attributes.append(token.lexeme)
                before_attribute = False
            index += 1

        file_options = self._file_options_from_tokens(tokens)
        if not names:
            names = self._builtin_names_from_tokens(tokens)
        generic_options = self._generic_options_from_tokens(names, tokens)
        picture_options = self._picture_options_from_tokens(names, tokens)
        based_options = self._based_options_from_tokens(names, tokens)
        pointer_names = self._pointer_names_from_tokens(names, tokens)
        structures = self._structures_from_tokens(tokens)
        return Declaration(
            names,
            attributes,
            dimensions,
            file_options,
            generic_options,
            picture_options,
            based_options,
            pointer_names,
            structures,
        )

    def _dimensions_from_tokens(self, tokens: list[Token], index: int) -> tuple[list[int], int]:
        dimensions: list[int] = []
        while index < len(tokens) and tokens[index].type != TokenType.RPAREN:
            if tokens[index].type == TokenType.NUMBER:
                dimensions.append(int(float(tokens[index].lexeme)))
            index += 1
        return dimensions, index + 1

    def _file_options_from_tokens(self, tokens: list[Token]) -> dict[str, str]:
        options: dict[str, str] = {}
        index = 0
        while index < len(tokens):
            token = tokens[index]
            upper = token.lexeme.upper()
            if upper in {"INPUT", "OUTPUT", "UPDATE"}:
                options["mode"] = upper
            elif upper in {"RECORD", "STREAM"}:
                options["organization"] = upper
            elif upper in {"TEXT", "BINARY"}:
                options["format"] = upper
            elif upper in {"RECFM", "LRECL", "PATH", "VSAM", "KEYOFFSET", "KEYLENGTH", "RECORDLENGTH"} and index + 2 < len(tokens):
                if tokens[index + 1].type == TokenType.LPAREN:
                    value = tokens[index + 2].lexeme
                    options[upper.lower()] = value.upper() if upper != "PATH" else value
            index += 1
        return options

    def _generic_options_from_tokens(self, names: list[str], tokens: list[Token]) -> dict[str, list[GenericAlternative]]:
        if not names:
            return {}
        alternatives: list[GenericAlternative] = []
        index = 0
        while index < len(tokens):
            if tokens[index].lexeme.upper() == "WHEN" and index >= 1 and index + 1 < len(tokens):
                procedure = tokens[index - 1].lexeme
                if tokens[index + 1].type == TokenType.LPAREN:
                    parameter_types: list[str] = []
                    index += 2
                    while index < len(tokens) and tokens[index].type != TokenType.RPAREN:
                        if tokens[index].type == TokenType.IDENTIFIER and tokens[index].lexeme.upper() not in {"WHEN"}:
                            parameter_types.append(tokens[index].lexeme.upper())
                        index += 1
                    alternatives.append(GenericAlternative(procedure, parameter_types))
            index += 1
        return {name: alternatives for name in names if alternatives}

    def _picture_options_from_tokens(self, names: list[str], tokens: list[Token]) -> dict[str, str]:
        if not names:
            return {}
        index = 0
        while index < len(tokens):
            upper = tokens[index].lexeme.upper()
            if upper in {"PICTURE", "PIC"}:
                pattern, _ = self._picture_pattern_from_tokens(tokens, index + 1)
                return {name: pattern for name in names}
            index += 1
        return {}

    def _picture_pattern_from_tokens(self, tokens: list[Token], index: int) -> tuple[str, int]:
        if index < len(tokens) and tokens[index].type == TokenType.STRING:
            return tokens[index].lexeme, index + 1
        if index < len(tokens) and tokens[index].type == TokenType.LPAREN:
            index += 1
            parts: list[str] = []
            depth = 1
            while index < len(tokens) and depth:
                token = tokens[index]
                if token.type == TokenType.LPAREN:
                    depth += 1
                    parts.append(token.lexeme)
                elif token.type == TokenType.RPAREN:
                    depth -= 1
                    if depth:
                        parts.append(token.lexeme)
                else:
                    parts.append(token.lexeme)
                index += 1
            return "".join(parts), index

        parts: list[str] = []
        while index < len(tokens) and tokens[index].type not in {TokenType.COMMA, TokenType.SEMICOLON}:
            if tokens[index].type in {TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.DOT, TokenType.PLUS, TokenType.MINUS}:
                parts.append(tokens[index].lexeme)
                index += 1
                continue
            break
        return "".join(parts), index

    def _based_options_from_tokens(self, names: list[str], tokens: list[Token]) -> dict[str, str | None]:
        if not names:
            return {}
        index = 0
        while index < len(tokens):
            if tokens[index].lexeme.upper() == "BASED":
                pointer: str | None = None
                if index + 2 < len(tokens) and tokens[index + 1].type == TokenType.LPAREN:
                    pointer = tokens[index + 2].lexeme
                return {name: pointer for name in names}
            index += 1
        return {}

    def _pointer_names_from_tokens(self, names: list[str], tokens: list[Token]) -> list[str]:
        if not names:
            return []
        if any(token.lexeme.upper() == "BUILTIN" for token in tokens):
            return []
        if any(token.lexeme.upper() in {"POINTER", "PTR"} for token in tokens):
            return names.copy()
        return []

    def _builtin_names_from_tokens(self, tokens: list[Token]) -> list[str]:
        if not any(token.lexeme.upper() == "BUILTIN" for token in tokens):
            return []
        for token in tokens:
            if token.type == TokenType.IDENTIFIER and token.lexeme.upper() != "BUILTIN":
                return [token.lexeme]
        return []

    def _structures_from_tokens(self, tokens: list[Token]) -> dict[str, StructureField]:
        segments = self._declaration_segments(tokens)
        roots: dict[str, StructureField] = {}
        stack: list[StructureField] = []
        for segment in segments:
            if len(segment) < 2 or segment[0].type != TokenType.NUMBER or segment[1].type != TokenType.IDENTIFIER:
                continue
            level = int(float(segment[0].lexeme))
            name_index = 1
            name = segment[name_index].lexeme
            dimensions: list[int] = []
            attr_start = name_index + 1
            if attr_start < len(segment) and segment[attr_start].type == TokenType.LPAREN:
                dimensions, attr_start = self._dimensions_from_tokens(segment, attr_start + 1)
            attributes = [token.lexeme for token in segment[attr_start:] if token.type not in {TokenType.LPAREN, TokenType.RPAREN, TokenType.COMMA}]
            field = StructureField(level, name, attributes, dimensions, [])
            while stack and stack[-1].level >= level:
                stack.pop()
            if stack:
                stack[-1].children.append(field)
            else:
                roots[name] = field
            stack.append(field)
        return {name: field for name, field in roots.items() if field.children}

    def _declaration_segments(self, tokens: list[Token]) -> list[list[Token]]:
        segments: list[list[Token]] = []
        current: list[Token] = []
        depth = 0
        for token in tokens:
            if token.type == TokenType.LPAREN:
                depth += 1
            elif token.type == TokenType.RPAREN:
                depth = max(depth - 1, 0)
            if token.type == TokenType.COMMA and depth == 0:
                if current:
                    segments.append(current)
                    current = []
                continue
            current.append(token)
        if current:
            segments.append(current)
        return segments

    def _procedure(self, name: str | None) -> Procedure:
        parameters: list[str] = []
        options: list[str] = []
        returns: str | None = None
        recursive = False

        if self._match(TokenType.LPAREN):
            parameters = self._identifier_list_until(TokenType.RPAREN)
        while not self._check(TokenType.SEMICOLON):
            if self._match_keyword("OPTIONS"):
                self._consume(TokenType.LPAREN, "Expected '(' after OPTIONS")
                options = self._identifier_list_until(TokenType.RPAREN)
            elif self._match_keyword("RETURNS"):
                self._consume(TokenType.LPAREN, "Expected '(' after RETURNS")
                returns = self._type_text(self._collect_until_balanced_rparen())
            elif self._match_keyword("RECURSIVE"):
                recursive = True
            else:
                raise self._error(self._peek(), "Expected PROCEDURE option")
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
        return Procedure(name, parameters, options, body, returns, recursive)

    def _collect_until_balanced_rparen(self) -> list[Token]:
        tokens: list[Token] = []
        depth = 0
        while not self._check(TokenType.EOF):
            if self._check(TokenType.LPAREN):
                depth += 1
                tokens.append(self._advance())
            elif self._check(TokenType.RPAREN):
                if depth == 0:
                    self._advance()
                    return tokens
                depth -= 1
                tokens.append(self._advance())
            else:
                tokens.append(self._advance())
        raise self._error(self._peek(), "Expected ')'")

    def _do_group(self) -> DoGroup:
        control_tokens = self._collect_until_semicolon()
        control = [token.lexeme for token in control_tokens]
        while_condition = self._do_control_condition(control_tokens, "WHILE")
        until_condition = self._do_control_condition(control_tokens, "UNTIL")
        body: list[Statement] = []

        while not self._check(TokenType.EOF) and not self._match_keyword("END"):
            if self._match_keyword("UNTIL"):
                until_condition = self._expression_from_tokens(self._collect_until_semicolon())
                continue
            if self._match_semicolon():
                continue
            body.append(self._statement())

        if not self._previous_keyword("END"):
            raise self._error(self._peek(), "Expected END for DO group")
        self._consume(TokenType.SEMICOLON, "Expected ';' after END")
        return DoGroup(control, body, while_condition, until_condition)

    def _do_control_condition(self, tokens: list[Token], keyword: str) -> Expression | None:
        for index, token in enumerate(tokens):
            if token.lexeme.upper() == keyword:
                condition_tokens = tokens[index + 1 :]
                if condition_tokens and condition_tokens[0].type == TokenType.LPAREN and condition_tokens[-1].type == TokenType.RPAREN:
                    condition_tokens = condition_tokens[1:-1]
                return self._expression_from_tokens(condition_tokens) if condition_tokens else None
        return None

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

    def _io_statement(self) -> IOStatement:
        operation = self._advance().lexeme.upper()
        tokens = self._collect_until_semicolon()
        file_name = self._option_value(tokens, "FILE")
        target = self._option_value(tokens, "INTO")
        source_tokens = self._option_tokens(tokens, "FROM")
        source = self._expression_from_tokens(source_tokens) if source_tokens else None
        options = self._io_options_from_tokens(tokens)
        return IOStatement(operation, file_name, target, source, options)

    def _select_statement(self) -> SelectStatement:
        header_tokens = self._collect_until_semicolon()
        expression_tokens = header_tokens
        if expression_tokens and expression_tokens[0].type == TokenType.LPAREN and expression_tokens[-1].type == TokenType.RPAREN:
            expression_tokens = expression_tokens[1:-1]
        expression = self._expression_from_tokens(expression_tokens) if expression_tokens else None
        branches: list[WhenBranch] = []
        otherwise: Statement | None = None

        while not self._check(TokenType.EOF) and not self._match_keyword("END"):
            if self._match_semicolon():
                continue
            if self._match_keyword("WHEN"):
                self._consume(TokenType.LPAREN, "Expected '(' after WHEN")
                expressions = self._expressions_until_rparen()
                branches.append(WhenBranch(expressions, self._statement()))
                continue
            if self._match_keyword("OTHERWISE", "OTHER"):
                otherwise = self._statement()
                continue
            raise self._error(self._peek(), "Expected WHEN, OTHERWISE, or END in SELECT")

        if not self._previous_keyword("END"):
            raise self._error(self._peek(), "Expected END for SELECT")
        self._consume(TokenType.SEMICOLON, "Expected ';' after SELECT END")
        return SelectStatement(expression, branches, otherwise)

    def _assignment(self) -> Assignment:
        target = self._assignment_target()
        self._consume(TokenType.ASSIGN, "Expected '=' after assignment target")
        return Assignment(target, self._expression())

    def _raw_statement(self) -> RawStatement:
        keyword = self._advance().lexeme
        tokens = [token.lexeme for token in self._collect_until_semicolon()]
        return RawStatement(keyword, tokens)

    def _goto_statement(self) -> GotoStatement:
        label = self._consume_identifier("Expected label after GOTO")
        self._consume(TokenType.SEMICOLON, "Expected ';' after GOTO statement")
        return GotoStatement(label.lexeme)

    def _preprocessor_statement(self) -> PreprocessorStatement:
        tokens = self._collect_until_semicolon()
        if not tokens:
            return PreprocessorStatement("NULL", [], "%")
        lexemes = [token.lexeme for token in tokens]
        command_tokens = [token for token in tokens if token.type != TokenType.PERCENT]
        if not command_tokens:
            return PreprocessorStatement("NULL", lexemes, "% " + " ".join(lexemes))
        command = command_tokens[0].lexeme.upper()
        arguments = lexemes[1:]
        if command == "GO" and len(command_tokens) > 1 and command_tokens[1].lexeme.upper() == "TO":
            command = "GOTO"
            arguments = lexemes[2:]
        return PreprocessorStatement(command, arguments, "% " + " ".join(lexemes))

    def _expression(self) -> Expression:
        return self._logical_or()

    def _logical_or(self) -> Expression:
        expression = self._logical_and()
        while self._match(TokenType.OR):
            operator = self._previous().lexeme
            right = self._logical_and()
            expression = BinaryExpression(expression, operator, right)
        return expression

    def _logical_and(self) -> Expression:
        expression = self._comparison()
        while self._match(TokenType.AND):
            operator = self._previous().lexeme
            right = self._comparison()
            expression = BinaryExpression(expression, operator, right)
        return expression

    def _comparison(self) -> Expression:
        expression = self._concatenation()
        while self._match(TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE):
            operator = self._previous().lexeme
            right = self._concatenation()
            expression = BinaryExpression(expression, operator, right)
        return expression

    def _concatenation(self) -> Expression:
        expression = self._term()
        while self._match(TokenType.CONCAT):
            operator = self._previous().lexeme
            right = self._term()
            expression = BinaryExpression(expression, operator, right)
        return expression

    def _term(self) -> Expression:
        expression = self._factor()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous().lexeme
            right = self._factor()
            expression = BinaryExpression(expression, operator, right)
        return expression

    def _factor(self) -> Expression:
        expression = self._unary()
        while self._match(TokenType.STAR, TokenType.SLASH):
            operator = self._previous().lexeme
            right = self._unary()
            expression = BinaryExpression(expression, operator, right)
        return expression

    def _unary(self) -> Expression:
        if self._match(TokenType.PLUS, TokenType.MINUS, TokenType.NOT):
            operator = self._previous().lexeme
            return UnaryExpression(operator, self._unary())
        if self._match_keyword("NOT"):
            return UnaryExpression("NOT", self._unary())
        return self._power()

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
            base = self._previous().lexeme
            fields: list[str] = []
            while self._match(TokenType.DOT):
                fields.append(self._consume_identifier("Expected field name after '.'").lexeme)
            if fields:
                return FieldReference(base, fields)
            return Identifier(base)
        if self._match(TokenType.LPAREN):
            expression = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return expression
        raise self._error(self._peek(), "Expected expression")

    def _expression_from_tokens(self, tokens: list[Token]) -> Expression:
        parser = Parser(tokens + [Token(TokenType.EOF, "", self._peek().line, self._peek().column)])
        return parser._expression()

    def _expressions_until_rparen(self) -> list[Expression]:
        expressions: list[Expression] = []
        if self._check(TokenType.RPAREN):
            self._advance()
            return expressions
        expressions.append(self._expression())
        while self._match(TokenType.COMMA):
            expressions.append(self._expression())
        self._consume(TokenType.RPAREN, "Expected ')' after expression list")
        return expressions

    def _option_value(self, tokens: list[Token], keyword: str) -> str | None:
        option_tokens = self._option_tokens(tokens, keyword)
        if not option_tokens:
            return None
        return option_tokens[0].lexeme

    def _option_tokens(self, tokens: list[Token], keyword: str) -> list[Token]:
        index = 0
        while index < len(tokens):
            if tokens[index].lexeme.upper() == keyword:
                if index + 1 < len(tokens) and tokens[index + 1].type == TokenType.LPAREN:
                    depth = 1
                    inner: list[Token] = []
                    index += 2
                    while index < len(tokens) and depth:
                        if tokens[index].type == TokenType.LPAREN:
                            depth += 1
                            inner.append(tokens[index])
                        elif tokens[index].type == TokenType.RPAREN:
                            depth -= 1
                            if depth:
                                inner.append(tokens[index])
                        else:
                            inner.append(tokens[index])
                        index += 1
                    return inner
                if index + 1 < len(tokens):
                    return [tokens[index + 1]]
            index += 1
        return []

    def _io_options_from_tokens(self, tokens: list[Token]) -> dict[str, Expression]:
        options: dict[str, Expression] = {}
        for keyword in ("KEY", "RRN", "RBA", "LENGTH", "COUNT"):
            option_tokens = self._option_tokens(tokens, keyword)
            if option_tokens:
                options[keyword.lower()] = self._expression_from_tokens(option_tokens)
        return options

    def _identifier_list_until(self, end: TokenType) -> list[str]:
        values: list[str] = []
        while not self._check(TokenType.EOF) and not self._check(end):
            if self._check(TokenType.IDENTIFIER):
                values.append(self._advance().lexeme)
            else:
                self._advance()
        self._consume(end, f"Expected {end.value!r}")
        return values

    def _type_text(self, tokens: list[Token]) -> str:
        return " ".join(token.lexeme for token in tokens if token.type not in {TokenType.LPAREN, TokenType.RPAREN})

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

    def _looks_like_assignment_target(self) -> bool:
        if not self._check(TokenType.IDENTIFIER):
            return False
        index = self.current + 1
        while index + 1 < len(self.tokens) and self.tokens[index].type == TokenType.DOT and self.tokens[index + 1].type == TokenType.IDENTIFIER:
            index += 2
        return index < len(self.tokens) and self.tokens[index].type == TokenType.ASSIGN

    def _assignment_target(self) -> str:
        parts = [self._consume_identifier("Expected assignment target").lexeme]
        while self._match(TokenType.DOT):
            parts.append(self._consume_identifier("Expected field name after '.'").lexeme)
        return ".".join(parts)

    def _starts_raw_statement(self) -> bool:
        return self._check_keyword(
            "ALLOCATE",
            "ALLOC",
            "BEGIN",
            "BUILTIN",
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
            "PUT",
            "RETURN",
            "REVERT",
            "REWRITE",
            "SIGNAL",
            "STOP",
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
