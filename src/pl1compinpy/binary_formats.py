from __future__ import annotations

import struct

from .ast import Program
from .executable_pipeline import assemble_executable


class BinaryFormatError(ValueError):
    pass


BINARY_FORMATS = (
    "pe32-x586-windows",
    "elf64-x86_64",
    "elf64-aarch64",
    "macho64-x86_64-macos",
    "macho64-arm64-macos",
)


def emit_binary(format_name: str, program: Program | None = None) -> bytes:
    if format_name == "pe32-x586-windows":
        return _pe32_x586_windows(program)
    if format_name == "elf64-x86_64":
        return _elf64_x86_64(program)
    if format_name == "elf64-aarch64":
        return _elf64_aarch64(program)
    if format_name == "macho64-x86_64-macos":
        return _macho64_x86_64_macos(program)
    if format_name == "macho64-arm64-macos":
        return _macho64_arm64_macos(program)
    raise BinaryFormatError(f"Unknown binary format: {format_name}")


def _align(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment


def _pe32_x586_windows(program: Program | None = None) -> bytes:
    image_base = 0x400000
    section_alignment = 0x1000
    file_alignment = 0x200
    text_rva = 0x1000
    text_raw = 0x200
    image = assemble_executable(program, "pe32-x586-windows", image_base=image_base, code_rva=text_rva) if program else None
    code = image.code if image else b"\x31\xc0\xc3"  # xor eax, eax; ret
    data = image.data if image else b""
    section_payload = code + data
    size_of_code = _align(len(section_payload), file_alignment)
    size_of_headers = text_raw
    size_of_image = _align(text_rva + len(section_payload), section_alignment)

    dos_stub = bytearray(0x80)
    dos_stub[0:2] = b"MZ"
    struct.pack_into("<I", dos_stub, 0x3C, len(dos_stub))

    pe = bytearray()
    pe.extend(b"PE\0\0")
    pe.extend(
        struct.pack(
            "<HHIIIHH",
            0x014C,  # IMAGE_FILE_MACHINE_I386
            1,
            0,
            0,
            0,
            0xE0,
            0x0102,  # executable, 32-bit
        )
    )
    pe.extend(
        struct.pack(
            "<HBBIIIIIIIIIHHHHHHIIIIHHIIIIII",
            0x010B,  # PE32
            0,
            0,
            size_of_code,
            0,
            0,
            text_rva,
            text_rva,
            0,
            image_base,
            section_alignment,
            file_alignment,
            4,
            0,
            0,
            0,
            4,
            0,
            0,
            size_of_image,
            size_of_headers,
            0,
            3,  # console subsystem
            0,
            0x100000,
            0x1000,
            0x100000,
            0x1000,
            0,
            16,
        )
    )
    pe.extend(b"\0" * (16 * 8))
    section = struct.pack(
        "<8sIIIIIIHHI",
        b".text\0\0\0",
        len(section_payload),
        text_rva,
        size_of_code,
        text_raw,
        0,
        0,
        0,
        0,
        0x60000020,  # code, execute, read
    )
    headers = bytes(dos_stub) + bytes(pe) + section
    headers = headers.ljust(text_raw, b"\0")
    return headers + section_payload.ljust(size_of_code, b"\0")


def _elf64_x86_64(program: Program | None = None) -> bytes:
    image = assemble_executable(program, "elf64-x86_64") if program else None
    code = image.code if image else b"\xb8\x3c\x00\x00\x00\x31\xff\x0f\x05"  # exit(0)
    data = image.data if image else b""
    return _elf64(machine=0x3E, code=code, data=data)


def _elf64_aarch64(program: Program | None = None) -> bytes:
    image = assemble_executable(program, "elf64-aarch64") if program else None
    code = image.code if image else (
        b"\x00\x00\x80\xd2"  # mov x0, #0
        b"\xa8\x0b\x80\xd2"  # mov x8, #93
        b"\x01\x00\x00\xd4"  # svc #0
    )
    data = image.data if image else b""
    return _elf64(machine=0xB7, code=code, data=data)


def _elf64(machine: int, code: bytes, data: bytes = b"") -> bytes:
    base = 0x400000
    header_size = 64
    ph_size = 56
    offset = 0x1000
    entry = base + offset
    payload = code + data
    file_size = offset + len(payload)

    ident = b"\x7fELF" + bytes([2, 1, 1, 0]) + b"\0" * 8
    ehdr = struct.pack(
        "<16sHHIQQQIHHHHHH",
        ident,
        2,
        machine,
        1,
        entry,
        header_size,
        0,
        0,
        header_size,
        ph_size,
        1,
        0,
        0,
        0,
    )
    phdr = struct.pack(
        "<IIQQQQQQ",
        1,
        5,  # read + execute
        0,
        base,
        base,
        file_size,
        file_size,
        0x1000,
    )
    return (ehdr + phdr).ljust(offset, b"\0") + payload


def _macho64_x86_64_macos(program: Program | None = None) -> bytes:
    image = assemble_executable(program, "macho64-x86_64-macos") if program else None
    code = image.code if image else b"\x31\xc0\xc3"
    data = image.data if image else b""
    return _macho64(cpu_type=0x01000007, cpu_subtype=3, code=code, data=data)


def _macho64_arm64_macos(program: Program | None = None) -> bytes:
    image = assemble_executable(program, "macho64-arm64-macos") if program else None
    code = image.code if image else b"\x00\x00\x80\xd2\xc0\x03\x5f\xd6"
    data = image.data if image else b""
    return _macho64(cpu_type=0x0100000C, cpu_subtype=0, code=code, data=data)


def _macho64(cpu_type: int, cpu_subtype: int, code: bytes, data: bytes = b"") -> bytes:
    pagezero = _segment_command("__PAGEZERO", vmaddr=0, vmsize=0x100000000, fileoff=0, filesize=0, maxprot=0, initprot=0)
    text_fileoff = 0x1000
    text_vmaddr = 0x100000000
    payload = code + data
    text_segment = _segment_command(
        "__TEXT",
        vmaddr=text_vmaddr,
        vmsize=0x1000,
        fileoff=text_fileoff,
        filesize=_align(len(payload), 0x1000),
        maxprot=5,
        initprot=5,
    )
    entryoff = text_fileoff
    lc_main = struct.pack("<IIQQ", 0x80000028, 24, entryoff, 0)
    commands = pagezero + text_segment + lc_main
    header = struct.pack(
        "<IiiIIIII",
        0xFEEDFACF,
        cpu_type,
        cpu_subtype,
        2,
        3,
        len(commands),
        0x00200085,
        0,
    )
    return (header + commands).ljust(text_fileoff, b"\0") + payload


def _segment_command(name: str, vmaddr: int, vmsize: int, fileoff: int, filesize: int, maxprot: int, initprot: int) -> bytes:
    return struct.pack(
        "<II16sQQQQiiII",
        0x19,
        72,
        name.encode("ascii").ljust(16, b"\0"),
        vmaddr,
        vmsize,
        fileoff,
        filesize,
        maxprot,
        initprot,
        0,
        0,
    )
