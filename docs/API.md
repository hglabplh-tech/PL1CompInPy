# PL1CompInPy API Reference

This file is generated from the Python source tree. Regenerate it with `python scripts/generate_api_docs.py`.

## Summary

- Modules: 53
- Classes: 153
- Functions and methods: 615

## `pl1compinpy`

Source: `pl1compinpy/__init__.py`

PL1CompInPy: a Python-based PL/1 compiler project.

## `pl1compinpy.__main__`

Source: `pl1compinpy/__main__.py`

Module containing main support for the PL/I compiler.

## `pl1compinpy.ast`

Source: `pl1compinpy/ast.py`

Compatibility wrapper for the core AST package.

## `pl1compinpy.builtins`

Source: `pl1compinpy/builtins/__init__.py`

PL/I builtin source management.

## `pl1compinpy.builtins.loader`

Source: `pl1compinpy/builtins/loader.py`

Module containing loader support for the PL/I compiler.

### Classes

#### `BuiltinError`

```python
class BuiltinError(ValueError)
```

Exception type raised for builtin errors.

Defined at line 7.

#### `BuiltinLibrary`

```python
class BuiltinLibrary
```

Data container describing builtin library values used by the compiler.

Defined at line 12.

Methods:

##### `BuiltinLibrary.source`

```python
def source(self, name: str) -> str
```

Performs source behavior in `BuiltinLibrary`.

Defined at line 15.

##### `BuiltinLibrary.include`

```python
def include(self, names: list[str]) -> str
```

Performs include behavior in `BuiltinLibrary`.

Defined at line 21.

### Functions

#### `include_builtins`

```python
def include_builtins(source: str, names: list[str] | None = None) -> str
```

Performs include builtins behavior in `pl1compinpy.builtins.loader`.

Defined at line 25.

## `pl1compinpy.builtins.pl1`

Source: `pl1compinpy/builtins/pl1/__init__.py`

Packaged PL/I builtin source files.

## `pl1compinpy.cli`

Source: `pl1compinpy/cli.py`

Module containing cli support for the PL/I compiler.

### Functions

#### `build_parser`

```python
def build_parser() -> argparse.ArgumentParser
```

Performs build parser behavior in `pl1compinpy.cli`.

Defined at line 9.

#### `main`

```python
def main(argv: list[str] | None = None) -> int
```

Performs main behavior in `pl1compinpy.cli`.

Defined at line 57.

## `pl1compinpy.codegen`

Source: `pl1compinpy/codegen/__init__.py`

Assembly, executable lowering, and binary container generation.

### Functions

#### `emit_code`

```python
def emit_code(program, target: str) -> str
```

Emits code output for the compiler.

Defined at line 16.

## `pl1compinpy.codegen.backends`

Source: `pl1compinpy/codegen/backends.py`

Module containing backends support for the PL/I compiler.

### Classes

#### `AssemblyTarget`

```python
class AssemblyTarget
```

Data container describing assembly target values used by the compiler.

Defined at line 34.

#### `BackendError`

```python
class BackendError(ValueError)
```

Exception type raised for backend errors.

Defined at line 57.

#### `SymbolTable`

```python
class SymbolTable
```

Data container describing symbol table values used by the compiler.

Defined at line 75.

Methods:

##### `SymbolTable.add_string`

```python
def add_string(self, value: str) -> str
```

Performs add string behavior in `SymbolTable`.

Defined at line 80.

#### `AssemblyEmitter`

```python
class AssemblyEmitter
```

Class implementing assembly emitter behavior in the PL/I compiler.

Defined at line 87.

Methods:

##### `AssemblyEmitter.__init__`

```python
def __init__(self, target: AssemblyTarget) -> None
```

Initializes an instance of `AssemblyEmitter`.

Defined at line 88.

##### `AssemblyEmitter._collect_symbols`

```python
def _collect_symbols(self, program: Program) -> None
```

Internal helper in `AssemblyEmitter` for collect symbols.

Defined at line 94.

##### `AssemblyEmitter._collect_statement`

```python
def _collect_statement(self, statement: Statement) -> None
```

Internal helper in `AssemblyEmitter` for collect statement.

Defined at line 98.

##### `AssemblyEmitter._collect_expression`

```python
def _collect_expression(self, expression: Expression) -> None
```

Internal helper in `AssemblyEmitter` for collect expression.

Defined at line 125.

##### `AssemblyEmitter._new_label`

```python
def _new_label(self, stem: str) -> str
```

Internal helper in `AssemblyEmitter` for new label.

Defined at line 141.

##### `AssemblyEmitter._symbol`

```python
def _symbol(self, name: str) -> str
```

Internal helper in `AssemblyEmitter` for symbol.

Defined at line 146.

##### `AssemblyEmitter._data_label`

```python
def _data_label(self, name: str) -> str
```

Internal helper in `AssemblyEmitter` for data label.

Defined at line 149.

##### `AssemblyEmitter._runtime_symbol`

```python
def _runtime_symbol(self, name: str) -> str
```

Internal helper in `AssemblyEmitter` for runtime symbol.

Defined at line 152.

##### `AssemblyEmitter._runtime_externs`

```python
def _runtime_externs(self) -> list[str]
```

Internal helper in `AssemblyEmitter` for runtime externs.

Defined at line 155.

##### `AssemblyEmitter._runtime_link_comments`

```python
def _runtime_link_comments(self, comment: str) -> list[str]
```

Internal helper in `AssemblyEmitter` for runtime link comments.

Defined at line 158.

##### `AssemblyEmitter._escaped_bytes`

```python
def _escaped_bytes(self, value: str) -> str
```

Internal helper in `AssemblyEmitter` for escaped bytes.

Defined at line 168.

##### `AssemblyEmitter._condition_jump`

```python
def _condition_jump(self, operator: str, if_false: bool) -> str
```

Internal helper in `AssemblyEmitter` for condition jump.

Defined at line 172.

##### `AssemblyEmitter._raw_put_arguments`

```python
def _raw_put_arguments(self, statement: RawStatement) -> list[Expression]
```

Internal helper in `AssemblyEmitter` for raw put arguments.

Defined at line 187.

#### `X586AssemblyEmitter`

```python
class X586AssemblyEmitter(AssemblyEmitter)
```

Class implementing x586 assembly emitter behavior in the PL/I compiler.

Defined at line 204.

Methods:

##### `X586AssemblyEmitter.emit`

```python
def emit(self, program: Program) -> str
```

Performs emit behavior in `X586AssemblyEmitter`.

Defined at line 205.

##### `X586AssemblyEmitter._statement`

```python
def _statement(self, statement: Statement) -> list[str]
```

Internal helper in `X586AssemblyEmitter` for statement.

Defined at line 229.

##### `X586AssemblyEmitter._do_group`

```python
def _do_group(self, statement: DoGroup) -> list[str]
```

Internal helper in `X586AssemblyEmitter` for do group.

Defined at line 263.

##### `X586AssemblyEmitter._if`

```python
def _if(self, statement: IfStatement) -> list[str]
```

Internal helper in `X586AssemblyEmitter` for if.

Defined at line 283.

##### `X586AssemblyEmitter._select`

```python
def _select(self, statement: SelectStatement) -> list[str]
```

Internal helper in `X586AssemblyEmitter` for select.

Defined at line 295.

##### `X586AssemblyEmitter._call`

```python
def _call(self, statement: Call) -> list[str]
```

Internal helper in `X586AssemblyEmitter` for call.

Defined at line 323.

##### `X586AssemblyEmitter._print_arguments`

```python
def _print_arguments(self, arguments: list[Expression]) -> list[str]
```

Internal helper in `X586AssemblyEmitter` for print arguments.

Defined at line 335.

##### `X586AssemblyEmitter._comparison`

```python
def _comparison(self, expression: Expression, false_label: str) -> list[str]
```

Internal helper in `X586AssemblyEmitter` for comparison.

Defined at line 346.

##### `X586AssemblyEmitter._expression`

```python
def _expression(self, expression: Expression) -> list[str]
```

Internal helper in `X586AssemblyEmitter` for expression.

Defined at line 358.

#### `X8664AssemblyEmitter`

```python
class X8664AssemblyEmitter(AssemblyEmitter)
```

Class implementing x8664 assembly emitter behavior in the PL/I compiler.

Defined at line 390.

Methods:

##### `X8664AssemblyEmitter.emit`

```python
def emit(self, program: Program) -> str
```

Performs emit behavior in `X8664AssemblyEmitter`.

Defined at line 391.

##### `X8664AssemblyEmitter._statement`

```python
def _statement(self, statement: Statement) -> list[str]
```

Internal helper in `X8664AssemblyEmitter` for statement.

Defined at line 417.

##### `X8664AssemblyEmitter._do_group`

```python
def _do_group(self, statement: DoGroup) -> list[str]
```

Internal helper in `X8664AssemblyEmitter` for do group.

Defined at line 451.

##### `X8664AssemblyEmitter._if`

```python
def _if(self, statement: IfStatement) -> list[str]
```

Internal helper in `X8664AssemblyEmitter` for if.

Defined at line 471.

##### `X8664AssemblyEmitter._select`

```python
def _select(self, statement: SelectStatement) -> list[str]
```

Internal helper in `X8664AssemblyEmitter` for select.

Defined at line 483.

##### `X8664AssemblyEmitter._call`

```python
def _call(self, statement: Call) -> list[str]
```

Internal helper in `X8664AssemblyEmitter` for call.

Defined at line 511.

##### `X8664AssemblyEmitter._print_arguments`

```python
def _print_arguments(self, arguments: list[Expression]) -> list[str]
```

Internal helper in `X8664AssemblyEmitter` for print arguments.

Defined at line 523.

##### `X8664AssemblyEmitter._comparison`

```python
def _comparison(self, expression: Expression, false_label: str) -> list[str]
```

Internal helper in `X8664AssemblyEmitter` for comparison.

Defined at line 550.

##### `X8664AssemblyEmitter._expression`

```python
def _expression(self, expression: Expression) -> list[str]
```

Internal helper in `X8664AssemblyEmitter` for expression.

Defined at line 562.

#### `Arm64AssemblyEmitter`

```python
class Arm64AssemblyEmitter(AssemblyEmitter)
```

Class implementing arm64 assembly emitter behavior in the PL/I compiler.

Defined at line 594.

Methods:

##### `Arm64AssemblyEmitter.emit`

```python
def emit(self, program: Program) -> str
```

Performs emit behavior in `Arm64AssemblyEmitter`.

Defined at line 595.

##### `Arm64AssemblyEmitter._statement`

```python
def _statement(self, statement: Statement) -> list[str]
```

Internal helper in `Arm64AssemblyEmitter` for statement.

Defined at line 623.

##### `Arm64AssemblyEmitter._do_group`

```python
def _do_group(self, statement: DoGroup) -> list[str]
```

Internal helper in `Arm64AssemblyEmitter` for do group.

Defined at line 658.

##### `Arm64AssemblyEmitter._if`

```python
def _if(self, statement: IfStatement) -> list[str]
```

Internal helper in `Arm64AssemblyEmitter` for if.

Defined at line 678.

##### `Arm64AssemblyEmitter._select`

```python
def _select(self, statement: SelectStatement) -> list[str]
```

Internal helper in `Arm64AssemblyEmitter` for select.

Defined at line 690.

##### `Arm64AssemblyEmitter._call`

```python
def _call(self, statement: Call) -> list[str]
```

Internal helper in `Arm64AssemblyEmitter` for call.

Defined at line 718.

##### `Arm64AssemblyEmitter._print_arguments`

```python
def _print_arguments(self, arguments: list[Expression]) -> list[str]
```

Internal helper in `Arm64AssemblyEmitter` for print arguments.

Defined at line 728.

##### `Arm64AssemblyEmitter._comparison`

```python
def _comparison(self, expression: Expression, false_label: str) -> list[str]
```

Internal helper in `Arm64AssemblyEmitter` for comparison.

Defined at line 754.

##### `Arm64AssemblyEmitter._expression`

```python
def _expression(self, expression: Expression) -> list[str]
```

Internal helper in `Arm64AssemblyEmitter` for expression.

Defined at line 778.

##### `Arm64AssemblyEmitter._escape_asciz`

```python
def _escape_asciz(self, value: str) -> str
```

Internal helper in `Arm64AssemblyEmitter` for escape asciz.

Defined at line 812.

### Functions

#### `emit_assembly`

```python
def emit_assembly(program: Program, target_name: str) -> str
```

Emits assembly output for the compiler.

Defined at line 61.

#### `_declaration_storage_names`

```python
def _declaration_storage_names(declaration: Declaration) -> list[str]
```

Internal helper in `pl1compinpy.codegen.backends` for declaration storage names.

Defined at line 816.

#### `_structure_leaf_names`

```python
def _structure_leaf_names(field: StructureField, prefix: list[str]) -> list[str]
```

Internal helper in `pl1compinpy.codegen.backends` for structure leaf names.

Defined at line 825.

## `pl1compinpy.codegen.binary_formats`

Source: `pl1compinpy/codegen/binary_formats.py`

Module containing binary formats support for the PL/I compiler.

### Classes

#### `BinaryFormatError`

```python
class BinaryFormatError(ValueError)
```

Exception type raised for binary format errors.

Defined at line 9.

### Functions

#### `emit_binary`

```python
def emit_binary(format_name: str, program: Program | None = None) -> bytes
```

Emits binary output for the compiler.

Defined at line 23.

#### `_align`

```python
def _align(value: int, alignment: int) -> int
```

Internal helper in `pl1compinpy.codegen.binary_formats` for align.

Defined at line 39.

#### `_pe32_x586_windows`

```python
def _pe32_x586_windows(program: Program | None = None) -> bytes
```

Internal helper in `pl1compinpy.codegen.binary_formats` for pe32 x586 windows.

Defined at line 43.

#### `_pe64_x86_64_windows`

```python
def _pe64_x86_64_windows(program: Program | None = None) -> bytes
```

Internal helper in `pl1compinpy.codegen.binary_formats` for pe64 x86 64 windows.

Defined at line 129.

#### `_elf64_x86_64`

```python
def _elf64_x86_64(program: Program | None = None) -> bytes
```

Internal helper in `pl1compinpy.codegen.binary_formats` for elf64 x86 64.

Defined at line 214.

#### `_elf64_aarch64`

```python
def _elf64_aarch64(program: Program | None = None) -> bytes
```

Internal helper in `pl1compinpy.codegen.binary_formats` for elf64 aarch64.

Defined at line 221.

#### `_elf64`

```python
def _elf64(machine: int, code: bytes, data: bytes = b'') -> bytes
```

Internal helper in `pl1compinpy.codegen.binary_formats` for elf64.

Defined at line 232.

#### `_macho64_x86_64_macos`

```python
def _macho64_x86_64_macos(program: Program | None = None) -> bytes
```

Internal helper in `pl1compinpy.codegen.binary_formats` for macho64 x86 64 macos.

Defined at line 273.

#### `_macho64_arm64_macos`

```python
def _macho64_arm64_macos(program: Program | None = None) -> bytes
```

Internal helper in `pl1compinpy.codegen.binary_formats` for macho64 arm64 macos.

Defined at line 280.

#### `_macho64`

```python
def _macho64(cpu_type: int, cpu_subtype: int, code: bytes, data: bytes = b'') -> bytes
```

Internal helper in `pl1compinpy.codegen.binary_formats` for macho64.

Defined at line 287.

#### `_segment_command`

```python
def _segment_command(name: str, vmaddr: int, vmsize: int, fileoff: int, filesize: int, maxprot: int, initprot: int) -> bytes
```

Internal helper in `pl1compinpy.codegen.binary_formats` for segment command.

Defined at line 318.

## `pl1compinpy.codegen.dotnet_executable`

Source: `pl1compinpy/codegen/dotnet_executable.py`

Module containing dotnet executable support for the PL/I compiler.

### Classes

#### `DotNetExecutableError`

```python
class DotNetExecutableError(RuntimeError)
```

Exception type raised for dot net executable errors.

Defined at line 12.

### Functions

#### `emit_dotnet_executable`

```python
def emit_dotnet_executable(program: Program, output: Path, ilasm: str | None = None) -> Path
```

Emits dotnet executable output for the compiler.

Defined at line 16.

## `pl1compinpy.codegen.dotnet_il`

Source: `pl1compinpy/codegen/dotnet_il.py`

Module containing dotnet il support for the PL/I compiler.

### Classes

#### `DotNetILEmitter`

```python
class DotNetILEmitter
```

Class implementing dot net ilemitter behavior in the PL/I compiler.

Defined at line 28.

Methods:

##### `DotNetILEmitter.emit`

```python
def emit(self, program: Program) -> str
```

Performs emit behavior in `DotNetILEmitter`.

Defined at line 29.

##### `DotNetILEmitter._procedure`

```python
def _procedure(self, name: str, procedure: Procedure) -> list[str]
```

Internal helper in `DotNetILEmitter` for procedure.

Defined at line 75.

##### `DotNetILEmitter._entrypoint_call`

```python
def _entrypoint_call(self, procedure_name: str, procedure: Procedure, returns: bool) -> list[str]
```

Internal helper in `DotNetILEmitter` for entrypoint call.

Defined at line 103.

##### `DotNetILEmitter._entrypoint_body`

```python
def _entrypoint_body(self, statements: list[object]) -> list[str]
```

Internal helper in `DotNetILEmitter` for entrypoint body.

Defined at line 123.

##### `DotNetILEmitter._statement`

```python
def _statement(self, statement: object, locals_map: dict[str, int], local_types: list[str]) -> list[str]
```

Internal helper in `DotNetILEmitter` for statement.

Defined at line 142.

##### `DotNetILEmitter._expression`

```python
def _expression(self, expression: object, locals_map: dict[str, int], local_types: list[str]) -> list[str]
```

Internal helper in `DotNetILEmitter` for expression.

Defined at line 168.

##### `DotNetILEmitter._call`

```python
def _call(self, call: Call, locals_map: dict[str, int], local_types: list[str]) -> list[str]
```

Internal helper in `DotNetILEmitter` for call.

Defined at line 186.

##### `DotNetILEmitter._local`

```python
def _local(self, name: str, locals_map: dict[str, int], local_types: list[str]) -> int
```

Internal helper in `DotNetILEmitter` for local.

Defined at line 203.

##### `DotNetILEmitter._int_constant`

```python
def _int_constant(self, value: int) -> list[str]
```

Internal helper in `DotNetILEmitter` for int constant.

Defined at line 209.

##### `DotNetILEmitter._main_name`

```python
def _main_name(self, program: Program) -> str | None
```

Internal helper in `DotNetILEmitter` for main name.

Defined at line 218.

##### `DotNetILEmitter._quote`

```python
def _quote(self, value: str) -> str
```

Internal helper in `DotNetILEmitter` for quote.

Defined at line 221.

### Functions

#### `emit_dotnet_il`

```python
def emit_dotnet_il(program: Program) -> str
```

Emits dotnet il output for the compiler.

Defined at line 226.

#### `_declaration_storage_names`

```python
def _declaration_storage_names(declaration: Declaration) -> list[str]
```

Internal helper in `pl1compinpy.codegen.dotnet_il` for declaration storage names.

Defined at line 230.

#### `_structure_leaf_names`

```python
def _structure_leaf_names(field: StructureField, prefix: list[str]) -> list[str]
```

Internal helper in `pl1compinpy.codegen.dotnet_il` for structure leaf names.

Defined at line 239.

## `pl1compinpy.codegen.executable_pipeline`

Source: `pl1compinpy/codegen/executable_pipeline.py`

Module containing executable pipeline support for the PL/I compiler.

### Classes

#### `Mnemonic`

```python
class Mnemonic
```

Data container describing mnemonic values used by the compiler.

Defined at line 37.

#### `ExecutableImage`

```python
class ExecutableImage
```

Data container describing executable image values used by the compiler.

Defined at line 43.

#### `LoweringContext`

```python
class LoweringContext
```

Data container describing lowering context values used by the compiler.

Defined at line 49.

Methods:

##### `LoweringContext.variable`

```python
def variable(self, name: str) -> int
```

Performs variable behavior in `LoweringContext`.

Defined at line 57.

##### `LoweringContext.local`

```python
def local(self, name: str) -> int
```

Performs local behavior in `LoweringContext`.

Defined at line 63.

##### `LoweringContext.local_bytes`

```python
def local_bytes(self) -> int
```

Performs local bytes behavior in `LoweringContext`.

Defined at line 71.

##### `LoweringContext.is_local`

```python
def is_local(self, name: str) -> bool
```

Performs is local behavior in `LoweringContext`.

Defined at line 74.

##### `LoweringContext.is_parameter`

```python
def is_parameter(self, name: str) -> bool
```

Performs is parameter behavior in `LoweringContext`.

Defined at line 77.

##### `LoweringContext.stack_offset`

```python
def stack_offset(self, name: str) -> int
```

Performs stack offset behavior in `LoweringContext`.

Defined at line 80.

##### `LoweringContext.string`

```python
def string(self, value: str) -> tuple[int, int]
```

Performs string behavior in `LoweringContext`.

Defined at line 87.

##### `LoweringContext.label`

```python
def label(self, stem: str) -> str
```

Performs label behavior in `LoweringContext`.

Defined at line 93.

#### `X586MnemonicAssembler`

```python
class X586MnemonicAssembler
```

Class implementing x586 mnemonic assembler behavior in the PL/I compiler.

Defined at line 455.

Methods:

##### `X586MnemonicAssembler.__init__`

```python
def __init__(self, image_base: int, code_rva: int, data: bytes, variables: dict[str, int]) -> None
```

Initializes an instance of `X586MnemonicAssembler`.

Defined at line 456.

##### `X586MnemonicAssembler.assemble`

```python
def assemble(self, mnemonics: list[Mnemonic]) -> bytes
```

Performs assemble behavior in `X586MnemonicAssembler`.

Defined at line 463.

##### `X586MnemonicAssembler._var_addr`

```python
def _var_addr(self, name: str) -> int
```

Internal helper in `X586MnemonicAssembler` for var addr.

Defined at line 471.

##### `X586MnemonicAssembler._data_addr`

```python
def _data_addr(self, offset: int) -> int
```

Internal helper in `X586MnemonicAssembler` for data addr.

Defined at line 474.

##### `X586MnemonicAssembler._code_size`

```python
def _code_size(self, mnemonics: list[Mnemonic]) -> int
```

Internal helper in `X586MnemonicAssembler` for code size.

Defined at line 477.

##### `X586MnemonicAssembler._label_offsets`

```python
def _label_offsets(self, mnemonics: list[Mnemonic]) -> dict[str, int]
```

Internal helper in `X586MnemonicAssembler` for label offsets.

Defined at line 480.

##### `X586MnemonicAssembler._size`

```python
def _size(self, mnemonic: Mnemonic) -> int
```

Internal helper in `X586MnemonicAssembler` for size.

Defined at line 489.

##### `X586MnemonicAssembler._encode`

```python
def _encode(self, mnemonic: Mnemonic, offset: int, labels: dict[str, int]) -> bytes
```

Internal helper in `X586MnemonicAssembler` for encode.

Defined at line 525.

##### `X586MnemonicAssembler._jfalse_opcode`

```python
def _jfalse_opcode(self, operator: str) -> bytes
```

Internal helper in `X586MnemonicAssembler` for jfalse opcode.

Defined at line 594.

#### `X8664MnemonicAssembler`

```python
class X8664MnemonicAssembler
```

Class implementing x8664 mnemonic assembler behavior in the PL/I compiler.

Defined at line 609.

Methods:

##### `X8664MnemonicAssembler.__init__`

```python
def __init__(self, image_base: int, code_rva: int, data: bytes, variables: dict[str, int], macos: bool = False, windows: bool = False) -> None
```

Initializes an instance of `X8664MnemonicAssembler`.

Defined at line 610.

##### `X8664MnemonicAssembler.assemble`

```python
def assemble(self, mnemonics: list[Mnemonic]) -> bytes
```

Performs assemble behavior in `X8664MnemonicAssembler`.

Defined at line 618.

#### `Arm64MnemonicAssembler`

```python
class Arm64MnemonicAssembler
```

Class implementing arm64 mnemonic assembler behavior in the PL/I compiler.

Defined at line 640.

Methods:

##### `Arm64MnemonicAssembler.__init__`

```python
def __init__(self, macos: bool = False) -> None
```

Initializes an instance of `Arm64MnemonicAssembler`.

Defined at line 641.

##### `Arm64MnemonicAssembler.assemble`

```python
def assemble(self, mnemonics: list[Mnemonic]) -> bytes
```

Performs assemble behavior in `Arm64MnemonicAssembler`.

Defined at line 644.

##### `Arm64MnemonicAssembler._mov_w0_imm`

```python
def _mov_w0_imm(self, value: int) -> bytes
```

Internal helper in `Arm64MnemonicAssembler` for mov w0 imm.

Defined at line 657.

##### `Arm64MnemonicAssembler._mov_x16_or_x8`

```python
def _mov_x16_or_x8(self, value: int) -> bytes
```

Internal helper in `Arm64MnemonicAssembler` for mov x16 or x8.

Defined at line 662.

### Functions

#### `lower_program`

```python
def lower_program(program: Program) -> tuple[list[Mnemonic], bytes, dict[str, int]]
```

Performs lower program behavior in `pl1compinpy.codegen.executable_pipeline`.

Defined at line 99.

#### `assemble_executable`

```python
def assemble_executable(program: Program, binary_format: str, *, image_base: int = 4194304, code_rva: int = 4096) -> ExecutableImage
```

Performs assemble executable behavior in `pl1compinpy.codegen.executable_pipeline`.

Defined at line 129.

#### `_collect_data`

```python
def _collect_data(statement: Statement, context: LoweringContext) -> None
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for collect data.

Defined at line 151.

#### `_collect_expression_data`

```python
def _collect_expression_data(expression: Expression, context: LoweringContext) -> None
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for collect expression data.

Defined at line 190.

#### `_is_procedure_definition`

```python
def _is_procedure_definition(statement: Statement) -> bool
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for is procedure definition.

Defined at line 207.

#### `_main_procedure_name`

```python
def _main_procedure_name(program: Program) -> str | None
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for main procedure name.

Defined at line 213.

#### `_lower_statement`

```python
def _lower_statement(statement: Statement, context: LoweringContext) -> list[Mnemonic]
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for lower statement.

Defined at line 217.

#### `_lower_do_group`

```python
def _lower_do_group(statement: DoGroup, context: LoweringContext) -> list[Mnemonic]
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for lower do group.

Defined at line 274.

#### `_lower_select`

```python
def _lower_select(statement: SelectStatement, context: LoweringContext) -> list[Mnemonic]
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for lower select.

Defined at line 295.

#### `_lower_procedure`

```python
def _lower_procedure(procedure: Procedure, context: LoweringContext) -> list[Mnemonic]
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for lower procedure.

Defined at line 326.

#### `_lower_call`

```python
def _lower_call(call: Call, context: LoweringContext) -> list[Mnemonic]
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for lower call.

Defined at line 346.

#### `_lower_expression`

```python
def _lower_expression(expression: Expression, context: LoweringContext) -> list[Mnemonic]
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for lower expression.

Defined at line 360.

#### `_declaration_storage_names`

```python
def _declaration_storage_names(declaration: Declaration) -> list[str]
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for declaration storage names.

Defined at line 388.

#### `_structure_leaf_names`

```python
def _structure_leaf_names(field: StructureField, prefix: list[str]) -> list[str]
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for structure leaf names.

Defined at line 397.

#### `_lower_condition_false_jump`

```python
def _lower_condition_false_jump(expression: Expression, false_label: str, context: LoweringContext) -> list[Mnemonic]
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for lower condition false jump.

Defined at line 406.

#### `_lower_display`

```python
def _lower_display(arguments: list[Expression], context: LoweringContext) -> list[Mnemonic]
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for lower display.

Defined at line 416.

#### `_load_name`

```python
def _load_name(name: str, context: LoweringContext) -> Mnemonic
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for load name.

Defined at line 428.

#### `_store_name`

```python
def _store_name(name: str, context: LoweringContext) -> Mnemonic
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for store name.

Defined at line 437.

#### `_push_reference`

```python
def _push_reference(name: str, context: LoweringContext) -> Mnemonic
```

Internal helper in `pl1compinpy.codegen.executable_pipeline` for push reference.

Defined at line 446.

## `pl1compinpy.codegen.jvm_bytecode`

Source: `pl1compinpy/codegen/jvm_bytecode.py`

Module containing jvm bytecode support for the PL/I compiler.

### Classes

#### `JVMBytecodeEmitter`

```python
class JVMBytecodeEmitter
```

Class implementing jvmbytecode emitter behavior in the PL/I compiler.

Defined at line 27.

Methods:

##### `JVMBytecodeEmitter.emit`

```python
def emit(self, program: Program) -> str
```

Performs emit behavior in `JVMBytecodeEmitter`.

Defined at line 28.

##### `JVMBytecodeEmitter._procedure`

```python
def _procedure(self, name: str, procedure: Procedure) -> list[str]
```

Internal helper in `JVMBytecodeEmitter` for procedure.

Defined at line 71.

##### `JVMBytecodeEmitter._procedure_body`

```python
def _procedure_body(self, procedure: Procedure, locals_map: dict[str, int], next_local: int) -> tuple[list[str], int]
```

Internal helper in `JVMBytecodeEmitter` for procedure body.

Defined at line 118.

##### `JVMBytecodeEmitter._expression`

```python
def _expression(self, expression: object, locals_map: dict[str, int]) -> list[str]
```

Internal helper in `JVMBytecodeEmitter` for expression.

Defined at line 155.

##### `JVMBytecodeEmitter._call`

```python
def _call(self, call: Call, locals_map: dict[str, int]) -> list[str]
```

Internal helper in `JVMBytecodeEmitter` for call.

Defined at line 180.

##### `JVMBytecodeEmitter._int_constant`

```python
def _int_constant(self, value: int) -> list[str]
```

Internal helper in `JVMBytecodeEmitter` for int constant.

Defined at line 188.

##### `JVMBytecodeEmitter._return_descriptor`

```python
def _return_descriptor(self, procedure: Procedure) -> str
```

Internal helper in `JVMBytecodeEmitter` for return descriptor.

Defined at line 197.

##### `JVMBytecodeEmitter._main_name`

```python
def _main_name(self, program: Program) -> str | None
```

Internal helper in `JVMBytecodeEmitter` for main name.

Defined at line 200.

### Functions

#### `emit_jvm_bytecode`

```python
def emit_jvm_bytecode(program: Program) -> str
```

Emits jvm bytecode output for the compiler.

Defined at line 204.

#### `_declaration_storage_names`

```python
def _declaration_storage_names(declaration: Declaration) -> list[str]
```

Internal helper in `pl1compinpy.codegen.jvm_bytecode` for declaration storage names.

Defined at line 208.

#### `_structure_leaf_names`

```python
def _structure_leaf_names(field: StructureField, prefix: list[str]) -> list[str]
```

Internal helper in `pl1compinpy.codegen.jvm_bytecode` for structure leaf names.

Defined at line 217.

## `pl1compinpy.codegen.jvm_classfile`

Source: `pl1compinpy/codegen/jvm_classfile.py`

Module containing jvm classfile support for the PL/I compiler.

### Classes

#### `ConstantPool`

```python
class ConstantPool
```

Data container describing constant pool values used by the compiler.

Defined at line 31.

Methods:

##### `ConstantPool.utf8`

```python
def utf8(self, value: str) -> int
```

Performs utf8 behavior in `ConstantPool`.

Defined at line 35.

##### `ConstantPool.class_info`

```python
def class_info(self, name: str) -> int
```

Performs class info behavior in `ConstantPool`.

Defined at line 42.

##### `ConstantPool.name_and_type`

```python
def name_and_type(self, name: str, descriptor: str) -> int
```

Performs name and type behavior in `ConstantPool`.

Defined at line 48.

##### `ConstantPool.method_ref`

```python
def method_ref(self, owner: str, name: str, descriptor: str) -> int
```

Performs method ref behavior in `ConstantPool`.

Defined at line 54.

##### `ConstantPool._add`

```python
def _add(self, entry: bytes) -> int
```

Internal helper in `ConstantPool` for add.

Defined at line 62.

##### `ConstantPool.bytes`

```python
def bytes(self) -> bytes
```

Performs bytes behavior in `ConstantPool`.

Defined at line 66.

#### `JVMProcedure`

```python
class JVMProcedure
```

Data container describing jvmprocedure values used by the compiler.

Defined at line 71.

Methods:

##### `JVMProcedure.descriptor`

```python
def descriptor(self) -> str
```

Performs descriptor behavior in `JVMProcedure`.

Defined at line 80.

#### `JVMClassFileEmitter`

```python
class JVMClassFileEmitter
```

Class implementing jvmclass file emitter behavior in the PL/I compiler.

Defined at line 84.

Methods:

##### `JVMClassFileEmitter.emit`

```python
def emit(self, program: Program, class_name: str = 'PL1Program') -> bytes
```

Performs emit behavior in `JVMClassFileEmitter`.

Defined at line 85.

##### `JVMClassFileEmitter._procedures`

```python
def _procedures(self, program: Program) -> list[JVMProcedure]
```

Internal helper in `JVMClassFileEmitter` for procedures.

Defined at line 137.

##### `JVMClassFileEmitter._procedure`

```python
def _procedure(self, name: str, procedure: Procedure) -> JVMProcedure
```

Internal helper in `JVMClassFileEmitter` for procedure.

Defined at line 146.

##### `JVMClassFileEmitter._return_value`

```python
def _return_value(self, statement: RawStatement, locals_map: dict[str, int]) -> bytes
```

Internal helper in `JVMClassFileEmitter` for return value.

Defined at line 176.

##### `JVMClassFileEmitter._expression`

```python
def _expression(self, expression: object, locals_map: dict[str, int]) -> bytes
```

Internal helper in `JVMClassFileEmitter` for expression.

Defined at line 183.

##### `JVMClassFileEmitter._constructor_code`

```python
def _constructor_code(self, pool: ConstantPool) -> bytes
```

Internal helper in `JVMClassFileEmitter` for constructor code.

Defined at line 199.

##### `JVMClassFileEmitter._method`

```python
def _method(self, pool: ConstantPool, name: str, descriptor: str, code: bytes, max_stack: int, max_locals: int) -> bytes
```

Internal helper in `JVMClassFileEmitter` for method.

Defined at line 202.

##### `JVMClassFileEmitter._iconst`

```python
def _iconst(self, value: int) -> bytes
```

Internal helper in `JVMClassFileEmitter` for iconst.

Defined at line 219.

##### `JVMClassFileEmitter._iload`

```python
def _iload(self, index: int) -> bytes
```

Internal helper in `JVMClassFileEmitter` for iload.

Defined at line 228.

##### `JVMClassFileEmitter._istore`

```python
def _istore(self, index: int) -> bytes
```

Internal helper in `JVMClassFileEmitter` for istore.

Defined at line 231.

##### `JVMClassFileEmitter._main_name`

```python
def _main_name(self, program: Program) -> str | None
```

Internal helper in `JVMClassFileEmitter` for main name.

Defined at line 234.

### Functions

#### `emit_jvm_class`

```python
def emit_jvm_class(program: Program, class_name: str = 'PL1Program') -> bytes
```

Emits jvm class output for the compiler.

Defined at line 238.

#### `emit_jvm_classes`

```python
def emit_jvm_classes(program: Program, class_name: str = 'PL1Program') -> dict[str, bytes]
```

Emits jvm classes output for the compiler.

Defined at line 242.

#### `_declaration_storage_names`

```python
def _declaration_storage_names(declaration: Declaration) -> list[str]
```

Internal helper in `pl1compinpy.codegen.jvm_classfile` for declaration storage names.

Defined at line 246.

#### `_structure_leaf_names`

```python
def _structure_leaf_names(field: StructureField, prefix: list[str]) -> list[str]
```

Internal helper in `pl1compinpy.codegen.jvm_classfile` for structure leaf names.

Defined at line 255.

## `pl1compinpy.codegen.libraries`

Source: `pl1compinpy/codegen/libraries.py`

Module containing libraries support for the PL/I compiler.

### Classes

#### `LibraryFormatError`

```python
class LibraryFormatError(ValueError)
```

Exception type raised for library format errors.

Defined at line 10.

#### `LibraryImage`

```python
class LibraryImage
```

Data container describing library image values used by the compiler.

Defined at line 24.

### Functions

#### `emit_library`

```python
def emit_library(format_name: str, program: Program | None = None, module_name: str = 'pl1module') -> bytes
```

Emits library output for the compiler.

Defined at line 29.

#### `_library_manifest`

```python
def _library_manifest(format_name: str, program: Program | None, module_name: str) -> bytes
```

Internal helper in `pl1compinpy.codegen.libraries` for library manifest.

Defined at line 42.

#### `_ar_archive`

```python
def _ar_archive(module_name: str, payload: bytes) -> bytes
```

Internal helper in `pl1compinpy.codegen.libraries` for ar archive.

Defined at line 56.

#### `_elf_shared`

```python
def _elf_shared(payload: bytes) -> bytes
```

Internal helper in `pl1compinpy.codegen.libraries` for elf shared.

Defined at line 62.

#### `_macho_dylib`

```python
def _macho_dylib(payload: bytes) -> bytes
```

Internal helper in `pl1compinpy.codegen.libraries` for macho dylib.

Defined at line 70.

#### `_pe_dll`

```python
def _pe_dll(payload: bytes) -> bytes
```

Internal helper in `pl1compinpy.codegen.libraries` for pe dll.

Defined at line 75.

## `pl1compinpy.codegen.linkers`

Source: `pl1compinpy/codegen/linkers.py`

Module containing linkers support for the PL/I compiler.

### Classes

#### `LinkRequest`

```python
class LinkRequest
```

Data container describing link request values used by the compiler.

Defined at line 10.

#### `LinkerError`

```python
class LinkerError(ValueError)
```

Exception type raised for linker errors.

Defined at line 15.

#### `ExecutableLinker`

```python
class ExecutableLinker
```

Facade for the platform executable container writers.

Defined at line 19.

Methods:

##### `ExecutableLinker.link`

```python
def link(self, request: LinkRequest) -> bytes
```

Performs link behavior in `ExecutableLinker`.

Defined at line 22.

#### `PELinker`

```python
class PELinker(ExecutableLinker)
```

Class implementing pelinker behavior in the PL/I compiler.

Defined at line 28.

Methods:

##### `PELinker.link_pe32_x586_windows`

```python
def link_pe32_x586_windows(self, program: Program | None = None) -> bytes
```

Performs link pe32 x586 windows behavior in `PELinker`.

Defined at line 29.

##### `PELinker.link_pe64_x86_64_windows`

```python
def link_pe64_x86_64_windows(self, program: Program | None = None) -> bytes
```

Performs link pe64 x86 64 windows behavior in `PELinker`.

Defined at line 32.

#### `ELFLinker`

```python
class ELFLinker(ExecutableLinker)
```

Class implementing elflinker behavior in the PL/I compiler.

Defined at line 36.

Methods:

##### `ELFLinker.link_elf64_x86_64`

```python
def link_elf64_x86_64(self, program: Program | None = None) -> bytes
```

Performs link elf64 x86 64 behavior in `ELFLinker`.

Defined at line 37.

##### `ELFLinker.link_elf64_aarch64`

```python
def link_elf64_aarch64(self, program: Program | None = None) -> bytes
```

Performs link elf64 aarch64 behavior in `ELFLinker`.

Defined at line 40.

#### `MachOLinker`

```python
class MachOLinker(ExecutableLinker)
```

Class implementing mach olinker behavior in the PL/I compiler.

Defined at line 44.

Methods:

##### `MachOLinker.link_macho64_x86_64_macos`

```python
def link_macho64_x86_64_macos(self, program: Program | None = None) -> bytes
```

Performs link macho64 x86 64 macos behavior in `MachOLinker`.

Defined at line 45.

##### `MachOLinker.link_macho64_arm64_macos`

```python
def link_macho64_arm64_macos(self, program: Program | None = None) -> bytes
```

Performs link macho64 arm64 macos behavior in `MachOLinker`.

Defined at line 48.

### Functions

#### `link_executable`

```python
def link_executable(format_name: str, program: Program | None = None) -> bytes
```

Performs link executable behavior in `pl1compinpy.codegen.linkers`.

Defined at line 52.

## `pl1compinpy.codegen.python_source`

Source: `pl1compinpy/codegen/python_source.py`

Module containing python source support for the PL/I compiler.

### Classes

#### `PythonSourceEmitter`

```python
class PythonSourceEmitter
```

Class implementing python source emitter behavior in the PL/I compiler.

Defined at line 30.

Methods:

##### `PythonSourceEmitter.emit`

```python
def emit(self, program: Program) -> str
```

Performs emit behavior in `PythonSourceEmitter`.

Defined at line 31.

##### `PythonSourceEmitter._statement`

```python
def _statement(self, statement: object, indent: int = 0) -> list[str]
```

Internal helper in `PythonSourceEmitter` for statement.

Defined at line 43.

##### `PythonSourceEmitter._io_statement`

```python
def _io_statement(self, statement: IOStatement, indent: int) -> list[str]
```

Internal helper in `PythonSourceEmitter` for io statement.

Defined at line 110.

##### `PythonSourceEmitter._select_statement`

```python
def _select_statement(self, statement: SelectStatement, indent: int) -> list[str]
```

Internal helper in `PythonSourceEmitter` for select statement.

Defined at line 125.

##### `PythonSourceEmitter._select_condition`

```python
def _select_condition(self, statement: SelectStatement, expressions: list[Expression]) -> str
```

Internal helper in `PythonSourceEmitter` for select condition.

Defined at line 138.

##### `PythonSourceEmitter._procedure`

```python
def _procedure(self, procedure: Procedure, indent: int) -> list[str]
```

Internal helper in `PythonSourceEmitter` for procedure.

Defined at line 146.

##### `PythonSourceEmitter._procedure_named`

```python
def _procedure_named(self, name: str, procedure: Procedure, indent: int) -> list[str]
```

Internal helper in `PythonSourceEmitter` for procedure named.

Defined at line 151.

##### `PythonSourceEmitter._body`

```python
def _body(self, statements: list[object], indent: int) -> list[str]
```

Internal helper in `PythonSourceEmitter` for body.

Defined at line 160.

##### `PythonSourceEmitter._expression`

```python
def _expression(self, expression: Expression) -> str
```

Internal helper in `PythonSourceEmitter` for expression.

Defined at line 168.

##### `PythonSourceEmitter._operator`

```python
def _operator(self, operator: str) -> str
```

Internal helper in `PythonSourceEmitter` for operator.

Defined at line 191.

##### `PythonSourceEmitter._declaration_initial_value`

```python
def _declaration_initial_value(self, declaration: Declaration, name: str) -> str
```

Internal helper in `PythonSourceEmitter` for declaration initial value.

Defined at line 207.

##### `PythonSourceEmitter._target`

```python
def _target(self, name: str) -> str
```

Internal helper in `PythonSourceEmitter` for target.

Defined at line 219.

##### `PythonSourceEmitter._pointer_target`

```python
def _pointer_target(self, name: str) -> tuple[str, str, list[str]]
```

Internal helper in `PythonSourceEmitter` for pointer target.

Defined at line 225.

##### `PythonSourceEmitter._structure_literal`

```python
def _structure_literal(self, field: object) -> str
```

Internal helper in `PythonSourceEmitter` for structure literal.

Defined at line 230.

##### `PythonSourceEmitter._main_arguments`

```python
def _main_arguments(self, procedure: Procedure) -> str
```

Internal helper in `PythonSourceEmitter` for main arguments.

Defined at line 244.

### Functions

#### `emit_python_source`

```python
def emit_python_source(program: Program) -> str
```

Emits python source output for the compiler.

Defined at line 257.

## `pl1compinpy.codegen.runtime_link`

Source: `pl1compinpy/codegen/runtime_link.py`

Module containing runtime link support for the PL/I compiler.

### Classes

#### `RuntimeLinkage`

```python
class RuntimeLinkage
```

Data container describing runtime linkage values used by the compiler.

Defined at line 10.

Methods:

##### `RuntimeLinkage.symbol`

```python
def symbol(self, name: str, prefix: str = '') -> str
```

Performs symbol behavior in `RuntimeLinkage`.

Defined at line 24.

#### `RuntimeLinkManifest`

```python
class RuntimeLinkManifest
```

Data container describing runtime link manifest values used by the compiler.

Defined at line 31.

Methods:

##### `RuntimeLinkManifest.to_bytes`

```python
def to_bytes(self) -> bytes
```

Performs to bytes behavior in `RuntimeLinkManifest`.

Defined at line 35.

### Functions

#### `runtime_linkage`

```python
def runtime_linkage(target: str) -> RuntimeLinkage
```

Performs runtime linkage behavior in `pl1compinpy.codegen.runtime_link`.

Defined at line 176.

#### `runtime_manifest`

```python
def runtime_manifest(target: str, program: Program | None = None) -> RuntimeLinkManifest
```

Performs runtime manifest behavior in `pl1compinpy.codegen.runtime_link`.

Defined at line 188.

#### `encoded_runtime_manifest`

```python
def encoded_runtime_manifest(target: str, program: Program | None = None) -> bytes
```

Performs encoded runtime manifest behavior in `pl1compinpy.codegen.runtime_link`.

Defined at line 192.

#### `_runtime_calls`

```python
def _runtime_calls(program: Program | None) -> set[str]
```

Internal helper in `pl1compinpy.codegen.runtime_link` for runtime calls.

Defined at line 196.

#### `_collect_runtime_calls`

```python
def _collect_runtime_calls(statement: Statement | None, calls: set[str]) -> None
```

Internal helper in `pl1compinpy.codegen.runtime_link` for collect runtime calls.

Defined at line 205.

## `pl1compinpy.compiler`

Source: `pl1compinpy/compiler.py`

Compatibility wrapper for the core compiler package.

## `pl1compinpy.core`

Source: `pl1compinpy/core/__init__.py`

Core AST and compiler orchestration.

## `pl1compinpy.core.ast`

Source: `pl1compinpy/core/ast.py`

Module containing ast support for the PL/I compiler.

### Classes

#### `AstNode`

```python
class AstNode
```

Class implementing ast node behavior in the PL/I compiler.

Defined at line 7.

Methods:

##### `AstNode.accept`

```python
def accept(self, visitor: 'AstVisitor') -> Any
```

Performs accept behavior in `AstNode`.

Defined at line 8.

#### `AstVisitor`

```python
class AstVisitor
```

Class implementing ast visitor behavior in the PL/I compiler.

Defined at line 12.

Methods:

##### `AstVisitor.visit`

```python
def visit(self, node: AstNode | None) -> Any
```

Performs visit behavior in `AstVisitor`.

Defined at line 13.

##### `AstVisitor.visit_children`

```python
def visit_children(self, node: AstNode) -> list[Any]
```

Performs visit children behavior in `AstVisitor`.

Defined at line 19.

##### `AstVisitor.generic_visit`

```python
def generic_visit(self, node: AstNode) -> Any
```

Performs generic visit behavior in `AstVisitor`.

Defined at line 26.

##### `AstVisitor._visit_value`

```python
def _visit_value(self, value: object) -> list[Any]
```

Internal helper in `AstVisitor` for visit value.

Defined at line 29.

#### `Program`

```python
class Program(AstNode)
```

Data container describing program values used by the compiler.

Defined at line 46.

#### `Statement`

```python
class Statement(AstNode)
```

Class implementing statement behavior in the PL/I compiler.

Defined at line 50.

#### `Assignment`

```python
class Assignment(Statement)
```

Data container describing assignment values used by the compiler.

Defined at line 55.

#### `StructureField`

```python
class StructureField(AstNode)
```

Data container describing structure field values used by the compiler.

Defined at line 61.

#### `Declaration`

```python
class Declaration(Statement)
```

Data container describing declaration values used by the compiler.

Defined at line 70.

#### `GenericAlternative`

```python
class GenericAlternative(AstNode)
```

Data container describing generic alternative values used by the compiler.

Defined at line 83.

#### `Call`

```python
class Call(Statement)
```

Data container describing call values used by the compiler.

Defined at line 89.

#### `Procedure`

```python
class Procedure(Statement)
```

Data container describing procedure values used by the compiler.

Defined at line 96.

#### `DoGroup`

```python
class DoGroup(Statement)
```

Data container describing do group values used by the compiler.

Defined at line 106.

#### `IfStatement`

```python
class IfStatement(Statement)
```

Data container describing if statement values used by the compiler.

Defined at line 114.

#### `IOStatement`

```python
class IOStatement(Statement)
```

Data container describing iostatement values used by the compiler.

Defined at line 121.

#### `SelectStatement`

```python
class SelectStatement(Statement)
```

Data container describing select statement values used by the compiler.

Defined at line 130.

#### `WhenBranch`

```python
class WhenBranch(AstNode)
```

Data container describing when branch values used by the compiler.

Defined at line 137.

#### `LabelledStatement`

```python
class LabelledStatement(Statement)
```

Data container describing labelled statement values used by the compiler.

Defined at line 143.

#### `GotoStatement`

```python
class GotoStatement(Statement)
```

Data container describing goto statement values used by the compiler.

Defined at line 149.

#### `PreprocessorStatement`

```python
class PreprocessorStatement(Statement)
```

Data container describing preprocessor statement values used by the compiler.

Defined at line 154.

#### `RawStatement`

```python
class RawStatement(Statement)
```

Data container describing raw statement values used by the compiler.

Defined at line 161.

#### `Expression`

```python
class Expression(AstNode)
```

Class implementing expression behavior in the PL/I compiler.

Defined at line 166.

#### `Identifier`

```python
class Identifier(Expression)
```

Data container describing identifier values used by the compiler.

Defined at line 171.

#### `FieldReference`

```python
class FieldReference(Expression)
```

Data container describing field reference values used by the compiler.

Defined at line 176.

Methods:

##### `FieldReference.name`

```python
def name(self) -> str
```

Performs name behavior in `FieldReference`.

Defined at line 181.

#### `PointerReference`

```python
class PointerReference(Expression)
```

Data container describing pointer reference values used by the compiler.

Defined at line 186.

Methods:

##### `PointerReference.name`

```python
def name(self) -> str
```

Performs name behavior in `PointerReference`.

Defined at line 192.

#### `FunctionCall`

```python
class FunctionCall(Expression)
```

Data container describing function call values used by the compiler.

Defined at line 198.

#### `NumberLiteral`

```python
class NumberLiteral(Expression)
```

Data container describing number literal values used by the compiler.

Defined at line 204.

#### `StringLiteral`

```python
class StringLiteral(Expression)
```

Data container describing string literal values used by the compiler.

Defined at line 209.

#### `BinaryExpression`

```python
class BinaryExpression(Expression)
```

Data container describing binary expression values used by the compiler.

Defined at line 214.

#### `UnaryExpression`

```python
class UnaryExpression(Expression)
```

Data container describing unary expression values used by the compiler.

Defined at line 221.

### Functions

#### `is_main_procedure`

```python
def is_main_procedure(procedure: Procedure) -> bool
```

Performs is main procedure behavior in `pl1compinpy.core.ast`.

Defined at line 226.

#### `procedure_from_statement`

```python
def procedure_from_statement(statement: Statement) -> Procedure | None
```

Performs procedure from statement behavior in `pl1compinpy.core.ast`.

Defined at line 230.

#### `procedure_entry_name`

```python
def procedure_entry_name(statement: Statement, default: str | None = None) -> str | None
```

Performs procedure entry name behavior in `pl1compinpy.core.ast`.

Defined at line 238.

#### `main_procedure_entry`

```python
def main_procedure_entry(program: Program) -> tuple[str, Procedure] | None
```

Performs main procedure entry behavior in `pl1compinpy.core.ast`.

Defined at line 250.

#### `main_procedure_name`

```python
def main_procedure_name(program: Program) -> str | None
```

Performs main procedure name behavior in `pl1compinpy.core.ast`.

Defined at line 259.

## `pl1compinpy.core.compiler`

Source: `pl1compinpy/core/compiler.py`

Module containing compiler support for the PL/I compiler.

### Classes

#### `Compiler`

```python
class Compiler
```

Class implementing compiler behavior in the PL/I compiler.

Defined at line 11.

Methods:

##### `Compiler.compile`

```python
def compile(self, source: str, target: str = 'python-source', builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None) -> str
```

Performs compile behavior in `Compiler`.

Defined at line 12.

##### `Compiler.compile_sources`

```python
def compile_sources(self, sources: list[str], target: str = 'python-source', builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None) -> str
```

Compiles PL/I input into sources output.

Defined at line 16.

##### `Compiler.compile_paths`

```python
def compile_paths(self, paths: list[str | Path], target: str = 'python-source', builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None) -> str
```

Compiles PL/I input into paths output.

Defined at line 20.

##### `Compiler.program_from_sources`

```python
def program_from_sources(self, sources: list[str], builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None)
```

Performs program from sources behavior in `Compiler`.

Defined at line 24.

##### `Compiler.program_from_paths`

```python
def program_from_paths(self, paths: list[str | Path], builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None)
```

Performs program from paths behavior in `Compiler`.

Defined at line 30.

### Functions

#### `compile_source`

```python
def compile_source(source: str, target: str = 'python-source', builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None) -> str
```

Compiles PL/I input into source output.

Defined at line 37.

#### `compile_sources`

```python
def compile_sources(sources: list[str], target: str = 'python-source', builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None) -> str
```

Compiles PL/I input into sources output.

Defined at line 41.

#### `compile_paths`

```python
def compile_paths(paths: list[str | Path], target: str = 'python-source', builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None) -> str
```

Compiles PL/I input into paths output.

Defined at line 45.

#### `available_targets`

```python
def available_targets() -> tuple[str, ...]
```

Performs available targets behavior in `pl1compinpy.core.compiler`.

Defined at line 49.

#### `available_binary_formats`

```python
def available_binary_formats() -> tuple[str, ...]
```

Performs available binary formats behavior in `pl1compinpy.core.compiler`.

Defined at line 53.

#### `available_library_formats`

```python
def available_library_formats() -> tuple[str, ...]
```

Performs available library formats behavior in `pl1compinpy.core.compiler`.

Defined at line 57.

#### `compile_binary`

```python
def compile_binary(format_name: str, source: str | None = None, builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None) -> bytes
```

Compiles PL/I input into binary output.

Defined at line 61.

#### `compile_jvm_classes`

```python
def compile_jvm_classes(source: str, builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None) -> dict[str, bytes]
```

Compiles PL/I input into jvm classes output.

Defined at line 66.

#### `compile_dotnet_executable`

```python
def compile_dotnet_executable(source: str, output: str | Path, builtins: list[str] | None = None, ilasm: str | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None) -> Path
```

Compiles PL/I input into dotnet executable output.

Defined at line 71.

#### `compile_library`

```python
def compile_library(format_name: str, source: str | None = None, builtins: list[str] | None = None, include_dirs: list[str | Path] | None = None, base_dir: str | Path | None = None, module_name: str = 'pl1module') -> bytes
```

Compiles PL/I input into library output.

Defined at line 76.

## `pl1compinpy.frontend`

Source: `pl1compinpy/frontend/__init__.py`

Lexing, keyword metadata, and parsing for PL1CompInPy.

## `pl1compinpy.frontend.include`

Source: `pl1compinpy/frontend/include.py`

Module containing include support for the PL/I compiler.

### Classes

#### `IncludeError`

```python
class IncludeError(ValueError)
```

Exception type raised for include errors.

Defined at line 8.

#### `IncludeExpander`

```python
class IncludeExpander
```

Data container describing include expander values used by the compiler.

Defined at line 13.

Methods:

##### `IncludeExpander.expand`

```python
def expand(self, source: str, *, base_dir: Path | None = None) -> str
```

Performs expand behavior in `IncludeExpander`.

Defined at line 19.

##### `IncludeExpander.expand_file`

```python
def expand_file(self, path: Path) -> str
```

Performs expand file behavior in `IncludeExpander`.

Defined at line 23.

##### `IncludeExpander._expand_source`

```python
def _expand_source(self, source: str, base_dir: Path, stack: list[Path]) -> str
```

Internal helper in `IncludeExpander` for expand source.

Defined at line 27.

##### `IncludeExpander._include_directive`

```python
def _include_directive(self, line: str) -> tuple[str, str] | None
```

Internal helper in `IncludeExpander` for include directive.

Defined at line 49.

##### `IncludeExpander._resolve_member`

```python
def _resolve_member(self, member: str, base_dir: Path) -> Path | None
```

Internal helper in `IncludeExpander` for resolve member.

Defined at line 63.

### Functions

#### `expand_includes`

```python
def expand_includes(source: str, include_dirs: list[str | Path] | None = None, *, base_dir: str | Path | None = None) -> str
```

Performs expand includes behavior in `pl1compinpy.frontend.include`.

Defined at line 78.

#### `expand_include_file`

```python
def expand_include_file(path: str | Path, include_dirs: list[str | Path] | None = None) -> str
```

Performs expand include file behavior in `pl1compinpy.frontend.include`.

Defined at line 83.

## `pl1compinpy.frontend.keywords`

Source: `pl1compinpy/frontend/keywords.py`

Module containing keywords support for the PL/I compiler.

### Classes

#### `KeywordInfo`

```python
class KeywordInfo
```

Data container describing keyword info values used by the compiler.

Defined at line 7.

### Functions

#### `_add`

```python
def _add(word: str, category: str, meaning: str, *aliases: str) -> None
```

Internal helper in `pl1compinpy.frontend.keywords` for add.

Defined at line 18.

#### `keyword_info`

```python
def keyword_info(word: str) -> KeywordInfo | None
```

Performs keyword info behavior in `pl1compinpy.frontend.keywords`.

Defined at line 175.

## `pl1compinpy.frontend.lexer`

Source: `pl1compinpy/frontend/lexer.py`

Module containing lexer support for the PL/I compiler.

### Classes

#### `TokenType`

```python
class TokenType(str, Enum)
```

Class implementing token type behavior in the PL/I compiler.

Defined at line 9.

#### `Token`

```python
class Token
```

Data container describing token values used by the compiler.

Defined at line 41.

Methods:

##### `Token.is_keyword`

```python
def is_keyword(self) -> bool
```

Performs is keyword behavior in `Token`.

Defined at line 49.

#### `LexerError`

```python
class LexerError(ValueError)
```

Exception type raised for lexer errors.

Defined at line 53.

#### `Lexer`

```python
class Lexer
```

Class implementing lexer behavior in the PL/I compiler.

Defined at line 57.

Methods:

##### `Lexer.__init__`

```python
def __init__(self, source: str) -> None
```

Initializes an instance of `Lexer`.

Defined at line 58.

##### `Lexer.tokenize`

```python
def tokenize(self) -> list[Token]
```

Tokenizes PL/I source text for the parser.

Defined at line 64.

##### `Lexer._at_end`

```python
def _at_end(self) -> bool
```

Internal helper in `Lexer` for at end.

Defined at line 87.

##### `Lexer._peek`

```python
def _peek(self) -> str
```

Internal helper in `Lexer` for peek.

Defined at line 90.

##### `Lexer._peek_next`

```python
def _peek_next(self) -> str
```

Internal helper in `Lexer` for peek next.

Defined at line 93.

##### `Lexer._advance`

```python
def _advance(self) -> str
```

Internal helper in `Lexer` for advance.

Defined at line 99.

##### `Lexer._advance_line`

```python
def _advance_line(self) -> None
```

Internal helper in `Lexer` for advance line.

Defined at line 105.

##### `Lexer._identifier`

```python
def _identifier(self) -> Token
```

Internal helper in `Lexer` for identifier.

Defined at line 110.

##### `Lexer._number`

```python
def _number(self) -> Token
```

Internal helper in `Lexer` for number.

Defined at line 119.

##### `Lexer._string`

```python
def _string(self) -> Token
```

Internal helper in `Lexer` for string.

Defined at line 131.

##### `Lexer._comment`

```python
def _comment(self) -> None
```

Internal helper in `Lexer` for comment.

Defined at line 146.

##### `Lexer._symbol`

```python
def _symbol(self) -> Token
```

Internal helper in `Lexer` for symbol.

Defined at line 162.

## `pl1compinpy.frontend.parser`

Source: `pl1compinpy/frontend/parser.py`

Module containing parser support for the PL/I compiler.

### Classes

#### `ParserError`

```python
class ParserError(ValueError)
```

Exception type raised for parser errors.

Defined at line 35.

#### `Parser`

```python
class Parser
```

Class implementing parser behavior in the PL/I compiler.

Defined at line 39.

Methods:

##### `Parser.__init__`

```python
def __init__(self, tokens: list[Token]) -> None
```

Initializes an instance of `Parser`.

Defined at line 40.

##### `Parser.parse`

```python
def parse(self) -> Program
```

Parses lexer tokens into the compiler's AST representation.

Defined at line 44.

##### `Parser._statement`

```python
def _statement(self) -> Statement
```

Internal helper in `Parser` for statement.

Defined at line 52.

##### `Parser._declaration`

```python
def _declaration(self) -> Declaration
```

Internal helper in `Parser` for declaration.

Defined at line 98.

##### `Parser._dimensions_from_tokens`

```python
def _dimensions_from_tokens(self, tokens: list[Token], index: int) -> tuple[list[int], int]
```

Internal helper in `Parser` for dimensions from tokens.

Defined at line 174.

##### `Parser._file_options_from_tokens`

```python
def _file_options_from_tokens(self, tokens: list[Token]) -> dict[str, str]
```

Internal helper in `Parser` for file options from tokens.

Defined at line 182.

##### `Parser._generic_options_from_tokens`

```python
def _generic_options_from_tokens(self, names: list[str], tokens: list[Token]) -> dict[str, list[GenericAlternative]]
```

Internal helper in `Parser` for generic options from tokens.

Defined at line 201.

##### `Parser._picture_options_from_tokens`

```python
def _picture_options_from_tokens(self, names: list[str], tokens: list[Token]) -> dict[str, str]
```

Internal helper in `Parser` for picture options from tokens.

Defined at line 220.

##### `Parser._picture_pattern_from_tokens`

```python
def _picture_pattern_from_tokens(self, tokens: list[Token], index: int) -> tuple[str, int]
```

Internal helper in `Parser` for picture pattern from tokens.

Defined at line 232.

##### `Parser._based_options_from_tokens`

```python
def _based_options_from_tokens(self, names: list[str], tokens: list[Token]) -> dict[str, str | None]
```

Internal helper in `Parser` for based options from tokens.

Defined at line 262.

##### `Parser._pointer_names_from_tokens`

```python
def _pointer_names_from_tokens(self, names: list[str], tokens: list[Token]) -> list[str]
```

Internal helper in `Parser` for pointer names from tokens.

Defined at line 275.

##### `Parser._builtin_names_from_tokens`

```python
def _builtin_names_from_tokens(self, tokens: list[Token]) -> list[str]
```

Internal helper in `Parser` for builtin names from tokens.

Defined at line 284.

##### `Parser._structures_from_tokens`

```python
def _structures_from_tokens(self, tokens: list[Token]) -> dict[str, StructureField]
```

Internal helper in `Parser` for structures from tokens.

Defined at line 292.

##### `Parser._declaration_segments`

```python
def _declaration_segments(self, tokens: list[Token]) -> list[list[Token]]
```

Internal helper in `Parser` for declaration segments.

Defined at line 317.

##### `Parser._procedure`

```python
def _procedure(self, name: str | None) -> Procedure
```

Internal helper in `Parser` for procedure.

Defined at line 336.

##### `Parser._collect_until_balanced_rparen`

```python
def _collect_until_balanced_rparen(self) -> list[Token]
```

Internal helper in `Parser` for collect until balanced rparen.

Defined at line 370.

##### `Parser._do_group`

```python
def _do_group(self) -> DoGroup
```

Internal helper in `Parser` for do group.

Defined at line 387.

##### `Parser._do_control_condition`

```python
def _do_control_condition(self, tokens: list[Token], keyword: str) -> Expression | None
```

Internal helper in `Parser` for do control condition.

Defined at line 407.

##### `Parser._if_statement`

```python
def _if_statement(self) -> IfStatement
```

Internal helper in `Parser` for if statement.

Defined at line 416.

##### `Parser._call_statement`

```python
def _call_statement(self) -> Call
```

Internal helper in `Parser` for call statement.

Defined at line 423.

##### `Parser._io_statement`

```python
def _io_statement(self) -> IOStatement
```

Internal helper in `Parser` for io statement.

Defined at line 442.

##### `Parser._select_statement`

```python
def _select_statement(self) -> SelectStatement
```

Internal helper in `Parser` for select statement.

Defined at line 452.

##### `Parser._assignment`

```python
def _assignment(self) -> Assignment
```

Internal helper in `Parser` for assignment.

Defined at line 479.

##### `Parser._raw_statement`

```python
def _raw_statement(self) -> RawStatement
```

Internal helper in `Parser` for raw statement.

Defined at line 484.

##### `Parser._goto_statement`

```python
def _goto_statement(self) -> GotoStatement
```

Internal helper in `Parser` for goto statement.

Defined at line 489.

##### `Parser._preprocessor_statement`

```python
def _preprocessor_statement(self) -> PreprocessorStatement
```

Internal helper in `Parser` for preprocessor statement.

Defined at line 494.

##### `Parser._expression`

```python
def _expression(self) -> Expression
```

Internal helper in `Parser` for expression.

Defined at line 509.

##### `Parser._parse_precedence`

```python
def _parse_precedence(self, minimum: int) -> Expression
```

Internal helper in `Parser` for parse precedence.

Defined at line 512.

##### `Parser._primary`

```python
def _primary(self) -> Expression
```

Internal helper in `Parser` for primary.

Defined at line 531.

##### `Parser._expression_from_tokens`

```python
def _expression_from_tokens(self, tokens: list[Token]) -> Expression
```

Internal helper in `Parser` for expression from tokens.

Defined at line 561.

##### `Parser._expressions_until_rparen`

```python
def _expressions_until_rparen(self) -> list[Expression]
```

Internal helper in `Parser` for expressions until rparen.

Defined at line 565.

##### `Parser._option_value`

```python
def _option_value(self, tokens: list[Token], keyword: str) -> str | None
```

Internal helper in `Parser` for option value.

Defined at line 576.

##### `Parser._option_tokens`

```python
def _option_tokens(self, tokens: list[Token], keyword: str) -> list[Token]
```

Internal helper in `Parser` for option tokens.

Defined at line 582.

##### `Parser._io_options_from_tokens`

```python
def _io_options_from_tokens(self, tokens: list[Token]) -> dict[str, Expression]
```

Internal helper in `Parser` for io options from tokens.

Defined at line 607.

##### `Parser._identifier_list_until`

```python
def _identifier_list_until(self, end: TokenType) -> list[str]
```

Internal helper in `Parser` for identifier list until.

Defined at line 615.

##### `Parser._type_text`

```python
def _type_text(self, tokens: list[Token]) -> str
```

Internal helper in `Parser` for type text.

Defined at line 625.

##### `Parser._collect_until_semicolon`

```python
def _collect_until_semicolon(self) -> list[Token]
```

Internal helper in `Parser` for collect until semicolon.

Defined at line 628.

##### `Parser._collect_until_keyword`

```python
def _collect_until_keyword(self, *keywords: str) -> list[Token]
```

Internal helper in `Parser` for collect until keyword.

Defined at line 642.

##### `Parser._looks_like_label`

```python
def _looks_like_label(self) -> bool
```

Internal helper in `Parser` for looks like label.

Defined at line 656.

##### `Parser._looks_like_assignment_target`

```python
def _looks_like_assignment_target(self) -> bool
```

Internal helper in `Parser` for looks like assignment target.

Defined at line 659.

##### `Parser._assignment_target`

```python
def _assignment_target(self) -> str
```

Internal helper in `Parser` for assignment target.

Defined at line 669.

##### `Parser._field_suffix`

```python
def _field_suffix(self) -> list[str]
```

Internal helper in `Parser` for field suffix.

Defined at line 679.

##### `Parser._starts_raw_statement`

```python
def _starts_raw_statement(self) -> bool
```

Internal helper in `Parser` for starts raw statement.

Defined at line 685.

##### `Parser._match`

```python
def _match(self, *types: TokenType) -> bool
```

Internal helper in `Parser` for match.

Defined at line 711.

##### `Parser._match_semicolon`

```python
def _match_semicolon(self) -> bool
```

Internal helper in `Parser` for match semicolon.

Defined at line 717.

##### `Parser._match_keyword`

```python
def _match_keyword(self, *keywords: str) -> bool
```

Internal helper in `Parser` for match keyword.

Defined at line 720.

##### `Parser._previous_keyword`

```python
def _previous_keyword(self, keyword: str) -> bool
```

Internal helper in `Parser` for previous keyword.

Defined at line 726.

##### `Parser._check`

```python
def _check(self, token_type: TokenType) -> bool
```

Internal helper in `Parser` for check.

Defined at line 729.

##### `Parser._check_next`

```python
def _check_next(self, token_type: TokenType) -> bool
```

Internal helper in `Parser` for check next.

Defined at line 732.

##### `Parser._check_keyword`

```python
def _check_keyword(self, *keywords: str) -> bool
```

Internal helper in `Parser` for check keyword.

Defined at line 737.

##### `Parser._check_next_keyword`

```python
def _check_next_keyword(self, *keywords: str) -> bool
```

Internal helper in `Parser` for check next keyword.

Defined at line 741.

##### `Parser._consume`

```python
def _consume(self, token_type: TokenType, message: str) -> Token
```

Internal helper in `Parser` for consume.

Defined at line 747.

##### `Parser._consume_identifier`

```python
def _consume_identifier(self, message: str) -> Token
```

Internal helper in `Parser` for consume identifier.

Defined at line 752.

##### `Parser._advance`

```python
def _advance(self) -> Token
```

Internal helper in `Parser` for advance.

Defined at line 757.

##### `Parser._peek`

```python
def _peek(self) -> Token
```

Internal helper in `Parser` for peek.

Defined at line 762.

##### `Parser._previous`

```python
def _previous(self) -> Token
```

Internal helper in `Parser` for previous.

Defined at line 765.

##### `Parser._error`

```python
def _error(self, token: Token, message: str) -> ParserError
```

Internal helper in `Parser` for error.

Defined at line 768.

## `pl1compinpy.frontend.precedence`

Source: `pl1compinpy/frontend/precedence.py`

Module containing precedence support for the PL/I compiler.

### Classes

#### `Associativity`

```python
class Associativity(str, Enum)
```

Class implementing associativity behavior in the PL/I compiler.

Defined at line 9.

#### `OperatorInfo`

```python
class OperatorInfo
```

Data container describing operator info values used by the compiler.

Defined at line 15.

### Functions

#### `binary_operator`

```python
def binary_operator(token: Token) -> OperatorInfo | None
```

Performs binary operator behavior in `pl1compinpy.frontend.precedence`.

Defined at line 74.

#### `prefix_operator`

```python
def prefix_operator(token: Token) -> OperatorInfo | None
```

Performs prefix operator behavior in `pl1compinpy.frontend.precedence`.

Defined at line 83.

#### `operator_precedence_table`

```python
def operator_precedence_table() -> list[OperatorInfo]
```

Performs operator precedence table behavior in `pl1compinpy.frontend.precedence`.

Defined at line 91.

## `pl1compinpy.frontend.preprocessor`

Source: `pl1compinpy/frontend/preprocessor.py`

Module containing preprocessor support for the PL/I compiler.

### Classes

#### `PreprocessorError`

```python
class PreprocessorError(ValueError)
```

Exception type raised for preprocessor errors.

Defined at line 74.

#### `CompileTimeSymbol`

```python
class CompileTimeSymbol
```

Data container describing compile time symbol values used by the compiler.

Defined at line 79.

#### `PreprocessorState`

```python
class PreprocessorState
```

Data container describing preprocessor state values used by the compiler.

Defined at line 88.

Methods:

##### `PreprocessorState.ensure_symbol`

```python
def ensure_symbol(self, name: str, datatype: str = 'CHARACTER') -> CompileTimeSymbol
```

Performs ensure symbol behavior in `PreprocessorState`.

Defined at line 97.

#### `_ConditionalFrame`

```python
class _ConditionalFrame
```

Data container describing conditional frame values used by the compiler.

Defined at line 105.

#### `IBMStylePreprocessor`

```python
class IBMStylePreprocessor
```

Small IBM PL/I-style compile-time layer used before lexing.

The class intentionally keeps macro procedures hook-oriented, but it evaluates
the common source-shaping directives that fit PL1CompInPy today: include
expansion, compile-time declarations and assignments, activation flags,
replacements, notes, and simple conditional blocks.

Defined at line 111.

Methods:

##### `IBMStylePreprocessor.__init__`

```python
def __init__(self, include_dirs: list[str | Path] | None = None, *, strict: bool = False, sysp_arm: str = '', suffixes: tuple[str, ...] = ('', '.pl1', '.pli', '.inc')) -> None
```

Initializes an instance of `IBMStylePreprocessor`.

Defined at line 120.

##### `IBMStylePreprocessor.preprocess`

```python
def preprocess(self, source: str, *, base_dir: str | Path | None = None) -> str
```

Performs preprocess behavior in `IBMStylePreprocessor`.

Defined at line 134.

##### `IBMStylePreprocessor.preprocess_file`

```python
def preprocess_file(self, path: str | Path) -> str
```

Performs preprocess file behavior in `IBMStylePreprocessor`.

Defined at line 138.

##### `IBMStylePreprocessor.compile_time_tables`

```python
def compile_time_tables(self) -> dict[str, Any]
```

Compiles PL/I input into time tables output.

Defined at line 143.

##### `IBMStylePreprocessor.register_builtin`

```python
def register_builtin(self, name: str, handler: Callable[..., Any]) -> None
```

Performs register builtin behavior in `IBMStylePreprocessor`.

Defined at line 152.

##### `IBMStylePreprocessor.apply_source_replacements`

```python
def apply_source_replacements(self, text: str) -> str
```

Performs apply source replacements behavior in `IBMStylePreprocessor`.

Defined at line 159.

##### `IBMStylePreprocessor._init_builtins`

```python
def _init_builtins(self) -> None
```

Internal helper in `IBMStylePreprocessor` for init builtins.

Defined at line 162.

##### `IBMStylePreprocessor._process_lines`

```python
def _process_lines(self, lines: list[str]) -> str
```

Internal helper in `IBMStylePreprocessor` for process lines.

Defined at line 190.

##### `IBMStylePreprocessor._directive`

```python
def _directive(self, line: str) -> tuple[str, str] | None
```

Internal helper in `IBMStylePreprocessor` for directive.

Defined at line 256.

##### `IBMStylePreprocessor._condition_payload`

```python
def _condition_payload(self, payload: str) -> str
```

Internal helper in `IBMStylePreprocessor` for condition payload.

Defined at line 262.

##### `IBMStylePreprocessor._declare`

```python
def _declare(self, payload: str) -> None
```

Internal helper in `IBMStylePreprocessor` for declare.

Defined at line 265.

##### `IBMStylePreprocessor._activate`

```python
def _activate(self, payload: str, active: bool) -> None
```

Internal helper in `IBMStylePreprocessor` for activate.

Defined at line 275.

##### `IBMStylePreprocessor._replace`

```python
def _replace(self, payload: str) -> None
```

Internal helper in `IBMStylePreprocessor` for replace.

Defined at line 280.

##### `IBMStylePreprocessor._assignment`

```python
def _assignment(self, command: str, payload: str) -> bool
```

Internal helper in `IBMStylePreprocessor` for assignment.

Defined at line 292.

##### `IBMStylePreprocessor._eval_expr`

```python
def _eval_expr(self, expr: str) -> Any
```

Internal helper in `IBMStylePreprocessor` for eval expr.

Defined at line 300.

##### `IBMStylePreprocessor._counter`

```python
def _counter(self) -> int
```

Internal helper in `IBMStylePreprocessor` for counter.

Defined at line 340.

##### `IBMStylePreprocessor._translate`

```python
def _translate(self, value: Any, to: Any, from_: Any | None = None) -> str
```

Internal helper in `IBMStylePreprocessor` for translate.

Defined at line 344.

### Functions

#### `preprocess_source`

```python
def preprocess_source(source: str, include_dirs: list[str | Path] | None = None, *, base_dir: str | Path | None = None, strict: bool = False, sysp_arm: str = '') -> str
```

Performs preprocess source behavior in `pl1compinpy.frontend.preprocessor`.

Defined at line 352.

#### `rewrite_identifiers_outside_literals`

```python
def rewrite_identifiers_outside_literals(text: str, mapping: dict[str, str]) -> str
```

Performs rewrite identifiers outside literals behavior in `pl1compinpy.frontend.preprocessor`.

Defined at line 363.

#### `split_top_level_commas`

```python
def split_top_level_commas(text: str) -> list[str]
```

Performs split top level commas behavior in `pl1compinpy.frontend.preprocessor`.

Defined at line 398.

#### `is_quoted_literal`

```python
def is_quoted_literal(text: str) -> bool
```

Performs is quoted literal behavior in `pl1compinpy.frontend.preprocessor`.

Defined at line 428.

#### `unquote_pli`

```python
def unquote_pli(text: str) -> str
```

Performs unquote pli behavior in `pl1compinpy.frontend.preprocessor`.

Defined at line 433.

## `pl1compinpy.runtime`

Source: `pl1compinpy/runtime/__init__.py`

Runtime normalization and calling-convention support.

## `pl1compinpy.runtime.arrays`

Source: `pl1compinpy/runtime/arrays.py`

Module containing arrays support for the PL/I compiler.

### Classes

#### `ArrayRuntimeError`

```python
class ArrayRuntimeError(ValueError)
```

Exception type raised for array runtime errors.

Defined at line 10.

#### `ArrayValue`

```python
class ArrayValue
```

Data container describing array value values used by the compiler.

Defined at line 15.

Methods:

##### `ArrayValue.__post_init__`

```python
def __post_init__(self) -> None
```

Internal helper in `ArrayValue` for post init.

Defined at line 22.

##### `ArrayValue.element_count`

```python
def element_count(self) -> int
```

Performs element count behavior in `ArrayValue`.

Defined at line 28.

##### `ArrayValue.index`

```python
def index(self, *subscripts: int) -> int
```

Performs index behavior in `ArrayValue`.

Defined at line 31.

##### `ArrayValue.get`

```python
def get(self, *subscripts: int) -> int
```

Performs get behavior in `ArrayValue`.

Defined at line 43.

##### `ArrayValue.set`

```python
def set(self, value: int, *subscripts: int) -> None
```

Performs set behavior in `ArrayValue`.

Defined at line 46.

#### `ArrayRuntime`

```python
class ArrayRuntime
```

Class implementing array runtime behavior in the PL/I compiler.

Defined at line 50.

Methods:

##### `ArrayRuntime.__init__`

```python
def __init__(self, heap: HeapRuntime | None = None) -> None
```

Initializes an instance of `ArrayRuntime`.

Defined at line 51.

##### `ArrayRuntime.allocate_array`

```python
def allocate_array(self, name: str, dimensions: list[int], element_size: int = 4) -> ArrayValue
```

Performs allocate array behavior in `ArrayRuntime`.

Defined at line 55.

##### `ArrayRuntime.free_array`

```python
def free_array(self, name: str) -> None
```

Performs free array behavior in `ArrayRuntime`.

Defined at line 64.

## `pl1compinpy.runtime.based`

Source: `pl1compinpy/runtime/based.py`

Module containing based support for the PL/I compiler.

### Classes

#### `BasedRuntimeError`

```python
class BasedRuntimeError(ValueError)
```

Exception type raised for based runtime errors.

Defined at line 8.

#### `PointerValue`

```python
class PointerValue
```

Data container describing pointer value values used by the compiler.

Defined at line 13.

Methods:

##### `PointerValue.is_null`

```python
def is_null(self) -> bool
```

Performs is null behavior in `PointerValue`.

Defined at line 18.

#### `BasedRecord`

```python
class BasedRecord
```

Data container describing based record values used by the compiler.

Defined at line 23.

#### `BasedRuntime`

```python
class BasedRuntime
```

Class implementing based runtime behavior in the PL/I compiler.

Defined at line 29.

Methods:

##### `BasedRuntime.__init__`

```python
def __init__(self, heap: HeapRuntime | None = None) -> None
```

Initializes an instance of `BasedRuntime`.

Defined at line 30.

##### `BasedRuntime.declare_pointer`

```python
def declare_pointer(self, name: str) -> PointerValue
```

Performs declare pointer behavior in `BasedRuntime`.

Defined at line 35.

##### `BasedRuntime.declare_based_record`

```python
def declare_based_record(self, name: str, size: int, pointer_name: str | None = None) -> BasedRecord
```

Performs declare based record behavior in `BasedRuntime`.

Defined at line 39.

##### `BasedRuntime.allocate_based`

```python
def allocate_based(self, record_name: str, pointer_name: str | None = None) -> PointerValue
```

Performs allocate based behavior in `BasedRuntime`.

Defined at line 48.

##### `BasedRuntime.set_pointer`

```python
def set_pointer(self, pointer_name: str, handle: int, offset: int = 0) -> PointerValue
```

Performs set pointer behavior in `BasedRuntime`.

Defined at line 59.

##### `BasedRuntime.set_pointer_to_record`

```python
def set_pointer_to_record(self, pointer_name: str, record_name: str, source_pointer: str | None = None) -> PointerValue
```

Performs set pointer to record behavior in `BasedRuntime`.

Defined at line 71.

##### `BasedRuntime.pointer_for_record`

```python
def pointer_for_record(self, record_name: str, pointer_name: str | None = None) -> PointerValue
```

Performs pointer for record behavior in `BasedRuntime`.

Defined at line 77.

##### `BasedRuntime.storage_for`

```python
def storage_for(self, record_name: str, pointer_name: str | None = None) -> memoryview
```

Performs storage for behavior in `BasedRuntime`.

Defined at line 87.

##### `BasedRuntime.write_record`

```python
def write_record(self, record_name: str, data: bytes, pointer_name: str | None = None) -> None
```

Performs write record behavior in `BasedRuntime`.

Defined at line 96.

##### `BasedRuntime.read_record`

```python
def read_record(self, record_name: str, pointer_name: str | None = None) -> bytes
```

Performs read record behavior in `BasedRuntime`.

Defined at line 104.

##### `BasedRuntime._record`

```python
def _record(self, name: str) -> BasedRecord
```

Internal helper in `BasedRuntime` for record.

Defined at line 107.

## `pl1compinpy.runtime.calculation`

Source: `pl1compinpy/runtime/calculation.py`

Module containing calculation support for the PL/I compiler.

### Classes

#### `CalculationError`

```python
class CalculationError(ValueError)
```

Exception type raised for calculation errors.

Defined at line 12.

#### `PL1Type`

```python
class PL1Type(str, Enum)
```

Class implementing pl1 type behavior in the PL/I compiler.

Defined at line 16.

#### `PL1Value`

```python
class PL1Value
```

Data container describing pl1 value values used by the compiler.

Defined at line 25.

Methods:

##### `PL1Value.truthy`

```python
def truthy(self) -> bool
```

Performs truthy behavior in `PL1Value`.

Defined at line 30.

#### `NumericTower`

```python
class NumericTower
```

Class implementing numeric tower behavior in the PL/I compiler.

Defined at line 40.

Methods:

##### `NumericTower.value`

```python
def value(self, raw: object, type_name: PL1Type | str | None = None) -> PL1Value
```

Performs value behavior in `NumericTower`.

Defined at line 48.

##### `NumericTower.cast`

```python
def cast(self, value: PL1Value, target: PL1Type | str) -> PL1Value
```

Performs cast behavior in `NumericTower`.

Defined at line 55.

##### `NumericTower.promote`

```python
def promote(self, left: PL1Value, right: PL1Value) -> tuple[PL1Value, PL1Value, PL1Type]
```

Performs promote behavior in `NumericTower`.

Defined at line 91.

##### `NumericTower._infer`

```python
def _infer(self, raw: object) -> PL1Type
```

Internal helper in `NumericTower` for infer.

Defined at line 99.

#### `CalculationEngine`

```python
class CalculationEngine
```

Class implementing calculation engine behavior in the PL/I compiler.

Defined at line 113.

Methods:

##### `CalculationEngine.__init__`

```python
def __init__(self, variables: dict[str, PL1Value | object] | None = None, resolver: Callable[[Expression], PL1Value | object] | None = None) -> None
```

Initializes an instance of `CalculationEngine`.

Defined at line 114.

##### `CalculationEngine.evaluate`

```python
def evaluate(self, expression: Expression) -> PL1Value
```

Performs evaluate behavior in `CalculationEngine`.

Defined at line 119.

##### `CalculationEngine.cast`

```python
def cast(self, value: PL1Value | object, target: PL1Type | str) -> PL1Value
```

Performs cast behavior in `CalculationEngine`.

Defined at line 147.

##### `CalculationEngine._number`

```python
def _number(self, text: str) -> PL1Value
```

Internal helper in `CalculationEngine` for number.

Defined at line 150.

##### `CalculationEngine._unary`

```python
def _unary(self, expression: UnaryExpression) -> PL1Value
```

Internal helper in `CalculationEngine` for unary.

Defined at line 155.

##### `CalculationEngine._binary`

```python
def _binary(self, expression: BinaryExpression) -> PL1Value
```

Internal helper in `CalculationEngine` for binary.

Defined at line 168.

##### `CalculationEngine._compare`

```python
def _compare(self, left: PL1Value, right: PL1Value, op: str) -> bool
```

Internal helper in `CalculationEngine` for compare.

Defined at line 204.

##### `CalculationEngine._comparable`

```python
def _comparable(self, value: object) -> object
```

Internal helper in `CalculationEngine` for comparable.

Defined at line 221.

## `pl1compinpy.runtime.calling`

Source: `pl1compinpy/runtime/calling.py`

Module containing calling support for the PL/I compiler.

### Classes

#### `RuntimeError`

```python
class RuntimeError(ValueError)
```

Exception type raised for runtime errors.

Defined at line 17.

### Functions

#### `normalize_calls`

```python
def normalize_calls(program: Program) -> Program
```

Performs normalize calls behavior in `pl1compinpy.runtime.calling`.

Defined at line 21.

#### `_procedure_table`

```python
def _procedure_table(statements: list[Statement]) -> dict[str, Procedure]
```

Internal helper in `pl1compinpy.runtime.calling` for procedure table.

Defined at line 29.

#### `_normalize_statement`

```python
def _normalize_statement(statement: Statement, procedures: dict[str, Procedure], table: FunctionTable) -> Statement
```

Internal helper in `pl1compinpy.runtime.calling` for normalize statement.

Defined at line 40.

#### `_normalize_call`

```python
def _normalize_call(call: Call, procedures: dict[str, Procedure], table: FunctionTable) -> Call
```

Internal helper in `pl1compinpy.runtime.calling` for normalize call.

Defined at line 67.

#### `_descriptor_parameter_names`

```python
def _descriptor_parameter_names(descriptor: FunctionDescriptor) -> list[str]
```

Internal helper in `pl1compinpy.runtime.calling` for descriptor parameter names.

Defined at line 87.

## `pl1compinpy.runtime.command_line`

Source: `pl1compinpy/runtime/command_line.py`

Module containing command line support for the PL/I compiler.

### Classes

#### `CommandLineRuntime`

```python
class CommandLineRuntime
```

Data container describing command line runtime values used by the compiler.

Defined at line 8.

Methods:

##### `CommandLineRuntime.from_argv`

```python
def from_argv(cls, argv: list[str] | tuple[str, ...] | None = None) -> 'CommandLineRuntime'
```

Performs from argv behavior in `CommandLineRuntime`.

Defined at line 12.

##### `CommandLineRuntime.program_name`

```python
def program_name(self) -> str
```

Performs program name behavior in `CommandLineRuntime`.

Defined at line 16.

##### `CommandLineRuntime.arguments`

```python
def arguments(self) -> tuple[str, ...]
```

Performs arguments behavior in `CommandLineRuntime`.

Defined at line 20.

##### `CommandLineRuntime.command`

```python
def command(self) -> str
```

Performs command behavior in `CommandLineRuntime`.

Defined at line 23.

##### `CommandLineRuntime.argc`

```python
def argc(self) -> int
```

Performs argc behavior in `CommandLineRuntime`.

Defined at line 26.

##### `CommandLineRuntime.argv_value`

```python
def argv_value(self, index: int) -> str
```

Performs argv value behavior in `CommandLineRuntime`.

Defined at line 29.

##### `CommandLineRuntime.bind_main_parameters`

```python
def bind_main_parameters(self, parameter_names: list[str]) -> list[object]
```

Performs bind main parameters behavior in `CommandLineRuntime`.

Defined at line 37.

## `pl1compinpy.runtime.decimal`

Source: `pl1compinpy/runtime/decimal.py`

Module containing decimal support for the PL/I compiler.

### Classes

#### `FixedDecimal`

```python
class FixedDecimal
```

Data container describing fixed decimal values used by the compiler.

Defined at line 15.

Methods:

##### `FixedDecimal.from_decimal`

```python
def from_decimal(cls, value: Decimal, precision: int, scale: int = 0) -> 'FixedDecimal'
```

Performs from decimal behavior in `FixedDecimal`.

Defined at line 21.

##### `FixedDecimal.from_string`

```python
def from_string(cls, text: str, precision: int, scale: int = 0) -> 'FixedDecimal'
```

Performs from string behavior in `FixedDecimal`.

Defined at line 29.

##### `FixedDecimal.from_int`

```python
def from_int(cls, value: int, precision: int, scale: int = 0) -> 'FixedDecimal'
```

Performs from int behavior in `FixedDecimal`.

Defined at line 33.

##### `FixedDecimal.from_float`

```python
def from_float(cls, value: float, precision: int, scale: int = 0) -> 'FixedDecimal'
```

Performs from float behavior in `FixedDecimal`.

Defined at line 37.

##### `FixedDecimal.decimal`

```python
def decimal(self) -> Decimal
```

Performs decimal behavior in `FixedDecimal`.

Defined at line 40.

##### `FixedDecimal.string`

```python
def string(self) -> str
```

Performs string behavior in `FixedDecimal`.

Defined at line 43.

##### `FixedDecimal.__str__`

```python
def __str__(self) -> str
```

Internal helper in `FixedDecimal` for str.

Defined at line 47.

##### `FixedDecimal.__eq__`

```python
def __eq__(self, other: object) -> bool
```

Internal helper in `FixedDecimal` for eq.

Defined at line 50.

##### `FixedDecimal.int`

```python
def int(self) -> int
```

Performs int behavior in `FixedDecimal`.

Defined at line 57.

##### `FixedDecimal.float`

```python
def float(self) -> float
```

Performs float behavior in `FixedDecimal`.

Defined at line 60.

##### `FixedDecimal.check`

```python
def check(self) -> None
```

Performs check behavior in `FixedDecimal`.

Defined at line 63.

##### `FixedDecimal.rescale`

```python
def rescale(self, precision: int, scale: int) -> 'FixedDecimal'
```

Performs rescale behavior in `FixedDecimal`.

Defined at line 68.

##### `FixedDecimal.add`

```python
def add(self, other: 'FixedDecimal') -> 'FixedDecimal'
```

Performs add behavior in `FixedDecimal`.

Defined at line 71.

##### `FixedDecimal.sub`

```python
def sub(self, other: 'FixedDecimal') -> 'FixedDecimal'
```

Performs sub behavior in `FixedDecimal`.

Defined at line 78.

##### `FixedDecimal.mul`

```python
def mul(self, other: 'FixedDecimal') -> 'FixedDecimal'
```

Performs mul behavior in `FixedDecimal`.

Defined at line 85.

##### `FixedDecimal.div`

```python
def div(self, other: 'FixedDecimal', precision: int | None = None, scale: int | None = None) -> 'FixedDecimal'
```

Performs div behavior in `FixedDecimal`.

Defined at line 88.

#### `ZonedDecimalCodec`

```python
class ZonedDecimalCodec
```

Class implementing zoned decimal codec behavior in the PL/I compiler.

Defined at line 102.

Methods:

##### `ZonedDecimalCodec.encode`

```python
def encode(value: FixedDecimal, signed: bool = True, overpunch: bool = True) -> str
```

Performs encode behavior in `ZonedDecimalCodec`.

Defined at line 104.

##### `ZonedDecimalCodec.decode`

```python
def decode(text: str, precision: int, scale: int = 0) -> FixedDecimal
```

Performs decode behavior in `ZonedDecimalCodec`.

Defined at line 114.

#### `PackedDecimalCodec`

```python
class PackedDecimalCodec
```

Class implementing packed decimal codec behavior in the PL/I compiler.

Defined at line 130.

Methods:

##### `PackedDecimalCodec.encode`

```python
def encode(value: FixedDecimal) -> bytes
```

Performs encode behavior in `PackedDecimalCodec`.

Defined at line 135.

##### `PackedDecimalCodec.decode`

```python
def decode(data: bytes | bytearray, precision: int, scale: int = 0) -> FixedDecimal
```

Performs decode behavior in `PackedDecimalCodec`.

Defined at line 144.

#### `DecimalRuntime`

```python
class DecimalRuntime
```

Class implementing decimal runtime behavior in the PL/I compiler.

Defined at line 162.

Methods:

##### `DecimalRuntime.fixed_decimal`

```python
def fixed_decimal(value: Decimal | str | int | float | FixedDecimal, precision: int, scale: int = 0) -> FixedDecimal
```

Performs fixed decimal behavior in `DecimalRuntime`.

Defined at line 164.

##### `DecimalRuntime.convert`

```python
def convert(value: Any, source: str, target: str, *, precision: int, scale: int = 0) -> Any
```

Performs convert behavior in `DecimalRuntime`.

Defined at line 176.

##### `DecimalRuntime.to_fixed_decimal`

```python
def to_fixed_decimal(value: Any, source: str, precision: int, scale: int = 0) -> FixedDecimal
```

Performs to fixed decimal behavior in `DecimalRuntime`.

Defined at line 196.

#### `CalculationBuiltinRuntime`

```python
class CalculationBuiltinRuntime
```

Class implementing calculation builtin runtime behavior in the PL/I compiler.

Defined at line 237.

Methods:

##### `CalculationBuiltinRuntime.ABS`

```python
def ABS(self, value: Any) -> Any
```

Performs abs behavior in `CalculationBuiltinRuntime`.

Defined at line 238.

##### `CalculationBuiltinRuntime.SIGN`

```python
def SIGN(self, value: Any) -> int
```

Performs sign behavior in `CalculationBuiltinRuntime`.

Defined at line 245.

##### `CalculationBuiltinRuntime.MIN`

```python
def MIN(self, *args: Any) -> Any
```

Performs min behavior in `CalculationBuiltinRuntime`.

Defined at line 249.

##### `CalculationBuiltinRuntime.MAX`

```python
def MAX(self, *args: Any) -> Any
```

Performs max behavior in `CalculationBuiltinRuntime`.

Defined at line 252.

##### `CalculationBuiltinRuntime.MOD`

```python
def MOD(self, left: Any, right: Any) -> int
```

Performs mod behavior in `CalculationBuiltinRuntime`.

Defined at line 255.

##### `CalculationBuiltinRuntime.TRUNC`

```python
def TRUNC(self, value: Any, scale: Any = 0) -> FixedDecimal
```

Performs trunc behavior in `CalculationBuiltinRuntime`.

Defined at line 258.

##### `CalculationBuiltinRuntime.ROUND`

```python
def ROUND(self, value: Any, scale: Any = 0) -> FixedDecimal
```

Performs round behavior in `CalculationBuiltinRuntime`.

Defined at line 263.

##### `CalculationBuiltinRuntime.CEIL`

```python
def CEIL(self, value: Any) -> int
```

Performs ceil behavior in `CalculationBuiltinRuntime`.

Defined at line 268.

##### `CalculationBuiltinRuntime.FLOOR`

```python
def FLOOR(self, value: Any) -> int
```

Performs floor behavior in `CalculationBuiltinRuntime`.

Defined at line 271.

##### `CalculationBuiltinRuntime.SQRT`

```python
def SQRT(self, value: Any) -> Any
```

Performs sqrt behavior in `CalculationBuiltinRuntime`.

Defined at line 274.

##### `CalculationBuiltinRuntime.EXP`

```python
def EXP(self, value: Any) -> float
```

Performs exp behavior in `CalculationBuiltinRuntime`.

Defined at line 279.

##### `CalculationBuiltinRuntime.LOG`

```python
def LOG(self, value: Any) -> float
```

Performs log behavior in `CalculationBuiltinRuntime`.

Defined at line 282.

##### `CalculationBuiltinRuntime.SIN`

```python
def SIN(self, value: Any) -> float
```

Performs sin behavior in `CalculationBuiltinRuntime`.

Defined at line 285.

##### `CalculationBuiltinRuntime.COS`

```python
def COS(self, value: Any) -> float
```

Performs cos behavior in `CalculationBuiltinRuntime`.

Defined at line 288.

##### `CalculationBuiltinRuntime.TAN`

```python
def TAN(self, value: Any) -> float
```

Performs tan behavior in `CalculationBuiltinRuntime`.

Defined at line 291.

##### `CalculationBuiltinRuntime.REAL`

```python
def REAL(self, value: Any) -> Any
```

Performs real behavior in `CalculationBuiltinRuntime`.

Defined at line 294.

##### `CalculationBuiltinRuntime.IMAG`

```python
def IMAG(self, value: Any) -> Any
```

Performs imag behavior in `CalculationBuiltinRuntime`.

Defined at line 297.

##### `CalculationBuiltinRuntime.CONJG`

```python
def CONJG(self, value: Any) -> complex
```

Performs conjg behavior in `CalculationBuiltinRuntime`.

Defined at line 300.

##### `CalculationBuiltinRuntime.LENGTH`

```python
def LENGTH(self, value: Any) -> int
```

Performs length behavior in `CalculationBuiltinRuntime`.

Defined at line 303.

##### `CalculationBuiltinRuntime.SUBSTR`

```python
def SUBSTR(self, value: Any, start: Any, count: Any | None = None) -> str
```

Performs substr behavior in `CalculationBuiltinRuntime`.

Defined at line 310.

##### `CalculationBuiltinRuntime.INDEX`

```python
def INDEX(self, value: Any, needle: Any) -> int
```

Performs index behavior in `CalculationBuiltinRuntime`.

Defined at line 315.

##### `CalculationBuiltinRuntime.FIXED_DECIMAL`

```python
def FIXED_DECIMAL(self, value: Any, precision: Any, scale: Any = 0) -> FixedDecimal
```

Performs fixed decimal behavior in `CalculationBuiltinRuntime`.

Defined at line 321.

##### `CalculationBuiltinRuntime.DECIMAL_TO_PACKED`

```python
def DECIMAL_TO_PACKED(self, value: Any, precision: Any, scale: Any = 0) -> bytes
```

Performs decimal to packed behavior in `CalculationBuiltinRuntime`.

Defined at line 324.

##### `CalculationBuiltinRuntime.DECIMAL_FROM_PACKED`

```python
def DECIMAL_FROM_PACKED(self, value: Any, precision: Any, scale: Any = 0) -> FixedDecimal
```

Performs decimal from packed behavior in `CalculationBuiltinRuntime`.

Defined at line 328.

##### `CalculationBuiltinRuntime.DECIMAL_TO_ZONED`

```python
def DECIMAL_TO_ZONED(self, value: Any, precision: Any, scale: Any = 0) -> str
```

Performs decimal to zoned behavior in `CalculationBuiltinRuntime`.

Defined at line 331.

##### `CalculationBuiltinRuntime.DECIMAL_FROM_ZONED`

```python
def DECIMAL_FROM_ZONED(self, value: Any, precision: Any, scale: Any = 0) -> FixedDecimal
```

Performs decimal from zoned behavior in `CalculationBuiltinRuntime`.

Defined at line 335.

### Functions

#### `to_decimal`

```python
def to_decimal(value: Any) -> Decimal
```

Performs to decimal behavior in `pl1compinpy.runtime.decimal`.

Defined at line 215.

#### `to_python_float`

```python
def to_python_float(value: Any) -> float
```

Performs to python float behavior in `pl1compinpy.runtime.decimal`.

Defined at line 231.

## `pl1compinpy.runtime.dynload`

Source: `pl1compinpy/runtime/dynload.py`

Module containing dynload support for the PL/I compiler.

### Classes

#### `DynamicLoadError`

```python
class DynamicLoadError(ValueError)
```

Exception type raised for dynamic load errors.

Defined at line 9.

#### `DynamicLibraryHandle`

```python
class DynamicLibraryHandle
```

Data container describing dynamic library handle values used by the compiler.

Defined at line 14.

#### `JavaClassLoadRequest`

```python
class JavaClassLoadRequest
```

Data container describing java class load request values used by the compiler.

Defined at line 20.

#### `DotNetAssemblyLoadRequest`

```python
class DotNetAssemblyLoadRequest
```

Data container describing dot net assembly load request values used by the compiler.

Defined at line 26.

#### `DynamicLoadRuntime`

```python
class DynamicLoadRuntime
```

Class implementing dynamic load runtime behavior in the PL/I compiler.

Defined at line 31.

Methods:

##### `DynamicLoadRuntime.dynload`

```python
def dynload(self, path: str | Path) -> DynamicLibraryHandle
```

Performs dynload behavior in `DynamicLoadRuntime`.

Defined at line 32.

##### `DynamicLoadRuntime.symbol`

```python
def symbol(self, library: DynamicLibraryHandle, name: str) -> Any
```

Performs symbol behavior in `DynamicLoadRuntime`.

Defined at line 39.

##### `DynamicLoadRuntime.java_class`

```python
def java_class(self, class_name: str, classpath: list[str] | tuple[str, ...] | None = None) -> JavaClassLoadRequest
```

Performs java class behavior in `DynamicLoadRuntime`.

Defined at line 45.

##### `DynamicLoadRuntime.dotnet_assembly`

```python
def dotnet_assembly(self, assembly_name: str, type_name: str | None = None) -> DotNetAssemblyLoadRequest
```

Performs dotnet assembly behavior in `DynamicLoadRuntime`.

Defined at line 48.

## `pl1compinpy.runtime.function_table`

Source: `pl1compinpy/runtime/function_table.py`

Module containing function table support for the PL/I compiler.

### Classes

#### `FunctionTableError`

```python
class FunctionTableError(ValueError)
```

Exception type raised for function table errors.

Defined at line 9.

#### `ParameterDescriptor`

```python
class ParameterDescriptor
```

Data container describing parameter descriptor values used by the compiler.

Defined at line 14.

#### `FunctionDescriptor`

```python
class FunctionDescriptor
```

Data container describing function descriptor values used by the compiler.

Defined at line 22.

Methods:

##### `FunctionDescriptor.normalized_name`

```python
def normalized_name(self) -> str
```

Performs normalized name behavior in `FunctionDescriptor`.

Defined at line 33.

#### `FunctionTable`

```python
class FunctionTable
```

Data container describing function table values used by the compiler.

Defined at line 38.

Methods:

##### `FunctionTable.add_function`

```python
def add_function(self, descriptor: FunctionDescriptor) -> FunctionDescriptor
```

Performs add function behavior in `FunctionTable`.

Defined at line 42.

##### `FunctionTable.add_runtime`

```python
def add_runtime(self, name: str, pointer: Callable[..., Any] | str, parameters: list[ParameterDescriptor] | None = None, returns: str | None = None, *, default_mode: str = 'reference', variadic: bool = False) -> FunctionDescriptor
```

Performs add runtime behavior in `FunctionTable`.

Defined at line 46.

##### `FunctionTable.add_builtin`

```python
def add_builtin(self, name: str, pointer: Callable[..., Any] | str, parameters: list[ParameterDescriptor] | None = None, returns: str | None = None, *, default_mode: str = 'reference', variadic: bool = False) -> FunctionDescriptor
```

Performs add builtin behavior in `FunctionTable`.

Defined at line 68.

##### `FunctionTable.add_procedure`

```python
def add_procedure(self, name: str, procedure: Procedure) -> FunctionDescriptor
```

Performs add procedure behavior in `FunctionTable`.

Defined at line 91.

##### `FunctionTable.merge`

```python
def merge(self, other: 'FunctionTable') -> 'FunctionTable'
```

Performs merge behavior in `FunctionTable`.

Defined at line 104.

##### `FunctionTable.declare_builtin`

```python
def declare_builtin(self, name: str) -> None
```

Performs declare builtin behavior in `FunctionTable`.

Defined at line 110.

##### `FunctionTable.get`

```python
def get(self, name: str) -> FunctionDescriptor
```

Performs get behavior in `FunctionTable`.

Defined at line 113.

##### `FunctionTable.validate_call`

```python
def validate_call(self, call: Call) -> FunctionDescriptor
```

Performs validate call behavior in `FunctionTable`.

Defined at line 119.

##### `FunctionTable.call`

```python
def call(self, name: str, *arguments: Any, mode: str = 'reference', **keyword_arguments: Any) -> Any
```

Performs call behavior in `FunctionTable`.

Defined at line 134.

##### `FunctionTable._validate_by_name`

```python
def _validate_by_name(self, call: Call, descriptor: FunctionDescriptor) -> None
```

Internal helper in `FunctionTable` for validate by name.

Defined at line 144.

### Functions

#### `build_dynamic_function_table`

```python
def build_dynamic_function_table(program: Program) -> FunctionTable
```

Performs build dynamic function table behavior in `pl1compinpy.runtime.function_table`.

Defined at line 151.

#### `declare_program_builtins`

```python
def declare_program_builtins(program: Program, table: FunctionTable) -> FunctionTable
```

Performs declare program builtins behavior in `pl1compinpy.runtime.function_table`.

Defined at line 158.

#### `declared_builtins`

```python
def declared_builtins(program: Program) -> set[str]
```

Performs declared builtins behavior in `pl1compinpy.runtime.function_table`.

Defined at line 164.

#### `_declare_statement_builtins`

```python
def _declare_statement_builtins(statement: Statement | None, table: FunctionTable) -> None
```

Internal helper in `pl1compinpy.runtime.function_table` for declare statement builtins.

Defined at line 170.

#### `_add_statement_function`

```python
def _add_statement_function(table: FunctionTable, statement: Statement) -> None
```

Internal helper in `pl1compinpy.runtime.function_table` for add statement function.

Defined at line 199.

#### `validate_program_calls`

```python
def validate_program_calls(program: Program, table: FunctionTable) -> None
```

Performs validate program calls behavior in `pl1compinpy.runtime.function_table`.

Defined at line 207.

#### `_validate_statement_calls`

```python
def _validate_statement_calls(statement: Statement | None, table: FunctionTable) -> None
```

Internal helper in `pl1compinpy.runtime.function_table` for validate statement calls.

Defined at line 212.

#### `_validate_expression_calls`

```python
def _validate_expression_calls(expression: Expression, table: FunctionTable) -> None
```

Internal helper in `pl1compinpy.runtime.function_table` for validate expression calls.

Defined at line 245.

#### `runtime_function_table`

```python
def runtime_function_table() -> FunctionTable
```

Performs runtime function table behavior in `pl1compinpy.runtime.function_table`.

Defined at line 257.

## `pl1compinpy.runtime.generics`

Source: `pl1compinpy/runtime/generics.py`

Module containing generics support for the PL/I compiler.

### Classes

#### `GenericRuntimeError`

```python
class GenericRuntimeError(ValueError)
```

Exception type raised for generic runtime errors.

Defined at line 7.

#### `GenericFunction`

```python
class GenericFunction
```

Data container describing generic function values used by the compiler.

Defined at line 24.

Methods:

##### `GenericFunction.when`

```python
def when(self, parameter_types: list[str], implementation: Callable[..., object]) -> 'GenericFunction'
```

Performs when behavior in `GenericFunction`.

Defined at line 28.

##### `GenericFunction.__call__`

```python
def __call__(self, *arguments: object) -> object
```

Internal helper in `GenericFunction` for call.

Defined at line 32.

#### `GenericRuntime`

```python
class GenericRuntime
```

Class implementing generic runtime behavior in the PL/I compiler.

Defined at line 41.

Methods:

##### `GenericRuntime.__init__`

```python
def __init__(self) -> None
```

Initializes an instance of `GenericRuntime`.

Defined at line 42.

##### `GenericRuntime.define`

```python
def define(self, name: str) -> GenericFunction
```

Performs define behavior in `GenericRuntime`.

Defined at line 45.

##### `GenericRuntime.call`

```python
def call(self, name: str, *arguments: object) -> object
```

Performs call behavior in `GenericRuntime`.

Defined at line 49.

### Functions

#### `pl1_type`

```python
def pl1_type(value: object) -> str
```

Performs pl1 type behavior in `pl1compinpy.runtime.generics`.

Defined at line 11.

## `pl1compinpy.runtime.heap`

Source: `pl1compinpy/runtime/heap.py`

Module containing heap support for the PL/I compiler.

### Classes

#### `HeapRuntimeError`

```python
class HeapRuntimeError(ValueError)
```

Exception type raised for heap runtime errors.

Defined at line 6.

#### `HeapBlock`

```python
class HeapBlock
```

Data container describing heap block values used by the compiler.

Defined at line 11.

Methods:

##### `HeapBlock.size`

```python
def size(self) -> int
```

Performs size behavior in `HeapBlock`.

Defined at line 16.

#### `HeapRuntime`

```python
class HeapRuntime
```

Class implementing heap runtime behavior in the PL/I compiler.

Defined at line 20.

Methods:

##### `HeapRuntime.__init__`

```python
def __init__(self) -> None
```

Initializes an instance of `HeapRuntime`.

Defined at line 21.

##### `HeapRuntime.allocate`

```python
def allocate(self, size: int) -> int
```

Performs allocate behavior in `HeapRuntime`.

Defined at line 25.

##### `HeapRuntime.free`

```python
def free(self, handle: int) -> None
```

Performs free behavior in `HeapRuntime`.

Defined at line 33.

##### `HeapRuntime.block`

```python
def block(self, handle: int) -> HeapBlock
```

Performs block behavior in `HeapRuntime`.

Defined at line 38.

## `pl1compinpy.runtime.io`

Source: `pl1compinpy/runtime/io.py`

Module containing io support for the PL/I compiler.

### Classes

#### `FileRuntimeError`

```python
class FileRuntimeError(ValueError)
```

Exception type raised for file runtime errors.

Defined at line 10.

#### `FileDescriptor`

```python
class FileDescriptor
```

Data container describing file descriptor values used by the compiler.

Defined at line 15.

Methods:

##### `FileDescriptor.from_declaration`

```python
def from_declaration(cls, declaration: Declaration, base_path: Path | None = None) -> 'FileDescriptor'
```

Performs from declaration behavior in `FileDescriptor`.

Defined at line 25.

#### `StdioRuntime`

```python
class StdioRuntime
```

Class implementing stdio runtime behavior in the PL/I compiler.

Defined at line 46.

Methods:

##### `StdioRuntime.__init__`

```python
def __init__(self) -> None
```

Initializes an instance of `StdioRuntime`.

Defined at line 47.

##### `StdioRuntime.open`

```python
def open(self, descriptor: FileDescriptor) -> None
```

Performs open behavior in `StdioRuntime`.

Defined at line 50.

##### `StdioRuntime.close`

```python
def close(self, descriptor: FileDescriptor) -> None
```

Performs close behavior in `StdioRuntime`.

Defined at line 54.

##### `StdioRuntime.write_record`

```python
def write_record(self, descriptor: FileDescriptor, data: bytes | str) -> None
```

Performs write record behavior in `StdioRuntime`.

Defined at line 59.

##### `StdioRuntime.read_record`

```python
def read_record(self, descriptor: FileDescriptor) -> bytes | str
```

Performs read record behavior in `StdioRuntime`.

Defined at line 81.

##### `StdioRuntime.execute`

```python
def execute(self, statement: IOStatement, descriptors: dict[str, FileDescriptor], variables: dict[str, object] | None = None) -> None
```

Performs execute behavior in `StdioRuntime`.

Defined at line 100.

##### `StdioRuntime._io_value`

```python
def _io_value(self, statement: IOStatement, variables: dict[str, object]) -> bytes | str
```

Internal helper in `StdioRuntime` for io value.

Defined at line 118.

##### `StdioRuntime._handle`

```python
def _handle(self, descriptor: FileDescriptor) -> BinaryIO
```

Internal helper in `StdioRuntime` for handle.

Defined at line 129.

## `pl1compinpy.runtime.picture`

Source: `pl1compinpy/runtime/picture.py`

Module containing picture support for the PL/I compiler.

### Classes

#### `PictureRuntimeError`

```python
class PictureRuntimeError(ValueError)
```

Exception type raised for picture runtime errors.

Defined at line 7.

#### `PictureSpec`

```python
class PictureSpec
```

Data container describing picture spec values used by the compiler.

Defined at line 12.

Methods:

##### `PictureSpec.scale`

```python
def scale(self) -> int
```

Performs scale behavior in `PictureSpec`.

Defined at line 16.

##### `PictureSpec.integer_digits`

```python
def integer_digits(self) -> int
```

Performs integer digits behavior in `PictureSpec`.

Defined at line 25.

##### `PictureSpec.storage_width`

```python
def storage_width(self) -> int
```

Performs storage width behavior in `PictureSpec`.

Defined at line 31.

##### `PictureSpec.format`

```python
def format(self, value: int | float | Decimal | str) -> str
```

Performs format behavior in `PictureSpec`.

Defined at line 34.

##### `PictureSpec.parse`

```python
def parse(self, text: str) -> Decimal
```

Parses lexer tokens into the compiler's AST representation.

Defined at line 67.

##### `PictureSpec._first_required_integer_index`

```python
def _first_required_integer_index(self) -> int
```

Internal helper in `PictureSpec` for first required integer index.

Defined at line 79.

##### `PictureSpec._digit_count`

```python
def _digit_count(self, text: str) -> int
```

Internal helper in `PictureSpec` for digit count.

Defined at line 87.

#### `PictureRuntime`

```python
class PictureRuntime
```

Class implementing picture runtime behavior in the PL/I compiler.

Defined at line 91.

Methods:

##### `PictureRuntime.compile`

```python
def compile(self, pattern: str) -> PictureSpec
```

Performs compile behavior in `PictureRuntime`.

Defined at line 92.

##### `PictureRuntime.fixed_to_picture`

```python
def fixed_to_picture(self, value: int | Decimal, pattern: str) -> str
```

Performs fixed to picture behavior in `PictureRuntime`.

Defined at line 99.

##### `PictureRuntime.float_to_picture`

```python
def float_to_picture(self, value: float, pattern: str) -> str
```

Performs float to picture behavior in `PictureRuntime`.

Defined at line 102.

##### `PictureRuntime.picture_to_fixed`

```python
def picture_to_fixed(self, text: str, pattern: str) -> Decimal
```

Performs picture to fixed behavior in `PictureRuntime`.

Defined at line 105.

##### `PictureRuntime.picture_to_float`

```python
def picture_to_float(self, text: str, pattern: str) -> float
```

Performs picture to float behavior in `PictureRuntime`.

Defined at line 108.

## `pl1compinpy.runtime.pointers`

Source: `pl1compinpy/runtime/pointers.py`

Module containing pointers support for the PL/I compiler.

### Classes

#### `PointerBuiltinRuntimeError`

```python
class PointerBuiltinRuntimeError(ValueError)
```

Exception type raised for pointer builtin runtime errors.

Defined at line 11.

#### `PointerBuiltinRuntime`

```python
class PointerBuiltinRuntime
```

Class implementing pointer builtin runtime behavior in the PL/I compiler.

Defined at line 15.

Methods:

##### `PointerBuiltinRuntime.POINTER`

```python
def POINTER(self, value: Any = None, offset: Any = 0) -> PointerValue
```

Performs pointer behavior in `PointerBuiltinRuntime`.

Defined at line 16.

##### `PointerBuiltinRuntime._integer`

```python
def _integer(self, value: Any) -> int
```

Internal helper in `PointerBuiltinRuntime` for integer.

Defined at line 28.

## `pl1compinpy.runtime.socket_io`

Source: `pl1compinpy/runtime/socket_io.py`

Module containing socket io support for the PL/I compiler.

### Classes

#### `SocketRuntimeError`

```python
class SocketRuntimeError(ValueError)
```

Exception type raised for socket runtime errors.

Defined at line 11.

#### `SocketSecureMode`

```python
class SocketSecureMode(str, Enum)
```

Class implementing socket secure mode behavior in the PL/I compiler.

Defined at line 15.

#### `SocketDescriptor`

```python
class SocketDescriptor
```

Data container describing socket descriptor values used by the compiler.

Defined at line 22.

Methods:

##### `SocketDescriptor.tcp_client`

```python
def tcp_client(cls, name: str, host: str, port: int, timeout: float | None = None) -> 'SocketDescriptor'
```

Performs tcp client behavior in `SocketDescriptor`.

Defined at line 36.

##### `SocketDescriptor.tcp_server`

```python
def tcp_server(cls, name: str, host: str = '127.0.0.1', port: int = 0, timeout: float | None = None) -> 'SocketDescriptor'
```

Performs tcp server behavior in `SocketDescriptor`.

Defined at line 40.

##### `SocketDescriptor.ssl_client`

```python
def ssl_client(cls, name: str, host: str, port: int, timeout: float | None = None, verify: bool = True) -> 'SocketDescriptor'
```

Performs ssl client behavior in `SocketDescriptor`.

Defined at line 44.

##### `SocketDescriptor.tls_client`

```python
def tls_client(cls, name: str, host: str, port: int, timeout: float | None = None, verify: bool = True) -> 'SocketDescriptor'
```

Performs tls client behavior in `SocketDescriptor`.

Defined at line 48.

#### `SocketHandle`

```python
class SocketHandle
```

Data container describing socket handle values used by the compiler.

Defined at line 53.

Methods:

##### `SocketHandle.address`

```python
def address(self) -> tuple[str, int]
```

Performs address behavior in `SocketHandle`.

Defined at line 59.

#### `SocketFileDescriptor`

```python
class SocketFileDescriptor
```

Data container describing socket file descriptor values used by the compiler.

Defined at line 65.

Methods:

##### `SocketFileDescriptor.from_endpoint`

```python
def from_endpoint(cls, endpoint: SocketDescriptor, *, recfm: str = 'UNIX', lrecl: int | None = None, text: bool = False) -> 'SocketFileDescriptor'
```

Performs from endpoint behavior in `SocketFileDescriptor`.

Defined at line 73.

#### `SocketRuntime`

```python
class SocketRuntime
```

Class implementing socket runtime behavior in the PL/I compiler.

Defined at line 84.

Methods:

##### `SocketRuntime.__init__`

```python
def __init__(self) -> None
```

Initializes an instance of `SocketRuntime`.

Defined at line 85.

##### `SocketRuntime.open`

```python
def open(self, descriptor: SocketDescriptor) -> SocketHandle
```

Performs open behavior in `SocketRuntime`.

Defined at line 88.

##### `SocketRuntime.listen`

```python
def listen(self, descriptor: SocketDescriptor, backlog: int = 1) -> SocketHandle
```

Performs listen behavior in `SocketRuntime`.

Defined at line 93.

##### `SocketRuntime.connect`

```python
def connect(self, descriptor: SocketDescriptor) -> SocketHandle
```

Performs connect behavior in `SocketRuntime`.

Defined at line 108.

##### `SocketRuntime.accept`

```python
def accept(self, listener_name: str, client_name: str) -> SocketHandle
```

Performs accept behavior in `SocketRuntime`.

Defined at line 117.

##### `SocketRuntime.send`

```python
def send(self, name: str, data: bytes | str) -> None
```

Performs send behavior in `SocketRuntime`.

Defined at line 139.

##### `SocketRuntime.receive`

```python
def receive(self, name: str, size: int = 4096) -> bytes
```

Performs receive behavior in `SocketRuntime`.

Defined at line 143.

##### `SocketRuntime.close`

```python
def close(self, name: str) -> None
```

Performs close behavior in `SocketRuntime`.

Defined at line 146.

##### `SocketRuntime.adopt`

```python
def adopt(self, name: str, stream: socket.socket | ssl.SSLSocket, secure: SocketSecureMode | str = SocketSecureMode.NONE) -> SocketHandle
```

Performs adopt behavior in `SocketRuntime`.

Defined at line 151.

##### `SocketRuntime.close_all`

```python
def close_all(self) -> None
```

Performs close all behavior in `SocketRuntime`.

Defined at line 157.

##### `SocketRuntime._handle`

```python
def _handle(self, name: str) -> SocketHandle
```

Internal helper in `SocketRuntime` for handle.

Defined at line 161.

##### `SocketRuntime._secure_mode`

```python
def _secure_mode(self, descriptor: SocketDescriptor) -> SocketSecureMode
```

Internal helper in `SocketRuntime` for secure mode.

Defined at line 167.

##### `SocketRuntime._client_context`

```python
def _client_context(self, descriptor: SocketDescriptor) -> ssl.SSLContext
```

Internal helper in `SocketRuntime` for client context.

Defined at line 170.

##### `SocketRuntime._server_context`

```python
def _server_context(self, descriptor: SocketDescriptor) -> ssl.SSLContext
```

Internal helper in `SocketRuntime` for server context.

Defined at line 179.

#### `SocketStreamRuntime`

```python
class SocketStreamRuntime
```

Class implementing socket stream runtime behavior in the PL/I compiler.

Defined at line 187.

Methods:

##### `SocketStreamRuntime.__init__`

```python
def __init__(self, primitive: SocketRuntime | None = None) -> None
```

Initializes an instance of `SocketStreamRuntime`.

Defined at line 188.

##### `SocketStreamRuntime.open`

```python
def open(self, descriptor: SocketFileDescriptor) -> SocketHandle
```

Performs open behavior in `SocketStreamRuntime`.

Defined at line 191.

##### `SocketStreamRuntime.close`

```python
def close(self, descriptor: SocketFileDescriptor) -> None
```

Performs close behavior in `SocketStreamRuntime`.

Defined at line 196.

##### `SocketStreamRuntime.adopt`

```python
def adopt(self, name: str, stream: socket.socket | ssl.SSLSocket, secure: SocketSecureMode | str = SocketSecureMode.NONE) -> SocketHandle
```

Performs adopt behavior in `SocketStreamRuntime`.

Defined at line 199.

##### `SocketStreamRuntime.write_payload`

```python
def write_payload(self, descriptor: SocketFileDescriptor, data: bytes | str) -> None
```

Performs write payload behavior in `SocketStreamRuntime`.

Defined at line 202.

##### `SocketStreamRuntime.read_payload`

```python
def read_payload(self, descriptor: SocketFileDescriptor, size: int | None = None) -> bytes | str
```

Performs read payload behavior in `SocketStreamRuntime`.

Defined at line 205.

##### `SocketStreamRuntime.write_record`

```python
def write_record(self, descriptor: SocketFileDescriptor, data: bytes | str) -> None
```

Performs write record behavior in `SocketStreamRuntime`.

Defined at line 208.

##### `SocketStreamRuntime.read_record`

```python
def read_record(self, descriptor: SocketFileDescriptor, size: int | None = None) -> bytes | str
```

Performs read record behavior in `SocketStreamRuntime`.

Defined at line 225.

##### `SocketStreamRuntime.execute`

```python
def execute(self, statement: IOStatement, descriptors: dict[str, SocketFileDescriptor], variables: dict[str, object] | None = None) -> None
```

Performs execute behavior in `SocketStreamRuntime`.

Defined at line 243.

##### `SocketStreamRuntime.close_all`

```python
def close_all(self) -> None
```

Performs close all behavior in `SocketStreamRuntime`.

Defined at line 261.

##### `SocketStreamRuntime._read_exact`

```python
def _read_exact(self, name: str, size: int) -> bytes
```

Internal helper in `SocketStreamRuntime` for read exact.

Defined at line 264.

##### `SocketStreamRuntime._io_value`

```python
def _io_value(self, statement: IOStatement, variables: dict[str, object]) -> bytes | str
```

Internal helper in `SocketStreamRuntime` for io value.

Defined at line 277.

## `pl1compinpy.runtime.strings`

Source: `pl1compinpy/runtime/strings.py`

Module containing strings support for the PL/I compiler.

### Classes

#### `StringRuntimeError`

```python
class StringRuntimeError(ValueError)
```

Exception type raised for string runtime errors.

Defined at line 8.

#### `StringValue`

```python
class StringValue
```

Data container describing string value values used by the compiler.

Defined at line 13.

Methods:

##### `StringValue.storage`

```python
def storage(self) -> bytearray
```

Performs storage behavior in `StringValue`.

Defined at line 18.

##### `StringValue.length`

```python
def length(self) -> int
```

Performs length behavior in `StringValue`.

Defined at line 22.

##### `StringValue.payload`

```python
def payload(self) -> bytes
```

Performs payload behavior in `StringValue`.

Defined at line 26.

##### `StringValue.text`

```python
def text(self, encoding: str = 'utf-8') -> str
```

Performs text behavior in `StringValue`.

Defined at line 29.

#### `StringRuntime`

```python
class StringRuntime
```

Class implementing string runtime behavior in the PL/I compiler.

Defined at line 33.

Methods:

##### `StringRuntime.__init__`

```python
def __init__(self, heap: HeapRuntime | None = None) -> None
```

Initializes an instance of `StringRuntime`.

Defined at line 34.

##### `StringRuntime.allocate`

```python
def allocate(self, data: bytes | str, encoding: str = 'utf-8') -> StringValue
```

Performs allocate behavior in `StringRuntime`.

Defined at line 37.

##### `StringRuntime.assign`

```python
def assign(self, value: StringValue, data: bytes | str, encoding: str = 'utf-8') -> None
```

Performs assign behavior in `StringRuntime`.

Defined at line 47.

##### `StringRuntime.length`

```python
def length(self, value: StringValue) -> int
```

Performs length behavior in `StringRuntime`.

Defined at line 56.

##### `StringRuntime.index`

```python
def index(self, value: StringValue, needle: StringValue | bytes | str, encoding: str = 'utf-8') -> int
```

Performs index behavior in `StringRuntime`.

Defined at line 59.

##### `StringRuntime.substr`

```python
def substr(self, value: StringValue, start: int, count: int | None = None) -> StringValue
```

Performs substr behavior in `StringRuntime`.

Defined at line 64.

## `pl1compinpy.runtime.structures`

Source: `pl1compinpy/runtime/structures.py`

Module containing structures support for the PL/I compiler.

### Classes

#### `StructureRuntimeError`

```python
class StructureRuntimeError(ValueError)
```

Exception type raised for structure runtime errors.

Defined at line 13.

#### `StructureFieldLayout`

```python
class StructureFieldLayout
```

Data container describing structure field layout values used by the compiler.

Defined at line 18.

Methods:

##### `StructureFieldLayout.qualified_name`

```python
def qualified_name(self) -> str
```

Performs qualified name behavior in `StructureFieldLayout`.

Defined at line 28.

#### `StructureValue`

```python
class StructureValue
```

Data container describing structure value values used by the compiler.

Defined at line 33.

Methods:

##### `StructureValue.get_field`

```python
def get_field(self, path: str | list[str] | tuple[str, ...]) -> Any
```

Performs get field behavior in `StructureValue`.

Defined at line 38.

##### `StructureValue.set_field`

```python
def set_field(self, path: str | list[str] | tuple[str, ...], value: Any) -> None
```

Performs set field behavior in `StructureValue`.

Defined at line 47.

##### `StructureValue.flattened`

```python
def flattened(self) -> dict[str, Any]
```

Performs flattened behavior in `StructureValue`.

Defined at line 58.

##### `StructureValue._flatten_values`

```python
def _flatten_values(self, current: dict[str, Any], prefix: list[str], values: dict[str, Any]) -> None
```

Internal helper in `StructureValue` for flatten values.

Defined at line 63.

#### `StructureRuntime`

```python
class StructureRuntime
```

Class implementing structure runtime behavior in the PL/I compiler.

Defined at line 72.

Methods:

##### `StructureRuntime.__init__`

```python
def __init__(self) -> None
```

Initializes an instance of `StructureRuntime`.

Defined at line 73.

##### `StructureRuntime.declare_structure`

```python
def declare_structure(self, field: StructureField) -> StructureValue
```

Performs declare structure behavior in `StructureRuntime`.

Defined at line 76.

##### `StructureRuntime.set_field`

```python
def set_field(self, structure_name: str, field_path: str | list[str] | tuple[str, ...], value: Any) -> None
```

Performs set field behavior in `StructureRuntime`.

Defined at line 82.

##### `StructureRuntime.get_field`

```python
def get_field(self, structure_name: str, field_path: str | list[str] | tuple[str, ...]) -> Any
```

Performs get field behavior in `StructureRuntime`.

Defined at line 85.

##### `StructureRuntime.flattened_offsets`

```python
def flattened_offsets(self, structure_name: str) -> dict[str, int]
```

Performs flattened offsets behavior in `StructureRuntime`.

Defined at line 88.

##### `StructureRuntime._structure`

```python
def _structure(self, name: str) -> StructureValue
```

Internal helper in `StructureRuntime` for structure.

Defined at line 93.

##### `StructureRuntime._layout`

```python
def _layout(self, field: StructureField, path: tuple[str, ...], offset: int) -> tuple[StructureFieldLayout, int]
```

Internal helper in `StructureRuntime` for layout.

Defined at line 99.

##### `StructureRuntime._field_size`

```python
def _field_size(self, field: StructureField) -> int
```

Internal helper in `StructureRuntime` for field size.

Defined at line 119.

##### `StructureRuntime._first_numeric_attribute`

```python
def _first_numeric_attribute(self, attributes: list[str]) -> int | None
```

Internal helper in `StructureRuntime` for first numeric attribute.

Defined at line 135.

##### `StructureRuntime._initial_values`

```python
def _initial_values(self, layout: StructureFieldLayout) -> dict[str, Any]
```

Internal helper in `StructureRuntime` for initial values.

Defined at line 143.

##### `StructureRuntime._default_value`

```python
def _default_value(self, layout: StructureFieldLayout) -> PL1Value
```

Internal helper in `StructureRuntime` for default value.

Defined at line 152.

##### `StructureRuntime._flatten_offsets`

```python
def _flatten_offsets(self, layout: StructureFieldLayout, values: dict[str, int]) -> None
```

Internal helper in `StructureRuntime` for flatten offsets.

Defined at line 162.

#### `BasedStructureRuntime`

```python
class BasedStructureRuntime
```

Class implementing based structure runtime behavior in the PL/I compiler.

Defined at line 170.

Methods:

##### `BasedStructureRuntime.__init__`

```python
def __init__(self) -> None
```

Initializes an instance of `BasedStructureRuntime`.

Defined at line 171.

##### `BasedStructureRuntime.declare_based_structure`

```python
def declare_based_structure(self, field: StructureField, pointer_name: str | None = None) -> None
```

Performs declare based structure behavior in `BasedStructureRuntime`.

Defined at line 175.

##### `BasedStructureRuntime.default_pointer_name`

```python
def default_pointer_name(self, structure_name: str) -> str | None
```

Performs default pointer name behavior in `BasedStructureRuntime`.

Defined at line 178.

##### `BasedStructureRuntime.set_field`

```python
def set_field(self, pointer: PointerValue, structure_name: str, field_path: str | list[str] | tuple[str, ...], value: Any) -> None
```

Performs set field behavior in `BasedStructureRuntime`.

Defined at line 181.

##### `BasedStructureRuntime.get_field`

```python
def get_field(self, pointer: PointerValue, structure_name: str, field_path: str | list[str] | tuple[str, ...]) -> Any
```

Performs get field behavior in `BasedStructureRuntime`.

Defined at line 184.

##### `BasedStructureRuntime.field_offsets`

```python
def field_offsets(self, structure_name: str) -> dict[str, int]
```

Performs field offsets behavior in `BasedStructureRuntime`.

Defined at line 187.

##### `BasedStructureRuntime._value`

```python
def _value(self, pointer: PointerValue, structure_name: str) -> StructureValue
```

Internal helper in `BasedStructureRuntime` for value.

Defined at line 193.

##### `BasedStructureRuntime._definition`

```python
def _definition(self, structure_name: str) -> tuple[StructureField, str | None]
```

Internal helper in `BasedStructureRuntime` for definition.

Defined at line 203.

### Functions

#### `flattened_structure_fields`

```python
def flattened_structure_fields(field: StructureField) -> list[str]
```

Performs flattened structure fields behavior in `pl1compinpy.runtime.structures`.

Defined at line 210.

#### `_path_parts`

```python
def _path_parts(path: str | list[str] | tuple[str, ...]) -> list[str]
```

Internal helper in `pl1compinpy.runtime.structures` for path parts.

Defined at line 216.

## `pl1compinpy.runtime.symbols`

Source: `pl1compinpy/runtime/symbols.py`

Module containing symbols support for the PL/I compiler.

### Classes

#### `SymbolKind`

```python
class SymbolKind(str, Enum)
```

Class implementing symbol kind behavior in the PL/I compiler.

Defined at line 11.

#### `StorageClass`

```python
class StorageClass(str, Enum)
```

Class implementing storage class behavior in the PL/I compiler.

Defined at line 21.

#### `SourceLocation`

```python
class SourceLocation
```

Data container describing source location values used by the compiler.

Defined at line 31.

#### `Symbol`

```python
class Symbol
```

Data container describing symbol values used by the compiler.

Defined at line 38.

Methods:

##### `Symbol.debugger_record`

```python
def debugger_record(self) -> dict[str, Any]
```

Performs debugger record behavior in `Symbol`.

Defined at line 51.

#### `SymbolTableError`

```python
class SymbolTableError(ValueError)
```

Exception type raised for symbol table errors.

Defined at line 67.

#### `SymbolTable`

```python
class SymbolTable
```

Class implementing symbol table behavior in the PL/I compiler.

Defined at line 71.

Methods:

##### `SymbolTable.__init__`

```python
def __init__(self) -> None
```

Initializes an instance of `SymbolTable`.

Defined at line 72.

##### `SymbolTable.enter_scope`

```python
def enter_scope(self, scope: str, parent: str = 'global') -> None
```

Performs enter scope behavior in `SymbolTable`.

Defined at line 76.

##### `SymbolTable.define`

```python
def define(self, symbol: Symbol) -> Symbol
```

Performs define behavior in `SymbolTable`.

Defined at line 80.

##### `SymbolTable.lookup`

```python
def lookup(self, name: str, scope: str = 'global') -> Symbol | None
```

Performs lookup behavior in `SymbolTable`.

Defined at line 86.

##### `SymbolTable.symbols`

```python
def symbols(self, scope: str | None = None) -> list[Symbol]
```

Performs symbols behavior in `SymbolTable`.

Defined at line 96.

##### `SymbolTable.debugger_records`

```python
def debugger_records(self) -> list[dict[str, Any]]
```

Performs debugger records behavior in `SymbolTable`.

Defined at line 104.

#### `SymbolTableBuilder`

```python
class SymbolTableBuilder
```

Class implementing symbol table builder behavior in the PL/I compiler.

Defined at line 108.

Methods:

##### `SymbolTableBuilder.__init__`

```python
def __init__(self) -> None
```

Initializes an instance of `SymbolTableBuilder`.

Defined at line 109.

##### `SymbolTableBuilder.build`

```python
def build(self, program: Program) -> SymbolTable
```

Performs build behavior in `SymbolTableBuilder`.

Defined at line 113.

##### `SymbolTableBuilder._statement`

```python
def _statement(self, statement: Statement, scope: str) -> None
```

Internal helper in `SymbolTableBuilder` for statement.

Defined at line 118.

##### `SymbolTableBuilder._procedure`

```python
def _procedure(self, name: str, procedure: Procedure, parent_scope: str) -> None
```

Internal helper in `SymbolTableBuilder` for procedure.

Defined at line 133.

##### `SymbolTableBuilder._declaration`

```python
def _declaration(self, declaration: Declaration, scope: str) -> None
```

Internal helper in `SymbolTableBuilder` for declaration.

Defined at line 143.

##### `SymbolTableBuilder._structure_fields`

```python
def _structure_fields(self, field: StructureField, scope: str, root: str) -> None
```

Internal helper in `SymbolTableBuilder` for structure fields.

Defined at line 168.

### Functions

#### `build_symbol_table`

```python
def build_symbol_table(program: Program) -> SymbolTable
```

Performs build symbol table behavior in `pl1compinpy.runtime.symbols`.

Defined at line 175.

## `pl1compinpy.runtime.types`

Source: `pl1compinpy/runtime/types.py`

Module containing types support for the PL/I compiler.

### Classes

#### `PliType`

```python
class PliType
```

Data container describing pli type values used by the compiler.

Defined at line 8.

Methods:

##### `PliType.canonical`

```python
def canonical(self) -> str
```

Performs canonical behavior in `PliType`.

Defined at line 17.

##### `PliType.arithmetic`

```python
def arithmetic(self) -> bool
```

Performs arithmetic behavior in `PliType`.

Defined at line 32.

##### `PliType.locator`

```python
def locator(self) -> bool
```

Performs locator behavior in `PliType`.

Defined at line 36.

#### `TypeMapping`

```python
class TypeMapping
```

Data container describing type mapping values used by the compiler.

Defined at line 41.

#### `PliTypeParser`

```python
class PliTypeParser
```

Class implementing pli type parser behavior in the PL/I compiler.

Defined at line 65.

Methods:

##### `PliTypeParser.parse`

```python
def parse(self, text: str | list[str] | tuple[str, ...] | None) -> PliType | None
```

Parses lexer tokens into the compiler's AST representation.

Defined at line 66.

##### `PliTypeParser.mapping_for`

```python
def mapping_for(self, pli_type: PliType | str | None) -> TypeMapping | None
```

Performs mapping for behavior in `PliTypeParser`.

Defined at line 97.

##### `PliTypeParser._normalize`

```python
def _normalize(self, text: str) -> str
```

Internal helper in `PliTypeParser` for normalize.

Defined at line 103.

##### `PliTypeParser._attributes`

```python
def _attributes(self, normalized: str) -> tuple[str, ...]
```

Internal helper in `PliTypeParser` for attributes.

Defined at line 106.

##### `PliTypeParser._first_int_paren`

```python
def _first_int_paren(self, text: str) -> int | None
```

Internal helper in `PliTypeParser` for first int paren.

Defined at line 109.

##### `PliTypeParser._precision`

```python
def _precision(self, text: str) -> tuple[int, int | None] | None
```

Internal helper in `PliTypeParser` for precision.

Defined at line 113.

##### `PliTypeParser._picture`

```python
def _picture(self, text: str) -> str | None
```

Internal helper in `PliTypeParser` for picture.

Defined at line 119.

### Functions

#### `parse_pli_type`

```python
def parse_pli_type(text: str | list[str] | tuple[str, ...] | None) -> PliType | None
```

Parses lexer tokens into the compiler's AST representation.

Defined at line 124.

## `pl1compinpy.runtime.visitor`

Source: `pl1compinpy/runtime/visitor.py`

Module containing visitor support for the PL/I compiler.

### Classes

#### `RuntimeVisitorError`

```python
class RuntimeVisitorError(ValueError)
```

Exception type raised for runtime visitor errors.

Defined at line 35.

#### `RuntimeExecutionVisitor`

```python
class RuntimeExecutionVisitor(AstVisitor)
```

Class implementing runtime execution visitor behavior in the PL/I compiler.

Defined at line 39.

Methods:

##### `RuntimeExecutionVisitor.__init__`

```python
def __init__(self, variables: dict[str, PL1Value | object] | None = None, max_loop: int = 10000, argv: list[str] | tuple[str, ...] | None = None) -> None
```

Initializes an instance of `RuntimeExecutionVisitor`.

Defined at line 40.

##### `RuntimeExecutionVisitor.visit_Program`

```python
def visit_Program(self, node: Program) -> Any
```

Performs visit program behavior in `RuntimeExecutionVisitor`.

Defined at line 53.

##### `RuntimeExecutionVisitor.visit_Declaration`

```python
def visit_Declaration(self, node: Declaration) -> None
```

Performs visit declaration behavior in `RuntimeExecutionVisitor`.

Defined at line 67.

##### `RuntimeExecutionVisitor.visit_Assignment`

```python
def visit_Assignment(self, node: Assignment) -> PL1Value
```

Performs visit assignment behavior in `RuntimeExecutionVisitor`.

Defined at line 98.

##### `RuntimeExecutionVisitor.visit_Call`

```python
def visit_Call(self, node: Call) -> Any
```

Performs visit call behavior in `RuntimeExecutionVisitor`.

Defined at line 118.

##### `RuntimeExecutionVisitor.visit_DoGroup`

```python
def visit_DoGroup(self, node: DoGroup) -> Any
```

Performs visit do group behavior in `RuntimeExecutionVisitor`.

Defined at line 126.

##### `RuntimeExecutionVisitor.visit_IfStatement`

```python
def visit_IfStatement(self, node: IfStatement) -> Any
```

Performs visit if statement behavior in `RuntimeExecutionVisitor`.

Defined at line 142.

##### `RuntimeExecutionVisitor.visit_SelectStatement`

```python
def visit_SelectStatement(self, node: SelectStatement) -> Any
```

Performs visit select statement behavior in `RuntimeExecutionVisitor`.

Defined at line 147.

##### `RuntimeExecutionVisitor.visit_LabelledStatement`

```python
def visit_LabelledStatement(self, node: LabelledStatement) -> Any
```

Performs visit labelled statement behavior in `RuntimeExecutionVisitor`.

Defined at line 158.

##### `RuntimeExecutionVisitor.visit_GotoStatement`

```python
def visit_GotoStatement(self, node: GotoStatement) -> Any
```

Performs visit goto statement behavior in `RuntimeExecutionVisitor`.

Defined at line 161.

##### `RuntimeExecutionVisitor.visit_PreprocessorStatement`

```python
def visit_PreprocessorStatement(self, node: PreprocessorStatement) -> Any
```

Performs visit preprocessor statement behavior in `RuntimeExecutionVisitor`.

Defined at line 164.

##### `RuntimeExecutionVisitor.visit_RawStatement`

```python
def visit_RawStatement(self, node: RawStatement) -> Any
```

Performs visit raw statement behavior in `RuntimeExecutionVisitor`.

Defined at line 167.

##### `RuntimeExecutionVisitor.evaluate`

```python
def evaluate(self, expression: Expression) -> PL1Value
```

Performs evaluate behavior in `RuntimeExecutionVisitor`.

Defined at line 170.

##### `RuntimeExecutionVisitor._execute_block`

```python
def _execute_block(self, statements: list[Statement]) -> Any
```

Internal helper in `RuntimeExecutionVisitor` for execute block.

Defined at line 191.

##### `RuntimeExecutionVisitor._dispatch_call`

```python
def _dispatch_call(self, name: str, arguments: list[object]) -> Any
```

Internal helper in `RuntimeExecutionVisitor` for dispatch call.

Defined at line 197.

##### `RuntimeExecutionVisitor._plain`

```python
def _plain(self, value: PL1Value | object) -> object
```

Internal helper in `RuntimeExecutionVisitor` for plain.

Defined at line 243.

##### `RuntimeExecutionVisitor._pointer_target`

```python
def _pointer_target(self, target: str) -> tuple[str, str, list[str]]
```

Internal helper in `RuntimeExecutionVisitor` for pointer target.

Defined at line 246.

##### `RuntimeExecutionVisitor._is_based_structure`

```python
def _is_based_structure(self, name: str) -> bool
```

Internal helper in `RuntimeExecutionVisitor` for is based structure.

Defined at line 251.

##### `RuntimeExecutionVisitor._pointer_value`

```python
def _pointer_value(self, name: str) -> object
```

Internal helper in `RuntimeExecutionVisitor` for pointer value.

Defined at line 254.

##### `RuntimeExecutionVisitor._default_pointer`

```python
def _default_pointer(self, structure_name: str) -> object
```

Internal helper in `RuntimeExecutionVisitor` for default pointer.

Defined at line 260.

## `pl1compinpy.vsam`

Source: `pl1compinpy/vsam/__init__.py`

Local VSAM-style catalog and binary data component runtime.

## `pl1compinpy.vsam.catalog`

Source: `pl1compinpy/vsam/catalog.py`

Module containing catalog support for the PL/I compiler.

### Classes

#### `VSAMError`

```python
class VSAMError(ValueError)
```

Exception type raised for compiler errors.

Defined at line 9.

#### `VSAMType`

```python
class VSAMType(str, Enum)
```

Class implementing vsamtype behavior in the PL/I compiler.

Defined at line 13.

#### `VSAMDefinition`

```python
class VSAMDefinition
```

Data container describing vsamdefinition values used by the compiler.

Defined at line 21.

#### `VSAMCatalog`

```python
class VSAMCatalog
```

Class implementing vsamcatalog behavior in the PL/I compiler.

Defined at line 34.

Methods:

##### `VSAMCatalog.__init__`

```python
def __init__(self, root: Path | str) -> None
```

Initializes an instance of `VSAMCatalog`.

Defined at line 35.

##### `VSAMCatalog.define`

```python
def define(cls, root: Path | str, name: str, organization: VSAMType | str, *, key_offset: int = 0, key_length: int = 0, record_length: int | None = None) -> 'VSAMCatalog'
```

Performs define behavior in `VSAMCatalog`.

Defined at line 43.

##### `VSAMCatalog.write`

```python
def write(self, record: bytes, *, key: bytes | str | None = None, rrn: int | None = None, rba: int | None = None) -> int
```

Performs write behavior in `VSAMCatalog`.

Defined at line 65.

##### `VSAMCatalog.read`

```python
def read(self, *, key: bytes | str | None = None, rrn: int | None = None, rba: int | None = None, length: int | None = None) -> bytes
```

Performs read behavior in `VSAMCatalog`.

Defined at line 77.

##### `VSAMCatalog._write_ksds`

```python
def _write_ksds(self, record: bytes, key: bytes | str | None) -> int
```

Internal helper in `VSAMCatalog` for write ksds.

Defined at line 99.

##### `VSAMCatalog._write_rrds`

```python
def _write_rrds(self, record: bytes, rrn: int | None) -> int
```

Internal helper in `VSAMCatalog` for write rrds.

Defined at line 110.

##### `VSAMCatalog._write_lds`

```python
def _write_lds(self, payload: bytes, rba: int | None) -> int
```

Internal helper in `VSAMCatalog` for write lds.

Defined at line 122.

##### `VSAMCatalog._append_record`

```python
def _append_record(self, record: bytes) -> int
```

Internal helper in `VSAMCatalog` for append record.

Defined at line 129.

##### `VSAMCatalog._append_raw`

```python
def _append_raw(self, payload: bytes) -> int
```

Internal helper in `VSAMCatalog` for append raw.

Defined at line 134.

##### `VSAMCatalog._read_record_at`

```python
def _read_record_at(self, rba: int) -> bytes
```

Internal helper in `VSAMCatalog` for read record at.

Defined at line 140.

##### `VSAMCatalog._read_at`

```python
def _read_at(self, rba: int, length: int) -> bytes
```

Internal helper in `VSAMCatalog` for read at.

Defined at line 149.

##### `VSAMCatalog._key_text`

```python
def _key_text(self, key: bytes | str) -> str
```

Internal helper in `VSAMCatalog` for key text.

Defined at line 158.

##### `VSAMCatalog._load`

```python
def _load(self) -> VSAMDefinition | None
```

Internal helper in `VSAMCatalog` for load.

Defined at line 161.

##### `VSAMCatalog._save`

```python
def _save(self) -> None
```

Internal helper in `VSAMCatalog` for save.

Defined at line 167.

## `pl1compinpy.vsam.io`

Source: `pl1compinpy/vsam/io.py`

Module containing io support for the PL/I compiler.

### Classes

#### `VSAMFileDescriptor`

```python
class VSAMFileDescriptor
```

Data container describing vsamfile descriptor values used by the compiler.

Defined at line 11.

Methods:

##### `VSAMFileDescriptor.from_declaration`

```python
def from_declaration(cls, declaration: Declaration, base_path: Path | None = None) -> 'VSAMFileDescriptor'
```

Performs from declaration behavior in `VSAMFileDescriptor`.

Defined at line 21.

#### `VSAMRuntime`

```python
class VSAMRuntime
```

Class implementing vsamruntime behavior in the PL/I compiler.

Defined at line 43.

Methods:

##### `VSAMRuntime.__init__`

```python
def __init__(self) -> None
```

Initializes an instance of `VSAMRuntime`.

Defined at line 44.

##### `VSAMRuntime.open`

```python
def open(self, descriptor: VSAMFileDescriptor) -> None
```

Performs open behavior in `VSAMRuntime`.

Defined at line 47.

##### `VSAMRuntime.close`

```python
def close(self, descriptor: VSAMFileDescriptor) -> None
```

Performs close behavior in `VSAMRuntime`.

Defined at line 62.

##### `VSAMRuntime.write_record`

```python
def write_record(self, descriptor: VSAMFileDescriptor, data: bytes | str, *, key: bytes | str | None = None, rrn: int | None = None, rba: int | None = None) -> int
```

Performs write record behavior in `VSAMRuntime`.

Defined at line 65.

##### `VSAMRuntime.read_record`

```python
def read_record(self, descriptor: VSAMFileDescriptor, *, key: bytes | str | None = None, rrn: int | None = None, rba: int | None = None, length: int | None = None) -> bytes
```

Performs read record behavior in `VSAMRuntime`.

Defined at line 77.

##### `VSAMRuntime.execute`

```python
def execute(self, statement: IOStatement, descriptors: dict[str, VSAMFileDescriptor], variables: dict[str, object] | None = None) -> None
```

Performs execute behavior in `VSAMRuntime`.

Defined at line 88.

##### `VSAMRuntime._catalog`

```python
def _catalog(self, descriptor: VSAMFileDescriptor) -> VSAMCatalog
```

Internal helper in `VSAMRuntime` for catalog.

Defined at line 118.

##### `VSAMRuntime._optional_value`

```python
def _optional_value(self, expression: Expression | None, variables: dict[str, object]) -> bytes | str | None
```

Internal helper in `VSAMRuntime` for optional value.

Defined at line 124.

##### `VSAMRuntime._optional_key`

```python
def _optional_key(self, descriptor: VSAMFileDescriptor, expression: Expression | None, variables: dict[str, object]) -> bytes | str | None
```

Internal helper in `VSAMRuntime` for optional key.

Defined at line 130.

##### `VSAMRuntime._optional_int`

```python
def _optional_int(self, expression: Expression | None, variables: dict[str, object]) -> int | None
```

Internal helper in `VSAMRuntime` for optional int.

Defined at line 136.

##### `VSAMRuntime._value`

```python
def _value(self, expression: Expression | None, variables: dict[str, object]) -> object
```

Internal helper in `VSAMRuntime` for value.

Defined at line 142.
