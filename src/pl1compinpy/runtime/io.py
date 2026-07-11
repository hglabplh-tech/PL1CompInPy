from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from ..core.ast import Declaration, Identifier, IOStatement, NumberLiteral, StringLiteral


class FileRuntimeError(ValueError):
    pass


@dataclass(frozen=True)
class FileDescriptor:
    name: str
    path: Path
    mode: str = "INPUT"
    organization: str = "RECORD"
    recfm: str = "UNIX"
    lrecl: int | None = None
    text: bool = False
    encoding: str = "utf-8"

    @classmethod
    def from_declaration(cls, declaration: Declaration, base_path: Path | None = None) -> "FileDescriptor":
        if not declaration.names:
            raise FileRuntimeError("FILE declaration needs a file name")
        name = declaration.names[0]
        options = declaration.file_options
        recfm = options.get("recfm", "UNIX").upper()
        lrecl = int(options["lrecl"]) if "lrecl" in options and options["lrecl"].isdigit() else None
        path = Path(options.get("path", name.lower()))
        if base_path and not path.is_absolute():
            path = base_path / path
        return cls(
            name=name,
            path=path,
            mode=options.get("mode", "INPUT").upper(),
            organization=options.get("organization", "RECORD").upper(),
            recfm=recfm,
            lrecl=lrecl,
            text=options.get("format", "BINARY").upper() == "TEXT",
        )


class StdioRuntime:
    def __init__(self) -> None:
        self._open_files: dict[str, BinaryIO] = {}
        self._last_record_start: dict[str, int] = {}

    def open(self, descriptor: FileDescriptor) -> None:
        descriptor.path.parent.mkdir(parents=True, exist_ok=True)
        if descriptor.mode == "INPUT":
            mode = "rb"
        elif descriptor.mode == "UPDATE":
            mode = "r+b" if descriptor.path.exists() else "w+b"
        elif descriptor.mode == "APPEND":
            mode = "r+b" if descriptor.path.exists() else "w+b"
        else:
            mode = "wb"
        self._open_files[descriptor.name] = descriptor.path.open(mode)
        if descriptor.mode == "APPEND":
            self._open_files[descriptor.name].seek(0, 2)

    def close(self, descriptor: FileDescriptor) -> None:
        handle = self._open_files.pop(descriptor.name, None)
        if handle:
            handle.close()
        self._last_record_start.pop(descriptor.name, None)

    def flush(self, descriptor: FileDescriptor) -> None:
        self._handle(descriptor).flush()

    def tell(self, descriptor: FileDescriptor) -> int:
        return self._handle(descriptor).tell()

    def seek(self, descriptor: FileDescriptor, offset: int, whence: int = 0) -> int:
        handle = self._handle(descriptor)
        return handle.seek(offset, whence)

    def delete(self, descriptor: FileDescriptor) -> None:
        self.close(descriptor)
        if descriptor.path.exists():
            descriptor.path.unlink()

    def write(self, descriptor: FileDescriptor, data: bytes | str | int | float, *, offset: int | None = None) -> None:
        if descriptor.organization == "STREAM" and descriptor.recfm not in {"F", "V"}:
            self.write_stream(descriptor, data, offset=offset)
        else:
            self.write_record(descriptor, data)

    def read(
        self,
        descriptor: FileDescriptor,
        *,
        size: int | None = None,
        offset: int | None = None,
        line: bool = False,
    ) -> bytes | str:
        if descriptor.organization == "STREAM" and descriptor.recfm not in {"F", "V"}:
            return self.read_stream(descriptor, size=size, offset=offset, line=line)
        return self.read_record(descriptor)

    def write_stream(self, descriptor: FileDescriptor, data: bytes | str | int | float, *, offset: int | None = None) -> None:
        handle = self._handle(descriptor)
        if offset is not None:
            handle.seek(offset)
        payload = self._payload(descriptor, data)
        handle.write(payload)
        if descriptor.text and not payload.endswith(b"\n"):
            handle.write(b"\n")

    def read_stream(
        self,
        descriptor: FileDescriptor,
        *,
        size: int | None = None,
        offset: int | None = None,
        line: bool = False,
    ) -> bytes | str:
        handle = self._handle(descriptor)
        if offset is not None:
            handle.seek(offset)
        if line or descriptor.text and size is None:
            payload = handle.readline().rstrip(b"\n")
        elif size is None:
            payload = handle.read()
        else:
            payload = handle.read(size)
        return payload.decode(descriptor.encoding) if descriptor.text else payload

    def write_record(self, descriptor: FileDescriptor, data: bytes | str | int | float) -> None:
        handle = self._handle(descriptor)
        payload = self._payload(descriptor, data)
        if descriptor.recfm == "V":
            if len(payload) > 0xFFFF:
                raise FileRuntimeError("V record exceeds two-byte length prefix")
            handle.write(len(payload).to_bytes(2, "big"))
            handle.write(payload)
        elif descriptor.recfm == "F":
            if descriptor.lrecl is None:
                raise FileRuntimeError("F record requires LRECL")
            if len(payload) > descriptor.lrecl:
                payload = payload[: descriptor.lrecl]
            pad = b" " if descriptor.text else b"\0"
            handle.write(payload.ljust(descriptor.lrecl, pad))
        else:
            handle.write(payload)
            if descriptor.text:
                handle.write(b"\n")

    def rewrite_record(self, descriptor: FileDescriptor, data: bytes | str | int | float, *, offset: int | None = None) -> None:
        handle = self._handle(descriptor)
        if offset is None:
            offset = self._last_record_start.get(descriptor.name)
        if offset is None:
            raise FileRuntimeError("REWRITE requires a prior READ or an explicit OFFSET/POSITION/RBA")
        handle.seek(offset)
        self.write_record(descriptor, data)

    def read_record(self, descriptor: FileDescriptor) -> bytes | str:
        handle = self._handle(descriptor)
        self._last_record_start[descriptor.name] = handle.tell()
        if descriptor.recfm == "V":
            length_bytes = handle.read(2)
            if not length_bytes:
                return "" if descriptor.text else b""
            if len(length_bytes) != 2:
                raise FileRuntimeError("Short V record length prefix")
            payload = handle.read(int.from_bytes(length_bytes, "big"))
        elif descriptor.recfm == "F":
            if descriptor.lrecl is None:
                raise FileRuntimeError("F record requires LRECL")
            payload = handle.read(descriptor.lrecl)
        else:
            payload = handle.readline() if descriptor.text else handle.read()
            if descriptor.text:
                payload = payload.rstrip(b"\n")
        return payload.decode(descriptor.encoding) if descriptor.text else payload

    def execute(self, statement: IOStatement, descriptors: dict[str, FileDescriptor], variables: dict[str, object] | None = None) -> None:
        variables = variables if variables is not None else {}
        if statement.file_name is None:
            raise FileRuntimeError(f"{statement.operation} requires FILE(name)")
        descriptor = descriptors[statement.file_name]
        offset = self._optional_int(statement, variables, "offset", "position", "rba")
        if statement.operation == "OPEN":
            self.open(descriptor)
        elif statement.operation == "CLOSE":
            self.close(descriptor)
        elif statement.operation == "READ":
            if statement.target is None:
                raise FileRuntimeError("READ requires INTO(name)")
            size = self._optional_int(statement, variables, "size", "length", "count")
            variables[statement.target] = self.read(descriptor, size=size, offset=offset, line="line" in statement.options)
        elif statement.operation == "WRITE":
            self.write(descriptor, self._io_value(statement, variables), offset=offset)
        elif statement.operation == "REWRITE":
            self.rewrite_record(descriptor, self._io_value(statement, variables), offset=offset)
        elif statement.operation == "LOCATE":
            target = statement.target
            if target:
                variables[target] = self.tell(descriptor)
        elif statement.operation == "DELETE":
            self.delete(descriptor)
        else:
            raise FileRuntimeError(f"Unsupported I/O operation: {statement.operation}")

    def _io_value(self, statement: IOStatement, variables: dict[str, object]) -> bytes | str | int | float:
        source = statement.source
        if isinstance(source, Identifier):
            value = variables.get(source.name, b"")
            return value if isinstance(value, (bytes, str, int, float)) else str(value)
        if isinstance(source, StringLiteral):
            return source.value
        if isinstance(source, NumberLiteral):
            return source.value
        return b""

    def _optional_int(self, statement: IOStatement, variables: dict[str, object], *names: str) -> int | None:
        for name in names:
            expression = statement.options.get(name)
            if expression is None:
                continue
            value = self._expression_value(expression, variables)
            if value is None:
                return None
            return int(value)
        return None

    def _expression_value(self, expression: object, variables: dict[str, object]) -> object:
        if isinstance(expression, Identifier):
            return variables.get(expression.name)
        if isinstance(expression, StringLiteral):
            return expression.value
        if isinstance(expression, NumberLiteral):
            return expression.value
        return None

    def _payload(self, descriptor: FileDescriptor, data: bytes | str | int | float) -> bytes:
        if isinstance(data, bytes):
            return data
        return str(data).encode(descriptor.encoding)

    def _handle(self, descriptor: FileDescriptor) -> BinaryIO:
        try:
            return self._open_files[descriptor.name]
        except KeyError as exc:
            raise FileRuntimeError(f"File is not open: {descriptor.name}") from exc


__all__ = ["FileDescriptor", "FileRuntimeError", "StdioRuntime"]
