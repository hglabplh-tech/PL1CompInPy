from __future__ import annotations

from pathlib import Path

from ..builtins import include_builtins
from ..codegen import BINARY_FORMATS, TARGETS, emit_binary, emit_code, emit_dotnet_executable, emit_jvm_classes
from ..frontend import Lexer, Parser
from ..runtime import normalize_calls


class Compiler:
    def compile(self, source: str, target: str = "python-source", builtins: list[str] | None = None) -> str:
        source = include_builtins(source, builtins)
        program = normalize_calls(Parser(Lexer(source).tokenize()).parse())
        return emit_code(program, target)


def compile_source(source: str, target: str = "python-source", builtins: list[str] | None = None) -> str:
    return Compiler().compile(source, target, builtins)


def available_targets() -> tuple[str, ...]:
    return tuple(TARGETS)


def available_binary_formats() -> tuple[str, ...]:
    return BINARY_FORMATS


def compile_binary(format_name: str, source: str | None = None, builtins: list[str] | None = None) -> bytes:
    source = include_builtins(source, builtins) if source is not None else None
    program = normalize_calls(Parser(Lexer(source).tokenize()).parse()) if source is not None else None
    return emit_binary(format_name, program)


def compile_jvm_classes(source: str, builtins: list[str] | None = None) -> dict[str, bytes]:
    source = include_builtins(source, builtins)
    program = normalize_calls(Parser(Lexer(source).tokenize()).parse())
    return emit_jvm_classes(program)


def compile_dotnet_executable(source: str, output: str | Path, builtins: list[str] | None = None, ilasm: str | None = None) -> Path:
    source = include_builtins(source, builtins)
    program = normalize_calls(Parser(Lexer(source).tokenize()).parse())
    return emit_dotnet_executable(program, Path(output), ilasm)
