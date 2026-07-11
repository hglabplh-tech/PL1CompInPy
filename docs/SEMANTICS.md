# Semantic Model Notes

This document records the current PL1CompInPy semantic model for operator precedence, PL/I type metadata, and debugger-oriented symbol tables.

## Source Findings

- IBM Enterprise PL/I documentation treats PL/I declarations as attribute combinations. Arithmetic data is best modeled by base (`BINARY` or `DECIMAL`), scale (`FIXED` or `FLOAT`), mode (`REAL` or `COMPLEX`), and precision/scale metadata. PL1CompInPy mirrors that with canonical `PliType` values such as `FIXED BINARY`, `FIXED DECIMAL`, `FLOAT BINARY`, `FLOAT DECIMAL`, `COMPLEX FIXED BINARY`, `COMPLEX FIXED DECIMAL`, `COMPLEX FLOAT BINARY`, and `COMPLEX FLOAT DECIMAL`.
- The PL/I `COMPLEX` attribute, also accepted through the common `CPLX` spelling, is an arithmetic mode rather than a separate statement family. The runtime therefore stores complex values as paired real and imaginary parts, promotes real operands into complex operands when needed, and keeps ordering comparisons invalid while allowing equality and inequality checks.
- Trusted PL/I references describe common complex-related builtins around construction/projection and mathematical functions. PL1CompInPy registers `COMPLEX`, `REAL`, `IMAG`, `CONJG`, `ABS`, `SQRT`, `EXP`, `LOG`, `SIN`, `COS`, and `TAN` in the static builtin table; source programs must still declare them with `DCL name BUILTIN;` or grouped `DCL (...) BUILTIN;` before use.
- PL/I also has non-arithmetic and locator categories that matter to code generation: `CHARACTER`, `BIT`, `PICTURE`, `POINTER`, `OFFSET`, `ENTRY`, arrays, structures, and based storage. These are kept as canonical type kinds with backend mappings instead of being reduced to Python primitives too early.
- PL/I comments are delimited by `/*` and `*/` and may appear wherever a blank is permitted. PL1CompInPy keeps the normal lexer behavior of treating comments as whitespace, and adds an opt-in preservation mode that records comments as `CommentSection` metadata on the parsed `Program`.
- PL/I storage semantics include programmer-managed `CONTROLLED` and `BASED` storage through `ALLOCATE`/`FREE`, `POINTER`/`OFFSET`, and area-like heap concepts. The project keeps standard `ALLOCATE`/`FREE` runtime descriptors, and adds declared internal `PL1RT_*` builtins as a compiler implementation layer for controlled runtime heap access from PL/I source.
- IBM-style PL/I precedence gives exponentiation the tightest binary binding, then prefix sign/not, multiplication/division, addition/subtraction, concatenation, comparisons, logical AND, and logical OR. The compiler now stores that in `pl1compinpy.frontend.precedence` and the parser uses precedence climbing against the same table.
- LLVM's tutorial keeps current-scope values in a `NamedValues` map during code generation; this matches the project direction of using one central table to answer name/type/storage questions instead of scattering ad hoc dictionaries through every backend.
- DWARF and Microsoft symbol-file documentation point to the debugger fields worth preserving now: source name, symbol kind, type, scope, storage location, and procedure/parameter relationship. `Symbol.debugger_record()` is shaped around those fields so native DWARF/PDB/Mach-O debug output can be added later.

## Current Implementation

- `PliTypeParser` canonicalizes PL/I declarations into `PliType` objects.
- `TYPE_MAPPINGS` records Python, JVM, .NET, x86_64, and Apple ARM64 representation notes.
- `SymbolTableBuilder` walks the AST and records variables, parameters, procedures, labels, structures, fields, pointer variables, and based storage.
- `operator_precedence_table()` exposes the parser's operator model for tests, docs, and future debugger expression evaluation.
- `ComplexRuntime` and `CalculationEngine` share the same precedence-driven expression tree: `**` binds tighter than unary and multiplicative/additive operators, and complex operands ride through the existing numeric tower instead of using a second evaluator.
- `InternalRuntimeBuiltins` wraps the same runtime heap model with pointer-returning allocation, reallocation, free, size, peek, poke, and fill helpers for future compiler-in-PL/I components.

## Debugger Direction

The best path is to keep the compiler-internal symbol table high-level and target-neutral first, then lower it into target formats:

- DWARF-style records for ELF and Mach-O: compilation unit, subprogram, variable, formal parameter, type, line mapping, and location expressions.
- PDB/CodeView-style records for Windows PE: procedure symbols, local symbols, type records, and source-line tables.
- JVM and .NET metadata/debug files: map PL/I symbols to class/method locals while preserving the original PL/I name and canonical type.

This avoids tying semantic analysis to one executable format and keeps future debugger work smaller.

## References

- IBM Enterprise PL/I for z/OS documentation: https://www.ibm.com/docs/en/epfz/6.2.0
- PL/I language summary and type categories: https://en.wikipedia.org/wiki/PL/I
- LLVM Kaleidoscope code generation and `NamedValues` symbol table: https://llvm.org/docs/tutorial/MyFirstLanguageFrontend/LangImpl03.html
- DWARF Version 5 debugging information standard: https://dwarfstd.org/doc/DWARF5.pdf
- Microsoft symbol files/PDB overview: https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/symbols-and-symbol-files
