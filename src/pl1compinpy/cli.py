from __future__ import annotations

import argparse
from pathlib import Path

from .compiler import available_binary_formats, available_library_formats, available_targets, compile_binary, compile_dotnet_executable, compile_jvm_classes, compile_library, compile_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pl1compinpy",
        description="Compile PL/1 source code with PL1CompInPy.",
    )
    parser.add_argument("source", nargs="+", type=Path, help="Path to one or more PL/1 source files")
    parser.add_argument("-o", "--output", type=Path, help="Write compiler output to this file")
    parser.add_argument(
        "--emit",
        choices=("text", "binary", "class", "dotnet-exe", "library"),
        default="text",
        help="Emit text output, a binary executable/container artifact, JVM class file(s), a .NET executable via ILAsm, or a library artifact",
    )
    parser.add_argument(
        "--binary-format",
        choices=available_binary_formats(),
        default="pe32-x586-windows",
        help="Binary file format used with --emit binary",
    )
    parser.add_argument(
        "--library-format",
        choices=available_library_formats(),
        default="static-ar",
        help="Library file format used with --emit library",
    )
    parser.add_argument(
        "-I",
        "--include-dir",
        action="append",
        type=Path,
        default=[],
        help="Directory searched for PL/I %%INCLUDE and %%XINCLUDE members",
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
        source = "\n".join(path.read_text(encoding="utf-8") for path in args.source)
        args.output.write_bytes(compile_binary(args.binary_format, source, args.builtin, args.include_dir, args.source[0].parent))
        return 0
    if args.emit == "library":
        if not args.output:
            build_parser().error("--emit library requires -o/--output")
        source = "\n".join(path.read_text(encoding="utf-8") for path in args.source)
        args.output.write_bytes(compile_library(args.library_format, source, args.builtin, args.include_dir, args.source[0].parent, args.output.stem))
        return 0
    if args.emit == "class":
        if not args.output:
            build_parser().error("--emit class requires -o/--output")
        source = "\n".join(path.read_text(encoding="utf-8") for path in args.source)
        classes = compile_jvm_classes(source, args.builtin, args.include_dir, args.source[0].parent)
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
        source = "\n".join(path.read_text(encoding="utf-8") for path in args.source)
        compile_dotnet_executable(source, args.output, args.builtin, include_dirs=args.include_dir, base_dir=args.source[0].parent)
        return 0

    output = compile_paths(args.source, target=args.target, builtins=args.builtin, include_dirs=args.include_dir)

    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0
