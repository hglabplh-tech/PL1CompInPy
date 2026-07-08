from __future__ import annotations

from pathlib import Path

from ..builtins import include_builtins
from ..codegen import BINARY_FORMATS, LIBRARY_FORMATS, TARGETS, emit_binary, emit_code, emit_dotnet_executable, emit_jvm_classes, emit_library
from ..frontend import IBMStylePreprocessor, Lexer, Parser
from ..runtime import normalize_calls


class Compiler:
    def compile(self, source: str, target: str = "python-source", builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None) -> str:
        program = self.program_from_sources([source], builtins, include_dirs, base_dir)
        return emit_code(program, target)

    def compile_sources(self, sources: list[str], target: str = "python-source", builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None) -> str:
        program = self.program_from_sources(sources, builtins, include_dirs, base_dir)
        return emit_code(program, target)

    def compile_paths(self, paths: list[str | Path], target: str = "python-source", builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None) -> str:
        program = self.program_from_paths(paths, builtins, include_dirs)
        return emit_code(program, target)

    def program_from_sources(self, sources: list[str], builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None):
        preprocessor = IBMStylePreprocessor([Path(path) for path in include_dirs or []], strict=bool(include_dirs or base_dir))
        expanded = "\n".join(preprocessor.preprocess(source, base_dir=Path(base_dir) if base_dir else None) for source in sources)
        expanded = include_builtins(expanded, builtins)
        return normalize_calls(Parser(Lexer(expanded).tokenize()).parse())

    def program_from_paths(self, paths: list[str | Path], builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None):
        preprocessor = IBMStylePreprocessor([Path(path) for path in include_dirs or []], strict=True)
        expanded = "\n".join(preprocessor.preprocess_file(Path(path)) for path in paths)
        expanded = include_builtins(expanded, builtins)
        return normalize_calls(Parser(Lexer(expanded).tokenize()).parse())


def compile_source(source: str, target: str = "python-source", builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None) -> str:
    return Compiler().compile(source, target, builtins, include_dirs, base_dir)


def compile_sources(sources: list[str], target: str = "python-source", builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None) -> str:
    return Compiler().compile_sources(sources, target, builtins, include_dirs, base_dir)


def compile_paths(paths: list[str | Path], target: str = "python-source", builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None) -> str:
    return Compiler().compile_paths(paths, target, builtins, include_dirs)


def available_targets() -> tuple[str, ...]:
    return tuple(TARGETS)


def available_binary_formats() -> tuple[str, ...]:
    return BINARY_FORMATS


def available_library_formats() -> tuple[str, ...]:
    return LIBRARY_FORMATS


def compile_binary(format_name: str, source: str | None = None, builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None) -> bytes:
    program = Compiler().program_from_sources([source], builtins, include_dirs, base_dir) if source is not None else None
    return emit_binary(format_name, program)


def compile_jvm_classes(source: str, builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None) -> dict[str, bytes]:
    program = Compiler().program_from_sources([source], builtins, include_dirs, base_dir)
    return emit_jvm_classes(program)


def compile_dotnet_executable(source: str, output: str | Path, builtins: list[str] | None = None, ilasm: str | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None) -> Path:
    program = Compiler().program_from_sources([source], builtins, include_dirs, base_dir)
    return emit_dotnet_executable(program, Path(output), ilasm)


def compile_library(format_name: str, source: str | None = None, builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None, module_name: str = "pl1module") -> bytes:
    program = Compiler().program_from_sources([source], builtins, include_dirs, base_dir) if source is not None else None
    return emit_library(format_name, program, module_name)
