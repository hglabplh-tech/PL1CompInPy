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

    def open(self, descriptor: FileDescriptor) -> None:
        mode = "rb" if descriptor.mode == "INPUT" else "w+b" if descriptor.mode == "UPDATE" else "wb"
        self._open_files[descriptor.name] = descriptor.path.open(mode)

    def close(self, descriptor: FileDescriptor) -> None:
        handle = self._open_files.pop(descriptor.name, None)
        if handle:
            handle.close()

    def write_record(self, descriptor: FileDescriptor, data: bytes | str) -> None:
        handle = self._handle(descriptor)
        payload = data.encode("utf-8") if isinstance(data, str) else data
        if descriptor.text and not isinstance(data, bytes):
            payload = data.encode("utf-8")
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

    def read_record(self, descriptor: FileDescriptor) -> bytes | str:
        handle = self._handle(descriptor)
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
        return payload.decode("utf-8") if descriptor.text else payload

    def execute(self, statement: IOStatement, descriptors: dict[str, FileDescriptor], variables: dict[str, object] | None = None) -> None:
        variables = variables if variables is not None else {}
        if statement.file_name is None:
            raise FileRuntimeError(f"{statement.operation} requires FILE(name)")
        descriptor = descriptors[statement.file_name]
        if statement.operation == "OPEN":
            self.open(descriptor)
        elif statement.operation == "CLOSE":
            self.close(descriptor)
        elif statement.operation == "READ":
            if statement.target is None:
                raise FileRuntimeError("READ requires INTO(name)")
            variables[statement.target] = self.read_record(descriptor)
        elif statement.operation == "WRITE":
            self.write_record(descriptor, self._io_value(statement, variables))
        else:
            raise FileRuntimeError(f"Unsupported I/O operation: {statement.operation}")

    def _io_value(self, statement: IOStatement, variables: dict[str, object]) -> bytes | str:
        source = statement.source
        if isinstance(source, Identifier):
            value = variables.get(source.name, b"")
            return value if isinstance(value, (bytes, str)) else str(value)
        if isinstance(source, StringLiteral):
            return source.value
        if isinstance(source, NumberLiteral):
            return source.value
        return b""

    def _handle(self, descriptor: FileDescriptor) -> BinaryIO:
        try:
            return self._open_files[descriptor.name]
        except KeyError as exc:
            raise FileRuntimeError(f"File is not open: {descriptor.name}") from exc


__all__ = ["FileDescriptor", "FileRuntimeError", "StdioRuntime"]
