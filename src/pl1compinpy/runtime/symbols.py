from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..core.ast import Declaration, LabelledStatement, Procedure, Program, Statement, StructureField, procedure_from_statement
from .types import PliType, PliTypeParser


class SymbolKind(str, Enum):
    VARIABLE = "variable"
    PARAMETER = "parameter"
    PROCEDURE = "procedure"
    STRUCTURE = "structure"
    FIELD = "field"
    LABEL = "label"
    BUILTIN = "builtin"


class StorageClass(str, Enum):
    AUTOMATIC = "automatic"
    STATIC = "static"
    BASED = "based"
    CONTROLLED = "controlled"
    PARAMETER = "parameter"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SourceLocation:
    file: str | None = None
    line: int | None = None
    column: int | None = None


@dataclass
class Symbol:
    name: str
    kind: SymbolKind
    pli_type: PliType | None = None
    scope: str = "global"
    storage: StorageClass = StorageClass.UNKNOWN
    dimensions: tuple[int, ...] = ()
    based_on: str | None = None
    returns: PliType | None = None
    parameters: tuple[str, ...] = ()
    location: SourceLocation = field(default_factory=SourceLocation)
    metadata: dict[str, Any] = field(default_factory=dict)

    def debugger_record(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind.value,
            "type": self.pli_type.canonical() if self.pli_type else None,
            "scope": self.scope,
            "storage": self.storage.value,
            "dimensions": list(self.dimensions),
            "based_on": self.based_on,
            "returns": self.returns.canonical() if self.returns else None,
            "parameters": list(self.parameters),
            "location": {"file": self.location.file, "line": self.location.line, "column": self.location.column},
            "metadata": self.metadata.copy(),
        }


class SymbolTableError(ValueError):
    pass


class SymbolTable:
    def __init__(self) -> None:
        self.scopes: dict[str, dict[str, Symbol]] = {"global": {}}
        self.parents: dict[str, str | None] = {"global": None}

    def enter_scope(self, scope: str, parent: str = "global") -> None:
        self.scopes.setdefault(scope, {})
        self.parents.setdefault(scope, parent)

    def define(self, symbol: Symbol) -> Symbol:
        self.enter_scope(symbol.scope, self.parents.get(symbol.scope) or "global")
        key = symbol.name.upper()
        self.scopes[symbol.scope][key] = symbol
        return symbol

    def lookup(self, name: str, scope: str = "global") -> Symbol | None:
        key = name.upper()
        current: str | None = scope
        while current is not None:
            symbol = self.scopes.get(current, {}).get(key)
            if symbol is not None:
                return symbol
            current = self.parents.get(current)
        return None

    def symbols(self, scope: str | None = None) -> list[Symbol]:
        if scope is not None:
            return list(self.scopes.get(scope, {}).values())
        out: list[Symbol] = []
        for entries in self.scopes.values():
            out.extend(entries.values())
        return out

    def debugger_records(self) -> list[dict[str, Any]]:
        return [symbol.debugger_record() for symbol in self.symbols()]


class SymbolTableBuilder:
    def __init__(self) -> None:
        self.type_parser = PliTypeParser()
        self.table = SymbolTable()

    def build(self, program: Program) -> SymbolTable:
        for statement in program.statements:
            self._statement(statement, "global")
        return self.table

    def _statement(self, statement: Statement, scope: str) -> None:
        if isinstance(statement, LabelledStatement):
            self.table.define(Symbol(statement.label, SymbolKind.LABEL, scope=scope))
            procedure = procedure_from_statement(statement)
            if procedure:
                self._procedure(statement.label, procedure, scope)
            else:
                self._statement(statement.statement, scope)
            return
        if isinstance(statement, Declaration):
            self._declaration(statement, scope)
            return
        if isinstance(statement, Procedure):
            self._procedure("MAIN" if "MAIN" in statement.options else "ANONYMOUS", statement, scope)

    def _procedure(self, name: str, procedure: Procedure, parent_scope: str) -> None:
        proc_scope = name.upper()
        self.table.enter_scope(proc_scope, parent_scope)
        returns = self.type_parser.parse(procedure.returns) if procedure.returns else None
        self.table.define(Symbol(name, SymbolKind.PROCEDURE, scope=parent_scope, returns=returns, parameters=tuple(procedure.parameters), metadata={"options": list(procedure.options), "recursive": procedure.recursive}))
        for parameter in procedure.parameters:
            self.table.define(Symbol(parameter, SymbolKind.PARAMETER, scope=proc_scope, storage=StorageClass.PARAMETER))
        for nested in procedure.body:
            self._statement(nested, proc_scope)

    def _declaration(self, declaration: Declaration, scope: str) -> None:
        for name in declaration.names:
            name_key = name.upper()
            pli_type = self.type_parser.parse(declaration.attributes)
            storage = StorageClass.BASED if name_key in declaration.based_options else StorageClass.AUTOMATIC
            kind = SymbolKind.STRUCTURE if name_key in declaration.structures else SymbolKind.VARIABLE
            if name_key in declaration.pointer_names:
                pli_type = self.type_parser.parse("POINTER")
            if "BUILTIN" in {attribute.upper() for attribute in declaration.attributes}:
                kind = SymbolKind.BUILTIN
            self.table.define(
                Symbol(
                    name_key,
                    kind,
                    pli_type=pli_type,
                    scope=scope,
                    storage=storage,
                    dimensions=tuple(declaration.dimensions.get(name_key, ())),
                    based_on=declaration.based_options.get(name_key),
                    metadata={"attributes": list(declaration.attributes), "file_options": declaration.file_options.copy()},
                )
            )
        for structure in declaration.structures.values():
            self._structure_fields(structure, scope, structure.name.upper())

    def _structure_fields(self, field: StructureField, scope: str, root: str) -> None:
        for child in field.children:
            path = f"{root}.{child.name.upper()}"
            self.table.define(Symbol(path, SymbolKind.FIELD, pli_type=self.type_parser.parse(child.attributes), scope=scope, dimensions=tuple(child.dimensions), metadata={"level": child.level}))
            self._structure_fields(child, scope, path)


def build_symbol_table(program: Program) -> SymbolTable:
    return SymbolTableBuilder().build(program)


__all__ = [
    "SourceLocation",
    "StorageClass",
    "Symbol",
    "SymbolKind",
    "SymbolTable",
    "SymbolTableBuilder",
    "SymbolTableError",
    "build_symbol_table",
]
