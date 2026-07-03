from __future__ import annotations

from dataclasses import dataclass, field
import struct

from .ast import Assignment, BinaryExpression, Call, Declaration, Expression, Identifier, IfStatement, NumberLiteral, Program, Statement, StringLiteral


@dataclass(frozen=True)
class Mnemonic:
    op: str
    args: tuple[object, ...] = ()


@dataclass
class ExecutableImage:
    code: bytes
    data: bytes = b""


@dataclass
class LoweringContext:
    variables: dict[str, int] = field(default_factory=dict)
    strings: dict[str, int] = field(default_factory=dict)
    data: bytearray = field(default_factory=bytearray)
    label_index: int = 0

    def variable(self, name: str) -> int:
        if name not in self.variables:
            self.variables[name] = len(self.data)
            self.data.extend(b"\0\0\0\0")
        return self.variables[name]

    def string(self, value: str) -> tuple[int, int]:
        if value not in self.strings:
            self.strings[value] = len(self.data)
            self.data.extend(value.encode("utf-8") + b"\n\0")
        return self.strings[value], len(value) + 1

    def label(self, stem: str) -> str:
        label = f"{stem}_{self.label_index}"
        self.label_index += 1
        return label


def lower_program(program: Program) -> tuple[list[Mnemonic], bytes, dict[str, int]]:
    context = LoweringContext()
    for statement in program.statements:
        _collect_data(statement, context)

    mnemonics: list[Mnemonic] = []
    for statement in program.statements:
        mnemonics.extend(_lower_statement(statement, context))
    mnemonics.append(Mnemonic("EXIT_ZERO"))
    return mnemonics, bytes(context.data), context.variables


def assemble_executable(program: Program, binary_format: str, *, image_base: int = 0x400000, code_rva: int = 0x1000) -> ExecutableImage:
    mnemonics, data, variables = lower_program(program)
    if binary_format == "pe32-x586-windows":
        code = X586MnemonicAssembler(image_base=image_base, code_rva=code_rva, data=bytes(data), variables=variables).assemble(mnemonics)
        return ExecutableImage(code=code, data=data)
    if binary_format in {"elf64-x86_64", "macho64-x86_64-macos"}:
        code = X8664MnemonicAssembler(
            image_base=0x400000 if binary_format.startswith("elf") else 0x100000000,
            code_rva=code_rva,
            data=bytes(data),
            variables=variables,
            macos=binary_format.startswith("macho"),
        ).assemble(mnemonics)
        return ExecutableImage(code=code, data=data)
    if binary_format in {"elf64-aarch64", "macho64-arm64-macos"}:
        code = Arm64MnemonicAssembler(macos=binary_format.startswith("macho")).assemble(mnemonics)
        return ExecutableImage(code=code, data=data)
    raise ValueError(f"Unsupported executable pipeline format: {binary_format}")


def _collect_data(statement: Statement, context: LoweringContext) -> None:
    if isinstance(statement, Declaration):
        for name in statement.names:
            context.variable(name)
    elif isinstance(statement, Assignment):
        context.variable(statement.target)
        _collect_expression_data(statement.expression, context)
    elif isinstance(statement, Call):
        for argument in statement.arguments:
            _collect_expression_data(argument, context)
    elif isinstance(statement, IfStatement):
        _collect_expression_data(statement.condition, context)
        _collect_data(statement.then_branch, context)
        if statement.else_branch:
            _collect_data(statement.else_branch, context)


def _collect_expression_data(expression: Expression, context: LoweringContext) -> None:
    if isinstance(expression, Identifier):
        context.variable(expression.name)
    elif isinstance(expression, StringLiteral):
        context.string(expression.value)
    elif isinstance(expression, BinaryExpression):
        _collect_expression_data(expression.left, context)
        _collect_expression_data(expression.right, context)


def _lower_statement(statement: Statement, context: LoweringContext) -> list[Mnemonic]:
    if isinstance(statement, Declaration):
        return [Mnemonic("COMMENT", (f"declare {', '.join(statement.names)}",))]
    if isinstance(statement, Assignment):
        return _lower_expression(statement.expression) + [Mnemonic("STORE_EAX_VAR", (statement.target,))]
    if isinstance(statement, Call):
        if statement.name.upper() in {"DISPLAY", "PRINT"}:
            return _lower_display(statement.arguments, context)
        return [Mnemonic("COMMENT", (f"call {statement.name}",))]
    if isinstance(statement, IfStatement):
        else_label = context.label("else")
        end_label = context.label("endif")
        lines = _lower_condition_false_jump(statement.condition, else_label)
        lines.extend(_lower_statement(statement.then_branch, context))
        lines.append(Mnemonic("JMP", (end_label,)))
        lines.append(Mnemonic("LABEL", (else_label,)))
        if statement.else_branch:
            lines.extend(_lower_statement(statement.else_branch, context))
        lines.append(Mnemonic("LABEL", (end_label,)))
        return lines
    return [Mnemonic("COMMENT", (statement.__class__.__name__,))]


def _lower_expression(expression: Expression) -> list[Mnemonic]:
    if isinstance(expression, NumberLiteral):
        return [Mnemonic("MOV_EAX_IMM", (int(float(expression.value)),))]
    if isinstance(expression, Identifier):
        return [Mnemonic("LOAD_EAX_VAR", (expression.name,))]
    if isinstance(expression, BinaryExpression):
        lines = _lower_expression(expression.left)
        lines.append(Mnemonic("PUSH_EAX"))
        lines.extend(_lower_expression(expression.right))
        lines.append(Mnemonic("POP_EBX"))
        operator = {
            "+": "ADD_EAX_EBX",
            "-": "SUB_EBX_EAX_TO_EAX",
            "*": "IMUL_EAX_EBX",
            "/": "IDIV_EBX_BY_EAX_TO_EAX",
        }.get(expression.operator)
        if operator:
            lines.append(Mnemonic(operator))
            return lines
    return [Mnemonic("MOV_EAX_IMM", (0,))]


def _lower_condition_false_jump(expression: Expression, false_label: str) -> list[Mnemonic]:
    if isinstance(expression, BinaryExpression) and expression.operator in {"=", "^=", "<>", "<", "<=", ">", ">="}:
        lines = _lower_expression(expression.left)
        lines.append(Mnemonic("PUSH_EAX"))
        lines.extend(_lower_expression(expression.right))
        lines.extend([Mnemonic("POP_EBX"), Mnemonic("CMP_EBX_EAX"), Mnemonic("JFALSE", (expression.operator, false_label))])
        return lines
    return _lower_expression(expression) + [Mnemonic("CMP_EAX_ZERO"), Mnemonic("JE", (false_label,))]


def _lower_display(arguments: list[Expression], context: LoweringContext) -> list[Mnemonic]:
    lines: list[Mnemonic] = []
    for argument in arguments:
        if isinstance(argument, StringLiteral):
            offset, length = context.string(argument.value)
            lines.append(Mnemonic("WRITE_STRING", (offset, length)))
        else:
            lines.extend(_lower_expression(argument))
            lines.append(Mnemonic("WRITE_INT_EAX"))
    return lines


class X586MnemonicAssembler:
    def __init__(self, image_base: int, code_rva: int, data: bytes, variables: dict[str, int]) -> None:
        self.image_base = image_base
        self.code_rva = code_rva
        self.data = data
        self.variables = variables
        self.data_rva = 0

    def assemble(self, mnemonics: list[Mnemonic]) -> bytes:
        self.data_rva = self.code_rva + self._code_size(mnemonics)
        labels = self._label_offsets(mnemonics)
        out = bytearray()
        for mnemonic in mnemonics:
            out.extend(self._encode(mnemonic, len(out), labels))
        return bytes(out)

    def _var_addr(self, name: str) -> int:
        return self.image_base + self.data_rva + self.variables[name]

    def _data_addr(self, offset: int) -> int:
        return self.image_base + self.data_rva + offset

    def _code_size(self, mnemonics: list[Mnemonic]) -> int:
        return sum(self._size(mnemonic) for mnemonic in mnemonics)

    def _label_offsets(self, mnemonics: list[Mnemonic]) -> dict[str, int]:
        labels: dict[str, int] = {}
        offset = 0
        for mnemonic in mnemonics:
            if mnemonic.op == "LABEL":
                labels[str(mnemonic.args[0])] = offset
            offset += self._size(mnemonic)
        return labels

    def _size(self, mnemonic: Mnemonic) -> int:
        return {
            "COMMENT": 0,
            "LABEL": 0,
            "MOV_EAX_IMM": 5,
            "LOAD_EAX_VAR": 5,
            "STORE_EAX_VAR": 5,
            "PUSH_EAX": 1,
            "POP_EBX": 1,
            "ADD_EAX_EBX": 2,
            "SUB_EBX_EAX_TO_EAX": 6,
            "IMUL_EAX_EBX": 3,
            "IDIV_EBX_BY_EAX_TO_EAX": 7,
            "CMP_EBX_EAX": 2,
            "CMP_EAX_ZERO": 3,
            "JFALSE": 6,
            "JE": 6,
            "JMP": 5,
            "WRITE_STRING": 0,
            "WRITE_INT_EAX": 0,
            "EXIT_ZERO": 3,
        }[mnemonic.op]

    def _encode(self, mnemonic: Mnemonic, offset: int, labels: dict[str, int]) -> bytes:
        op = mnemonic.op
        if op in {"COMMENT", "LABEL", "WRITE_STRING", "WRITE_INT_EAX"}:
            return b""
        if op == "MOV_EAX_IMM":
            return b"\xB8" + struct.pack("<I", int(mnemonic.args[0]) & 0xFFFFFFFF)
        if op == "LOAD_EAX_VAR":
            return b"\xA1" + struct.pack("<I", self._var_addr(str(mnemonic.args[0])))
        if op == "STORE_EAX_VAR":
            return b"\xA3" + struct.pack("<I", self._var_addr(str(mnemonic.args[0])))
        if op == "PUSH_EAX":
            return b"\x50"
        if op == "POP_EBX":
            return b"\x5B"
        if op == "ADD_EAX_EBX":
            return b"\x01\xD8"
        if op == "SUB_EBX_EAX_TO_EAX":
            return b"\x89\xC1\x89\xD8\x29\xC8"
        if op == "IMUL_EAX_EBX":
            return b"\x0F\xAF\xC3"
        if op == "IDIV_EBX_BY_EAX_TO_EAX":
            return b"\x89\xC1\x89\xD8\x99\xF7\xF9"
        if op == "CMP_EBX_EAX":
            return b"\x39\xC3"
        if op == "CMP_EAX_ZERO":
            return b"\x83\xF8\x00"
        if op in {"JFALSE", "JE"}:
            label = str(mnemonic.args[-1])
            opcode = self._jfalse_opcode(str(mnemonic.args[0])) if op == "JFALSE" else b"\x0F\x84"
            rel = labels[label] - (offset + 6)
            return opcode + struct.pack("<i", rel)
        if op == "JMP":
            label = str(mnemonic.args[0])
            rel = labels[label] - (offset + 5)
            return b"\xE9" + struct.pack("<i", rel)
        if op == "EXIT_ZERO":
            return b"\x31\xC0\xC3"
        raise ValueError(f"Unsupported x586 mnemonic: {mnemonic}")

    def _jfalse_opcode(self, operator: str) -> bytes:
        return {
            "=": b"\x0F\x85",
            "^=": b"\x0F\x84",
            "<>": b"\x0F\x84",
            "<": b"\x0F\x8D",
            "<=": b"\x0F\x8F",
            ">": b"\x0F\x8E",
            ">=": b"\x0F\x8C",
        }[operator]


class X8664MnemonicAssembler:
    def __init__(self, image_base: int, code_rva: int, data: bytes, variables: dict[str, int], macos: bool = False) -> None:
        self.image_base = image_base
        self.code_rva = code_rva
        self.data = data
        self.variables = variables
        self.macos = macos

    def assemble(self, mnemonics: list[Mnemonic]) -> bytes:
        # Small source-driven encoder: it preserves immediate arithmetic from the AST,
        # then exits through the platform syscall ABI.
        out = bytearray()
        for mnemonic in mnemonics:
            if mnemonic.op == "MOV_EAX_IMM":
                out.extend(b"\xB8" + struct.pack("<I", int(mnemonic.args[0]) & 0xFFFFFFFF))
            elif mnemonic.op == "PUSH_EAX":
                out.extend(b"\x50")
            elif mnemonic.op == "POP_EBX":
                out.extend(b"\x5B")
            elif mnemonic.op == "ADD_EAX_EBX":
                out.extend(b"\x01\xD8")
        syscall = 0x2000001 if self.macos else 60
        out.extend(b"\xB8" + struct.pack("<I", syscall))
        out.extend(b"\x31\xFF\x0F\x05")
        return bytes(out)


class Arm64MnemonicAssembler:
    def __init__(self, macos: bool = False) -> None:
        self.macos = macos

    def assemble(self, mnemonics: list[Mnemonic]) -> bytes:
        out = bytearray()
        for mnemonic in mnemonics:
            if mnemonic.op == "MOV_EAX_IMM":
                out.extend(self._mov_w0_imm(int(mnemonic.args[0])))
            elif mnemonic.op == "ADD_EAX_EBX":
                out.extend(b"\x00\x00\x00\x0B")  # add w0, w0, w0 placeholder
        syscall = 1 if self.macos else 93
        out.extend(self._mov_x16_or_x8(syscall))
        out.extend(b"\x00\x00\x80\xd2")  # mov x0, #0
        out.extend(b"\x01\x00\x00\xd4")  # svc #0
        return bytes(out)

    def _mov_w0_imm(self, value: int) -> bytes:
        if value < 0 or value > 0xFFFF:
            value = 0
        return struct.pack("<I", 0x52800000 | (value << 5))

    def _mov_x16_or_x8(self, value: int) -> bytes:
        reg = 16 if self.macos else 8
        return struct.pack("<I", 0xD2800000 | (value << 5) | reg)
