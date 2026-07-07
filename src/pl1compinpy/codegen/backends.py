from __future__ import annotations

from dataclasses import dataclass, field

from ..core.ast import (
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
    SelectStatement,
    Statement,
    StringLiteral,
)
from .runtime_link import runtime_linkage


@dataclass(frozen=True)
class AssemblyTarget:
    name: str
    arch: str
    platform: str
    symbol_prefix: str
    entry_symbol: str
    printf_symbol: str
    exit_symbol: str | None = None


TARGETS = {
    "python": None,
    "python-source": None,
    "jvm-bytecode": None,
    "dotnet-il": None,
    "x586-windows": AssemblyTarget("x586-windows", "x586", "windows", "_", "_main", "_printf"),
    "x586-macos": AssemblyTarget("x586-macos", "x586", "macos", "_", "_main", "_printf"),
    "x86_64-windows": AssemblyTarget("x86_64-windows", "x86_64", "windows", "", "main", "printf"),
    "arm64-macos": AssemblyTarget("arm64-macos", "arm64", "macos", "_", "_main", "_printf"),
    "arm64-windows": AssemblyTarget("arm64-windows", "arm64", "windows", "", "main", "printf"),
}


class BackendError(ValueError):
    pass


def emit_assembly(program: Program, target_name: str) -> str:
    target = TARGETS.get(target_name)
    if target is None:
        raise BackendError(f"Unknown assembly target: {target_name}")
    if target.arch == "x586":
        return X586AssemblyEmitter(target).emit(program)
    if target.arch == "x86_64":
        return X8664AssemblyEmitter(target).emit(program)
    if target.arch == "arm64":
        return Arm64AssemblyEmitter(target).emit(program)
    raise BackendError(f"Unsupported target architecture: {target.arch}")


@dataclass
class SymbolTable:
    variables: set[str] = field(default_factory=set)
    strings: dict[str, str] = field(default_factory=dict)
    next_string: int = 0

    def add_string(self, value: str) -> str:
        if value not in self.strings:
            self.strings[value] = f"Lstr{self.next_string}"
            self.next_string += 1
        return self.strings[value]


class AssemblyEmitter:
    def __init__(self, target: AssemblyTarget) -> None:
        self.target = target
        self.symbols = SymbolTable()
        self.label_index = 0
        self.runtime_linkage = runtime_linkage(target.name)

    def _collect_symbols(self, program: Program) -> None:
        for statement in program.statements:
            self._collect_statement(statement)

    def _collect_statement(self, statement: Statement) -> None:
        if isinstance(statement, Assignment):
            self.symbols.variables.add(statement.target)
            self._collect_expression(statement.expression)
        elif isinstance(statement, Declaration):
            self.symbols.variables.update(statement.names)
        elif isinstance(statement, Call):
            for argument in statement.arguments:
                self._collect_expression(argument)
        elif isinstance(statement, Procedure):
            for child in statement.body:
                self._collect_statement(child)
        elif isinstance(statement, DoGroup):
            for child in statement.body:
                self._collect_statement(child)
        elif isinstance(statement, IfStatement):
            self._collect_expression(statement.condition)
            self._collect_statement(statement.then_branch)
            if statement.else_branch:
                self._collect_statement(statement.else_branch)
        elif isinstance(statement, LabelledStatement):
            self._collect_statement(statement.statement)
        elif isinstance(statement, RawStatement):
            for token in statement.tokens:
                if token.startswith("'") and token.endswith("'"):
                    self.symbols.add_string(token[1:-1])

    def _collect_expression(self, expression: Expression) -> None:
        if isinstance(expression, Identifier):
            self.symbols.variables.add(expression.name)
        elif isinstance(expression, StringLiteral):
            self.symbols.add_string(expression.value)
        elif isinstance(expression, BinaryExpression):
            self._collect_expression(expression.left)
            self._collect_expression(expression.right)

    def _new_label(self, stem: str) -> str:
        label = f".L{stem}{self.label_index}"
        self.label_index += 1
        return label

    def _symbol(self, name: str) -> str:
        return f"{self.target.symbol_prefix}{name}"

    def _runtime_symbol(self, name: str) -> str:
        return self.runtime_linkage.symbol(name, self.target.symbol_prefix)

    def _runtime_externs(self) -> list[str]:
        return [f"extern {self._runtime_symbol(self.runtime_linkage.startup_symbol)}", f"extern {self._runtime_symbol(self.runtime_linkage.shutdown_symbol)}"]

    def _runtime_link_comments(self, comment: str) -> list[str]:
        linkage = self.runtime_linkage
        lines = [
            f"{comment} runtime-link: {linkage.runtime_kind}",
            f"{comment} runtime-static: {', '.join(linkage.static_libraries) or 'none'}",
            f"{comment} runtime-dynamic: {', '.join(linkage.dynamic_libraries) or 'none'}",
            f"{comment} c-runtime: {linkage.c_runtime or 'managed'}",
        ]
        return lines

    def _escaped_bytes(self, value: str) -> str:
        parts = [str(ord(char)) for char in value]
        return ", ".join(parts + ["0"])

    def _condition_jump(self, operator: str, if_false: bool) -> str:
        jumps = {
            "=": ("jne", "je"),
            "^=": ("je", "jne"),
            "¬=": ("je", "jne"),
            "~=": ("je", "jne"),
            "<>": ("je", "jne"),
            "<": ("jge", "jl"),
            "<=": ("jg", "jle"),
            ">": ("jle", "jg"),
            ">=": ("jl", "jge"),
            "=>": ("jl", "jge"),
        }
        return jumps.get(operator, ("je", "jne"))[0 if if_false else 1]

    def _raw_put_arguments(self, statement: RawStatement) -> list[Expression]:
        if statement.keyword.upper() != "PUT":
            return []
        expressions: list[Expression] = []
        for token in statement.tokens:
            upper = token.upper()
            if upper in {"LIST", "SKIP", "(", ")", ","}:
                continue
            if token.startswith("'") and token.endswith("'"):
                expressions.append(StringLiteral(token[1:-1]))
            elif token.isdigit():
                expressions.append(NumberLiteral(token))
            elif token.isidentifier():
                expressions.append(Identifier(token))
        return expressions


class X586AssemblyEmitter(AssemblyEmitter):
    def emit(self, program: Program) -> str:
        self._collect_symbols(program)
        lines = [
            "; PL1CompInPy generated x586 assembly",
            f"; target: {self.target.name}",
            *self._runtime_link_comments(";"),
            f"extern {self.target.printf_symbol}",
            *self._runtime_externs(),
            f"global {self.target.entry_symbol}",
            "section .data",
            "fmt_int db \"%d\", 10, 0",
            "fmt_str db \"%s\", 10, 0",
        ]
        for name in sorted(self.symbols.variables):
            lines.append(f"{name} dd 0")
        for value, label in self.symbols.strings.items():
            lines.append(f"{label} db {self._escaped_bytes(value)}")

        lines.extend(["section .text", f"{self.target.entry_symbol}:", f"    call {self._runtime_symbol(self.runtime_linkage.startup_symbol)}"])
        for statement in program.statements:
            lines.extend(self._statement(statement))
        lines.extend([f"    call {self._runtime_symbol(self.runtime_linkage.shutdown_symbol)}", "    xor eax, eax", "    ret"])
        return "\n".join(lines) + "\n"

    def _statement(self, statement: Statement) -> list[str]:
        if isinstance(statement, Assignment):
            lines = self._expression(statement.expression)
            lines.append(f"    mov [{statement.target}], eax")
            return lines
        if isinstance(statement, Declaration):
            return [f"    ; declare {', '.join(statement.names)} {' '.join(statement.attributes)}".rstrip()]
        if isinstance(statement, Call):
            return self._call(statement)
        if isinstance(statement, Procedure):
            lines = [f"{self._symbol(statement.name or 'anonymous_procedure')}:"]
            for child in statement.body:
                lines.extend(self._statement(child))
            lines.append("    ret")
            return lines
        if isinstance(statement, DoGroup):
            return self._do_group(statement)
        if isinstance(statement, IfStatement):
            return self._if(statement)
        if isinstance(statement, SelectStatement):
            return self._select(statement)
        if isinstance(statement, LabelledStatement):
            return [f"{statement.label}:"] + self._statement(statement.statement)
        if isinstance(statement, RawStatement):
            args = self._raw_put_arguments(statement)
            if args:
                return self._print_arguments(args)
            return [f"    ; unsupported statement preserved: {statement.keyword} {' '.join(statement.tokens)}".rstrip()]
        raise BackendError(f"Unsupported statement for x586 backend: {statement!r}")

    def _do_group(self, statement: DoGroup) -> list[str]:
        if statement.while_condition is None and statement.until_condition is None:
            lines: list[str] = []
            for child in statement.body:
                lines.extend(self._statement(child))
            return lines
        start = self._new_label("do")
        end = self._new_label("enddo")
        lines = [f"{start}:"]
        if statement.while_condition:
            lines.extend(self._comparison(statement.while_condition, end))
        for child in statement.body:
            lines.extend(self._statement(child))
        if statement.until_condition:
            lines.extend(self._comparison(statement.until_condition, start))
        else:
            lines.append(f"    jmp {start}")
        lines.append(f"{end}:")
        return lines

    def _if(self, statement: IfStatement) -> list[str]:
        else_label = self._new_label("else")
        end_label = self._new_label("endif")
        lines = self._comparison(statement.condition, else_label)
        lines.extend(self._statement(statement.then_branch))
        lines.append(f"    jmp {end_label}")
        lines.append(f"{else_label}:")
        if statement.else_branch:
            lines.extend(self._statement(statement.else_branch))
        lines.append(f"{end_label}:")
        return lines

    def _select(self, statement: SelectStatement) -> list[str]:
        end = self._new_label("select_end")
        lines: list[str] = []
        for branch in statement.when_branches:
            next_branch = self._new_label("select_next")
            matched = self._new_label("select_matched")
            for expression in branch.expressions:
                value_next = self._new_label("select_value_next")
                if statement.expression:
                    lines.extend(self._expression(statement.expression))
                    lines.append("    push eax")
                    lines.extend(self._expression(expression))
                    lines.extend(["    mov ebx, eax", "    pop eax", "    cmp eax, ebx"])
                    lines.append(f"    {self._condition_jump('=', if_false=True)} {value_next}")
                else:
                    lines.extend(self._comparison(expression, value_next))
                lines.append(f"    jmp {matched}")
                lines.append(f"{value_next}:")
            lines.append(f"    jmp {next_branch}")
            lines.append(f"{matched}:")
            lines.extend(self._statement(branch.statement))
            lines.append(f"    jmp {end}")
            lines.append(f"{next_branch}:")
        if statement.otherwise:
            lines.extend(self._statement(statement.otherwise))
        lines.append(f"{end}:")
        return lines

    def _call(self, statement: Call) -> list[str]:
        if statement.name.upper() in {"DISPLAY", "PRINT"}:
            return self._print_arguments(statement.arguments)
        lines = []
        for argument in reversed(statement.arguments):
            lines.extend(self._expression(argument))
            lines.append("    push eax")
        lines.append(f"    call {self._symbol(statement.name)}")
        if statement.arguments:
            lines.append(f"    add esp, {len(statement.arguments) * 4}")
        return lines

    def _print_arguments(self, arguments: list[Expression]) -> list[str]:
        lines: list[str] = []
        for argument in arguments:
            if isinstance(argument, StringLiteral):
                label = self.symbols.add_string(argument.value)
                lines.extend([f"    push {label}", "    push fmt_str", f"    call {self.target.printf_symbol}", "    add esp, 8"])
            else:
                lines.extend(self._expression(argument))
                lines.extend(["    push eax", "    push fmt_int", f"    call {self.target.printf_symbol}", "    add esp, 8"])
        return lines

    def _comparison(self, expression: Expression, false_label: str) -> list[str]:
        if isinstance(expression, BinaryExpression) and expression.operator in {"=", "^=", "¬=", "~=", "<>", "<", "<=", ">", ">=", "=>"}:
            lines = self._expression(expression.left)
            lines.append("    push eax")
            lines.extend(self._expression(expression.right))
            lines.extend(["    mov ebx, eax", "    pop eax", "    cmp eax, ebx"])
            lines.append(f"    {self._condition_jump(expression.operator, if_false=True)} {false_label}")
            return lines
        lines = self._expression(expression)
        lines.extend(["    cmp eax, 0", f"    je {false_label}"])
        return lines

    def _expression(self, expression: Expression) -> list[str]:
        if isinstance(expression, NumberLiteral):
            return [f"    mov eax, {expression.value}"]
        if isinstance(expression, Identifier):
            return [f"    mov eax, [{expression.name}]"]
        if isinstance(expression, StringLiteral):
            return [f"    mov eax, {self.symbols.add_string(expression.value)}"]
        if isinstance(expression, BinaryExpression):
            lines = self._expression(expression.left)
            lines.append("    push eax")
            lines.extend(self._expression(expression.right))
            lines.extend(["    mov ebx, eax", "    pop eax"])
            if expression.operator == "+":
                lines.append("    add eax, ebx")
            elif expression.operator == "-":
                lines.append("    sub eax, ebx")
            elif expression.operator == "*":
                lines.append("    imul eax, ebx")
            elif expression.operator == "/":
                lines.extend(["    cdq", "    idiv ebx"])
            else:
                raise BackendError(f"Unsupported x586 expression operator: {expression.operator}")
            return lines
        raise BackendError(f"Unsupported x586 expression: {expression!r}")


class X8664AssemblyEmitter(AssemblyEmitter):
    def emit(self, program: Program) -> str:
        self._collect_symbols(program)
        lines = [
            "; PL1CompInPy generated x86_64 assembly",
            f"; target: {self.target.name}",
            *self._runtime_link_comments(";"),
            "bits 64",
            "default rel",
            f"extern {self.target.printf_symbol}",
            *self._runtime_externs(),
            f"global {self.target.entry_symbol}",
            "section .data",
            "fmt_int db \"%d\", 10, 0",
            "fmt_str db \"%s\", 10, 0",
        ]
        for name in sorted(self.symbols.variables):
            lines.append(f"{name} dq 0")
        for value, label in self.symbols.strings.items():
            lines.append(f"{label} db {self._escaped_bytes(value)}")

        lines.extend(["section .text", f"{self.target.entry_symbol}:", f"    call {self._runtime_symbol(self.runtime_linkage.startup_symbol)}"])
        for statement in program.statements:
            lines.extend(self._statement(statement))
        lines.extend([f"    call {self._runtime_symbol(self.runtime_linkage.shutdown_symbol)}", "    xor eax, eax", "    ret"])
        return "\n".join(lines) + "\n"

    def _statement(self, statement: Statement) -> list[str]:
        if isinstance(statement, Assignment):
            lines = self._expression(statement.expression)
            lines.append(f"    mov [rel {statement.target}], rax")
            return lines
        if isinstance(statement, Declaration):
            return [f"    ; declare {', '.join(statement.names)} {' '.join(statement.attributes)}".rstrip()]
        if isinstance(statement, Call):
            return self._call(statement)
        if isinstance(statement, Procedure):
            lines = [f"{self._symbol(statement.name or 'anonymous_procedure')}:"]
            for child in statement.body:
                lines.extend(self._statement(child))
            lines.append("    ret")
            return lines
        if isinstance(statement, DoGroup):
            return self._do_group(statement)
        if isinstance(statement, IfStatement):
            return self._if(statement)
        if isinstance(statement, SelectStatement):
            return self._select(statement)
        if isinstance(statement, LabelledStatement):
            return [f"{statement.label}:"] + self._statement(statement.statement)
        if isinstance(statement, RawStatement):
            args = self._raw_put_arguments(statement)
            if args:
                return self._print_arguments(args)
            return [f"    ; unsupported statement preserved: {statement.keyword} {' '.join(statement.tokens)}".rstrip()]
        raise BackendError(f"Unsupported x86_64 backend statement: {statement!r}")

    def _do_group(self, statement: DoGroup) -> list[str]:
        if statement.while_condition is None and statement.until_condition is None:
            lines: list[str] = []
            for child in statement.body:
                lines.extend(self._statement(child))
            return lines
        start = self._new_label("do")
        end = self._new_label("enddo")
        lines = [f"{start}:"]
        if statement.while_condition:
            lines.extend(self._comparison(statement.while_condition, end))
        for child in statement.body:
            lines.extend(self._statement(child))
        if statement.until_condition:
            lines.extend(self._comparison(statement.until_condition, start))
        else:
            lines.append(f"    jmp {start}")
        lines.append(f"{end}:")
        return lines

    def _if(self, statement: IfStatement) -> list[str]:
        else_label = self._new_label("else")
        end_label = self._new_label("endif")
        lines = self._comparison(statement.condition, else_label)
        lines.extend(self._statement(statement.then_branch))
        lines.append(f"    jmp {end_label}")
        lines.append(f"{else_label}:")
        if statement.else_branch:
            lines.extend(self._statement(statement.else_branch))
        lines.append(f"{end_label}:")
        return lines

    def _select(self, statement: SelectStatement) -> list[str]:
        end = self._new_label("select_end")
        lines: list[str] = []
        for branch in statement.when_branches:
            next_branch = self._new_label("select_next")
            matched = self._new_label("select_matched")
            for expression in branch.expressions:
                value_next = self._new_label("select_value_next")
                if statement.expression:
                    lines.extend(self._expression(statement.expression))
                    lines.append("    push rax")
                    lines.extend(self._expression(expression))
                    lines.extend(["    mov rbx, rax", "    pop rax", "    cmp rax, rbx"])
                    lines.append(f"    {self._condition_jump('=', if_false=True)} {value_next}")
                else:
                    lines.extend(self._comparison(expression, value_next))
                lines.append(f"    jmp {matched}")
                lines.append(f"{value_next}:")
            lines.append(f"    jmp {next_branch}")
            lines.append(f"{matched}:")
            lines.extend(self._statement(branch.statement))
            lines.append(f"    jmp {end}")
            lines.append(f"{next_branch}:")
        if statement.otherwise:
            lines.extend(self._statement(statement.otherwise))
        lines.append(f"{end}:")
        return lines

    def _call(self, statement: Call) -> list[str]:
        if statement.name.upper() in {"DISPLAY", "PRINT"}:
            return self._print_arguments(statement.arguments)
        lines: list[str] = []
        for argument in reversed(statement.arguments):
            lines.extend(self._expression(argument))
            lines.append("    push rax")
        lines.extend(["    sub rsp, 32", f"    call {self._symbol(statement.name)}", "    add rsp, 32"])
        if statement.arguments:
            lines.append(f"    add rsp, {len(statement.arguments) * 8}")
        return lines

    def _print_arguments(self, arguments: list[Expression]) -> list[str]:
        lines: list[str] = []
        for argument in arguments:
            if isinstance(argument, StringLiteral):
                label = self.symbols.add_string(argument.value)
                lines.extend(
                    [
                        "    sub rsp, 40",
                        "    lea rcx, [rel fmt_str]",
                        f"    lea rdx, [rel {label}]",
                        f"    call {self.target.printf_symbol}",
                        "    add rsp, 40",
                    ]
                )
            else:
                lines.extend(self._expression(argument))
                lines.extend(
                    [
                        "    sub rsp, 40",
                        "    lea rcx, [rel fmt_int]",
                        "    mov rdx, rax",
                        f"    call {self.target.printf_symbol}",
                        "    add rsp, 40",
                    ]
                )
        return lines

    def _comparison(self, expression: Expression, false_label: str) -> list[str]:
        if isinstance(expression, BinaryExpression) and expression.operator in {"=", "^=", "¬=", "~=", "<>", "<", "<=", ">", ">=", "=>"}:
            lines = self._expression(expression.left)
            lines.append("    push rax")
            lines.extend(self._expression(expression.right))
            lines.extend(["    mov rbx, rax", "    pop rax", "    cmp rax, rbx"])
            lines.append(f"    {self._condition_jump(expression.operator, if_false=True)} {false_label}")
            return lines
        lines = self._expression(expression)
        lines.extend(["    cmp rax, 0", f"    je {false_label}"])
        return lines

    def _expression(self, expression: Expression) -> list[str]:
        if isinstance(expression, NumberLiteral):
            return [f"    mov rax, {expression.value}"]
        if isinstance(expression, Identifier):
            return [f"    mov rax, [rel {expression.name}]"]
        if isinstance(expression, StringLiteral):
            return [f"    lea rax, [rel {self.symbols.add_string(expression.value)}]"]
        if isinstance(expression, BinaryExpression):
            lines = self._expression(expression.left)
            lines.append("    push rax")
            lines.extend(self._expression(expression.right))
            lines.extend(["    mov rbx, rax", "    pop rax"])
            if expression.operator == "+":
                lines.append("    add rax, rbx")
            elif expression.operator == "-":
                lines.append("    sub rax, rbx")
            elif expression.operator == "*":
                lines.append("    imul rax, rbx")
            elif expression.operator == "/":
                lines.extend(["    cqo", "    idiv rbx"])
            else:
                raise BackendError(f"Unsupported x86_64 expression operator: {expression.operator}")
            return lines
        raise BackendError(f"Unsupported x86_64 expression: {expression!r}")


class Arm64AssemblyEmitter(AssemblyEmitter):
    def emit(self, program: Program) -> str:
        self._collect_symbols(program)
        lines = [
            "// PL1CompInPy generated ARM64 assembly",
            f"// target: {self.target.name}",
            *self._runtime_link_comments("//"),
            ".data",
            'fmt_int: .asciz "%d\\n"',
            'fmt_str: .asciz "%s\\n"',
        ]
        for name in sorted(self.symbols.variables):
            lines.extend([f".balign 4", f"{name}: .word 0"])
        for value, label in self.symbols.strings.items():
            lines.append(f'{label}: .asciz "{self._escape_asciz(value)}"')

        lines.extend([
            ".text",
            f".extern {self._runtime_symbol(self.runtime_linkage.startup_symbol)}",
            f".extern {self._runtime_symbol(self.runtime_linkage.shutdown_symbol)}",
            f".globl {self.target.entry_symbol}",
            f"{self.target.entry_symbol}:",
            f"    bl {self._runtime_symbol(self.runtime_linkage.startup_symbol)}",
        ])
        for statement in program.statements:
            lines.extend(self._statement(statement))
        lines.extend([f"    bl {self._runtime_symbol(self.runtime_linkage.shutdown_symbol)}", "    mov w0, #0", "    ret"])
        return "\n".join(lines) + "\n"

    def _statement(self, statement: Statement) -> list[str]:
        if isinstance(statement, Assignment):
            lines = self._expression(statement.expression)
            lines.extend([f"    adrp x1, {statement.target}@PAGE", f"    add x1, x1, {statement.target}@PAGEOFF", "    str w0, [x1]"])
            return lines
        if isinstance(statement, Declaration):
            return [f"    // declare {', '.join(statement.names)} {' '.join(statement.attributes)}".rstrip()]
        if isinstance(statement, Call):
            return self._call(statement)
        if isinstance(statement, Procedure):
            lines = [f"{self._symbol(statement.name or 'anonymous_procedure')}:"]
            for child in statement.body:
                lines.extend(self._statement(child))
            lines.append("    ret")
            return lines
        if isinstance(statement, DoGroup):
            return self._do_group(statement)
        if isinstance(statement, IfStatement):
            return self._if(statement)
        if isinstance(statement, SelectStatement):
            return self._select(statement)
        if isinstance(statement, LabelledStatement):
            return [f"{statement.label}:"] + self._statement(statement.statement)
        if isinstance(statement, RawStatement):
            args = self._raw_put_arguments(statement)
            if args:
                return self._print_arguments(args)
            return [f"    // unsupported statement preserved: {statement.keyword} {' '.join(statement.tokens)}".rstrip()]
        raise BackendError(f"Unsupported ARM64 backend statement: {statement!r}")

    def _do_group(self, statement: DoGroup) -> list[str]:
        if statement.while_condition is None and statement.until_condition is None:
            lines: list[str] = []
            for child in statement.body:
                lines.extend(self._statement(child))
            return lines
        start = self._new_label("do")
        end = self._new_label("enddo")
        lines = [f"{start}:"]
        if statement.while_condition:
            lines.extend(self._comparison(statement.while_condition, end))
        for child in statement.body:
            lines.extend(self._statement(child))
        if statement.until_condition:
            lines.extend(self._comparison(statement.until_condition, start))
        else:
            lines.append(f"    b {start}")
        lines.append(f"{end}:")
        return lines

    def _if(self, statement: IfStatement) -> list[str]:
        else_label = self._new_label("else")
        end_label = self._new_label("endif")
        lines = self._comparison(statement.condition, else_label)
        lines.extend(self._statement(statement.then_branch))
        lines.append(f"    b {end_label}")
        lines.append(f"{else_label}:")
        if statement.else_branch:
            lines.extend(self._statement(statement.else_branch))
        lines.append(f"{end_label}:")
        return lines

    def _select(self, statement: SelectStatement) -> list[str]:
        end = self._new_label("select_end")
        lines: list[str] = []
        for branch in statement.when_branches:
            next_branch = self._new_label("select_next")
            matched = self._new_label("select_matched")
            for expression in branch.expressions:
                value_next = self._new_label("select_value_next")
                if statement.expression:
                    lines.extend(self._expression(statement.expression))
                    lines.append("    mov w8, w0")
                    lines.extend(self._expression(expression))
                    lines.append("    cmp w8, w0")
                    lines.append(f"    b.ne {value_next}")
                else:
                    lines.extend(self._comparison(expression, value_next))
                lines.append(f"    b {matched}")
                lines.append(f"{value_next}:")
            lines.append(f"    b {next_branch}")
            lines.append(f"{matched}:")
            lines.extend(self._statement(branch.statement))
            lines.append(f"    b {end}")
            lines.append(f"{next_branch}:")
        if statement.otherwise:
            lines.extend(self._statement(statement.otherwise))
        lines.append(f"{end}:")
        return lines

    def _call(self, statement: Call) -> list[str]:
        if statement.name.upper() in {"DISPLAY", "PRINT"}:
            return self._print_arguments(statement.arguments)
        lines: list[str] = []
        for index, argument in enumerate(statement.arguments[:8]):
            lines.extend(self._expression(argument))
            lines.append(f"    mov w{index}, w0")
        lines.append(f"    bl {self._symbol(statement.name)}")
        return lines

    def _print_arguments(self, arguments: list[Expression]) -> list[str]:
        lines: list[str] = []
        for argument in arguments:
            if isinstance(argument, StringLiteral):
                label = self.symbols.add_string(argument.value)
                lines.extend(
                    [
                        "    adrp x0, fmt_str@PAGE",
                        "    add x0, x0, fmt_str@PAGEOFF",
                        f"    adrp x1, {label}@PAGE",
                        f"    add x1, x1, {label}@PAGEOFF",
                        f"    bl {self.target.printf_symbol}",
                    ]
                )
            else:
                lines.extend(self._expression(argument))
                lines.extend(
                    [
                        "    mov w1, w0",
                        "    adrp x0, fmt_int@PAGE",
                        "    add x0, x0, fmt_int@PAGEOFF",
                        f"    bl {self.target.printf_symbol}",
                    ]
                )
        return lines

    def _comparison(self, expression: Expression, false_label: str) -> list[str]:
        if isinstance(expression, BinaryExpression) and expression.operator in {"=", "^=", "¬=", "~=", "<>", "<", "<=", ">", ">=", "=>"}:
            lines = self._expression(expression.left)
            lines.append("    mov w8, w0")
            lines.extend(self._expression(expression.right))
            lines.append("    cmp w8, w0")
            branch = {
                "=": "b.ne",
                "^=": "b.eq",
                "¬=": "b.eq",
                "~=": "b.eq",
                "<>": "b.eq",
                "<": "b.ge",
                "<=": "b.gt",
                ">": "b.le",
                ">=": "b.lt",
                "=>": "b.lt",
            }[expression.operator]
            lines.append(f"    {branch} {false_label}")
            return lines
        lines = self._expression(expression)
        lines.extend(["    cmp w0, #0", f"    b.eq {false_label}"])
        return lines

    def _expression(self, expression: Expression) -> list[str]:
        if isinstance(expression, NumberLiteral):
            return [f"    mov w0, #{expression.value}"]
        if isinstance(expression, Identifier):
            return [f"    adrp x0, {expression.name}@PAGE", f"    add x0, x0, {expression.name}@PAGEOFF", "    ldr w0, [x0]"]
        if isinstance(expression, StringLiteral):
            label = self.symbols.add_string(expression.value)
            return [f"    adrp x0, {label}@PAGE", f"    add x0, x0, {label}@PAGEOFF"]
        if isinstance(expression, BinaryExpression):
            lines = self._expression(expression.left)
            lines.append("    mov w8, w0")
            lines.extend(self._expression(expression.right))
            if expression.operator == "+":
                lines.append("    add w0, w8, w0")
            elif expression.operator == "-":
                lines.append("    sub w0, w8, w0")
            elif expression.operator == "*":
                lines.append("    mul w0, w8, w0")
            elif expression.operator == "/":
                lines.append("    sdiv w0, w8, w0")
            else:
                raise BackendError(f"Unsupported ARM64 expression operator: {expression.operator}")
            return lines
        raise BackendError(f"Unsupported ARM64 expression: {expression!r}")

    def _escape_asciz(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
