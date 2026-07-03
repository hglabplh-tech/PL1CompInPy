from __future__ import annotations

from dataclasses import dataclass

from ..core.ast import Program
from .binary_formats import BINARY_FORMATS, emit_binary


@dataclass(frozen=True)
class LinkRequest:
    format_name: str
    program: Program | None = None


class LinkerError(ValueError):
    pass


class ExecutableLinker:
    """Facade for the platform executable container writers."""

    def link(self, request: LinkRequest) -> bytes:
        if request.format_name not in BINARY_FORMATS:
            raise LinkerError(f"Unknown executable format: {request.format_name}")
        return emit_binary(request.format_name, request.program)


class PELinker(ExecutableLinker):
    def link_pe32_x586_windows(self, program: Program | None = None) -> bytes:
        return self.link(LinkRequest("pe32-x586-windows", program))

    def link_pe64_x86_64_windows(self, program: Program | None = None) -> bytes:
        return self.link(LinkRequest("pe64-x86_64-windows", program))


class ELFLinker(ExecutableLinker):
    def link_elf64_x86_64(self, program: Program | None = None) -> bytes:
        return self.link(LinkRequest("elf64-x86_64", program))

    def link_elf64_aarch64(self, program: Program | None = None) -> bytes:
        return self.link(LinkRequest("elf64-aarch64", program))


class MachOLinker(ExecutableLinker):
    def link_macho64_x86_64_macos(self, program: Program | None = None) -> bytes:
        return self.link(LinkRequest("macho64-x86_64-macos", program))

    def link_macho64_arm64_macos(self, program: Program | None = None) -> bytes:
        return self.link(LinkRequest("macho64-arm64-macos", program))


def link_executable(format_name: str, program: Program | None = None) -> bytes:
    return ExecutableLinker().link(LinkRequest(format_name, program))
