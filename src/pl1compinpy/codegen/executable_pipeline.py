from __future__ import annotations

from dataclasses import dataclass, field
import struct

from ..core.ast import (
    Assignment,
    BinaryExpression,
    Call,
    Declaration,
    DoGroup,
    Expression,
    GotoStatement,
    Identifier,
    IfStatement,
    LabelledStatement,
    NumberLiteral,
    PreprocessorStatement,
    Procedure,
    Program,
    RawStatement,
    SelectStatement,
    Statement,
    StringLiteral,
    main_procedure_entry,
    main_procedure_name,
    procedure_entry_name,
)
from .runtime_link import encoded_runtime_manifest


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
    local_scopes: list[dict[str, int]] = field(default_factory=list)
    parameter_scopes: list[dict[str, int]] = field(default_factory=list)

    def variable(self, name: str) -> int:
        if name not in self.variables:
            self.variables[name] = len(self.data)
            self.data.extend(b"\0\0\0\0")
        return self.variables[name]

    def local(self, name: str) -> int:
        if not self.local_scopes:
            return self.variable(name)
        scope = self.local_scopes[-1]
        if name not in scope:
            scope[name] = -4 * (len(scope) + 1)
        return scope[name]

    def local_bytes(self) -> int:
        return len(self.local_scopes[-1]) * 4 if self.local_scopes else 0

    def is_local(self, name: str) -> bool:
        return bool(self.local_scopes and name in self.local_scopes[-1])

    def is_parameter(self, name: str) -> bool:
        return bool(self.parameter_scopes and name in self.parameter_scopes[-1])

    def stack_offset(self, name: str) -> int:
        if self.is_local(name):
            return self.local_scopes[-1][name]
        if self.is_parameter(name):
            return self.parameter_scopes[-1][name]
        raise KeyError(name)

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
    procedure_statements = [statement for statement in program.statements if _is_procedure_definition(statement)]
    main_statements = [statement for statement in program.statements if not _is_procedure_definition(statement)]
    main_entry = main_procedure_entry(program)
    main_procedure = main_entry[0] if main_entry else None
    main_parameters = main_entry[1].parameters if main_entry else []

    if procedure_statements:
        mnemonics.append(Mnemonic("JMP", ("__main",)))
        for statement in procedure_statements:
            mnemonics.extend(_lower_statement(statement, context))
        mnemonics.append(Mnemonic("LABEL", ("__main",)))
        if main_procedure:
            for _ in reversed(main_parameters):
                mnemonics.extend([Mnemonic("MOV_EAX_IMM", (0,)), Mnemonic("PUSH_EAX"), Mnemonic("COMMENT", ("main command-line parameter placeholder",))])
            mnemonics.append(Mnemonic("CALL_PROC", (main_procedure, len(main_parameters))))
        for statement in main_statements:
            mnemonics.extend(_lower_statement(statement, context))
    else:
        for statement in main_statements:
            mnemonics.extend(_lower_statement(statement, context))
    mnemonics.append(Mnemonic("EXIT_ZERO"))
    return mnemonics, bytes(context.data), context.variables


def assemble_executable(program: Program, binary_format: str, *, image_base: int = 0x400000, code_rva: int = 0x1000) -> ExecutableImage:
    mnemonics, data, variables = lower_program(program)
    data = data + encoded_runtime_manifest(binary_format, program)
    if binary_format == "pe32-x586-windows":
        code = X586MnemonicAssembler(image_base=image_base, code_rva=code_rva, data=bytes(data), variables=variables).assemble(mnemonics)
        return ExecutableImage(code=code, data=data)
    if binary_format in {"pe64-x86_64-windows", "elf64-x86_64", "macho64-x86_64-macos"}:
        code = X8664MnemonicAssembler(
            image_base=image_base if binary_format.startswith("pe") else (0x400000 if binary_format.startswith("elf") else 0x100000000),
            code_rva=code_rva,
            data=bytes(data),
            variables=variables,
            macos=binary_format.startswith("macho"),
            windows=binary_format.startswith("pe"),
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
    elif isinstance(statement, DoGroup):
        if statement.while_condition:
            _collect_expression_data(statement.while_condition, context)
        if statement.until_condition:
            _collect_expression_data(statement.until_condition, context)
        for child in statement.body:
            _collect_data(child, context)
    elif isinstance(statement, SelectStatement):
        if statement.expression:
            _collect_expression_data(statement.expression, context)
        for branch in statement.when_branches:
            for expression in branch.expressions:
                _collect_expression_data(expression, context)
            _collect_data(branch.statement, context)
        if statement.otherwise:
            _collect_data(statement.otherwise, context)
    elif isinstance(statement, LabelledStatement):
        _collect_data(statement.statement, context)
    elif isinstance(statement, (GotoStatement, PreprocessorStatement)):
        return
    elif isinstance(statement, Procedure):
        return


def _collect_expression_data(expression: Expression, context: LoweringContext) -> None:
    if isinstance(expression, Identifier):
        context.variable(expression.name)
    elif isinstance(expression, StringLiteral):
        context.string(expression.value)
    elif isinstance(expression, BinaryExpression):
        _collect_expression_data(expression.left, context)
        _collect_expression_data(expression.right, context)


def _is_procedure_definition(statement: Statement) -> bool:
    return isinstance(statement, Procedure) or (
        isinstance(statement, LabelledStatement) and isinstance(statement.statement, Procedure)
    )


def _main_procedure_name(program: Program) -> str | None:
    return main_procedure_name(program)


def _lower_statement(statement: Statement, context: LoweringContext) -> list[Mnemonic]:
    if isinstance(statement, Declaration):
        if context.local_scopes:
            for name in statement.names:
                context.local(name)
        return [Mnemonic("COMMENT", (f"declare {', '.join(statement.names)}",))]
    if isinstance(statement, Assignment):
        return _lower_expression(statement.expression, context) + [_store_name(statement.target, context)]
    if isinstance(statement, Call):
        if statement.name.upper() in {"DISPLAY", "PRINT"}:
            return _lower_display(statement.arguments, context)
        return _lower_call(statement, context)
    if isinstance(statement, LabelledStatement):
        if isinstance(statement.statement, Procedure):
            procedure = statement.statement
            return _lower_procedure(
                Procedure(
                    procedure.name or statement.label,
                    procedure.parameters,
                    procedure.options,
                    procedure.body,
                    procedure.returns,
                    procedure.recursive,
                ),
                context,
            )
        return [Mnemonic("LABEL", (statement.label,))] + _lower_statement(statement.statement, context)
    if isinstance(statement, GotoStatement):
        return [Mnemonic("JMP", (statement.label,))]
    if isinstance(statement, PreprocessorStatement):
        return [Mnemonic("COMMENT", (f"preprocessor {statement.command} {' '.join(statement.arguments)}".rstrip(),))]
    if isinstance(statement, Procedure):
        return _lower_procedure(statement, context)
    if isinstance(statement, IfStatement):
        else_label = context.label("else")
        end_label = context.label("endif")
        lines = _lower_condition_false_jump(statement.condition, else_label, context)
        lines.extend(_lower_statement(statement.then_branch, context))
        lines.append(Mnemonic("JMP", (end_label,)))
        lines.append(Mnemonic("LABEL", (else_label,)))
        if statement.else_branch:
            lines.extend(_lower_statement(statement.else_branch, context))
        lines.append(Mnemonic("LABEL", (end_label,)))
        return lines
    if isinstance(statement, DoGroup):
        return _lower_do_group(statement, context)
    if isinstance(statement, SelectStatement):
        return _lower_select(statement, context)
    if isinstance(statement, RawStatement) and statement.keyword.upper() == "RETURN":
        if statement.tokens:
            if statement.tokens[0].isdigit():
                return [Mnemonic("MOV_EAX_IMM", (int(statement.tokens[0]),))]
            return [_load_name(statement.tokens[0], context)]
        return [Mnemonic("MOV_EAX_IMM", (0,))]
    return [Mnemonic("COMMENT", (statement.__class__.__name__,))]


def _lower_do_group(statement: DoGroup, context: LoweringContext) -> list[Mnemonic]:
    if statement.while_condition is None and statement.until_condition is None:
        lines: list[Mnemonic] = []
        for child in statement.body:
            lines.extend(_lower_statement(child, context))
        return lines
    start_label = context.label("do")
    end_label = context.label("enddo")
    lines = [Mnemonic("LABEL", (start_label,))]
    if statement.while_condition is not None:
        lines.extend(_lower_condition_false_jump(statement.while_condition, end_label, context))
    for child in statement.body:
        lines.extend(_lower_statement(child, context))
    if statement.until_condition is not None:
        lines.extend(_lower_condition_false_jump(statement.until_condition, start_label, context))
    else:
        lines.append(Mnemonic("JMP", (start_label,)))
    lines.append(Mnemonic("LABEL", (end_label,)))
    return lines


def _lower_select(statement: SelectStatement, context: LoweringContext) -> list[Mnemonic]:
    end_label = context.label("select_end")
    lines: list[Mnemonic] = []
    for branch in statement.when_branches:
        next_label = context.label("select_next")
        matched_label = context.label("select_matched")
        for expression in branch.expressions:
            value_next_label = context.label("select_value_next")
            if statement.expression is not None:
                lines.extend(_lower_expression(statement.expression, context))
                lines.append(Mnemonic("PUSH_EAX"))
                lines.extend(_lower_expression(expression, context))
                lines.extend([Mnemonic("POP_EBX"), Mnemonic("CMP_EBX_EAX"), Mnemonic("JFALSE", ("=", value_next_label))])
            else:
                lines.extend(_lower_condition_false_jump(expression, value_next_label, context))
            lines.append(Mnemonic("JMP", (matched_label,)))
            lines.append(Mnemonic("LABEL", (value_next_label,)))
        if not branch.expressions:
            lines.append(Mnemonic("JMP", (next_label,)))
        else:
            lines.append(Mnemonic("JMP", (next_label,)))
            lines.append(Mnemonic("LABEL", (matched_label,)))
        lines.extend(_lower_statement(branch.statement, context))
        lines.append(Mnemonic("JMP", (end_label,)))
        lines.append(Mnemonic("LABEL", (next_label,)))
    if statement.otherwise:
        lines.extend(_lower_statement(statement.otherwise, context))
    lines.append(Mnemonic("LABEL", (end_label,)))
    return lines


def _lower_procedure(procedure: Procedure, context: LoweringContext) -> list[Mnemonic]:
    name = procedure.name or ("MAIN" if "MAIN" in {option.upper() for option in procedure.options} else "anonymous_procedure")
    parameter_scope = {parameter: 8 + index * 4 for index, parameter in enumerate(procedure.parameters)}
    context.parameter_scopes.append(parameter_scope)
    context.local_scopes.append({})
    for child in procedure.body:
        if isinstance(child, Declaration):
            for local_name in child.names:
                context.local(local_name)
    local_bytes = context.local_bytes()

    lines = [Mnemonic("LABEL", (name,)), Mnemonic("ENTER_FRAME", (local_bytes,))]
    for child in procedure.body:
        lines.extend(_lower_statement(child, context))
    lines.append(Mnemonic("LEAVE_RET", (len(procedure.parameters) * 4,)))
    context.local_scopes.pop()
    context.parameter_scopes.pop()
    return lines


def _lower_call(call: Call, context: LoweringContext) -> list[Mnemonic]:
    lines: list[Mnemonic] = []
    for argument in reversed(call.arguments):
        if isinstance(argument, Identifier):
            lines.append(_push_reference(argument.name, context))
        else:
            lines.extend(_lower_expression(argument, context))
            lines.append(Mnemonic("PUSH_VALUE_TEMP"))
    lines.append(Mnemonic("CALL_PROC", (call.name, len(call.arguments))))
    if call.arguments:
        lines.append(Mnemonic("CLEAN_ARGS", (len(call.arguments) * 4,)))
    return lines


def _lower_expression(expression: Expression, context: LoweringContext) -> list[Mnemonic]:
    if isinstance(expression, NumberLiteral):
        return [Mnemonic("MOV_EAX_IMM", (int(float(expression.value)),))]
    if isinstance(expression, Identifier):
        return [_load_name(expression.name, context)]
    if isinstance(expression, BinaryExpression):
        lines = _lower_expression(expression.left, context)
        lines.append(Mnemonic("PUSH_EAX"))
        lines.extend(_lower_expression(expression.right, context))
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


def _lower_condition_false_jump(expression: Expression, false_label: str, context: LoweringContext) -> list[Mnemonic]:
    if isinstance(expression, BinaryExpression) and expression.operator in {"=", "^=", "¬=", "~=", "<>", "<", "<=", ">", ">=", "=>"}:
        lines = _lower_expression(expression.left, context)
        lines.append(Mnemonic("PUSH_EAX"))
        lines.extend(_lower_expression(expression.right, context))
        lines.extend([Mnemonic("POP_EBX"), Mnemonic("CMP_EBX_EAX"), Mnemonic("JFALSE", (expression.operator, false_label))])
        return lines
    return _lower_expression(expression, context) + [Mnemonic("CMP_EAX_ZERO"), Mnemonic("JE", (false_label,))]


def _lower_display(arguments: list[Expression], context: LoweringContext) -> list[Mnemonic]:
    lines: list[Mnemonic] = []
    for argument in arguments:
        if isinstance(argument, StringLiteral):
            offset, length = context.string(argument.value)
            lines.append(Mnemonic("WRITE_STRING", (offset, length)))
        else:
            lines.extend(_lower_expression(argument, context))
            lines.append(Mnemonic("WRITE_INT_EAX"))
    return lines


def _load_name(name: str, context: LoweringContext) -> Mnemonic:
    if context.is_local(name):
        return Mnemonic("LOAD_EAX_LOCAL", (context.stack_offset(name),))
    if context.is_parameter(name):
        return Mnemonic("LOAD_EAX_REF_PARAM", (context.stack_offset(name),))
    context.variable(name)
    return Mnemonic("LOAD_EAX_VAR", (name,))


def _store_name(name: str, context: LoweringContext) -> Mnemonic:
    if context.is_local(name):
        return Mnemonic("STORE_EAX_LOCAL", (context.stack_offset(name),))
    if context.is_parameter(name):
        return Mnemonic("STORE_EAX_REF_PARAM", (context.stack_offset(name),))
    context.variable(name)
    return Mnemonic("STORE_EAX_VAR", (name,))


def _push_reference(name: str, context: LoweringContext) -> Mnemonic:
    if context.is_local(name):
        return Mnemonic("PUSH_LOCAL_REF", (context.stack_offset(name),))
    if context.is_parameter(name):
        return Mnemonic("PUSH_PARAM_REF", (context.stack_offset(name),))
    context.variable(name)
    return Mnemonic("PUSH_GLOBAL_REF", (name,))


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
        if mnemonic.op == "ENTER_FRAME":
            return 3 + (6 if int(mnemonic.args[0]) else 0)
        return {
            "COMMENT": 0,
            "LABEL": 0,
            "MOV_EAX_IMM": 5,
            "LOAD_EAX_VAR": 5,
            "STORE_EAX_VAR": 5,
            "LOAD_EAX_LOCAL": 3,
            "STORE_EAX_LOCAL": 3,
            "LOAD_EAX_REF_PARAM": 5,
            "STORE_EAX_REF_PARAM": 5,
            "PUSH_GLOBAL_REF": 5,
            "PUSH_LOCAL_REF": 4,
            "PUSH_PARAM_REF": 3,
            "PUSH_VALUE_TEMP": 1,
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
            "CALL_PROC": 5,
            "CLEAN_ARGS": 3,
            "LEAVE_RET": 4,
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
        if op == "LOAD_EAX_LOCAL":
            return b"\x8B\x45" + struct.pack("b", int(mnemonic.args[0]))
        if op == "STORE_EAX_LOCAL":
            return b"\x89\x45" + struct.pack("b", int(mnemonic.args[0]))
        if op == "LOAD_EAX_REF_PARAM":
            return b"\x8B\x4D" + struct.pack("b", int(mnemonic.args[0])) + b"\x8B\x01"
        if op == "STORE_EAX_REF_PARAM":
            return b"\x8B\x4D" + struct.pack("b", int(mnemonic.args[0])) + b"\x89\x01"
        if op == "PUSH_GLOBAL_REF":
            return b"\x68" + struct.pack("<I", self._var_addr(str(mnemonic.args[0])))
        if op == "PUSH_LOCAL_REF":
            return b"\x8D\x45" + struct.pack("b", int(mnemonic.args[0])) + b"\x50"
        if op == "PUSH_PARAM_REF":
            return b"\xFF\x75" + struct.pack("b", int(mnemonic.args[0]))
        if op == "PUSH_VALUE_TEMP":
            return b"\x50"
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
        if op == "CALL_PROC":
            label = str(mnemonic.args[0])
            rel = labels[label] - (offset + 5)
            return b"\xE8" + struct.pack("<i", rel)
        if op == "CLEAN_ARGS":
            return b"\x83\xC4" + struct.pack("B", int(mnemonic.args[0]) & 0xFF)
        if op == "ENTER_FRAME":
            local_bytes = int(mnemonic.args[0])
            code = b"\x55\x89\xE5"
            if local_bytes:
                code += b"\x81\xEC" + struct.pack("<I", local_bytes)
            return code
        if op == "LEAVE_RET":
            return b"\xC9\xC2" + struct.pack("<H", int(mnemonic.args[0]) & 0xFFFF)
        if op == "EXIT_ZERO":
            return b"\x31\xC0\xC3"
        raise ValueError(f"Unsupported x586 mnemonic: {mnemonic}")

    def _jfalse_opcode(self, operator: str) -> bytes:
        return {
            "=": b"\x0F\x85",
            "^=": b"\x0F\x84",
            "¬=": b"\x0F\x84",
            "~=": b"\x0F\x84",
            "<>": b"\x0F\x84",
            "<": b"\x0F\x8D",
            "<=": b"\x0F\x8F",
            ">": b"\x0F\x8E",
            ">=": b"\x0F\x8C",
            "=>": b"\x0F\x8C",
        }[operator]


class X8664MnemonicAssembler:
    def __init__(self, image_base: int, code_rva: int, data: bytes, variables: dict[str, int], macos: bool = False, windows: bool = False) -> None:
        self.image_base = image_base
        self.code_rva = code_rva
        self.data = data
        self.variables = variables
        self.macos = macos
        self.windows = windows

    def assemble(self, mnemonics: list[Mnemonic]) -> bytes:
        # Small source-driven encoder: it preserves immediate arithmetic from the AST,
        # then exits through the platform ABI.
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
        if self.windows:
            out.extend(b"\x31\xC0\xC3")
            return bytes(out)
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
