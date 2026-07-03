from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..core.ast import Declaration, Expression, Identifier, IOStatement, NumberLiteral, StringLiteral
from .catalog import VSAMCatalog, VSAMError, VSAMType


@dataclass(frozen=True)
class VSAMFileDescriptor:
    name: str
    path: Path
    organization: VSAMType = VSAMType.KSDS
    mode: str = "INPUT"
    key_offset: int = 0
    key_length: int = 0
    record_length: int | None = None

    @classmethod
    def from_declaration(cls, declaration: Declaration, base_path: Path | None = None) -> "VSAMFileDescriptor":
        if not declaration.names:
            raise VSAMError("VSAM FILE declaration needs a file name")
        options = declaration.file_options
        if "vsam" not in options:
            raise VSAMError("VSAM FILE declaration needs ENVIRONMENT(VSAM(...))")
        name = declaration.names[0]
        path = Path(options.get("path", name.lower()))
        if base_path and not path.is_absolute():
            path = base_path / path
        record_length = options.get("recordlength") or options.get("lrecl")
        return cls(
            name=name,
            path=path,
            organization=VSAMType(options["vsam"]),
            mode=options.get("mode", "INPUT").upper(),
            key_offset=int(options.get("keyoffset", "0")),
            key_length=int(options.get("keylength", "0")),
            record_length=int(record_length) if record_length and str(record_length).isdigit() else None,
        )


class VSAMRuntime:
    def __init__(self) -> None:
        self._open_catalogs: dict[str, VSAMCatalog] = {}

    def open(self, descriptor: VSAMFileDescriptor) -> None:
        if descriptor.mode in {"OUTPUT", "UPDATE"} or not (descriptor.path / "catalog.json").exists():
            catalog = VSAMCatalog.define(
                descriptor.path,
                descriptor.name,
                descriptor.organization,
                key_offset=descriptor.key_offset,
                key_length=descriptor.key_length,
                record_length=descriptor.record_length,
            )
        else:
            catalog = VSAMCatalog(descriptor.path)
        self._open_catalogs[descriptor.name] = catalog

    def close(self, descriptor: VSAMFileDescriptor) -> None:
        self._open_catalogs.pop(descriptor.name, None)

    def write_record(
        self,
        descriptor: VSAMFileDescriptor,
        data: bytes | str,
        *,
        key: bytes | str | None = None,
        rrn: int | None = None,
        rba: int | None = None,
    ) -> int:
        payload = data.encode("utf-8") if isinstance(data, str) else data
        return self._catalog(descriptor).write(payload, key=key, rrn=rrn, rba=rba)

    def read_record(
        self,
        descriptor: VSAMFileDescriptor,
        *,
        key: bytes | str | None = None,
        rrn: int | None = None,
        rba: int | None = None,
        length: int | None = None,
    ) -> bytes:
        return self._catalog(descriptor).read(key=key, rrn=rrn, rba=rba, length=length)

    def execute(self, statement: IOStatement, descriptors: dict[str, VSAMFileDescriptor], variables: dict[str, object] | None = None) -> None:
        variables = variables if variables is not None else {}
        if statement.file_name is None:
            raise VSAMError(f"{statement.operation} requires FILE(name)")
        descriptor = descriptors[statement.file_name]
        if statement.operation == "OPEN":
            self.open(descriptor)
        elif statement.operation == "CLOSE":
            self.close(descriptor)
        elif statement.operation == "WRITE":
            self.write_record(
                descriptor,
                self._value(statement.source, variables),
                key=self._optional_key(descriptor, statement.options.get("key"), variables),
                rrn=self._optional_int(statement.options.get("rrn"), variables),
                rba=self._optional_int(statement.options.get("rba"), variables),
            )
        elif statement.operation == "READ":
            if statement.target is None:
                raise VSAMError("VSAM READ requires INTO(name)")
            variables[statement.target] = self.read_record(
                descriptor,
                key=self._optional_key(descriptor, statement.options.get("key"), variables),
                rrn=self._optional_int(statement.options.get("rrn"), variables),
                rba=self._optional_int(statement.options.get("rba"), variables),
                length=self._optional_int(statement.options.get("length") or statement.options.get("count"), variables),
            )
        else:
            raise VSAMError(f"Unsupported VSAM I/O operation: {statement.operation}")

    def _catalog(self, descriptor: VSAMFileDescriptor) -> VSAMCatalog:
        try:
            return self._open_catalogs[descriptor.name]
        except KeyError as exc:
            raise VSAMError(f"VSAM file is not open: {descriptor.name}") from exc

    def _optional_value(self, expression: Expression | None, variables: dict[str, object]) -> bytes | str | None:
        if expression is None:
            return None
        value = self._value(expression, variables)
        return value if isinstance(value, (bytes, str)) else str(value)

    def _optional_key(self, descriptor: VSAMFileDescriptor, expression: Expression | None, variables: dict[str, object]) -> bytes | str | None:
        value = self._optional_value(expression, variables)
        if descriptor.organization == VSAMType.KSDS and isinstance(value, str):
            return value.encode("utf-8")
        return value

    def _optional_int(self, expression: Expression | None, variables: dict[str, object]) -> int | None:
        if expression is None:
            return None
        value = self._value(expression, variables)
        return int(value)

    def _value(self, expression: Expression | None, variables: dict[str, object]) -> object:
        if isinstance(expression, Identifier):
            return variables.get(expression.name, b"")
        if isinstance(expression, StringLiteral):
            return expression.value
        if isinstance(expression, NumberLiteral):
            return int(float(expression.value))
        return b""


__all__ = ["VSAMFileDescriptor", "VSAMRuntime"]
