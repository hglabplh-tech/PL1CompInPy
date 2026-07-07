from __future__ import annotations

from dataclasses import dataclass
import struct

from ..core.ast import Program, main_procedure_name
from .runtime_link import encoded_runtime_manifest


class LibraryFormatError(ValueError):
    pass


LIBRARY_FORMATS = (
    "static-ar",
    "static-lib-windows",
    "shared-elf64",
    "shared-macho64",
    "shared-pe64",
)


@dataclass(frozen=True)
class LibraryImage:
    format_name: str
    data: bytes


def emit_library(format_name: str, program: Program | None = None, module_name: str = "pl1module") -> bytes:
    manifest = _library_manifest(format_name, program, module_name)
    if format_name in {"static-ar", "static-lib-windows"}:
        return _ar_archive(module_name, manifest)
    if format_name == "shared-elf64":
        return _elf_shared(manifest)
    if format_name == "shared-macho64":
        return _macho_dylib(manifest)
    if format_name == "shared-pe64":
        return _pe_dll(manifest)
    raise LibraryFormatError(f"Unknown library format: {format_name}")


def _library_manifest(format_name: str, program: Program | None, module_name: str) -> bytes:
    target = {
        "shared-pe64": "pe64-x86_64-windows",
        "shared-elf64": "elf64-x86_64",
        "shared-macho64": "macho64-x86_64-macos",
        "static-lib-windows": "pe64-x86_64-windows",
    }.get(format_name, "elf64-x86_64")
    main = main_procedure_name(program) if program else None
    payload = (
        f"PL1LIB\nmodule={module_name}\nformat={format_name}\nmain={main or ''}\n"
    ).encode("utf-8")
    return payload + encoded_runtime_manifest(target, program)


def _ar_archive(module_name: str, payload: bytes) -> bytes:
    name = (module_name[:14] + "/").ljust(16)
    header = f"{name}{0:<12}{0:<6}{0:<6}{0o100644:<8}{len(payload):<10}`\n".encode("ascii")
    return b"!<arch>\n" + header + payload + (b"\n" if len(payload) % 2 else b"")


def _elf_shared(payload: bytes) -> bytes:
    header = bytearray(64)
    header[:4] = b"\x7fELF"
    header[4:7] = b"\x02\x01\x01"
    struct.pack_into("<HHIQQQIHHHHHH", header, 16, 3, 0x3E, 1, 0, 64, 0, 0, 64, 0, 0, 64, 0, 0)
    return bytes(header) + payload


def _macho_dylib(payload: bytes) -> bytes:
    header = struct.pack("<IiiIIII", 0xFEEDFACF, 0x01000007, 3, 6, 0, 0, 0)
    return header + payload


def _pe_dll(payload: bytes) -> bytes:
    dos_stub = bytearray(0x80)
    dos_stub[:2] = b"MZ"
    struct.pack_into("<I", dos_stub, 0x3C, len(dos_stub))
    pe = bytearray(b"PE\0\0")
    pe.extend(struct.pack("<HHIIIHH", 0x8664, 0, 0, 0, 0, 0xF0, 0x2022))
    pe.extend(b"\0" * 0xF0)
    return bytes(dos_stub) + bytes(pe) + payload


__all__ = ["LIBRARY_FORMATS", "LibraryFormatError", "LibraryImage", "emit_library"]
