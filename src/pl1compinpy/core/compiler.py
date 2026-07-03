from __future__ import annotations

from ..codegen import BINARY_FORMATS, TARGETS, emit_binary, emit_code
from ..frontend import Lexer, Parser
from ..runtime import normalize_calls


class Compiler:
    def compile(self, source: str, target: str = "python-source") -> str:
        program = normalize_calls(Parser(Lexer(source).tokenize()).parse())
        return emit_code(program, target)


def compile_source(source: str, target: str = "python-source") -> str:
    return Compiler().compile(source, target)


def available_targets() -> tuple[str, ...]:
    return tuple(TARGETS)


def available_binary_formats() -> tuple[str, ...]:
    return BINARY_FORMATS


def compile_binary(format_name: str, source: str | None = None) -> bytes:
    program = normalize_calls(Parser(Lexer(source).tokenize()).parse()) if source is not None else None
    return emit_binary(format_name, program)
