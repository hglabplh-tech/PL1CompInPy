"""Assembly, executable lowering, and binary container generation."""

from .backends import TARGETS, BackendError, emit_assembly
from .binary_formats import BINARY_FORMATS, BinaryFormatError, emit_binary
from .executable_pipeline import ExecutableImage, Mnemonic, assemble_executable, lower_program
from .jvm_bytecode import emit_jvm_bytecode
from .jvm_classfile import JAVA_17_MAJOR_VERSION, emit_jvm_class, emit_jvm_classes
from .linkers import ELFLinker, ExecutableLinker, LinkRequest, MachOLinker, PELinker, link_executable
from .python_source import emit_python_source


def emit_code(program, target: str) -> str:
    if target in {"python", "python-source"}:
        return emit_python_source(program)
    if target == "jvm-bytecode":
        return emit_jvm_bytecode(program)
    return emit_assembly(program, target)

__all__ = [
    "BINARY_FORMATS",
    "BackendError",
    "BinaryFormatError",
    "ExecutableImage",
    "ExecutableLinker",
    "ELFLinker",
    "LinkRequest",
    "MachOLinker",
    "Mnemonic",
    "PELinker",
    "TARGETS",
    "assemble_executable",
    "emit_assembly",
    "emit_binary",
    "emit_code",
    "emit_jvm_bytecode",
    "emit_jvm_class",
    "emit_jvm_classes",
    "emit_python_source",
    "JAVA_17_MAJOR_VERSION",
    "link_executable",
    "lower_program",
]
