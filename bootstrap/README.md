# PL/I Bootstrap Sources

This directory starts the self-hosting path for PL1CompInPy.

The files here are written in the PL/I dialect currently accepted by the
Python implementation. They are not yet a complete self-hosted compiler, but
they define the compiler architecture in PL/I source so future work can move
passes from Python into PL/I step by step.

## Modules

- `bootstrap_lexer.pl1`: token model and scanner procedures for the current dialect.
- `bootstrap_parser.pl1`: recursive-descent parser shape for the currently supported PL/I subset.
- `bootstrap_runtime.pl1`: PL/I declarations for the runtime services and internal heap builtins.
- `bootstrap_compiler.pl1`: bootstrap driver that wires lexer, parser, semantic/runtime tables, and backend selection.

## Contract

The bootstrap sources are expected to parse with the current Python frontend.
Dedicated tests verify that these modules keep parsing and that the important
entry procedures remain present.
