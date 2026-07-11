# Sponsoring PL1CompInPy

PL1CompInPy is a Python-based PL/I compiler project for learning, research, experimentation, and preservation of compiler knowledge around a historically important systems and business programming language.

The project is intentionally broad: it has a lexer, parser, visitor-enabled AST, semantic type model, runtime services, examples, tests, and starter backends for Python source, JVM bytecode/class output, .NET IL, native assembler, and executable container formats. That makes it useful not only as a compiler experiment, but also as a readable study project for students and researchers who want to understand how language frontends, runtimes, symbol tables, and backends connect.

## Why This Project Is Worth Sponsoring

PL/I sits at an interesting meeting point of business computing, systems programming, records, files, mainframe concepts, procedure calls, strong data declarations, and practical runtime services. Many modern developers rarely get a chance to study those ideas in a compact, open, Python-readable implementation. PL1CompInPy turns those topics into something inspectable and teachable.

Sponsorship helps because compiler projects need steady, patient work. Each feature has several layers: syntax, AST representation, semantic checks, runtime behavior, backend lowering, examples, tests, and documentation. Funding gives the project room to improve those layers carefully instead of only adding isolated syntax fragments.

## Good For Students

PL1CompInPy is well suited for students because it exposes the compiler pipeline in approachable Python modules:

- Lexing and contextual keyword recognition show how a language can use words such as `IF`, `CALL`, or `DECLARE` without treating every keyword as globally reserved.
- Parsing covers declarations, assignments, procedure calls, labels, `GOTO`, `DO WHILE`, `DO UNTIL`, `IF/THEN/ELSE`, `SELECT/WHEN/OTHERWISE`, structures, pointer-qualified based references, preprocessor commands, and function-call expressions.
- The AST uses a visitor pattern, giving students a practical path to build analysis, interpretation, transformation, or code generation passes.
- The runtime includes arrays, strings, files, records, sockets, VSAM-style datasets, pointers, based storage, function tables, decimal values, picture formatting, and complex arithmetic.
- The backends demonstrate how one source language can be lowered toward Python, JVM, .NET, native assembler, and executable container formats.

This gives students a laboratory for language design, compiler construction, runtime systems, binary formats, and legacy-language modernization without needing to begin from a blank page.

## Good For Research

The project also provides a useful research base. It already includes semantic notes, a central operator-precedence model, canonical PL/I type parsing, backend type mappings, and a debugger-oriented symbol table direction. That makes it a good place to explore:

- Language preservation and modernization for PL/I-like systems.
- Translation between legacy declarations and modern runtime representations.
- Symbol tables and future debugger metadata for DWARF, PDB/CodeView, JVM, and .NET.
- Runtime design for records, based pointers, heap storage, file organizations, socket streams, and VSAM-style access methods.
- Cross-target backend comparison across managed and native platforms.
- Teaching-friendly models for procedure calls, call by reference, call by name normalization, builtin declaration rules, and runtime function tables.

Sponsorship can turn these ideas into better-tested, better-documented, and more reusable research material.

## Current Technical Base

The current project already includes:

- A Python package with command-line compilation.
- A PL/I-like lexer and parser.
- Contextual keyword metadata for statements, attributes, I/O words, conditions, and preprocessor/listing words.
- Multi-source compilation and include expansion.
- IBM-style compile-time preprocessing for several practical directives.
- `PROC OPTIONS(MAIN)`, command-line binding, recursive procedure metadata, and return metadata.
- Function tables for runtime functions, dynamically detected user functions, and declared builtins.
- A typed calculation engine with PL/I-style operator precedence.
- Fixed decimal, packed decimal, zoned decimal, picture, string, pointer, based structure, and complex arithmetic runtime support.
- Runtime file I/O, record I/O, socket I/O, socket streams, generic dispatch, and VSAM-style dataset support.
- Backends for Python source, JVM bytecode/class output, .NET IL/executable emission, x586, x86_64, and ARM64-oriented assembly text.
- Binary/container writers for PE, ELF, and Mach-O starter artifacts.
- Static and shared-library artifact support.
- Tests, examples, API documentation, semantic notes, and project markdown.

## What Sponsorship Supports

Sponsorship helps fund work that benefits the whole project:

- More complete PL/I language coverage.
- Stronger semantic checking and diagnostics.
- Better symbol-table integration for future debugger support.
- More complete runtime behavior for files, records, pointers, structures, arrays, decimals, complex numbers, sockets, and VSAM-style data.
- More capable native, JVM, and .NET backends.
- Executable integration tests for generated artifacts.
- More examples for students and researchers.
- Better documentation that explains both the implementation and the language concepts.

## Suggested Sponsorship Message

Use this description when presenting the project to potential sponsors:

> PL1CompInPy is an educational and research-oriented PL/I compiler written in Python. It preserves and explains important compiler, runtime, and legacy-language concepts through a readable implementation with a lexer, parser, visitor AST, semantic model, runtime services, examples, tests, and multiple backend targets. Sponsoring the project helps students learn compiler construction, helps researchers explore language modernization and runtime design, and helps keep PL/I-related knowledge accessible in an open project.

## Values

The project is open under the MIT License and has a Code of Conduct. Sponsorship should support a learning-friendly, respectful, technically careful project where students, researchers, and curious engineers can study real compiler architecture step by step.
