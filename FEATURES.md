# Features

## Current Features

- Python package structure using `pyproject.toml`.
- Command-line compiler entry point via `python -m pl1compinpy`.
- PL/1 lexer with contextual keyword metadata.
- PL/1 parser producing an AST for assignments, declarations, calls, procedures, labels, `DO` groups, and `IF/THEN/ELSE`.
- Keyword catalog covering PL/1 statements, declaration attributes, storage attributes, I/O words, conditions, and preprocessor/listing words.
- Python-like text emitter for early compiler validation.
- Assembly text emitters for:
  - `x586-windows`
  - `x586-macos`
  - `arm64-macos`
  - `arm64-windows`
- Executable pipeline:
  - source
  - lexer
  - parser
  - AST
  - executable mnemonics
  - machine code
  - executable container
- Runtime calling convention:
  - local variables allocated in stack frames
  - parameters pushed right to left
  - call by reference
  - call by name normalized to sorted call by reference
- Binary/container writers for:
  - `pe32-x586-windows`
  - `elf64-x86_64`
  - `elf64-aarch64`
  - `macho64-x86_64-macos`
  - `macho64-arm64-macos`
- Unit tests for lexer, parser, compiler output, assembly output, and binary signatures.

## Supported PL/1 Subset

- Integer variable declarations.
- Integer assignments.
- Arithmetic with `+`, `-`, `*`, and `/`.
- Procedure calls.
- Basic output through `CALL DISPLAY(...)`, `CALL PRINT(...)`, and basic `PUT LIST(...)`.
- Procedure calls with by-reference and by-name normalization.
- `IF/THEN/ELSE` comparisons using `=`, `^=`, `<>`, `<`, `<=`, `>`, and `>=`.
- Labels and simple procedure bodies.
- Simple `DO` groups.

## Planned Features

- Full declaration attribute validation.
- Complete PL/1 expression precedence and type semantics.
- Broader I/O support beyond starter console output.
- Complete platform runtime/linker integration for generated binaries.
- More complete x86_64 and ARM64 instruction encoders.
- Symbol tables, scopes, diagnostics, and semantic analysis.
- Integration tests that execute generated binaries on supported platforms.
