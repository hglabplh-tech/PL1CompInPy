# PL1CompInPy

PL1CompInPy is a starter Python project for a PL/1 compiler.

## Project Documents

- [Features](FEATURES.md)
- [Generated API Reference](docs/API.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [MIT License](LICENSE)

The initial implementation provides a small compiler pipeline:

- lexical analysis for a useful subset of PL/1-like syntax
- parsing of assignments, declarations, calls, labels, `GOTO`/`GO TO`, control blocks, I/O statements, and preprocessor commands
- contextual keyword recognition for PL/1 statement, attribute, condition, I/O, and preprocessor words
- a visitor-enabled AST intermediate representation
- readable Python-like/Python-source output plus starter native, JVM, and .NET backends

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
- data attributes: `FIXED`, `FLOAT`, `BINARY`, `DECIMAL`, `REAL`, `COMPLEX`, `CHARACTER`, `BIT`, `POINTER`, `PICTURE`, and related aliases
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

Compile several source modules with PL/I include members:

```bash
python -m pl1compinpy examples/language/multi_source_main.pl1 examples/language/module_helper.pl1
python -m pl1compinpy examples/language/include_main.pl1 -I examples/language
```

Emit assembly instead of the default Python-like output:

```bash
python -m pl1compinpy examples/hello.pl1 --target python-source
python -m pl1compinpy examples/hello.pl1 --target jvm-bytecode
python -m pl1compinpy examples/hello.pl1 --target dotnet-il
python -m pl1compinpy examples/hello.pl1 --target x586-windows
python -m pl1compinpy examples/hello.pl1 --target x86_64-windows
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
python -m pl1compinpy examples/hello.pl1 --emit binary --binary-format pe64-x86_64-windows -o hello-x64.exe
python -m pl1compinpy examples/hello.pl1 --emit binary --binary-format elf64-x86_64 -o hello-x86_64.elf
python -m pl1compinpy examples/hello.pl1 --emit binary --binary-format elf64-aarch64 -o hello-aarch64.elf
python -m pl1compinpy examples/hello.pl1 --emit binary --binary-format macho64-x86_64-macos -o hello-intel-macos
python -m pl1compinpy examples/hello.pl1 --emit binary --binary-format macho64-arm64-macos -o hello-m2-macos
```

Create a static or dynamic-library style artifact:

```bash
python -m pl1compinpy examples/language/multi_source_main.pl1 examples/language/module_helper.pl1 --emit library --library-format static-ar -o libmulti.a
python -m pl1compinpy examples/language/multi_source_main.pl1 examples/language/module_helper.pl1 --emit library --library-format shared-elf64 -o libmulti.so
python -m pl1compinpy examples/language/multi_source_main.pl1 examples/language/module_helper.pl1 --emit library --library-format shared-pe64 -o multi.dll
```

The companion script `examples/backend/library_artifacts.py` shows the same static archive and shared-library artifact flow from the Python API.

Create a JVM `.class` file using Java 17 classfile version 61:

```bash
python -m pl1compinpy examples/backend/jvm_bytecode.pl1 --emit class -o PL1Program.class
```

Create a .NET executable using Microsoft ILAsm:

```bash
python -m pl1compinpy examples/backend/dotnet_il.pl1 --emit dotnet-exe -o PL1Program.exe
```

Run tests:

```bash
python -m unittest discover -s tests
```

The test suite covers include expansion, strict include errors, recursive include protection, multi-source compilation, CLI library output, library manifests, dynamic-load runtime dispatch, and generated API documentation for the public compiler surface.

## Assembly Back Ends

The project includes backend emitters for:

- `python-source`: Python source code
- `jvm-bytecode`: JVM bytecode-style textual output
- `--emit class`: binary JVM `.class` output targeting JDK 17 classfile version 61
- `dotnet-il`: .NET Common Intermediate Language / ILAsm textual output
- `--emit dotnet-exe`: invokes ILAsm to turn generated .NET IL into a PE `.exe`
- `x586-windows`: 32-bit x86-style assembly for Windows toolchains using C `printf`
- `x86_64-windows`: 64-bit x86 assembly for Windows x64 toolchains using C `printf`
- `x586-macos`: 32-bit x86-style assembly with macOS symbol naming
- `arm64-macos`: Apple Silicon/M2-style ARM64 assembly using macOS symbol naming
- `arm64-windows`: ARM64-style assembly with Windows symbol naming

Currently supported compiler features:

- integer variable declarations and storage
- integer assignment with `+`, `-`, `*`, and `/`
- level-numbered structures/records with nested scalar fields and dotted field references such as `CUSTOMER.ADDRESS.ZIP`
- pointer-qualified based structure references such as `P->REC.ID`, plus default `BASED(P)` access through `REC.ID`
- example coverage for default based access, explicit pointer-qualified access, and multiple pointer views over one based structure
- PL/I-style expression precedence for `**`, unary operators, `*`/`/`, `+`/`-`, `||`, comparisons, `&`/`AND`, and `|`/`OR`, driven by a central precedence table
- `IF/THEN/ELSE` comparisons with `=`, `^=`, `<>`, `<`, `<=`, `>`, and `>=`
- `DO WHILE` pre-test loops and post-test `DO ... UNTIL` loops
- `SELECT`/`WHEN`/`OTHERWISE` conditional groups
- labels and `GOTO`/`GO TO` branch statements
- parsed `%` preprocessor commands such as `%DECLARE`, `%IF`, `%DO`, `%INCLUDE`, `%REPLACE`, `%GOTO`, `%PROCEDURE`, `%RETURN`, and listing controls
- IBM-style preprocessing before lexing for `%DECLARE`, compile-time assignment, `%ACTIVATE`, `%DEACTIVATE`, `%REPLACE`, `%NOTE`, simple `%IF/%ELSE/%END` selection, and compile-time builtins such as `PARMSET`, `SYSPARM`, `LENGTH`, `SUBSTR`, `UPPERCASE`, and `LOWERCASE`
- `%INCLUDE`, `%XINCLUDE`, `%INSCAN`, and `%XINSCAN` source expansion before lexing, with include directories and recursive include protection
- multi-source compilation where the module containing `PROC OPTIONS(MAIN)` is treated as the main module
- labels and procedure bodies
- `PROC OPTIONS(MAIN)` as a program entry point, including unnamed `PROC OPTIONS(MAIN)` treated as entry name `MAIN`
- `PROC(PARM) OPTIONS(MAIN)` command-line binding, where the first parameter receives the command tail
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
- `pe64-x86_64-windows`: Windows PE32+ `.exe` format for x86_64/AMD64
- `elf64-x86_64`: ELF64 executable container for Intel/AMD 64-bit Unix-style systems
- `elf64-aarch64`: ELF64 executable container for ARM64/AArch64 Unix-style systems
- `macho64-x86_64-macos`: Mach-O 64-bit executable container for Intel macOS
- `macho64-arm64-macos`: Mach-O 64-bit executable container for Apple Silicon/M2 macOS

macOS uses Mach-O, not ELF. ELF is provided for Unix-style targets; Apple Intel and M2 targets
use Mach-O containers.

The binary layer exposes explicit PE, ELF, and Mach-O linker classes in `pl1compinpy.codegen.linkers`.
The `pe32-x586-windows` and `pe64-x86_64-windows` paths include source-driven instruction encoding
for starter arithmetic and exit code. The ELF and Mach-O paths use the same mnemonic pipeline and
have starter encoders for Intel and ARM64 machine code, ready to be expanded with full runtime I/O
and platform linker details.

## Runtime Model

The executable pipeline includes a first runtime calling convention:

- procedure-local variables are allocated in the procedure stack frame
- procedure parameters are passed on the stack from right to left
- default procedure calls use call by reference
- by-reference arguments pass the address of the caller variable, similar to C pointer-style calls
- `CALL P(B,A) BY NAME;` is normalized by matching argument names to `P`'s parameter names, sorting them into parameter order, and lowering the result as a by-reference call
- user procedures are registered in a dynamic function table as they are detected
- runtime services are registered in a static function table with PL/I-like names, pointer targets, parameter descriptions, return types, and call modes
- command-line runtime services expose `COMMAND`, `ARGC`, and `ARGV`, and direct runtime execution binds main procedure parameters from host `argv`
- PL/I builtins are also registered in the static table, but a source program must declare them with `DCL name BUILTIN;` before calls are accepted
- declared static builtins now include `SUBSTR`, `LENGTH`, `INDEX`, `POINTER`, `COMPLEX`, `REAL`, `IMAG`, `CONJG`, `ABS`, `SIGN`, `MIN`, `MAX`, `MOD`, `ROUND`, `TRUNC`, `CEIL`, `FLOOR`, complex-capable math helpers, and fixed-decimal conversion helpers
- `CALL` validation uses the merged runtime and dynamic tables before lowering
- procedure definitions are emitted before main code and the entry path jumps over them, so procedures run only when called
- native targets use a C-style runtime link model: generated objects reference `pl1rt_init`/`pl1rt_shutdown`, then the final executable is resolved against a PL/I runtime object/archive or shared/import library plus the platform C runtime
- library emission supports static archive-style artifacts and starter shared-library containers for ELF `.so`, Mach-O dynamic libraries, and Windows DLL/COFF-linkage workflows
- JVM output links the runtime through the `pl1compinpy/runtime/PL1Runtime` class on the classpath
- .NET IL links the runtime through the `PL1CompInPy.Runtime` managed assembly
- dynamic-load runtime services include `DYNLOAD`/`DYNSYM` for native libraries plus Java class-load and .NET assembly-load descriptors
- AST nodes support a visitor pattern through `accept`, and runtime execution has a `RuntimeExecutionVisitor` for future compiler passes and runtime checks; see `examples/runtime/runtime_visitor.py`
- semantic analysis includes canonical `PliType` parsing, backend type mappings, and a debugger-oriented `SymbolTable` with scope, storage, dimensions, based-pointer, procedure, parameter, and field records
- arithmetic semantics include `COMPLEX`/`CPLX` as a first-class arithmetic mode, runtime `ComplexValue` storage, complex promotion in the numeric tower, and equality-only comparison semantics for complex values
- Python source output passes `" ".join(sys.argv[1:])` to the first `OPTIONS(MAIN)` procedure parameter; native/JVM/.NET backends now identify the same main entry and reserve argument slots for parameterized mains
- backend control-flow lowering treats simple `DO` as a block, `DO WHILE` as a pre-test loop, `DO ... UNTIL` as a post-test loop, `IF/THEN/ELSE` as decisions, and `SELECT/WHEN/OTHERWISE` as branches
- GOTO statements are parsed as AST nodes and lowered to unconditional branches for the native mnemonic/assembly backends, while Python, JVM text, and .NET IL outputs preserve the branch intent in their target form
- PL/I preprocessor statements are parsed into `PreprocessorStatement` AST nodes when they are not consumed by the compile-time preprocessor, so future macro expansion can still use the visitor pipeline; current backends preserve remaining commands as target comments

The examples include an imported PL/I quicksort library at `examples/language/quicksort_imported.pli`; it is kept unchanged as a larger reference source while the current compiler subset grows toward it. Semantic notes for operator precedence, PL/I type modeling, and debugger symbol tables live in `docs/SEMANTICS.md`.

The runtime also includes starter storage and I/O services:

- PL/I-style array declarations such as `DCL A(10) FIXED BIN(31);`
- PL/I-style level-numbered structure/record declarations such as `DCL 1 CUSTOMER, 2 ID FIXED BIN(31), 2 NAME CHAR(20);`
- runtime structure values with nested field get/set, simple field-size layout, and flattened field storage for native/JVM/.NET backends
- heap allocation helpers used by dynamic array storage
- `FLOAT` declarations initialized as floating-point values in Python output
- `PICTURE`/`PIC` decimal display patterns using digit positions such as `9`, zero-suppressed `Z`, stored decimal `.`, and implied decimal `V`
- conversion helpers between fixed decimal, float, picture-formatted storage, packed decimal bytes, and zoned decimal text
- calculation engine with fixed binary, scaled fixed decimal, float, bit, and character values plus explicit casts and numeric promotion
- exported `FixedDecimal`, `PackedDecimalCodec`, `ZonedDecimalCodec`, `DecimalRuntime`, and `CalculationBuiltinRuntime` APIs for runtime callers
- `POINTER` locator variables and `BASED(pointer)` record storage bound to heap blocks through pointer values
- declared `POINTER` builtin support for normalizing null pointers, existing pointer values, and numeric handle/offset pairs into runtime `PointerValue` objects
- pointer-qualified based structure member access with explicit `P->REC.FIELD` references and default-pointer `REC.FIELD` references
- based structure examples cover default pointer access, explicit pointer-qualified access, and multiple pointer locators sharing one structure definition
- string storage as two bytes of big-endian length followed by sequential payload bytes, with runtime `LENGTH`, `SUBSTR`, and `INDEX` helpers over the stored payload
- a first packaged PL/I builtin source file for `SUBSTR(string, start[, length])`
- static builtin call checking for `DCL SUBSTR BUILTIN;`
- examples for declared numeric, string, and pointer builtins in `examples/builtins/numeric_string_builtins.pl1` and `examples/builtins/pointer.pl1`
- PL/I-style file declarations such as `DCL F FILE RECORD OUTPUT ENVIRONMENT(RECFM(V), LRECL(80), PATH('out.dat')) BINARY;`
- PL/I-style file statements: `OPEN FILE(F);`, `READ FILE(F) INTO(BUF);`, `WRITE FILE(F) FROM(BUF);`, and `CLOSE FILE(F);`
- normal Unix-style stream files
- fixed-record files using `RECFM(F)` and `LRECL(n)`
- variable-record files using `RECFM(V)`, represented here with a two-byte big-endian length prefix followed by record data
- binary and text record payloads
- primitive TCP socket I/O runtime with client/server sockets, SSL client sockets, and TLS client sockets
- file-like socket stream layer for easier text/binary payload `READ`/`WRITE`, with Unix-style, fixed, and variable record framing
- static runtime function descriptors for `ALLOC`, `FREE`, file I/O, VSAM I/O, TCP/IP, SSL, and TLS helpers
- runtime link manifests embedded in generated native executable payloads, recording the target runtime libraries and used runtime calls
- generic function dispatch by argument type, using runtime lambda implementations
- local VSAM-style datasets with a catalog file plus binary data file for KSDS, ESDS, RRDS, and LDS organizations
- VSAM runtime descriptors and I/O dispatch for `OPEN`, `WRITE FROM`, KSDS keyed `READ`, ESDS RBA `READ`, RRDS RRN `READ`/`WRITE`, LDS RBA/LENGTH `READ`, and `CLOSE`

## Project Layout

```text
PL1CompInPy/
  pyproject.toml
  docs/
    API.md
  scripts/
    generate_api_docs.py
  src/pl1compinpy/
    builtins/
      loader.py
      pl1/
        substr.pl1
    cli.py
    codegen/
      backends.py
      binary_formats.py
      dotnet_executable.py
      dotnet_il.py
      executable_pipeline.py
      jvm_bytecode.py
      libraries.py
      python_source.py
    compiler.py
    core/
      ast.py
      compiler.py
    frontend/
      include.py
      keywords.py
      lexer.py
      parser.py
    runtime/
      arrays.py
      based.py
      calculation.py
      calling.py
      command_line.py
      decimal.py
      dynload.py
      function_table.py
      heap.py
      io.py
      picture.py
      socket_io.py
      strings.py
    vsam/
      catalog.py
      io.py
  tests/
```
