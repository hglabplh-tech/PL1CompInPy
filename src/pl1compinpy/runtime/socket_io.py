from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import socket
import ssl


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


__all__ = ["SocketDescriptor", "SocketHandle", "SocketRuntime", "SocketRuntimeError", "SocketSecureMode"]
