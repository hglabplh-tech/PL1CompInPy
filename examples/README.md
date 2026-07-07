# Examples

These examples cover the compiler features currently implemented in PL1CompInPy.

## Language

- `language/declarations.pl1`: declarations, assignment, and display calls
- `language/calculation_engine.pl1`: operator precedence, numeric promotion, and logical expressions
- `language/control_structures.pl1`: `IF/THEN/ELSE`
- `language/do_while_until.pl1`: `DO WHILE` and post-test `DO ... UNTIL`
- `language/select_when.pl1`: `SELECT` with `WHEN` and `OTHERWISE`
- `language/visitor_control_blocks.pl1`: visitor/backend control blocks with `DO`, `DO WHILE`, `DO ... UNTIL`, `IF`, `SELECT`, and condition aliases
- `language/goto_labels.pl1`: labels plus `GOTO` and `GO TO`
- `language/preprocessor_commands.pl1`: parsed `%` preprocessor command forms
- `language/include_main.pl1` and `language/include_common.pli`: `%INCLUDE` source expansion
- `language/multi_source_main.pl1` and `language/module_helper.pl1`: separate source modules compiled together
- `language/procedure_main.pl1`: `PROC OPTIONS(MAIN)` and `RETURNS`
- `language/command_line_main.pl1`: `PROC(PARM) OPTIONS(MAIN)` command-line parameter binding
- `language/call_by_reference.pl1`: by-reference calls
- `language/call_by_name.pl1`: by-name call normalization
- `language/recursive_proc.pl1`: recursive procedure metadata and ordinary call continuation
- `language/generic.pl1`: `GENERIC` declaration with type-based alternatives
- `language/picture_float.pl1`: `PICTURE`/`PIC` declarations and `FLOAT` data

## Runtime

- `runtime/arrays.pl1`: array declarations
- `runtime/based_pointer.pl1`: `POINTER` and `BASED(pointer)` declaration shape
- `runtime/file_unix_text.pl1`: Unix-style text file declaration
- `runtime/file_record_v.pl1`: variable-record file declaration
- `runtime/file_record_f.pl1`: fixed-record file declaration
- `runtime/file_read_write.pl1`: `OPEN`, `READ`, `WRITE`, and `CLOSE` file statements
- `runtime/function_table.py`: dynamic user function table and static runtime function table lookup
- `runtime/fixed_decimal_packed_zoned.py`: fixed decimal, packed decimal, zoned decimal, and two-byte string runtime APIs
- `runtime/dynload.py`: native/managed dynamic loading descriptor usage
- `runtime/runtime_visitor.py`: direct use of the AST `RuntimeExecutionVisitor`
- `runtime/socket_io.py`: primitive runtime TCP socket send/receive example
- `runtime/socket_stream.py`: file-like socket payload records above primitive sockets
- `runtime/socket_primitive_sender.pl1`: primitive `TCPIP_OPEN`, `TCPIP_SEND`, and `TCPIP_CLOSE` call usage
- `runtime/socket_primitive_receiver.pl1`: primitive `TCPIP_OPEN`, `TCPIP_RECEIVE`, and `TCPIP_CLOSE` call usage
- `runtime/socket_streams.pl1`: PL/I socket stream `SOCKET_OPEN`, `SOCKET_WRITE`, `SOCKET_READ`, and `SOCKET_CLOSE` usage

## Builtins

- `builtins/substr.pl1`: compile with `--builtin SUBSTR`
- `builtins/declared_substr.pl1`: `DCL SUBSTR BUILTIN;` enables a static PL/I builtin call
- `builtins/numeric_string_builtins.pl1`: declared static numeric and string builtins through the function table

## Backends

- `backend/python_source.pl1`: Python source backend
- `backend/jvm_bytecode.pl1`: JVM bytecode-style backend
- `backend/dotnet_il.pl1`: .NET ILAsm-compatible backend
- `backend/binary_entry.pl1`: binary executable/container entry-point example
- `backend/library_artifacts.py`: static archive and shared-library artifact creation

## VSAM

- `vsam/ksds.pl1`: keyed sequential data set declaration
- `vsam/esds.pl1`: entry sequenced data set declaration
- `vsam/rrds.pl1`: relative record data set declaration
- `vsam/lds.pl1`: linear data set declaration
- `vsam/io_ksds.pl1`: VSAM `OPEN`, `WRITE`, keyed `READ`, and `CLOSE`
- `vsam/io_esds.pl1`: VSAM ESDS `OPEN`, `WRITE`, RBA `READ`, and `CLOSE`
- `vsam/io_rrds.pl1`: VSAM RRDS `OPEN`, RRN `WRITE`, RRN `READ`, and `CLOSE`
- `vsam/io_lds.pl1`: VSAM LDS `OPEN`, RBA `WRITE`, RBA/LENGTH `READ`, and `CLOSE`
