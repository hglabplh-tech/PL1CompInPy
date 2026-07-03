"""Runtime normalization and calling-convention support."""

from .arrays import ArrayRuntime, ArrayRuntimeError, ArrayValue
from .calling import RuntimeError, normalize_calls
from .heap import HeapBlock, HeapRuntime, HeapRuntimeError
from .io import FileDescriptor, FileRuntimeError, StdioRuntime

__all__ = [
    "ArrayRuntime",
    "ArrayRuntimeError",
    "ArrayValue",
    "FileDescriptor",
    "FileRuntimeError",
    "HeapBlock",
    "HeapRuntime",
    "HeapRuntimeError",
    "RuntimeError",
    "StdioRuntime",
    "normalize_calls",
]
