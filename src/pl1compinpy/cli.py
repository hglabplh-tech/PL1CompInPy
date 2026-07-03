from __future__ import annotations

import argparse
from pathlib import Path

from .compiler import available_binary_formats, available_targets, compile_binary, compile_dotnet_executable, compile_jvm_classes, compile_source


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pl1compinpy",
        description="Compile PL/1 source code with PL1CompInPy.",
    )
    parser.add_argument("source", type=Path, help="Path to a PL/1 source file")
    parser.add_argument("-o", "--output", type=Path, help="Write compiler output to this file")
    parser.add_argument(
        "--emit",
        choices=("text", "binary", "class", "dotnet-exe"),
        default="text",
        help="Emit text output, a binary executable/container artifact, JVM class file(s), or a .NET executable via ILAsm",
    )
    parser.add_argument(
        "--binary-format",
        choices=available_binary_formats(),
        default="pe32-x586-windows",
        help="Binary file format used with --emit binary",
    )
    parser.add_argument(
        "--target",
        choices=available_targets(),
        default="python-source",
        help="Compiler output target",
    )
    parser.add_argument(
        "--builtin",
        action="append",
        default=[],
        help="Include a packaged PL/I builtin source file, e.g. --builtin SUBSTR",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.emit == "binary":
        if not args.output:
            build_parser().error("--emit binary requires -o/--output")
        args.output.write_bytes(compile_binary(args.binary_format, args.source.read_text(encoding="utf-8"), args.builtin))
        return 0
    if args.emit == "class":
        if not args.output:
            build_parser().error("--emit class requires -o/--output")
        classes = compile_jvm_classes(args.source.read_text(encoding="utf-8"), args.builtin)
        if len(classes) == 1 and args.output.suffix == ".class":
            args.output.write_bytes(next(iter(classes.values())))
        else:
            args.output.mkdir(parents=True, exist_ok=True)
            for filename, content in classes.items():
                (args.output / filename).write_bytes(content)
        return 0
    if args.emit == "dotnet-exe":
        if not args.output:
            build_parser().error("--emit dotnet-exe requires -o/--output")
        compile_dotnet_executable(args.source.read_text(encoding="utf-8"), args.output, args.builtin)
        return 0

    output = compile_source(args.source.read_text(encoding="utf-8"), target=args.target, builtins=args.builtin)

    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0
