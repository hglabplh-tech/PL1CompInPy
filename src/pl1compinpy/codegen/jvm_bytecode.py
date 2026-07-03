from __future__ import annotations

from ..core.ast import Assignment, BinaryExpression, Call, Declaration, Identifier, LabelledStatement, NumberLiteral, Procedure, Program, RawStatement


class JVMBytecodeEmitter:
    def emit(self, program: Program) -> str:
        lines = [
            ".class public PL1Program",
            ".super java/lang/Object",
            "",
            ".method public <init>()V",
            "    aload_0",
            "    invokespecial java/lang/Object/<init>()V",
            "    return",
            ".end method",
            "",
        ]
        for statement in program.statements:
            procedure = statement.statement if isinstance(statement, LabelledStatement) and isinstance(statement.statement, Procedure) else statement
            if isinstance(procedure, Procedure):
                name = procedure.name or (statement.label if isinstance(statement, LabelledStatement) else "anonymous")
                lines.extend(self._procedure(name, procedure))
                lines.append("")
        main = self._main_name(program)
        if main:
            lines.extend(
                [
                    ".method public static main([Ljava/lang/String;)V",
                    "    invokestatic PL1Program/" + main + "()I",
                    "    pop",
                    "    return",
                    ".end method",
                ]
            )
        return "\n".join(lines) + "\n"

    def _procedure(self, name: str, procedure: Procedure) -> list[str]:
        descriptor = "(" + ("I" * len(procedure.parameters)) + ")" + self._return_descriptor(procedure)
        lines = [
            f".method public static {name}{descriptor}",
            "    .limit stack 16",
            "    .limit locals 16",
        ]
        locals_map = {parameter: index for index, parameter in enumerate(procedure.parameters)}
        next_local = len(locals_map)
        for statement in procedure.body:
            if isinstance(statement, Declaration):
                for var_name in statement.names:
                    if var_name not in locals_map:
                        locals_map[var_name] = next_local
                        next_local += 1
                        lines.extend(["    iconst_0", f"    istore {locals_map[var_name]}"])
            elif isinstance(statement, Assignment):
                lines.extend(self._expression(statement.expression, locals_map))
                lines.append(f"    istore {locals_map.setdefault(statement.target, len(locals_map))}")
            elif isinstance(statement, Call):
                lines.extend(self._call(statement, locals_map))
                lines.append("    pop")
            elif isinstance(statement, RawStatement) and statement.keyword.upper() == "RETURN":
                if statement.tokens and statement.tokens[0] in locals_map:
                    lines.append(f"    iload {locals_map[statement.tokens[0]]}")
                elif statement.tokens and statement.tokens[0].isdigit():
                    lines.extend(self._int_constant(int(statement.tokens[0])))
                else:
                    lines.append("    iconst_0")
                lines.append("    ireturn")
        if procedure.returns:
            lines.extend(["    iconst_0", "    ireturn"])
        else:
            lines.append("    return")
        lines.append(".end method")
        return lines

    def _expression(self, expression: object, locals_map: dict[str, int]) -> list[str]:
        if isinstance(expression, NumberLiteral):
            return self._int_constant(int(float(expression.value)))
        if isinstance(expression, Identifier):
            return [f"    iload {locals_map.setdefault(expression.name, len(locals_map))}"]
        if isinstance(expression, BinaryExpression):
            lines = self._expression(expression.left, locals_map)
            lines.extend(self._expression(expression.right, locals_map))
            lines.append(
                {
                    "+": "    iadd",
                    "-": "    isub",
                    "*": "    imul",
                    "/": "    idiv",
                }.get(expression.operator, "    iadd")
            )
            return lines
        return ["    iconst_0"]

    def _call(self, call: Call, locals_map: dict[str, int]) -> list[str]:
        lines: list[str] = []
        for argument in call.arguments:
            lines.extend(self._expression(argument, locals_map))
        descriptor = "(" + ("I" * len(call.arguments)) + ")I"
        lines.append(f"    invokestatic PL1Program/{call.name}{descriptor}")
        return lines

    def _int_constant(self, value: int) -> list[str]:
        if value == -1:
            return ["    iconst_m1"]
        if 0 <= value <= 5:
            return [f"    iconst_{value}"]
        if -128 <= value <= 127:
            return [f"    bipush {value}"]
        return [f"    ldc {value}"]

    def _return_descriptor(self, procedure: Procedure) -> str:
        return "I" if procedure.returns else "V"

    def _main_name(self, program: Program) -> str | None:
        for statement in program.statements:
            procedure = statement.statement if isinstance(statement, LabelledStatement) and isinstance(statement.statement, Procedure) else statement
            if isinstance(procedure, Procedure) and "MAIN" in {option.upper() for option in procedure.options}:
                return procedure.name or (statement.label if isinstance(statement, LabelledStatement) else None)
        return None


def emit_jvm_bytecode(program: Program) -> str:
    return JVMBytecodeEmitter().emit(program)

