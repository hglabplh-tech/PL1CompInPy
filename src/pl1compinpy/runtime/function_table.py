from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..core.ast import Call, Declaration, Identifier, LabelledStatement, Procedure, Program, RawStatement, SelectStatement, Statement


class FunctionTableError(ValueError):
    pass


@dataclass(frozen=True)
class ParameterDescriptor:
    name: str
    type_name: str = "ANY"
    mode: str = "reference"
    optional: bool = False


@dataclass(frozen=True)
class FunctionDescriptor:
    name: str
    pointer: Callable[..., Any] | Procedure | str
    parameters: tuple[ParameterDescriptor, ...] = ()
    returns: str | None = None
    default_mode: str = "reference"
    source: str = "runtime"
    variadic: bool = False
    requires_declaration: bool = False

    @property
    def normalized_name(self) -> str:
        return self.name.upper()


@dataclass
class FunctionTable:
    functions: dict[str, FunctionDescriptor] = field(default_factory=dict)
    declared_builtins: set[str] = field(default_factory=set)

    def add_function(self, descriptor: FunctionDescriptor) -> FunctionDescriptor:
        self.functions[descriptor.normalized_name] = descriptor
        return descriptor

    def add_runtime(
        self,
        name: str,
        pointer: Callable[..., Any] | str,
        parameters: list[ParameterDescriptor] | None = None,
        returns: str | None = None,
        *,
        default_mode: str = "reference",
        variadic: bool = False,
    ) -> FunctionDescriptor:
        return self.add_function(
            FunctionDescriptor(
                name,
                pointer,
                tuple(parameters or ()),
                returns,
                default_mode=default_mode,
                source="runtime",
                variadic=variadic,
            )
        )

    def add_builtin(
        self,
        name: str,
        pointer: Callable[..., Any] | str,
        parameters: list[ParameterDescriptor] | None = None,
        returns: str | None = None,
        *,
        default_mode: str = "reference",
        variadic: bool = False,
    ) -> FunctionDescriptor:
        return self.add_function(
            FunctionDescriptor(
                name,
                pointer,
                tuple(parameters or ()),
                returns,
                default_mode=default_mode,
                source="builtin",
                variadic=variadic,
                requires_declaration=True,
            )
        )

    def add_procedure(self, name: str, procedure: Procedure) -> FunctionDescriptor:
        parameters = tuple(ParameterDescriptor(parameter, mode="reference") for parameter in procedure.parameters)
        return self.add_function(
            FunctionDescriptor(
                name,
                procedure,
                parameters,
                returns=procedure.returns,
                default_mode="reference",
                source="dynamic",
            )
        )

    def merge(self, other: "FunctionTable") -> "FunctionTable":
        merged = FunctionTable(dict(self.functions), set(self.declared_builtins))
        merged.functions.update(other.functions)
        merged.declared_builtins.update(other.declared_builtins)
        return merged

    def declare_builtin(self, name: str) -> None:
        self.declared_builtins.add(name.upper())

    def get(self, name: str) -> FunctionDescriptor:
        try:
            return self.functions[name.upper()]
        except KeyError as exc:
            raise FunctionTableError(f"Unknown function: {name}") from exc

    def validate_call(self, call: Call) -> FunctionDescriptor:
        descriptor = self.get(call.name)
        if descriptor.requires_declaration and descriptor.normalized_name not in self.declared_builtins:
            raise FunctionTableError(f"Builtin function {call.name} must be declared with BUILTIN before use")
        required = [parameter for parameter in descriptor.parameters if not parameter.optional]
        if not descriptor.variadic and not (len(required) <= len(call.arguments) <= len(descriptor.parameters)):
            raise FunctionTableError(
                f"CALL {call.name} expects {len(required)}"
                + (f"..{len(descriptor.parameters)}" if len(required) != len(descriptor.parameters) else "")
                + f" arguments, got {len(call.arguments)}"
            )
        if call.mode == "name":
            self._validate_by_name(call, descriptor)
        return descriptor

    def call(self, name: str, *arguments: Any, mode: str = "reference", **keyword_arguments: Any) -> Any:
        descriptor = self.get(name)
        synthetic = Call(name, [], mode)
        if not descriptor.variadic and len(arguments) + len(keyword_arguments) > len(descriptor.parameters):
            raise FunctionTableError(f"CALL {name} received too many arguments")
        self.validate_call(synthetic if descriptor.variadic else Call(name, [Identifier(parameter.name) for parameter in descriptor.parameters[: len(arguments)]], mode))
        if not callable(descriptor.pointer):
            raise FunctionTableError(f"Function {name} has no executable runtime pointer")
        return descriptor.pointer(*arguments, **keyword_arguments)

    def _validate_by_name(self, call: Call, descriptor: FunctionDescriptor) -> None:
        named_arguments = {getattr(argument, "name", "").upper() for argument in call.arguments}
        required_names = {parameter.name.upper() for parameter in descriptor.parameters if not parameter.optional}
        if not required_names.issubset(named_arguments):
            raise FunctionTableError(f"CALL {call.name} BY NAME arguments do not match function table parameters")


def build_dynamic_function_table(program: Program) -> FunctionTable:
    table = FunctionTable()
    for statement in program.statements:
        _add_statement_function(table, statement)
    return table


def declare_program_builtins(program: Program, table: FunctionTable) -> FunctionTable:
    for statement in program.statements:
        _declare_statement_builtins(statement, table)
    return table


def declared_builtins(program: Program) -> set[str]:
    table = FunctionTable()
    declare_program_builtins(program, table)
    return table.declared_builtins


def _declare_statement_builtins(statement: Statement | None, table: FunctionTable) -> None:
    from ..core.ast import DoGroup, IfStatement

    if statement is None:
        return
    if isinstance(statement, Declaration) and any(attribute.upper() == "BUILTIN" for attribute in statement.attributes):
        for name in statement.names:
            table.declare_builtin(name)
    elif isinstance(statement, RawStatement) and statement.keyword.upper() == "BUILTIN":
        for token in statement.tokens:
            if token.isidentifier():
                table.declare_builtin(token)
    elif isinstance(statement, Procedure):
        for child in statement.body:
            _declare_statement_builtins(child, table)
    elif isinstance(statement, LabelledStatement):
        _declare_statement_builtins(statement.statement, table)
    elif isinstance(statement, DoGroup):
        for child in statement.body:
            _declare_statement_builtins(child, table)
    elif isinstance(statement, IfStatement):
        _declare_statement_builtins(statement.then_branch, table)
        _declare_statement_builtins(statement.else_branch, table)
    elif isinstance(statement, SelectStatement):
        for branch in statement.when_branches:
            _declare_statement_builtins(branch.statement, table)
        _declare_statement_builtins(statement.otherwise, table)


def _add_statement_function(table: FunctionTable, statement: Statement) -> None:
    if isinstance(statement, Procedure) and statement.name:
        table.add_procedure(statement.name, statement)
    elif isinstance(statement, LabelledStatement) and isinstance(statement.statement, Procedure):
        procedure = statement.statement
        table.add_procedure(procedure.name or statement.label, procedure)


def validate_program_calls(program: Program, table: FunctionTable) -> None:
    for statement in program.statements:
        _validate_statement_calls(statement, table)


def _validate_statement_calls(statement: Statement | None, table: FunctionTable) -> None:
    from ..core.ast import DoGroup, IfStatement, IOStatement, RawStatement

    if statement is None or isinstance(statement, (IOStatement, RawStatement)):
        return
    if isinstance(statement, Call):
        table.validate_call(statement)
    elif isinstance(statement, Procedure):
        for child in statement.body:
            _validate_statement_calls(child, table)
    elif isinstance(statement, LabelledStatement):
        _validate_statement_calls(statement.statement, table)
    elif isinstance(statement, DoGroup):
        for child in statement.body:
            _validate_statement_calls(child, table)
    elif isinstance(statement, IfStatement):
        _validate_statement_calls(statement.then_branch, table)
        _validate_statement_calls(statement.else_branch, table)
    elif isinstance(statement, SelectStatement):
        for branch in statement.when_branches:
            _validate_statement_calls(branch.statement, table)
        _validate_statement_calls(statement.otherwise, table)


def runtime_function_table() -> FunctionTable:
    table = FunctionTable()
    any_ref = lambda name: ParameterDescriptor(name, "ANY", "reference")
    any_value = lambda name: ParameterDescriptor(name, "ANY", "value")
    file_ref = lambda name="FILE": ParameterDescriptor(name, "FILE", "reference")
    socket_ref = lambda name="SOCKET": ParameterDescriptor(name, "SOCKET", "reference")

    table.add_runtime("DISPLAY", "runtime.display", [any_value("VALUE")], variadic=True)
    table.add_runtime("PRINT", "runtime.print", [any_value("VALUE")], variadic=True)
    table.add_runtime("PUT", "runtime.put", [any_value("VALUE")], variadic=True)
    table.add_runtime("GET", "runtime.get", [any_ref("TARGET")], variadic=True)
    table.add_builtin("SUBSTR", "builtins.substr", [ParameterDescriptor("S", "CHARACTER"), ParameterDescriptor("START", "FIXED BIN"), ParameterDescriptor("COUNT", "FIXED BIN", optional=True)], returns="CHARACTER")
    table.add_builtin("LENGTH", "builtins.length", [ParameterDescriptor("VALUE", "ANY")], returns="FIXED BIN")
    table.add_builtin("INDEX", "builtins.index", [ParameterDescriptor("SOURCE", "CHARACTER"), ParameterDescriptor("NEEDLE", "CHARACTER")], returns="FIXED BIN")
    for name in ("ABS", "SIGN", "CEIL", "FLOOR", "SQRT", "EXP", "LOG", "SIN", "COS", "TAN", "REAL", "IMAG", "CONJG"):
        table.add_builtin(name, f"builtins.{name.lower()}", [ParameterDescriptor("VALUE", "ANY")], returns="ANY")
    for name in ("MIN", "MAX"):
        table.add_builtin(name, f"builtins.{name.lower()}", [ParameterDescriptor("VALUE", "ANY")], returns="ANY", variadic=True)
    table.add_builtin("MOD", "builtins.mod", [ParameterDescriptor("LEFT", "ANY"), ParameterDescriptor("RIGHT", "ANY")], returns="FIXED BIN")
    table.add_builtin("TRUNC", "builtins.trunc", [ParameterDescriptor("VALUE", "ANY"), ParameterDescriptor("SCALE", "FIXED BIN", optional=True)], returns="FIXED DEC")
    table.add_builtin("ROUND", "builtins.round", [ParameterDescriptor("VALUE", "ANY"), ParameterDescriptor("SCALE", "FIXED BIN", optional=True)], returns="FIXED DEC")

    for name in ("ALLOCATE", "ALLOC"):
        table.add_runtime(name, "runtime.heap.allocate", [ParameterDescriptor("SIZE", "FIXED BIN")], returns="POINTER")
    table.add_runtime("FREE", "runtime.heap.free", [ParameterDescriptor("POINTER", "POINTER")])

    table.add_runtime("OPEN", "runtime.io.open", [file_ref()])
    table.add_runtime("CLOSE", "runtime.io.close", [file_ref()])
    table.add_runtime("READ", "runtime.io.read", [file_ref(), any_ref("TARGET")])
    table.add_runtime("WRITE", "runtime.io.write", [file_ref(), any_value("SOURCE")])
    table.add_runtime("REWRITE", "runtime.io.rewrite", [file_ref(), any_value("SOURCE")])
    table.add_runtime("LOCATE", "runtime.io.locate", [file_ref()], returns="POINTER")
    table.add_runtime("DELETE", "runtime.io.delete", [file_ref()])

    table.add_runtime("VSAM_OPEN", "runtime.vsam.open", [file_ref("VSAMFILE")])
    table.add_runtime("VSAM_CLOSE", "runtime.vsam.close", [file_ref("VSAMFILE")])
    table.add_runtime("VSAM_READ", "runtime.vsam.read", [file_ref("VSAMFILE"), any_ref("TARGET")])
    table.add_runtime("VSAM_WRITE", "runtime.vsam.write", [file_ref("VSAMFILE"), any_value("SOURCE")])

    table.add_runtime("TCPIP", "runtime.socket.open", [socket_ref()], returns="SOCKET")
    table.add_runtime("TCPIP_OPEN", "runtime.socket.open", [socket_ref()], returns="SOCKET")
    table.add_runtime("TCPIP_CONNECT", "runtime.socket.connect", [socket_ref()], returns="SOCKET")
    table.add_runtime("TCPIP_ACCEPT", "runtime.socket.accept", [socket_ref()], returns="SOCKET")
    table.add_runtime("TCPIP_SEND", "runtime.socket.send", [socket_ref(), any_value("DATA")])
    table.add_runtime("TCPIP_RECEIVE", "runtime.socket.receive", [socket_ref(), ParameterDescriptor("SIZE", "FIXED BIN", optional=True)], returns="CHARACTER")
    table.add_runtime("TCPIP_CLOSE", "runtime.socket.close", [socket_ref()])
    table.add_runtime("SOCKET_OPEN", "runtime.socket_stream.open", [socket_ref()], returns="SOCKET")
    table.add_runtime("SOCKET_READ", "runtime.socket_stream.read_record", [socket_ref(), any_ref("TARGET")])
    table.add_runtime("SOCKET_WRITE", "runtime.socket_stream.write_record", [socket_ref(), any_value("SOURCE")])
    table.add_runtime("SOCKET_CLOSE", "runtime.socket_stream.close", [socket_ref()])
    table.add_runtime("SSL_SOCKET", "runtime.socket.ssl", [socket_ref()], returns="SOCKET")
    table.add_runtime("TLS_SOCKET", "runtime.socket.tls", [socket_ref()], returns="SOCKET")

    return table


RUNTIME_FUNCTION_TABLE = runtime_function_table()


__all__ = [
    "FunctionDescriptor",
    "FunctionTable",
    "FunctionTableError",
    "ParameterDescriptor",
    "RUNTIME_FUNCTION_TABLE",
    "build_dynamic_function_table",
    "declare_program_builtins",
    "declared_builtins",
    "runtime_function_table",
    "validate_program_calls",
]
