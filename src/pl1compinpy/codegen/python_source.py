from __future__ import annotations

from ..core.ast import (
    Assignment,
    BinaryExpression,
    Call,
    Declaration,
    DoGroup,
    Expression,
    Identifier,
    IfStatement,
    IOStatement,
    LabelledStatement,
    NumberLiteral,
    Procedure,
    Program,
    RawStatement,
    SelectStatement,
    StringLiteral,
)


class PythonSourceEmitter:
    def emit(self, program: Program) -> str:
        lines: list[str] = []
        main_name = self._main_procedure_name(program)
        for statement in program.statements:
            lines.extend(self._statement(statement))
        if main_name:
            lines.extend(["", 'if __name__ == "__main__":', f"    {main_name}()"])
        return "\n".join(lines) + ("\n" if lines else "")

    def _statement(self, statement: object, indent: int = 0) -> list[str]:
        prefix = " " * indent
        if isinstance(statement, Assignment):
            return [f"{prefix}{statement.target} = {self._expression(statement.expression)}"]
        if isinstance(statement, Declaration):
            return [f"{prefix}{name} = {self._declaration_initial_value(statement, name)}" for name in statement.names] or [f"{prefix}pass"]
        if isinstance(statement, Call):
            arguments = ", ".join(self._expression(argument) for argument in statement.arguments)
            return [f"{prefix}{statement.name}({arguments})"]
        if isinstance(statement, Procedure):
            return self._procedure(statement, indent)
        if isinstance(statement, DoGroup):
            if statement.while_condition:
                lines = [f"{prefix}while {self._expression(statement.while_condition)}:"]
            else:
                lines = [f"{prefix}while True:"]
            lines.extend(self._body(statement.body, indent + 4))
            if statement.until_condition:
                lines.extend([f"{prefix}    if {self._expression(statement.until_condition)}:", f"{prefix}        break"])
            return lines
        if isinstance(statement, IfStatement):
            lines = [f"{prefix}if {self._expression(statement.condition)}:"]
            lines.extend(self._statement(statement.then_branch, indent + 4))
            if statement.else_branch:
                lines.append(f"{prefix}else:")
                lines.extend(self._statement(statement.else_branch, indent + 4))
            return lines
        if isinstance(statement, IOStatement):
            return self._io_statement(statement, indent)
        if isinstance(statement, SelectStatement):
            return self._select_statement(statement, indent)
        if isinstance(statement, LabelledStatement):
            if isinstance(statement.statement, Procedure):
                procedure = statement.statement
                return self._procedure(
                    Procedure(
                        procedure.name or statement.label,
                        procedure.parameters,
                        procedure.options,
                        procedure.body,
                        procedure.returns,
                        procedure.recursive,
                    ),
                    indent,
                )
            lines = [f"{prefix}# label {statement.label}"]
            lines.extend(self._statement(statement.statement, indent))
            return lines
        if isinstance(statement, RawStatement):
            if statement.keyword.upper() == "RETURN":
                value = " ".join(statement.tokens)
                return [f"{prefix}return {value}".rstrip()]
            rest = " ".join(statement.tokens)
            return [f"{prefix}# {statement.keyword} {rest}".rstrip()]
        raise TypeError(f"Unsupported statement: {statement!r}")

    def _io_statement(self, statement: IOStatement, indent: int) -> list[str]:
        prefix = " " * indent
        file_name = statement.file_name or "None"
        if statement.operation == "OPEN":
            return [f"{prefix}runtime.open({file_name})"]
        if statement.operation == "CLOSE":
            return [f"{prefix}runtime.close({file_name})"]
        if statement.operation == "READ":
            target = statement.target or "_"
            return [f"{prefix}{target} = runtime.read_record({file_name})"]
        if statement.operation == "WRITE":
            source = self._expression(statement.source) if statement.source else "b''"
            return [f"{prefix}runtime.write_record({file_name}, {source})"]
        return [f"{prefix}# unsupported I/O operation {statement.operation}"]

    def _select_statement(self, statement: SelectStatement, indent: int) -> list[str]:
        prefix = " " * indent
        lines: list[str] = []
        for index, branch in enumerate(statement.when_branches):
            keyword = "if" if index == 0 else "elif"
            condition = self._select_condition(statement, branch.expressions)
            lines.append(f"{prefix}{keyword} {condition}:")
            lines.extend(self._statement(branch.statement, indent + 4))
        if statement.otherwise:
            lines.append(f"{prefix}else:")
            lines.extend(self._statement(statement.otherwise, indent + 4))
        return lines or [f"{prefix}pass"]

    def _select_condition(self, statement: SelectStatement, expressions: list[Expression]) -> str:
        if not expressions:
            return "False"
        if statement.expression:
            subject = self._expression(statement.expression)
            return " or ".join(f"{subject} == {self._expression(expression)}" for expression in expressions)
        return " or ".join(self._expression(expression) for expression in expressions)

    def _procedure(self, procedure: Procedure, indent: int) -> list[str]:
        prefix = " " * indent
        name = procedure.name or "anonymous_procedure"
        parameters = ", ".join(procedure.parameters)
        returns = f"  # returns {procedure.returns}" if procedure.returns else ""
        recursive = "  # recursive" if procedure.recursive else ""
        lines = [f"{prefix}def {name}({parameters}):{returns}{recursive}"]
        lines.extend(self._body(procedure.body, indent + 4))
        return lines

    def _body(self, statements: list[object], indent: int) -> list[str]:
        if not statements:
            return [" " * indent + "pass"]
        lines: list[str] = []
        for child in statements:
            lines.extend(self._statement(child, indent))
        return lines or [" " * indent + "pass"]

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
            return f"({left} {self._operator(expression.operator)} {right})"
        raise TypeError(f"Unsupported expression: {expression!r}")

    def _operator(self, operator: str) -> str:
        return {
            "=": "==",
            "^=": "!=",
            "<>": "!=",
            "||": "+",
            "&": "and",
            "|": "or",
            "**": "**",
        }.get(operator, operator)

    def _declaration_initial_value(self, declaration: Declaration, name: str) -> str:
        attributes = {attribute.upper() for attribute in declaration.attributes}
        if name in declaration.pointer_names or "POINTER" in attributes or "PTR" in attributes:
            return "None"
        if name in declaration.based_options:
            return "None"
        if name in declaration.picture_options:
            return repr("")
        if "FLOAT" in attributes:
            return "0.0"
        return "0"

    def _main_procedure_name(self, program: Program) -> str | None:
        for statement in program.statements:
            procedure = statement.statement if isinstance(statement, LabelledStatement) and isinstance(statement.statement, Procedure) else statement
            if isinstance(procedure, Procedure) and "MAIN" in {option.upper() for option in procedure.options}:
                return procedure.name or (statement.label if isinstance(statement, LabelledStatement) else None)
        return None


def emit_python_source(program: Program) -> str:
    return PythonSourceEmitter().emit(program)
