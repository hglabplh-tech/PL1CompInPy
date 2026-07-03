import unittest
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pl1compinpy import compile_source
from pl1compinpy.compiler import compile_binary
from pl1compinpy.codegen.executable_pipeline import lower_program
from pl1compinpy.ast import Call, Declaration, IfStatement, LabelledStatement, Procedure
from pl1compinpy.frontend.lexer import Lexer, TokenType
from pl1compinpy.frontend.parser import Parser
from pl1compinpy.runtime import ArrayRuntime, FileDescriptor, StdioRuntime, normalize_calls


class CompilerTests(unittest.TestCase):
    def test_tokenizes_assignment(self):
        tokens = Lexer("TOTAL = A + 10;").tokenize()

        self.assertEqual(
            [token.type for token in tokens],
            [
                TokenType.IDENTIFIER,
                TokenType.ASSIGN,
                TokenType.IDENTIFIER,
                TokenType.PLUS,
                TokenType.NUMBER,
                TokenType.SEMICOLON,
                TokenType.EOF,
            ],
        )

    def test_compiles_assignment(self):
        self.assertEqual(compile_source("TOTAL = A + 10;"), "TOTAL = (A + 10)\n")

    def test_compiles_call(self):
        self.assertEqual(compile_source("CALL DISPLAY('HELLO', TOTAL);"), "DISPLAY('HELLO', TOTAL)\n")

    def test_keywords_are_contextual_not_reserved(self):
        tokens = Lexer("IF = THEN;").tokenize()

        self.assertEqual(tokens[0].type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[0].keyword.word, "IF")
        self.assertEqual(compile_source("IF = THEN;"), "IF = THEN\n")

    def test_skips_comments(self):
        tokens = Lexer("A = 1; /* comment */ B = 2;").tokenize()

        self.assertEqual([token.lexeme for token in tokens[:-1]], ["A", "=", "1", ";", "B", "=", "2", ";"])

    def test_parses_declaration(self):
        program = Parser(Lexer("DCL TOTAL FIXED BIN(31);").tokenize()).parse()

        self.assertIsInstance(program.statements[0], Declaration)
        self.assertEqual(program.statements[0].names, ["TOTAL"])
        self.assertEqual(program.statements[0].attributes, ["FIXED", "BIN"])

    def test_parses_array_declaration(self):
        program = Parser(Lexer("DCL A(10) FIXED BIN(31), B(2,3) FIXED BIN(31);").tokenize()).parse()
        declaration = program.statements[0]

        self.assertEqual(declaration.names, ["A", "B"])
        self.assertEqual(declaration.dimensions["A"], [10])
        self.assertEqual(declaration.dimensions["B"], [2, 3])

    def test_parses_file_descriptor_declaration(self):
        source = "DCL F FILE RECORD OUTPUT ENVIRONMENT(RECFM(V), LRECL(80), PATH('out.dat')) BINARY;"
        declaration = Parser(Lexer(source).tokenize()).parse().statements[0]

        self.assertEqual(declaration.names, ["F"])
        self.assertIn("FILE", declaration.attributes)
        self.assertEqual(declaration.file_options["mode"], "OUTPUT")
        self.assertEqual(declaration.file_options["organization"], "RECORD")
        self.assertEqual(declaration.file_options["recfm"], "V")
        self.assertEqual(declaration.file_options["lrecl"], "80")
        self.assertEqual(declaration.file_options["path"], "out.dat")

    def test_parses_labelled_procedure(self):
        program = Parser(
            Lexer("HELLO: PROC OPTIONS(MAIN); DCL TOTAL FIXED BIN(31); END HELLO;").tokenize()
        ).parse()

        self.assertIsInstance(program.statements[0], LabelledStatement)
        self.assertIsInstance(program.statements[0].statement, Procedure)

    def test_parses_if_then_else(self):
        program = Parser(Lexer("IF TOTAL = 0 THEN CALL ZERO(); ELSE CALL NONZERO();").tokenize()).parse()

        self.assertIsInstance(program.statements[0], IfStatement)

    def test_emits_x586_windows_assignment_control_and_io(self):
        source = "DCL TOTAL FIXED BIN(31); TOTAL = 40 + 2; IF TOTAL = 42 THEN CALL DISPLAY(TOTAL);"
        assembly = compile_source(source, target="x586-windows")

        self.assertIn("global _main", assembly)
        self.assertIn("TOTAL dd 0", assembly)
        self.assertIn("add eax, ebx", assembly)
        self.assertIn("cmp eax, ebx", assembly)
        self.assertIn("call _printf", assembly)

    def test_emits_arm64_macos_assignment_control_and_io(self):
        source = "DCL TOTAL FIXED BIN(31); TOTAL = 40 + 2; IF TOTAL = 42 THEN CALL DISPLAY(TOTAL);"
        assembly = compile_source(source, target="arm64-macos")

        self.assertIn(".globl _main", assembly)
        self.assertIn("TOTAL: .word 0", assembly)
        self.assertIn("add w0, w8, w0", assembly)
        self.assertIn("cmp w8, w0", assembly)
        self.assertIn("bl _printf", assembly)

    def test_creates_windows_x586_exe_container(self):
        binary = compile_binary("pe32-x586-windows")

        self.assertEqual(binary[:2], b"MZ")
        self.assertIn(b"PE\0\0", binary[:256])

    def test_creates_elf_for_intel_and_arm(self):
        self.assertEqual(compile_binary("elf64-x86_64")[:4], b"\x7fELF")
        self.assertEqual(compile_binary("elf64-aarch64")[:4], b"\x7fELF")

    def test_creates_macho_for_apple_intel_and_m2(self):
        self.assertEqual(compile_binary("macho64-x86_64-macos")[:4], b"\xcf\xfa\xed\xfe")
        self.assertEqual(compile_binary("macho64-arm64-macos")[:4], b"\xcf\xfa\xed\xfe")

    def test_lowers_ast_to_executable_mnemonics(self):
        program = Parser(Lexer("DCL TOTAL FIXED BIN(31); TOTAL = 40 + 2;").tokenize()).parse()
        mnemonics, data, variables = lower_program(program)

        self.assertIn("TOTAL", variables)
        self.assertEqual(len(data), 4)
        self.assertEqual([mnemonic.op for mnemonic in mnemonics if mnemonic.op != "COMMENT"][:5], [
            "MOV_EAX_IMM",
            "PUSH_EAX",
            "MOV_EAX_IMM",
            "POP_EBX",
            "ADD_EAX_EBX",
        ])

    def test_binary_output_uses_source_generated_machine_code(self):
        binary = compile_binary("pe32-x586-windows", "DCL TOTAL FIXED BIN(31); TOTAL = 40 + 2;")
        code = binary[0x200:0x240]

        self.assertIn(b"\xB8\x28\x00\x00\x00", code)
        self.assertIn(b"\xB8\x02\x00\x00\x00", code)
        self.assertIn(b"\x01\xD8", code)
        self.assertIn(b"\xA3", code)

    def test_call_by_name_normalizes_to_reference_parameter_order(self):
        program = Parser(Lexer("P: PROC(A,B); END P; CALL P(B,A) BY NAME;").tokenize()).parse()
        normalized = normalize_calls(program)
        call = normalized.statements[1]

        self.assertIsInstance(call, Call)
        self.assertEqual(call.mode, "reference")
        self.assertEqual([argument.name for argument in call.arguments], ["A", "B"])

    def test_runtime_lowers_locals_to_stack_and_parameters_to_references(self):
        source = "P: PROC(A); DCL TEMP FIXED BIN(31); TEMP = A + 1; A = TEMP; END P;"
        program = normalize_calls(Parser(Lexer(source).tokenize()).parse())
        mnemonics, _, _ = lower_program(program)
        ops = [mnemonic.op for mnemonic in mnemonics]

        self.assertIn("ENTER_FRAME", ops)
        self.assertIn("LOAD_EAX_REF_PARAM", ops)
        self.assertIn("STORE_EAX_LOCAL", ops)
        self.assertIn("STORE_EAX_REF_PARAM", ops)

    def test_runtime_pushes_call_arguments_right_to_left_by_reference(self):
        source = "P: PROC(A,B); END P; DCL A FIXED BIN(31), B FIXED BIN(31); CALL P(A,B);"
        program = normalize_calls(Parser(Lexer(source).tokenize()).parse())
        mnemonics, _, _ = lower_program(program)
        call_index = [mnemonic.op for mnemonic in mnemonics].index("CALL_PROC")
        pushed = mnemonics[call_index - 2 : call_index]

        self.assertEqual([mnemonic.op for mnemonic in pushed], ["PUSH_GLOBAL_REF", "PUSH_GLOBAL_REF"])
        self.assertEqual([mnemonic.args[0] for mnemonic in pushed], ["B", "A"])

    def test_runtime_entry_jumps_over_procedure_definitions(self):
        source = "P: PROC(A); A = 1; END P; DCL A FIXED BIN(31); CALL P(A);"
        program = normalize_calls(Parser(Lexer(source).tokenize()).parse())
        mnemonics, _, _ = lower_program(program)

        self.assertEqual(mnemonics[0], type(mnemonics[0])("JMP", ("__main",)))
        self.assertIn(type(mnemonics[0])("LABEL", ("__main",)), mnemonics)

    def test_runtime_entry_calls_proc_options_main(self):
        source = "MAIN: PROC OPTIONS(MAIN); END MAIN;"
        program = normalize_calls(Parser(Lexer(source).tokenize()).parse())
        mnemonics, _, _ = lower_program(program)
        main_label = mnemonics.index(type(mnemonics[0])("LABEL", ("__main",)))

        self.assertEqual(mnemonics[main_label + 1], type(mnemonics[0])("CALL_PROC", ("MAIN", 0)))

    def test_parses_proc_main_recursive_returns(self):
        program = Parser(
            Lexer("MAIN: PROC OPTIONS(MAIN) RECURSIVE RETURNS(FIXED BIN(31)); RETURN 0; END MAIN;").tokenize()
        ).parse()
        procedure = program.statements[0].statement

        self.assertIsInstance(procedure, Procedure)
        self.assertIn("MAIN", procedure.options)
        self.assertTrue(procedure.recursive)
        self.assertEqual(procedure.returns, "FIXED BIN 31")

    def test_python_source_backend_emits_main_entry(self):
        source = "MAIN: PROC OPTIONS(MAIN) RETURNS(FIXED); RETURN 0; END MAIN;"
        output = compile_source(source, target="python-source")

        self.assertIn("def MAIN():  # returns FIXED", output)
        self.assertIn('if __name__ == "__main__":', output)
        self.assertIn("    MAIN()", output)

    def test_jvm_bytecode_backend_emits_main_and_return_descriptor(self):
        source = "MAIN: PROC OPTIONS(MAIN) RETURNS(FIXED); RETURN 0; END MAIN;"
        output = compile_source(source, target="jvm-bytecode")

        self.assertIn(".class public PL1Program", output)
        self.assertIn(".method public static MAIN()I", output)
        self.assertIn(".method public static main([Ljava/lang/String;)V", output)
        self.assertIn("invokestatic PL1Program/MAIN()I", output)

    def test_recursive_call_lowers_as_normal_call_with_continuation(self):
        source = "FACT: PROC(N) RECURSIVE RETURNS(FIXED); CALL FACT(N); RETURN N; END FACT;"
        program = normalize_calls(Parser(Lexer(source).tokenize()).parse())
        mnemonics, _, _ = lower_program(program)
        ops = [mnemonic.op for mnemonic in mnemonics]
        call_index = ops.index("CALL_PROC")

        self.assertEqual(mnemonics[call_index].args[0], "FACT")
        self.assertEqual(ops[call_index + 1], "CLEAN_ARGS")
        self.assertIn("LEAVE_RET", ops[call_index + 2 :])

    def test_runtime_allocates_arrays_on_heap(self):
        runtime = ArrayRuntime()
        array = runtime.allocate_array("A", [2, 3])

        array.set(42, 2, 3)
        self.assertEqual(array.get(2, 3), 42)
        self.assertEqual(runtime.heap.block(array.heap_handle).size, 24)

    def test_runtime_writes_and_reads_v_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            descriptor = FileDescriptor("F", Path(tmp) / "v.dat", mode="OUTPUT", recfm="V")
            runtime = StdioRuntime()
            runtime.open(descriptor)
            runtime.write_record(descriptor, b"ABC")
            runtime.close(descriptor)

            self.assertEqual((Path(tmp) / "v.dat").read_bytes(), b"\x00\x03ABC")

            input_descriptor = FileDescriptor("F", Path(tmp) / "v.dat", mode="INPUT", recfm="V")
            runtime.open(input_descriptor)
            self.assertEqual(runtime.read_record(input_descriptor), b"ABC")
            runtime.close(input_descriptor)

    def test_runtime_writes_fixed_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            descriptor = FileDescriptor("F", Path(tmp) / "f.dat", mode="OUTPUT", recfm="F", lrecl=5, text=True)
            runtime = StdioRuntime()
            runtime.open(descriptor)
            runtime.write_record(descriptor, "XY")
            runtime.close(descriptor)

            self.assertEqual((Path(tmp) / "f.dat").read_bytes(), b"XY   ")

    def test_file_descriptor_from_pl1_declaration(self):
        source = "DCL F FILE RECORD INPUT ENVIRONMENT(RECFM(F), LRECL(12), PATH('input.dat')) TEXT;"
        declaration = Parser(Lexer(source).tokenize()).parse().statements[0]
        descriptor = FileDescriptor.from_declaration(declaration, Path("/tmp"))

        self.assertEqual(descriptor.name, "F")
        self.assertEqual(descriptor.path, Path("/tmp/input.dat"))
        self.assertEqual(descriptor.mode, "INPUT")
        self.assertEqual(descriptor.recfm, "F")
        self.assertEqual(descriptor.lrecl, 12)
        self.assertTrue(descriptor.text)


if __name__ == "__main__":
    unittest.main()
