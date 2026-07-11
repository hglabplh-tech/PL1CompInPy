import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pl1compinpy.frontend.lexer import Lexer
from pl1compinpy.frontend.parser import Parser
from pl1compinpy.ast import LabelledStatement, Procedure


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = PROJECT_ROOT / "bootstrap"


class BootstrapSourceTests(unittest.TestCase):
    def parse_bootstrap(self, name: str):
        return Parser(Lexer((BOOTSTRAP / name).read_text(encoding="utf-8")).tokenize()).parse()

    def procedure_names(self, program) -> set[str]:
        names: set[str] = set()
        for statement in program.statements:
            if isinstance(statement, Procedure) and statement.name:
                names.add(statement.name)
            elif isinstance(statement, LabelledStatement) and isinstance(statement.statement, Procedure):
                names.add(statement.label)
                if statement.statement.name:
                    names.add(statement.statement.name)
        return names

    def test_bootstrap_sources_parse(self):
        for source in sorted(BOOTSTRAP.glob("*.pl1")):
            with self.subTest(source=source.name):
                program = Parser(Lexer(source.read_text(encoding="utf-8")).tokenize()).parse()
                self.assertGreater(len(program.statements), 0)

    def test_bootstrap_lexer_declares_scanner_phases(self):
        names = self.procedure_names(self.parse_bootstrap("bootstrap_lexer.pl1"))

        self.assertIn("BOOTSTRAP_LEXER", names)
        self.assertIn("LEX_COMMENT", names)
        self.assertIn("LEX_IDENTIFIER", names)
        self.assertIn("LEX_SYMBOL", names)

    def test_bootstrap_parser_declares_complete_current_constructs(self):
        names = self.procedure_names(self.parse_bootstrap("bootstrap_parser.pl1"))

        for name in {
            "BOOTSTRAP_PARSER",
            "PARSER_DECLARE",
            "PARSER_PROCEDURE",
            "PARSER_DO_GROUP",
            "PARSER_IF",
            "PARSER_SELECT",
            "PARSER_IO",
            "PARSER_ASSIGNMENT",
            "PARSER_CALL",
            "PARSER_EXPRESSION",
        }:
            self.assertIn(name, names)

    def test_bootstrap_runtime_registers_current_runtime_families(self):
        text = (BOOTSTRAP / "bootstrap_runtime.pl1").read_text(encoding="utf-8")

        for marker in ("PL1RT_ALLOC", "PL1RT_PEEK", "RT_LOOKUP", "RT_VALIDATE_BUILTIN", "OPEN", "VSAM_OPEN", "TCPIP_OPEN", "COMPLEX", "DECIMAL_TO_PACKED"):
            self.assertIn(marker, text)

    def test_bootstrap_m3_backend_declares_arm64_emitter(self):
        names = self.procedure_names(self.parse_bootstrap("bootstrap_backend_m3.pl1"))
        text = (BOOTSTRAP / "bootstrap_backend_m3.pl1").read_text(encoding="utf-8")

        for name in {"BOOTSTRAP_BACKEND_M3", "M3_EMIT_PROLOGUE", "M3_EMIT_TEXT_SECTION", "M3_EMIT_MOV_IMMEDIATE", "M3_EMIT_STORE_W0"}:
            self.assertIn(name, names)
        for marker in (".globl _main", "bl _pl1rt_init", "macho64-arm64-macos", "str w0"):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
