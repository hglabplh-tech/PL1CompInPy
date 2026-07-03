"""Assembly, executable lowering, and binary container generation."""

from .backends import TARGETS, BackendError, emit_assembly
from .binary_formats import BINARY_FORMATS, BinaryFormatError, emit_binary
from .dotnet_executable import DotNetExecutableError, emit_dotnet_executable
from .dotnet_il import emit_dotnet_il
from .executable_pipeline import ExecutableImage, Mnemonic, assemble_executable, lower_program
from .jvm_bytecode import emit_jvm_bytecode
from .jvm_classfile import JAVA_17_MAJOR_VERSION, emit_jvm_class, emit_jvm_classes
from .linkers import ELFLinker, ExecutableLinker, LinkRequest, MachOLinker, PELinker, link_executable
from .python_source import emit_python_source
from .runtime_link import RuntimeLinkage, RuntimeLinkManifest, encoded_runtime_manifest, runtime_linkage, runtime_manifest


def emit_code(program, target: str) -> str:
    if target in {"python", "python-source"}:
        return emit_python_source(program)
    if target == "jvm-bytecode":
        return emit_jvm_bytecode(program)
    if target == "dotnet-il":
        return emit_dotnet_il(program)
    return emit_assembly(program, target)

__all__ = [
    "BINARY_FORMATS",
    "BackendError",
    "BinaryFormatError",
    "DotNetExecutableError",
    "ExecutableImage",
    "ExecutableLinker",
    "ELFLinker",
    "LinkRequest",
    "MachOLinker",
    "Mnemonic",
    "PELinker",
    "RuntimeLinkage",
    "RuntimeLinkManifest",
    "TARGETS",
    "assemble_executable",
    "emit_assembly",
    "emit_binary",
    "emit_code",
    "emit_dotnet_executable",
    "emit_dotnet_il",
    "emit_jvm_bytecode",
    "emit_jvm_class",
    "emit_jvm_classes",
    "emit_python_source",
    "encoded_runtime_manifest",
    "JAVA_17_MAJOR_VERSION",
    "link_executable",
    "lower_program",
    "runtime_linkage",
    "runtime_manifest",
]
