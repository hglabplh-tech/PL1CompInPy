import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pl1compinpy import compile_source
from pl1compinpy.compiler import compile_binary
from pl1compinpy.executable_pipeline import lower_program
from pl1compinpy.ast import Declaration, IfStatement, LabelledStatement, Procedure
from pl1compinpy.lexer import Lexer, TokenType
from pl1compinpy.parser import Parser


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


if __name__ == "__main__":
    unittest.main()
