from __future__ import annotations

import argparse
from pathlib import Path

from .compiler import available_binary_formats, available_targets, compile_binary, compile_source


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pl1compinpy",
        description="Compile PL/1 source code with PL1CompInPy.",
    )
    parser.add_argument("source", type=Path, help="Path to a PL/1 source file")
    parser.add_argument("-o", "--output", type=Path, help="Write compiler output to this file")
    parser.add_argument(
        "--emit",
        choices=("text", "binary"),
        default="text",
        help="Emit text output or a binary executable/container artifact",
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
        default="python",
        help="Compiler output target",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.emit == "binary":
        if not args.output:
            build_parser().error("--emit binary requires -o/--output")
        args.output.write_bytes(compile_binary(args.binary_format, args.source.read_text(encoding="utf-8")))
        return 0

    output = compile_source(args.source.read_text(encoding="utf-8"), target=args.target)

    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0
