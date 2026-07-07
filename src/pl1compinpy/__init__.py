"""PL1CompInPy: a Python-based PL/1 compiler project."""

from .compiler import Compiler, compile_paths, compile_source, compile_sources

__all__ = ["Compiler", "compile_paths", "compile_source", "compile_sources"]
__version__ = "0.1.0"
