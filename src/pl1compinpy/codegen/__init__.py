"""Assembly, executable lowering, and binary container generation."""

from .backends import TARGETS, BackendError, emit_assembly
from .binary_formats import BINARY_FORMATS, BinaryFormatError, emit_binary
from .executable_pipeline import ExecutableImage, Mnemonic, assemble_executable, lower_program

__all__ = [
    "BINARY_FORMATS",
    "BackendError",
    "BinaryFormatError",
    "ExecutableImage",
    "Mnemonic",
    "TARGETS",
    "assemble_executable",
    "emit_assembly",
    "emit_binary",
    "lower_program",
]
