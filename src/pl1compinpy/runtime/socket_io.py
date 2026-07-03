from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import socket
import ssl

from ..core.ast import IOStatement, Identifier, NumberLiteral, StringLiteral


class SocketRuntimeError(ValueError):
    pass


class SocketSecureMode(str, Enum):
    NONE = "NONE"
    SSL = "SSL"
    TLS = "TLS"


@dataclass(frozen=True)
class SocketDescriptor:
    name: str
    host: str = "127.0.0.1"
    port: int = 0
    mode: str = "CLIENT"
    secure: SocketSecureMode | str = SocketSecureMode.NONE
    server_hostname: str | None = None
    timeout: float | None = None
    cafile: str | None = None
    certfile: str | None = None
    keyfile: str | None = None
    verify: bool = True

    @classmethod
    def tcp_client(cls, name: str, host: str, port: int, timeout: float | None = None) -> "SocketDescriptor":
        return cls(name=name, host=host, port=port, mode="CLIENT", timeout=timeout)

    @classmethod
    def tcp_server(cls, name: str, host: str = "127.0.0.1", port: int = 0, timeout: float | None = None) -> "SocketDescriptor":
        return cls(name=name, host=host, port=port, mode="SERVER", timeout=timeout)

    @classmethod
    def ssl_client(cls, name: str, host: str, port: int, timeout: float | None = None, verify: bool = True) -> "SocketDescriptor":
        return cls(name=name, host=host, port=port, mode="CLIENT", secure=SocketSecureMode.SSL, server_hostname=host, timeout=timeout, verify=verify)

    @classmethod
    def tls_client(cls, name: str, host: str, port: int, timeout: float | None = None, verify: bool = True) -> "SocketDescriptor":
        return cls(name=name, host=host, port=port, mode="CLIENT", secure=SocketSecureMode.TLS, server_hostname=host, timeout=timeout, verify=verify)


@dataclass
class SocketHandle:
    descriptor: SocketDescriptor
    socket: socket.socket | ssl.SSLSocket
    listening: bool = False

    @property
    def address(self) -> tuple[str, int]:
        host, port = self.socket.getsockname()[:2]
        return str(host), int(port)


@dataclass(frozen=True)
class SocketFileDescriptor:
    name: str
    endpoint: SocketDescriptor | None = None
    recfm: str = "UNIX"
    lrecl: int | None = None
    text: bool = False

    @classmethod
    def from_endpoint(
        cls,
        endpoint: SocketDescriptor,
        *,
        recfm: str = "UNIX",
        lrecl: int | None = None,
        text: bool = False,
    ) -> "SocketFileDescriptor":
        return cls(endpoint.name, endpoint, recfm.upper(), lrecl, text)


class SocketRuntime:
    def __init__(self) -> None:
        self._handles: dict[str, SocketHandle] = {}

    def open(self, descriptor: SocketDescriptor) -> SocketHandle:
        if descriptor.mode.upper() in {"SERVER", "LISTEN"}:
            return self.listen(descriptor)
        return self.connect(descriptor)

    def listen(self, descriptor: SocketDescriptor, backlog: int = 1) -> SocketHandle:
        raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            raw.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if descriptor.timeout is not None:
                raw.settimeout(descriptor.timeout)
            raw.bind((descriptor.host, descriptor.port))
            raw.listen(backlog)
            handle = SocketHandle(descriptor, raw, listening=True)
            self._handles[descriptor.name] = handle
            return handle
        except OSError:
            raw.close()
            raise

    def connect(self, descriptor: SocketDescriptor) -> SocketHandle:
        raw = socket.create_connection((descriptor.host, descriptor.port), timeout=descriptor.timeout)
        stream: socket.socket | ssl.SSLSocket = raw
        if self._secure_mode(descriptor) != SocketSecureMode.NONE:
            stream = self._client_context(descriptor).wrap_socket(raw, server_hostname=descriptor.server_hostname or descriptor.host)
        handle = SocketHandle(descriptor, stream, listening=False)
        self._handles[descriptor.name] = handle
        return handle

    def accept(self, listener_name: str, client_name: str) -> SocketHandle:
        listener = self._handle(listener_name)
        if not listener.listening:
            raise SocketRuntimeError(f"Socket is not listening: {listener_name}")
        raw, address = listener.socket.accept()
        if listener.descriptor.timeout is not None:
            raw.settimeout(listener.descriptor.timeout)
        stream: socket.socket | ssl.SSLSocket = raw
        if self._secure_mode(listener.descriptor) != SocketSecureMode.NONE:
            stream = self._server_context(listener.descriptor).wrap_socket(raw, server_side=True)
        descriptor = SocketDescriptor(
            name=client_name,
            host=str(address[0]),
            port=int(address[1]),
            mode="ACCEPTED",
            secure=listener.descriptor.secure,
            timeout=listener.descriptor.timeout,
        )
        handle = SocketHandle(descriptor, stream, listening=False)
        self._handles[client_name] = handle
        return handle

    def send(self, name: str, data: bytes | str) -> None:
        payload = data.encode("utf-8") if isinstance(data, str) else data
        self._handle(name).socket.sendall(payload)

    def receive(self, name: str, size: int = 4096) -> bytes:
        return self._handle(name).socket.recv(size)

    def close(self, name: str) -> None:
        handle = self._handles.pop(name, None)
        if handle is not None:
            handle.socket.close()

    def adopt(self, name: str, stream: socket.socket | ssl.SSLSocket, secure: SocketSecureMode | str = SocketSecureMode.NONE) -> SocketHandle:
        descriptor = SocketDescriptor(name=name, mode="ADOPTED", secure=secure)
        handle = SocketHandle(descriptor, stream, listening=False)
        self._handles[name] = handle
        return handle

    def close_all(self) -> None:
        for name in list(self._handles):
            self.close(name)

    def _handle(self, name: str) -> SocketHandle:
        try:
            return self._handles[name]
        except KeyError as exc:
            raise SocketRuntimeError(f"Socket is not open: {name}") from exc

    def _secure_mode(self, descriptor: SocketDescriptor) -> SocketSecureMode:
        return descriptor.secure if isinstance(descriptor.secure, SocketSecureMode) else SocketSecureMode(str(descriptor.secure).upper())

    def _client_context(self, descriptor: SocketDescriptor) -> ssl.SSLContext:
        context = ssl.create_default_context(cafile=descriptor.cafile)
        if not descriptor.verify:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        if descriptor.certfile:
            context.load_cert_chain(descriptor.certfile, descriptor.keyfile)
        return context

    def _server_context(self, descriptor: SocketDescriptor) -> ssl.SSLContext:
        if not descriptor.certfile:
            raise SocketRuntimeError("SSL/TLS server sockets require certfile")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(descriptor.certfile, descriptor.keyfile)
        return context


class SocketStreamRuntime:
    def __init__(self, primitive: SocketRuntime | None = None) -> None:
        self.primitive = primitive if primitive is not None else SocketRuntime()

    def open(self, descriptor: SocketFileDescriptor) -> SocketHandle:
        if descriptor.endpoint is None:
            raise SocketRuntimeError(f"Socket descriptor {descriptor.name} has no endpoint to open")
        return self.primitive.open(descriptor.endpoint)

    def close(self, descriptor: SocketFileDescriptor) -> None:
        self.primitive.close(descriptor.name)

    def adopt(self, name: str, stream: socket.socket | ssl.SSLSocket, secure: SocketSecureMode | str = SocketSecureMode.NONE) -> SocketHandle:
        return self.primitive.adopt(name, stream, secure)

    def write_payload(self, descriptor: SocketFileDescriptor, data: bytes | str) -> None:
        self.write_record(descriptor, data)

    def read_payload(self, descriptor: SocketFileDescriptor, size: int | None = None) -> bytes | str:
        return self.read_record(descriptor, size)

    def write_record(self, descriptor: SocketFileDescriptor, data: bytes | str) -> None:
        payload = data.encode("utf-8") if isinstance(data, str) else data
        recfm = descriptor.recfm.upper()
        if recfm == "V":
            if len(payload) > 0xFFFF:
                raise SocketRuntimeError("V socket record exceeds two-byte length prefix")
            self.primitive.send(descriptor.name, len(payload).to_bytes(2, "big") + payload)
        elif recfm == "F":
            if descriptor.lrecl is None:
                raise SocketRuntimeError("F socket record requires LRECL")
            if len(payload) > descriptor.lrecl:
                payload = payload[: descriptor.lrecl]
            pad = b" " if descriptor.text else b"\0"
            self.primitive.send(descriptor.name, payload.ljust(descriptor.lrecl, pad))
        else:
            self.primitive.send(descriptor.name, payload + (b"\n" if descriptor.text else b""))

    def read_record(self, descriptor: SocketFileDescriptor, size: int | None = None) -> bytes | str:
        recfm = descriptor.recfm.upper()
        if recfm == "V":
            length_bytes = self._read_exact(descriptor.name, 2)
            if not length_bytes:
                payload = b""
            else:
                payload = self._read_exact(descriptor.name, int.from_bytes(length_bytes, "big"))
        elif recfm == "F":
            if descriptor.lrecl is None:
                raise SocketRuntimeError("F socket record requires LRECL")
            payload = self._read_exact(descriptor.name, descriptor.lrecl)
        else:
            payload = self.primitive.receive(descriptor.name, size or 4096)
            if descriptor.text:
                payload = payload.rstrip(b"\n")
        return payload.decode("utf-8") if descriptor.text else payload

    def execute(self, statement: IOStatement, descriptors: dict[str, SocketFileDescriptor], variables: dict[str, object] | None = None) -> None:
        variables = variables if variables is not None else {}
        if statement.file_name is None:
            raise SocketRuntimeError(f"{statement.operation} requires FILE(name)")
        descriptor = descriptors[statement.file_name]
        if statement.operation == "OPEN":
            self.open(descriptor)
        elif statement.operation == "CLOSE":
            self.close(descriptor)
        elif statement.operation == "READ":
            if statement.target is None:
                raise SocketRuntimeError("READ requires INTO(name)")
            variables[statement.target] = self.read_record(descriptor)
        elif statement.operation == "WRITE":
            self.write_record(descriptor, self._io_value(statement, variables))
        else:
            raise SocketRuntimeError(f"Unsupported socket I/O operation: {statement.operation}")

    def close_all(self) -> None:
        self.primitive.close_all()

    def _read_exact(self, name: str, size: int) -> bytes:
        chunks: list[bytes] = []
        remaining = size
        while remaining:
            chunk = self.primitive.receive(name, remaining)
            if not chunk:
                if chunks:
                    raise SocketRuntimeError("Short socket record")
                return b""
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

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


__all__ = [
    "SocketDescriptor",
    "SocketFileDescriptor",
    "SocketHandle",
    "SocketRuntime",
    "SocketRuntimeError",
    "SocketSecureMode",
    "SocketStreamRuntime",
]
