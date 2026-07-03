# PL1CompInPy

PL1CompInPy is a starter Python project for a PL/1 compiler.

## Project Documents

- [Features](FEATURES.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [MIT License](LICENSE)

The initial implementation provides a small compiler pipeline:

- lexical analysis for a useful subset of PL/1-like syntax
- parsing of simple assignment and `CALL` statements
- contextual keyword recognition for PL/1 statement, attribute, condition, I/O, and preprocessor words
- an intermediate representation
- readable Python-like output for early testing

## PL/1 Keyword Model

Classic PL/I does not reserve keywords globally. A word such as `IF`, `CALL`, or `DECLARE`
can still be used as an identifier when the surrounding syntax makes that role clear. For
that reason, PL1CompInPy keeps words as identifier tokens and attaches optional keyword
metadata from `pl1compinpy.keywords.KEYWORD_CATALOG`.

The current catalog covers the main language-reference families:

- structural statements: `PROCEDURE`, `PROC`, `ENTRY`, `BEGIN`, `DO`, `END`
- declaration statements: `DECLARE`, `DCL`, `DEFAULT`, `DFT`, `FORMAT`
- flow-control statements: `CALL`, `IF`, `THEN`, `ELSE`, `SELECT`, `GO`, `GOTO`, `RETURN`, `STOP`
- condition statements and conditions: `ON`, `SIGNAL`, `REVERT`, `ERROR`, `FINISH`, `ENDFILE`, `ZERODIVIDE`, and related conditions
- storage statements and attributes: `ALLOCATE`, `ALLOC`, `FREE`, `AUTOMATIC`, `STATIC`, `BASED`, `CONTROLLED`
- data attributes: `FIXED`, `FLOAT`, `BINARY`, `DECIMAL`, `CHARACTER`, `BIT`, `POINTER`, `PICTURE`, and related aliases
- I/O statements and options: `OPEN`, `CLOSE`, `GET`, `PUT`, `READ`, `WRITE`, `REWRITE`, `LOCATE`, `DELETE`, `LIST`, `SKIP`, `KEY`
- preprocessor/listing words: `INCLUDE`, `XINCLUDE`, `ACTIVATE`, `DEACTIVATE`, `REPLACE`, `PAGE`, `PRINT`, `PUSH`, `POP`

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pl1compinpy --help
```

Compile a file:

```bash
python -m pl1compinpy examples/hello.pl1
```

Emit assembly instead of the default Python-like output:

```bash
python -m pl1compinpy examples/hello.pl1 --target python-source
python -m pl1compinpy examples/hello.pl1 --target jvm-bytecode
python -m pl1compinpy examples/hello.pl1 --target x586-windows
python -m pl1compinpy examples/hello.pl1 --target x586-macos
python -m pl1compinpy examples/hello.pl1 --target arm64-macos
python -m pl1compinpy examples/hello.pl1 --target arm64-windows
```

Include packaged PL/I builtin source before compiling:

```bash
python -m pl1compinpy examples/hello.pl1 --builtin SUBSTR
```

Create a binary executable/container artifact:

```bash
python -m pl1compinpy examples/hello.pl1 --emit binary --binary-format pe32-x586-windows -o hello.exe
python -m pl1compinpy examples/hello.pl1 --emit binary --binary-format elf64-x86_64 -o hello-x86_64.elf
python -m pl1compinpy examples/hello.pl1 --emit binary --binary-format elf64-aarch64 -o hello-aarch64.elf
python -m pl1compinpy examples/hello.pl1 --emit binary --binary-format macho64-x86_64-macos -o hello-intel-macos
python -m pl1compinpy examples/hello.pl1 --emit binary --binary-format macho64-arm64-macos -o hello-m2-macos
```

Run tests:

```bash
python -m unittest discover -s tests
```

## Assembly Back Ends

The project includes backend emitters for:

- `python-source`: Python source code
- `jvm-bytecode`: JVM bytecode-style textual output
- `x586-windows`: 32-bit x86-style assembly for Windows toolchains using C `printf`
- `x586-macos`: 32-bit x86-style assembly with macOS symbol naming
- `arm64-macos`: Apple Silicon/M2-style ARM64 assembly using macOS symbol naming
- `arm64-windows`: ARM64-style assembly with Windows symbol naming

Currently supported compiler features:

- integer variable declarations and storage
- integer assignment with `+`, `-`, `*`, and `/`
- `IF/THEN/ELSE` comparisons with `=`, `^=`, `<>`, `<`, `<=`, `>`, and `>=`
- simple `DO` groups as loops
- labels and procedure bodies
- `PROC OPTIONS(MAIN)` as a program entry point
- `PROC RECURSIVE` metadata, with recursive calls lowered as ordinary calls that continue at the next statement after return
- `PROC RETURNS(...)` metadata for function return type
- console output through `CALL DISPLAY(...)`, `CALL PRINT(...)`, and basic `PUT LIST(...)`

The emitters generate readable assembler text. They are intentionally small and direct so the
runtime calling conventions and target-specific prologues can be refined as the compiler grows.

## Binary Formats

The binary writer now follows the compiler pipeline:

```text
PL/1 source -> lexer -> parser -> AST -> executable mnemonics -> machine code -> binary container
```

For example, a PL/1 assignment such as `TOTAL = 40 + 2;` is lowered into mnemonic operations
such as `MOV_EAX_IMM`, `PUSH_EAX`, `POP_EBX`, `ADD_EAX_EBX`, and `STORE_EAX_VAR`, then encoded
as machine-code bytes before being placed in the executable file.

The binary writer currently creates minimal executable/container files with correct platform
signatures and source-derived starter code:

- `pe32-x586-windows`: Windows PE32 `.exe` format for 32-bit x86/x586
- `elf64-x86_64`: ELF64 executable container for Intel/AMD 64-bit Unix-style systems
- `elf64-aarch64`: ELF64 executable container for ARM64/AArch64 Unix-style systems
- `macho64-x86_64-macos`: Mach-O 64-bit executable container for Intel macOS
- `macho64-arm64-macos`: Mach-O 64-bit executable container for Apple Silicon/M2 macOS

macOS uses Mach-O, not ELF. ELF is provided for Unix-style targets; Apple Intel and M2 targets
use Mach-O containers.

The most complete binary path today is `pe32-x586-windows`, which includes variable storage and
source-driven x586 instruction encoding. The ELF and Mach-O paths use the same mnemonic pipeline
and have starter encoders for Intel and ARM64 machine code, ready to be expanded with full runtime
I/O and platform linker details.

## Runtime Model

The executable pipeline includes a first runtime calling convention:

- procedure-local variables are allocated in the procedure stack frame
- procedure parameters are passed on the stack from right to left
- default procedure calls use call by reference
- by-reference arguments pass the address of the caller variable, similar to C pointer-style calls
- `CALL P(B,A) BY NAME;` is normalized by matching argument names to `P`'s parameter names, sorting them into parameter order, and lowering the result as a by-reference call
- procedure definitions are emitted before main code and the entry path jumps over them, so procedures run only when called

The runtime also includes starter storage and I/O services:

- PL/I-style array declarations such as `DCL A(10) FIXED BIN(31);`
- heap allocation helpers used by dynamic array storage
- string storage as two bytes of big-endian length followed by sequential payload bytes
- a first packaged PL/I builtin source file for `SUBSTR(string, start[, length])`
- PL/I-style file declarations such as `DCL F FILE RECORD OUTPUT ENVIRONMENT(RECFM(V), LRECL(80), PATH('out.dat')) BINARY;`
- normal Unix-style stream files
- fixed-record files using `RECFM(F)` and `LRECL(n)`
- variable-record files using `RECFM(V)`, represented here with a two-byte big-endian length prefix followed by record data
- binary and text record payloads

## Project Layout

```text
PL1CompInPy/
  pyproject.toml
  src/pl1compinpy/
    builtins/
      loader.py
      pl1/
        substr.pl1
    cli.py
    codegen/
      backends.py
      binary_formats.py
      executable_pipeline.py
      jvm_bytecode.py
      python_source.py
    compiler.py
    core/
      ast.py
      compiler.py
    frontend/
      keywords.py
      lexer.py
      parser.py
    runtime/
      arrays.py
      calling.py
      heap.py
      io.py
      strings.py
  tests/
```
