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
    StringLiteral,
    StructureField,
    main_procedure_entry,
    main_procedure_name,
    procedure_entry_name,
)
from .runtime_link import runtime_linkage


class DotNetILEmitter:
    def emit(self, program: Program) -> str:
        linkage = runtime_linkage("dotnet-il")
        lines = [
            ".assembly extern mscorlib {}",
            ".assembly extern PL1CompInPy.Runtime {}",
            f"// runtime-link: {', '.join(linkage.managed_references)}",
            ".assembly PL1Program {}",
            ".module PL1Program.exe",
            ".corflags 0x00000001",
            "",
            ".class public auto ansi beforefieldinit PL1Program",
            "       extends [mscorlib]System.Object",
            "{",
            "  .method public hidebysig specialname rtspecialname instance void .ctor() cil managed",
            "  {",
            "    .maxstack 8",
            "    ldarg.0",
            "    call instance void [mscorlib]System.Object::.ctor()",
            "    ret",
            "  }",
            "",
        ]
        procedures: list[tuple[str, Procedure]] = []
        top_level = []
        for statement in program.statements:
            procedure = statement.statement if isinstance(statement, LabelledStatement) and isinstance(statement.statement, Procedure) else statement
            if isinstance(procedure, Procedure):
                name = procedure_entry_name(statement, "anonymous") or "anonymous"
                procedures.append((name, procedure))
            else:
                top_level.append(statement)

        for name, procedure in procedures:
            lines.extend(self._procedure(name, procedure))
            lines.append("")

        main_entry = main_procedure_entry(program)
        if main_entry:
            main_name, main_procedure = main_entry
            returns = bool(main_procedure.returns)
            lines.extend(self._entrypoint_call(main_name, main_procedure, returns))
        else:
            lines.extend(self._entrypoint_body(top_level))
        lines.append("}")
        return "\n".join(lines) + "\n"

    def _procedure(self, name: str, procedure: Procedure) -> list[str]:
        return_type = "int32" if procedure.returns else "void"
        parameters = ", ".join("int32 " + parameter for parameter in procedure.parameters)
        lines = [
            f"  .method public hidebysig static {return_type} {name}({parameters}) cil managed",
            "  {",
            "    .maxstack 16",
        ]
        locals_map: dict[str, int] = {}
        local_types: list[str] = []
        prologue: list[str] = []
        for index, parameter in enumerate(procedure.parameters):
            local_index = self._local(parameter, locals_map, local_types)
            prologue.extend([f"    ldarg {index}", f"    stloc {local_index}"])
        body_lines: list[str] = []
        for statement in procedure.body:
            body_lines.extend(self._statement(statement, locals_map, local_types))
        if local_types:
            lines.append("    .locals init (" + ", ".join(local_types) + ")")
        lines.extend(prologue)
        lines.extend(body_lines)
        if procedure.returns:
            lines.extend(["    ldc.i4.0", "    ret"])
        else:
            lines.append("    ret")
        lines.extend(["  }"])
        return lines

    def _entrypoint_call(self, procedure_name: str, procedure: Procedure, returns: bool) -> list[str]:
        lines = [
            "  .method public hidebysig static void Main(string[] args) cil managed",
            "  {",
            "    .entrypoint",
            "    .maxstack 8",
            "    call void [PL1CompInPy.Runtime]PL1CompInPy.Runtime.PL1Runtime::Init()",
        ]
        if procedure.parameters:
            lines.append("    // PL/I MAIN command-line parameter placeholder")
        for _ in procedure.parameters:
            lines.append("    ldc.i4.0")
        descriptor = ", ".join("int32" for _ in procedure.parameters)
        if returns:
            lines.extend([f"    call int32 PL1Program::{procedure_name}({descriptor})", "    pop"])
        else:
            lines.append(f"    call void PL1Program::{procedure_name}({descriptor})")
        lines.extend(["    call void [PL1CompInPy.Runtime]PL1CompInPy.Runtime.PL1Runtime::Shutdown()", "    ret", "  }"])
        return lines

    def _entrypoint_body(self, statements: list[object]) -> list[str]:
        locals_map: dict[str, int] = {}
        local_types: list[str] = []
        body_lines: list[str] = []
        for statement in statements:
            body_lines.extend(self._statement(statement, locals_map, local_types))
        lines = [
            "  .method public hidebysig static void Main(string[] args) cil managed",
            "  {",
            "    .entrypoint",
            "    .maxstack 16",
        ]
        if local_types:
            lines.append("    .locals init (" + ", ".join(local_types) + ")")
        lines.append("    call void [PL1CompInPy.Runtime]PL1CompInPy.Runtime.PL1Runtime::Init()")
        lines.extend(body_lines)
        lines.extend(["    call void [PL1CompInPy.Runtime]PL1CompInPy.Runtime.PL1Runtime::Shutdown()", "    ret", "  }"])
        return lines

    def _statement(self, statement: object, locals_map: dict[str, int], local_types: list[str]) -> list[str]:
        if isinstance(statement, Declaration):
            lines: list[str] = []
            for name in _declaration_storage_names(statement):
                index = self._local(name, locals_map, local_types)
                lines.extend(["    ldc.i4.0", f"    stloc {index}"])
            return lines
        if isinstance(statement, Assignment):
            index = self._local(statement.target, locals_map, local_types)
            return self._expression(statement.expression, locals_map, local_types) + [f"    stloc {index}"]
        if isinstance(statement, Call):
            return self._call(statement, locals_map, local_types)
        if isinstance(statement, RawStatement) and statement.keyword.upper() == "RETURN":
            if statement.tokens and statement.tokens[0] in locals_map:
                return [f"    ldloc {locals_map[statement.tokens[0]]}", "    ret"]
            if statement.tokens and statement.tokens[0].isdigit():
                return self._int_constant(int(statement.tokens[0])) + ["    ret"]
            return ["    ldc.i4.0", "    ret"]
        if isinstance(statement, LabelledStatement):
            return [f"  {statement.label}:"] + self._statement(statement.statement, locals_map, local_types)
        if isinstance(statement, GotoStatement):
            return [f"    br {statement.label}"]
        if isinstance(statement, PreprocessorStatement):
            return [f"    // preprocessor {statement.command} {' '.join(statement.arguments)}".rstrip()]
        return []

    def _expression(self, expression: object, locals_map: dict[str, int], local_types: list[str]) -> list[str]:
        if isinstance(expression, NumberLiteral):
            return self._int_constant(int(float(expression.value)))
        if isinstance(expression, Identifier):
            return [f"    ldloc {self._local(expression.name, locals_map, local_types)}"]
        if isinstance(expression, FieldReference):
            return [f"    ldloc {self._local(expression.name, locals_map, local_types)}"]
        if isinstance(expression, PointerReference):
            return [f"    ldloc {self._local(expression.name, locals_map, local_types)}"]
        if isinstance(expression, FunctionCall):
            return [f"    // function expression {expression.name} lowered as zero", "    ldc.i4.0"]
        if isinstance(expression, BinaryExpression):
            lines = self._expression(expression.left, locals_map, local_types)
            lines.extend(self._expression(expression.right, locals_map, local_types))
            lines.append({"+": "    add", "-": "    sub", "*": "    mul", "/": "    div"}.get(expression.operator, "    add"))
            return lines
        return ["    ldc.i4.0"]

    def _call(self, call: Call, locals_map: dict[str, int], local_types: list[str]) -> list[str]:
        if call.name.upper() in {"DISPLAY", "PRINT"}:
            lines: list[str] = []
            for argument in call.arguments:
                if isinstance(argument, StringLiteral):
                    lines.extend([f"    ldstr {self._quote(argument.value)}", "    call void [mscorlib]System.Console::WriteLine(string)"])
                else:
                    lines.extend(self._expression(argument, locals_map, local_types))
                    lines.append("    call void [mscorlib]System.Console::WriteLine(int32)")
            return lines
        lines = []
        for argument in call.arguments:
            lines.extend(self._expression(argument, locals_map, local_types))
        descriptor = ", ".join("int32" for _ in call.arguments)
        lines.extend([f"    call int32 PL1Program::{call.name}({descriptor})", "    pop"])
        return lines

    def _local(self, name: str, locals_map: dict[str, int], local_types: list[str]) -> int:
        if name not in locals_map:
            locals_map[name] = len(locals_map)
            local_types.append(f"int32 V_{locals_map[name]}")
        return locals_map[name]

    def _int_constant(self, value: int) -> list[str]:
        if value == -1:
            return ["    ldc.i4.m1"]
        if 0 <= value <= 8:
            return [f"    ldc.i4.{value}"]
        if -128 <= value <= 127:
            return [f"    ldc.i4.s {value}"]
        return [f"    ldc.i4 {value}"]

    def _main_name(self, program: Program) -> str | None:
        return main_procedure_name(program)

    def _quote(self, value: str) -> str:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'


def emit_dotnet_il(program: Program) -> str:
    return DotNetILEmitter().emit(program)


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
