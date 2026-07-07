from __future__ import annotations

from dataclasses import dataclass, field
import struct

from ..core.ast import (
    Assignment,
    BinaryExpression,
    Call,
    Declaration,
    FieldReference,
    Identifier,
    LabelledStatement,
    NumberLiteral,
    Procedure,
    Program,
    RawStatement,
    StructureField,
    main_procedure_name,
    procedure_entry_name,
)
from .runtime_link import runtime_linkage


JAVA_17_MAJOR_VERSION = 61


@dataclass
class ConstantPool:
    entries: list[bytes] = field(default_factory=list)
    index: dict[tuple[object, ...], int] = field(default_factory=dict)

    def utf8(self, value: str) -> int:
        key = ("utf8", value)
        if key not in self.index:
            encoded = value.encode("utf-8")
            self.index[key] = self._add(b"\x01" + struct.pack(">H", len(encoded)) + encoded)
        return self.index[key]

    def class_info(self, name: str) -> int:
        key = ("class", name)
        if key not in self.index:
            self.index[key] = self._add(b"\x07" + struct.pack(">H", self.utf8(name)))
        return self.index[key]

    def name_and_type(self, name: str, descriptor: str) -> int:
        key = ("name_type", name, descriptor)
        if key not in self.index:
            self.index[key] = self._add(b"\x0c" + struct.pack(">HH", self.utf8(name), self.utf8(descriptor)))
        return self.index[key]

    def method_ref(self, owner: str, name: str, descriptor: str) -> int:
        key = ("method_ref", owner, name, descriptor)
        if key not in self.index:
            self.index[key] = self._add(
                b"\x0a" + struct.pack(">HH", self.class_info(owner), self.name_and_type(name, descriptor))
            )
        return self.index[key]

    def _add(self, entry: bytes) -> int:
        self.entries.append(entry)
        return len(self.entries)

    def bytes(self) -> bytes:
        return struct.pack(">H", len(self.entries) + 1) + b"".join(self.entries)


@dataclass
class JVMProcedure:
    name: str
    parameters: list[str]
    returns: str | None
    code: bytes
    max_stack: int = 16
    max_locals: int = 16

    @property
    def descriptor(self) -> str:
        return "(" + ("I" * len(self.parameters)) + ")" + ("I" if self.returns else "V")


class JVMClassFileEmitter:
    def emit(self, program: Program, class_name: str = "PL1Program") -> bytes:
        linkage = runtime_linkage("jvm-bytecode")
        runtime_type = linkage.managed_type or "pl1compinpy/runtime/PL1Runtime"
        procedures = self._procedures(program)
        main_name = self._main_name(program)
        pool = ConstantPool()

        this_class = pool.class_info(class_name)
        super_class = pool.class_info("java/lang/Object")
        code_name = pool.utf8("Code")
        pool.method_ref("java/lang/Object", "<init>", "()V")
        for procedure in procedures:
            pool.utf8(procedure.name)
            pool.utf8(procedure.descriptor)
        if main_name:
            pool.utf8("main")
            pool.utf8("([Ljava/lang/String;)V")
            pool.method_ref(runtime_type, linkage.startup_symbol, "()V")
            pool.method_ref(runtime_type, linkage.shutdown_symbol, "()V")
            target = next((procedure for procedure in procedures if procedure.name == main_name), None)
            if target:
                pool.method_ref(class_name, target.name, target.descriptor)

        methods = [self._method(pool, "<init>", "()V", self._constructor_code(pool), max_stack=1, max_locals=1)]
        methods.extend(self._method(pool, procedure.name, procedure.descriptor, procedure.code, procedure.max_stack, procedure.max_locals) for procedure in procedures)
        if main_name:
            target = next((procedure for procedure in procedures if procedure.name == main_name), None)
            if target:
                main_code = b"\xb8" + struct.pack(">H", pool.method_ref(runtime_type, linkage.startup_symbol, "()V"))
                for _ in target.parameters:
                    main_code += self._iconst(0)
                main_code += b"\xb8" + struct.pack(">H", pool.method_ref(class_name, target.name, target.descriptor))
                if target.returns:
                    main_code += b"\x57"
                main_code += b"\xb8" + struct.pack(">H", pool.method_ref(runtime_type, linkage.shutdown_symbol, "()V"))
                main_code += b"\xb1"
                methods.append(self._method(pool, "main", "([Ljava/lang/String;)V", main_code, max_stack=1, max_locals=1))

        return b"".join(
            [
                b"\xca\xfe\xba\xbe",
                struct.pack(">HH", 0, JAVA_17_MAJOR_VERSION),
                pool.bytes(),
                struct.pack(">HHH", 0x0021, this_class, super_class),
                struct.pack(">H", 0),
                struct.pack(">H", 0),
                struct.pack(">H", len(methods)),
                b"".join(methods),
                struct.pack(">H", 0),
            ]
        )

    def _procedures(self, program: Program) -> list[JVMProcedure]:
        results: list[JVMProcedure] = []
        for statement in program.statements:
            procedure = statement.statement if isinstance(statement, LabelledStatement) and isinstance(statement.statement, Procedure) else statement
            if isinstance(procedure, Procedure):
                name = procedure_entry_name(statement, "anonymous") or "anonymous"
                results.append(self._procedure(name, procedure))
        return results

    def _procedure(self, name: str, procedure: Procedure) -> JVMProcedure:
        locals_map = {parameter: index for index, parameter in enumerate(procedure.parameters)}
        code = bytearray()
        returned = False
        for statement in procedure.body:
            if isinstance(statement, Declaration):
                for var_name in _declaration_storage_names(statement):
                    if var_name not in locals_map:
                        locals_map[var_name] = len(locals_map)
                        code.extend(self._iconst(0))
                        code.extend(self._istore(locals_map[var_name]))
            elif isinstance(statement, Assignment):
                code.extend(self._expression(statement.expression, locals_map))
                code.extend(self._istore(locals_map.setdefault(statement.target, len(locals_map))))
            elif isinstance(statement, RawStatement) and statement.keyword.upper() == "RETURN":
                code.extend(self._return_value(statement, locals_map))
                code.append(0xAC)
                returned = True
            elif isinstance(statement, Call):
                # Calls are emitted by the textual backend. The binary backend keeps
                # this first classfile pass conservative unless the callee signature is known.
                pass
        if not returned:
            if procedure.returns:
                code.extend(self._iconst(0))
                code.append(0xAC)
            else:
                code.append(0xB1)
        return JVMProcedure(name, procedure.parameters, procedure.returns, bytes(code), max_locals=max(len(locals_map), 1))

    def _return_value(self, statement: RawStatement, locals_map: dict[str, int]) -> bytes:
        if statement.tokens and statement.tokens[0].isdigit():
            return self._iconst(int(statement.tokens[0]))
        if statement.tokens and statement.tokens[0] in locals_map:
            return self._iload(locals_map[statement.tokens[0]])
        return self._iconst(0)

    def _expression(self, expression: object, locals_map: dict[str, int]) -> bytes:
        if isinstance(expression, NumberLiteral):
            return self._iconst(int(float(expression.value)))
        if isinstance(expression, Identifier):
            return self._iload(locals_map.setdefault(expression.name, len(locals_map)))
        if isinstance(expression, FieldReference):
            return self._iload(locals_map.setdefault(expression.name, len(locals_map)))
        if isinstance(expression, BinaryExpression):
            opcode = {"+": 0x60, "-": 0x64, "*": 0x68, "/": 0x6C}.get(expression.operator, 0x60)
            return self._expression(expression.left, locals_map) + self._expression(expression.right, locals_map) + bytes([opcode])
        return self._iconst(0)

    def _constructor_code(self, pool: ConstantPool) -> bytes:
        return b"\x2a\xb7" + struct.pack(">H", pool.method_ref("java/lang/Object", "<init>", "()V")) + b"\xb1"

    def _method(self, pool: ConstantPool, name: str, descriptor: str, code: bytes, max_stack: int, max_locals: int) -> bytes:
        code_attribute = b"".join(
            [
                struct.pack(">HHI", max_stack, max_locals, len(code)),
                code,
                struct.pack(">H", 0),
                struct.pack(">H", 0),
            ]
        )
        return b"".join(
            [
                struct.pack(">HHHH", 0x0009 if name != "<init>" else 0x0001, pool.utf8(name), pool.utf8(descriptor), 1),
                struct.pack(">HI", pool.utf8("Code"), len(code_attribute)),
                code_attribute,
            ]
        )

    def _iconst(self, value: int) -> bytes:
        if value == -1:
            return b"\x02"
        if 0 <= value <= 5:
            return bytes([0x03 + value])
        if -128 <= value <= 127:
            return b"\x10" + struct.pack("b", value)
        return b"\x10\x00"

    def _iload(self, index: int) -> bytes:
        return bytes([0x1A + index]) if 0 <= index <= 3 else b"\x15" + bytes([index])

    def _istore(self, index: int) -> bytes:
        return bytes([0x3B + index]) if 0 <= index <= 3 else b"\x36" + bytes([index])

    def _main_name(self, program: Program) -> str | None:
        return main_procedure_name(program)


def emit_jvm_class(program: Program, class_name: str = "PL1Program") -> bytes:
    return JVMClassFileEmitter().emit(program, class_name)


def emit_jvm_classes(program: Program, class_name: str = "PL1Program") -> dict[str, bytes]:
    return {f"{class_name}.class": emit_jvm_class(program, class_name)}


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
