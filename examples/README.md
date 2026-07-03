# Examples

These examples cover the compiler features currently implemented in PL1CompInPy.

## Language

- `language/declarations.pl1`: declarations, assignment, and display calls
- `language/control_structures.pl1`: `IF/THEN/ELSE`
- `language/procedure_main.pl1`: `PROC OPTIONS(MAIN)` and `RETURNS`
- `language/call_by_reference.pl1`: by-reference calls
- `language/call_by_name.pl1`: by-name call normalization
- `language/recursive_proc.pl1`: recursive procedure metadata and ordinary call continuation

## Runtime

- `runtime/arrays.pl1`: array declarations
- `runtime/file_unix_text.pl1`: Unix-style text file declaration
- `runtime/file_record_v.pl1`: variable-record file declaration
- `runtime/file_record_f.pl1`: fixed-record file declaration

## Builtins

- `builtins/substr.pl1`: compile with `--builtin SUBSTR`

## Backends

- `backend/python_source.pl1`: Python source backend
- `backend/jvm_bytecode.pl1`: JVM bytecode-style backend
- `backend/binary_entry.pl1`: binary executable/container entry-point example

