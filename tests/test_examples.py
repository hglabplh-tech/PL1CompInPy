import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pl1compinpy import compile_paths, compile_source
from pl1compinpy.ast import GotoStatement, PreprocessorStatement
from pl1compinpy.compiler import compile_binary
from pl1compinpy.frontend.lexer import Lexer
from pl1compinpy.frontend.parser import Parser
from pl1compinpy.runtime import RuntimeExecutionVisitor, normalize_calls


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = PROJECT_ROOT / "examples"


class ExampleTests(unittest.TestCase):
    def example_source(self, relative: str) -> str:
        return (EXAMPLES / relative).read_text(encoding="utf-8")

    def parse_example(self, relative: str):
        return Parser(Lexer(self.example_source(relative)).tokenize()).parse()

    def test_all_pl1_examples_parse(self):
        examples = sorted(path for path in EXAMPLES.rglob("*.pl1"))

        self.assertGreaterEqual(len(examples), 10)
        for example in examples:
            with self.subTest(example=example.relative_to(EXAMPLES)):
                Parser(Lexer(example.read_text(encoding="utf-8")).tokenize()).parse()

    def test_language_declarations_compile_to_python_source(self):
        output = compile_source(self.example_source("language/declarations.pl1"))

        self.assertIn("TOTAL = (40 + 2)", output)
        self.assertIn("DISPLAY('TOTAL', TOTAL)", output)

    def test_control_structure_example_compiles(self):
        output = compile_source(self.example_source("language/control_structures.pl1"))

        self.assertIn("if (TOTAL == 42):", output)
        self.assertIn("DISPLAY('ANSWER')", output)

    def test_main_procedure_example_emits_python_entry(self):
        output = compile_source(self.example_source("language/procedure_main.pl1"))

        self.assertIn("def MAIN():  # returns FIXED BIN 31", output)
        self.assertIn('if __name__ == "__main__":', output)
        self.assertIn("    MAIN()", output)

    def test_call_by_name_example_normalizes_argument_order(self):
        program = normalize_calls(self.parse_example("language/call_by_name.pl1"))
        call = program.statements[-1]

        self.assertEqual(call.name, "ADDPAIR")
        self.assertEqual(call.mode, "reference")
        self.assertEqual([argument.name for argument in call.arguments], ["LEFT", "RIGHT"])

    def test_recursive_example_preserves_recursive_metadata(self):
        program = self.parse_example("language/recursive_proc.pl1")
        procedure = program.statements[0].statement

        self.assertTrue(procedure.recursive)
        self.assertEqual(procedure.returns, "FIXED BIN 31")

    def test_arrays_example_captures_dimensions(self):
        declaration = self.parse_example("runtime/arrays.pl1").statements[0]
        matrix_declaration = self.parse_example("runtime/arrays.pl1").statements[1]

        self.assertEqual(declaration.dimensions["A"], [10])
        self.assertEqual(matrix_declaration.dimensions["MATRIX"], [2, 3])

    def test_file_examples_capture_record_options(self):
        v_decl = self.parse_example("runtime/file_record_v.pl1").statements[0]
        f_decl = self.parse_example("runtime/file_record_f.pl1").statements[0]
        unix_decl = self.parse_example("runtime/file_unix_text.pl1").statements[0]

        self.assertEqual(v_decl.file_options["recfm"], "V")
        self.assertEqual(f_decl.file_options["recfm"], "F")
        self.assertEqual(f_decl.file_options["lrecl"], "80")
        self.assertEqual(unix_decl.file_options["format"], "TEXT")
        self.assertEqual(unix_decl.file_options["organization"], "STREAM")

    def test_socket_pl1_examples_match_runtime_function_table(self):
        sender = normalize_calls(self.parse_example("runtime/socket_primitive_sender.pl1"))
        receiver = normalize_calls(self.parse_example("runtime/socket_primitive_receiver.pl1"))
        streams = normalize_calls(self.parse_example("runtime/socket_streams.pl1"))

        self.assertEqual([statement.name for statement in sender.statements[-3:]], ["TCPIP_OPEN", "TCPIP_SEND", "TCPIP_CLOSE"])
        self.assertEqual([statement.name for statement in receiver.statements[-3:]], ["TCPIP_OPEN", "TCPIP_RECEIVE", "TCPIP_CLOSE"])
        self.assertEqual([statement.name for statement in streams.statements[-5:]], ["SOCKET_OPEN", "SOCKET_WRITE", "SOCKET_READ", "SOCKET_CLOSE", "SOCKET_CLOSE"])

    def test_visitor_control_blocks_example_runs_with_runtime_visitor(self):
        program = normalize_calls(self.parse_example("language/visitor_control_blocks.pl1"))
        visitor = RuntimeExecutionVisitor()

        visitor.visit(program)

        self.assertEqual(visitor.variables["TOTAL"].value, 4)
        self.assertEqual(visitor.output, ["TOTAL IS NOT ZERO", "TOTAL REACHED FOUR"])

    def test_goto_and_preprocessor_examples_compile(self):
        goto_program = self.parse_example("language/goto_labels.pl1")
        preprocessor_program = self.parse_example("language/preprocessor_commands.pl1")

        self.assertTrue(any(isinstance(statement, GotoStatement) for statement in goto_program.statements))
        self.assertTrue(any(isinstance(statement, PreprocessorStatement) for statement in preprocessor_program.statements))
        self.assertIn("# goto SKIP_INITIAL_ASSIGNMENT", compile_source(self.example_source("language/goto_labels.pl1"), target="python-source"))
        self.assertIn("# preprocessor DECLARE FEATURE FIXED", compile_source(self.example_source("language/preprocessor_commands.pl1"), target="python-source"))

    def test_include_and_multi_source_examples_compile(self):
        include_output = compile_paths([EXAMPLES / "language/include_main.pl1"], target="python-source", include_dirs=[EXAMPLES / "language"])
        multi_output = compile_paths([EXAMPLES / "language/multi_source_main.pl1", EXAMPLES / "language/module_helper.pl1"], target="python-source")

        self.assertIn("INCLUDED_TOTAL = 0", include_output)
        self.assertIn("def MAIN():", multi_output)
        self.assertIn("def HELPER():", multi_output)

    def test_numeric_string_builtins_example_uses_static_builtin_table(self):
        program = normalize_calls(self.parse_example("builtins/numeric_string_builtins.pl1"))
        calls = [statement.name for statement in program.statements if hasattr(statement, "name")]

        self.assertEqual(calls, ["LENGTH", "INDEX", "ABS", "MIN", "MAX", "MOD", "ROUND", "TRUNC"])

    def test_pointer_builtin_example_uses_static_builtin_table(self):
        program = normalize_calls(self.parse_example("builtins/pointer.pl1"))
        calls = [statement.name for statement in program.statements if hasattr(statement, "name")]

        self.assertEqual(calls, ["POINTER", "POINTER", "POINTER", "POINTER"])

    def test_pointer_offset_example_uses_static_builtin_table(self):
        program = normalize_calls(self.parse_example("builtins/pointer_offsets.pl1"))
        calls = [statement.name for statement in program.statements if hasattr(statement, "name")]

        self.assertEqual(calls, ["POINTER", "POINTER", "POINTER", "POINTER", "POINTER"])

    def test_builtin_substr_example_includes_builtin_source(self):
        output = compile_source(self.example_source("builtins/substr.pl1"), builtins=["SUBSTR"])

        self.assertIn("def SUBSTR", output)
        self.assertIn("SOURCE = 0", output)

    def test_backend_python_source_example(self):
        output = compile_source(self.example_source("backend/python_source.pl1"), target="python-source")

        self.assertIn("def MAIN():", output)
        self.assertIn("DISPLAY('PYTHON SOURCE BACKEND')", output)

    def test_backend_jvm_bytecode_example(self):
        output = compile_source(self.example_source("backend/jvm_bytecode.pl1"), target="jvm-bytecode")

        self.assertIn(".class public PL1Program", output)
        self.assertIn(".method public static MAIN()I", output)

    def test_backend_dotnet_il_example(self):
        output = compile_source(self.example_source("backend/dotnet_il.pl1"), target="dotnet-il")

        self.assertIn(".assembly PL1Program", output)
        self.assertIn(".entrypoint", output)
        self.assertIn("System.Console::WriteLine", output)

    def test_backend_assembly_examples(self):
        source = self.example_source("language/declarations.pl1")
        self.assertIn("global _main", compile_source(source, target="x586-windows"))
        self.assertIn("global main", compile_source(self.example_source("backend/x86_64_windows.pl1"), target="x86_64-windows"))
        self.assertIn(".globl _main", compile_source(source, target="arm64-macos"))

    def test_backend_binary_entry_example(self):
        source = self.example_source("backend/binary_entry.pl1")

        self.assertEqual(compile_binary("pe32-x586-windows", source)[:2], b"MZ")
        self.assertEqual(compile_binary("pe64-x86_64-windows", source)[:2], b"MZ")
        self.assertEqual(compile_binary("elf64-x86_64", source)[:4], b"\x7fELF")
        self.assertEqual(compile_binary("macho64-arm64-macos", source)[:4], b"\xcf\xfa\xed\xfe")


if __name__ == "__main__":
    unittest.main()
