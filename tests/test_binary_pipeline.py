import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pl1compinpy.cli import main as cli_main
from pl1compinpy.compiler import compile_binary
from pl1compinpy.frontend.lexer import Lexer
from pl1compinpy.frontend.parser import Parser
from pl1compinpy.runtime import RuntimeExecutionVisitor, normalize_calls


BINARY_RESULT_SOURCE = """
DCL LEFT FIXED BIN(31);
DCL RIGHT FIXED BIN(31);
DCL RESULT FIXED BIN(31);

LEFT = 40;
RIGHT = 2;
RESULT = LEFT + RIGHT;
CALL DISPLAY(RESULT);
"""


class BinaryPipelineTests(unittest.TestCase):
    def runtime_result(self) -> tuple[int, list[object]]:
        program = normalize_calls(Parser(Lexer(BINARY_RESULT_SOURCE).tokenize()).parse())
        visitor = RuntimeExecutionVisitor()
        visitor.visit(program)
        return visitor.variables["RESULT"].value, visitor.output

    def test_binary_compile_artifacts_and_runtime_result_match(self):
        expected_signatures = {
            "pe32-x586-windows": b"MZ",
            "pe64-x86_64-windows": b"MZ",
            "elf64-x86_64": b"\x7fELF",
            "elf64-aarch64": b"\x7fELF",
            "macho64-x86_64-macos": b"\xcf\xfa\xed\xfe",
            "macho64-arm64-macos": b"\xcf\xfa\xed\xfe",
        }

        result, output = self.runtime_result()

        self.assertEqual(result, 42)
        self.assertEqual(output, [42])
        for format_name, signature in expected_signatures.items():
            with self.subTest(format=format_name):
                binary = compile_binary(format_name, BINARY_RESULT_SOURCE)
                self.assertTrue(binary.startswith(signature))
                self.assertIn(b"PL1RTLINK\0", binary)
                self.assertIn(f'"target":"{format_name}"'.encode("utf-8"), binary)

    def test_x86_binary_contains_source_derived_immediates(self):
        binary = compile_binary("elf64-x86_64", BINARY_RESULT_SOURCE)

        self.assertIn(b"\xB8\x28\x00\x00\x00", binary)
        self.assertIn(b"\xB8\x02\x00\x00\x00", binary)
        self.assertIn(b"\x01\xD8", binary)

    def test_cli_binary_emit_writes_file_and_runtime_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "binary_result.pl1"
            output = root / "binary_result.elf"
            source.write_text(BINARY_RESULT_SOURCE, encoding="utf-8")

            exit_code = cli_main([str(source), "--emit", "binary", "--binary-format", "elf64-x86_64", "-o", str(output)])

            result, runtime_output = self.runtime_result()
            self.assertEqual(exit_code, 0)
            self.assertEqual(result, 42)
            self.assertEqual(runtime_output, [42])
            self.assertTrue(output.read_bytes().startswith(b"\x7fELF"))


if __name__ == "__main__":
    unittest.main()
