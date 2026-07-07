from __future__ import annotations

from ..core.ast import (
    Assignment,
    BinaryExpression,
    Call,
    Declaration,
    FieldReference,
    FunctionCall,
    GotoStatement,
    Identifier,
    LabelledStatement,
    NumberLiteral,
    PreprocessorStatement,
    Procedure,
    Program,
    PointerReference,
    RawStatement,
    StructureField,
    main_procedure_entry,
    main_procedure_name,
    procedure_entry_name,
)
from .runtime_link import runtime_linkage


class JVMBytecodeEmitter:
    def emit(self, program: Program) -> str:
        linkage = runtime_linkage("jvm-bytecode")
        runtime_type = linkage.managed_type or "pl1compinpy/runtime/PL1Runtime"
        lines = [
            f"; runtime-link: {', '.join(linkage.managed_references)}",
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
                name = procedure_entry_name(statement, "anonymous") or "anonymous"
                lines.extend(self._procedure(name, procedure))
                lines.append("")
        main_entry = main_procedure_entry(program)
        if main_entry:
            main, procedure = main_entry
            descriptor = "(" + ("I" * len(procedure.parameters)) + ")" + self._return_descriptor(procedure)
            call_lines = ["    iconst_0" for _ in procedure.parameters]
            if procedure.parameters:
                call_lines.insert(0, "    ; PL/I MAIN command-line parameter placeholder")
            call_lines.append("    invokestatic PL1Program/" + main + descriptor)
            if procedure.returns:
                call_lines.append("    pop")
            lines.extend(
                [
                    ".method public static main([Ljava/lang/String;)V",
                    f"    invokestatic {runtime_type}/{linkage.startup_symbol}()V",
                    *call_lines,
                    f"    invokestatic {runtime_type}/{linkage.shutdown_symbol}()V",
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
                for var_name in _declaration_storage_names(statement):
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
            elif isinstance(statement, LabelledStatement):
                lines.append(f"{statement.label}:")
                nested = Procedure(procedure.name, procedure.parameters, procedure.options, [statement.statement], procedure.returns, procedure.recursive)
                nested_lines = self._procedure_body(nested, locals_map, next_local)
                lines.extend(nested_lines[0])
                next_local = nested_lines[1]
            elif isinstance(statement, GotoStatement):
                lines.append(f"    goto {statement.label}")
            elif isinstance(statement, PreprocessorStatement):
                lines.append(f"    ; preprocessor {statement.command} {' '.join(statement.arguments)}".rstrip())
        if procedure.returns:
            lines.extend(["    iconst_0", "    ireturn"])
        else:
            lines.append("    return")
        lines.append(".end method")
        return lines

    def _procedure_body(self, procedure: Procedure, locals_map: dict[str, int], next_local: int) -> tuple[list[str], int]:
        lines: list[str] = []
        for statement in procedure.body:
            if isinstance(statement, Declaration):
                for var_name in _declaration_storage_names(statement):
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
            elif isinstance(statement, LabelledStatement):
                lines.append(f"{statement.label}:")
                nested_lines, next_local = self._procedure_body(
                    Procedure(procedure.name, procedure.parameters, procedure.options, [statement.statement], procedure.returns, procedure.recursive),
                    locals_map,
                    next_local,
                )
                lines.extend(nested_lines)
            elif isinstance(statement, GotoStatement):
                lines.append(f"    goto {statement.label}")
            elif isinstance(statement, PreprocessorStatement):
                lines.append(f"    ; preprocessor {statement.command} {' '.join(statement.arguments)}".rstrip())
        return lines, next_local

    def _expression(self, expression: object, locals_map: dict[str, int]) -> list[str]:
        if isinstance(expression, NumberLiteral):
            return self._int_constant(int(float(expression.value)))
        if isinstance(expression, Identifier):
            return [f"    iload {locals_map.setdefault(expression.name, len(locals_map))}"]
        if isinstance(expression, FieldReference):
            return [f"    iload {locals_map.setdefault(expression.name, len(locals_map))}"]
        if isinstance(expression, PointerReference):
            return [f"    iload {locals_map.setdefault(expression.name, len(locals_map))}"]
        if isinstance(expression, FunctionCall):
            return ["    iconst_0", f"    ; function expression {expression.name} lowered as zero"]
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
        return main_procedure_name(program)


def emit_jvm_bytecode(program: Program) -> str:
    return JVMBytecodeEmitter().emit(program)


def _declaration_storage_names(declaration: Declaration) -> list[str]:
    if declaration.structures:
        names: list[str] = []
        for field in declaration.structures.values():
            names.extend(_structure_leaf_names(field, [field.name]))
        return names
    return declaration.names


def _structure_leaf_names(field: StructureField, prefix: list[str]) -> list[str]:
    if not field.children:
        return [".".join(prefix)]
    names: list[str] = []
    for child in field.children:
        names.extend(_structure_leaf_names(child, [*prefix, child.name]))
    return names
