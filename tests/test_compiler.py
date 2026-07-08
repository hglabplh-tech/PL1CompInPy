import unittest
from decimal import Decimal
from pathlib import Path
import sys
import struct
import socket
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pl1compinpy import compile_paths, compile_source, compile_sources
from pl1compinpy.builtins import BuiltinLibrary
from pl1compinpy.compiler import compile_binary, compile_jvm_classes, compile_library
from pl1compinpy.codegen.dotnet_executable import DotNetExecutableError
from pl1compinpy.codegen.jvm_classfile import JAVA_17_MAJOR_VERSION
from pl1compinpy.codegen.executable_pipeline import lower_program
from pl1compinpy.codegen.linkers import ELFLinker, MachOLinker, PELinker
from pl1compinpy.codegen.runtime_link import runtime_linkage
from pl1compinpy.cli import main as cli_main
from pl1compinpy.ast import (
    AstVisitor,
    BinaryExpression,
    Call,
    Declaration,
    DoGroup,
    FieldReference,
    FunctionCall,
    GotoStatement,
    Identifier,
    IOStatement,
    IfStatement,
    LabelledStatement,
    PreprocessorStatement,
    Procedure,
    PointerReference,
    SelectStatement,
    StructureField,
    main_procedure_name,
)
from pl1compinpy.frontend import operator_precedence_table
from pl1compinpy.frontend.include import IncludeError, IncludeExpander
from pl1compinpy.frontend.preprocessor import IBMStylePreprocessor, preprocess_source
from pl1compinpy.frontend.lexer import Lexer, TokenType
from pl1compinpy.frontend.parser import Parser
from pl1compinpy.runtime import (
    ArrayRuntime,
    BasedRuntime,
    FileDescriptor,
    GenericRuntime,
    FunctionDescriptor,
    FunctionTable,
    FunctionTableError,
    CalculationBuiltinRuntime,
    CommandLineRuntime,
    ComplexRuntime,
    ComplexValue,
    DecimalRuntime,
    DynamicLoadRuntime,
    PictureRuntime,
    CalculationEngine,
    FixedDecimal,
    ParameterDescriptor,
    PackedDecimalCodec,
    PointerBuiltinRuntime,
    PointerValue,
    RUNTIME_FUNCTION_TABLE,
    StdioRuntime,
    StringRuntime,
    StructureRuntime,
    PliTypeParser,
    TYPE_MAPPINGS,
    SymbolKind,
    StorageClass,
    build_symbol_table,
    ZonedDecimalCodec,
    PL1Type,
    PL1Value,
    RuntimeExecutionVisitor,
    SocketDescriptor,
    SocketFileDescriptor,
    SocketRuntime,
    SocketSecureMode,
    SocketStreamRuntime,
    build_dynamic_function_table,
    declared_builtins,
    normalize_calls,
)
from pl1compinpy.vsam import VSAMCatalog, VSAMFileDescriptor, VSAMRuntime, VSAMType


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

    def test_tokenizes_pointer_qualified_reference(self):
        tokens = Lexer("P->REC.ID = 7;").tokenize()

        self.assertEqual(
            [token.type for token in tokens[:6]],
            [TokenType.IDENTIFIER, TokenType.ARROW, TokenType.IDENTIFIER, TokenType.DOT, TokenType.IDENTIFIER, TokenType.ASSIGN],
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

    def test_include_expander_resolves_include_and_xinclude_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "common.inc").write_text("DCL SHARED FIXED BIN(31);\n", encoding="utf-8")
            source = "%INCLUDE 'common';\n%XINCLUDE 'common';\n%XINCLUDE 'common';\nSHARED = 7;"

            expanded = IncludeExpander([root]).expand(source, base_dir=root)

            self.assertEqual(expanded.count("DCL SHARED"), 1)
            self.assertIn("SHARED = 7;", expanded)

    def test_compile_paths_compiles_included_and_multiple_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "decls.pli").write_text("DCL SHARED FIXED BIN(31);\n", encoding="utf-8")
            main = root / "main.pl1"
            helper = root / "helper.pl1"
            main.write_text("%INCLUDE 'decls';\nMAIN: PROC OPTIONS(MAIN); CALL HELPER(); END MAIN;\n", encoding="utf-8")
            helper.write_text("HELPER: PROC; SHARED = 1; END HELPER;\n", encoding="utf-8")

            output = compile_paths([main, helper], target="python-source", include_dirs=[root])

            self.assertIn("SHARED = 0", output)
            self.assertIn("def MAIN():", output)
            self.assertIn("def HELPER():", output)

    def test_compile_sources_combines_modules_and_selects_options_main(self):
        output = compile_sources(
            [
                "HELPER: PROC; CALL DISPLAY('HELPER'); END HELPER;",
                "MAIN: PROC OPTIONS(MAIN); CALL HELPER(); END MAIN;",
            ],
            target="python-source",
        )

        self.assertIn("def HELPER():", output)
        self.assertIn("def MAIN():", output)
        self.assertIn("    MAIN()", output)

    def test_include_expander_strict_mode_reports_missing_member_and_recursion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.inc").write_text("%INCLUDE 'b';\n", encoding="utf-8")
            (root / "b.inc").write_text("%INCLUDE 'a';\n", encoding="utf-8")
            expander = IncludeExpander([root], strict=True)

            with self.assertRaises(IncludeError):
                expander.expand("%INCLUDE 'missing';", base_dir=root)
            with self.assertRaises(IncludeError):
                expander.expand_file(root / "a.inc")

    def test_ibm_style_preprocessor_replaces_and_selects_active_branch(self):
        source = (
            "%DECLARE FEATURE FIXED;\n"
            "%FEATURE = 1;\n"
            "%REPLACE RESULT BY PREPROCESSED_RESULT;\n"
            "%IF FEATURE %THEN;\n"
            "DCL RESULT FIXED BIN(31);\n"
            "RESULT = 42;\n"
            "%ELSE;\n"
            "DCL RESULT FIXED BIN(31);\n"
            "RESULT = 0;\n"
            "%END;\n"
        )

        preprocessed = preprocess_source(source)
        output = compile_source(source)

        self.assertIn("DCL PREPROCESSED_RESULT FIXED BIN(31);", preprocessed)
        self.assertIn("PREPROCESSED_RESULT = 42;", preprocessed)
        self.assertNotIn("RESULT = 0;", preprocessed)
        self.assertIn("PREPROCESSED_RESULT = 42", output)

    def test_ibm_style_preprocessor_builtins_notes_and_tables(self):
        preprocessor = IBMStylePreprocessor(sysp_arm="DEBUG TRACE")
        preprocessed = preprocessor.preprocess(
            "%DECLARE FLAG FIXED;\n"
            "%FLAG = PARMSET('DEBUG');\n"
            "%NOTE UPPERCASE('preprocessor active');\n"
            "%IF FLAG %THEN;\n"
            "ACTIVE = 1;\n"
            "%ELSE;\n"
            "ACTIVE = 0;\n"
            "%END;\n"
        )
        tables = preprocessor.compile_time_tables()

        self.assertEqual(preprocessed.strip(), "ACTIVE = 1;")
        self.assertIn("PARMSET", tables["builtins"])
        self.assertIn("ACTIVATE", tables["directives"])
        self.assertEqual(tables["symbols"]["FLAG"]["value"], True)
        self.assertEqual(tables["notes"], ["PREPROCESSOR ACTIVE"])

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

    def test_parses_picture_float_pointer_and_based_declarations(self):
        program = Parser(
            Lexer("DCL AMOUNT PIC'ZZZ9.99'; DCL RATE FLOAT DECIMAL(16); DCL P POINTER; DCL REC BASED(P);").tokenize()
        ).parse()
        amount = program.statements[0]
        rate = program.statements[1]
        pointer = program.statements[2]
        record = program.statements[3]

        self.assertEqual(amount.picture_options["AMOUNT"], "ZZZ9.99")
        self.assertIn("FLOAT", rate.attributes)
        self.assertEqual(pointer.pointer_names, ["P"])
        self.assertEqual(record.based_options["REC"], "P")

    def test_parses_level_number_based_record_declaration(self):
        declaration = Parser(Lexer("DCL 1 REC BASED(P), 2 ID FIXED BIN(31);").tokenize()).parse().statements[0]

        self.assertEqual(declaration.names, ["REC"])
        self.assertEqual(declaration.based_options["REC"], "P")

    def test_parses_structure_declaration_and_field_references(self):
        program = Parser(
            Lexer(
                "DCL 1 CUSTOMER, 2 ID FIXED BIN(31), 2 ADDRESS, 3 ZIP FIXED BIN(31); "
                "CUSTOMER.ID = 1001; CUSTOMER.ADDRESS.ZIP = CUSTOMER.ID + 1;"
            ).tokenize()
        ).parse()
        declaration = program.statements[0]
        assignment = program.statements[2]

        self.assertIsInstance(declaration.structures["CUSTOMER"], StructureField)
        self.assertEqual([field.name for field in declaration.structures["CUSTOMER"].children], ["ID", "ADDRESS"])
        self.assertEqual(declaration.structures["CUSTOMER"].children[1].children[0].name, "ZIP")
        self.assertEqual(program.statements[1].target, "CUSTOMER.ID")
        self.assertEqual(assignment.target, "CUSTOMER.ADDRESS.ZIP")
        self.assertIsInstance(assignment.expression.left, FieldReference)
        self.assertEqual(assignment.expression.left.name, "CUSTOMER.ID")

    def test_parses_pointer_qualified_based_structure_references(self):
        program = Parser(
            Lexer(
                "DCL POINTER BUILTIN; DCL P POINTER; "
                "DCL 1 REC BASED(P), 2 ID FIXED BIN(31); "
                "P = POINTER(100); P->REC.ID = P->REC.ID + 1;"
            ).tokenize()
        ).parse()
        pointer_assignment = program.statements[3]
        field_assignment = program.statements[4]

        self.assertIsInstance(pointer_assignment.expression, FunctionCall)
        self.assertEqual(pointer_assignment.expression.name, "POINTER")
        self.assertEqual(field_assignment.target, "P->REC.ID")
        self.assertIsInstance(field_assignment.expression.left, PointerReference)
        self.assertEqual(field_assignment.expression.left.name, "P->REC.ID")

    def test_structure_fields_compile_to_python_and_assembly_backends(self):
        source = (
            "MAIN: PROC OPTIONS(MAIN); "
            "DCL 1 CUSTOMER, 2 ID FIXED BIN(31), 2 ZIP FIXED BIN(31); "
            "CUSTOMER.ID = 7; CUSTOMER.ZIP = CUSTOMER.ID + 1; "
            "END MAIN;"
        )

        python_output = compile_source(source, target="python-source")
        x586_output = compile_source(source, target="x586-windows")
        jvm_output = compile_source(source, target="jvm-bytecode")
        dotnet_output = compile_source(source, target="dotnet-il")

        self.assertIn("CUSTOMER = {'ID': 0, 'ZIP': 0}", python_output)
        self.assertIn("CUSTOMER['ID'] = 7", python_output)
        self.assertIn("CUSTOMER['ZIP'] = (CUSTOMER['ID'] + 1)", python_output)
        self.assertIn("CUSTOMER_ID dd 0", x586_output)
        self.assertIn("mov [CUSTOMER_ID], eax", x586_output)
        self.assertIn("istore", jvm_output)
        self.assertIn(".locals init", dotnet_output)

    def test_structure_runtime_declares_fields_offsets_and_values(self):
        declaration = Parser(
            Lexer("DCL 1 CUSTOMER, 2 ID FIXED BIN(31), 2 NAME CHAR(20), 2 ADDRESS, 3 ZIP FIXED BIN(31);").tokenize()
        ).parse().statements[0]
        runtime = StructureRuntime()

        value = runtime.declare_structure(declaration.structures["CUSTOMER"])
        runtime.set_field("CUSTOMER", "ID", PL1Value(1001, PL1Type.FIXED_BIN))
        runtime.set_field("CUSTOMER", ["ADDRESS", "ZIP"], PL1Value(55123, PL1Type.FIXED_BIN))

        self.assertEqual(value.get_field("ID").value, 1001)
        self.assertEqual(value.get_field("ADDRESS.ZIP").value, 55123)
        self.assertEqual(runtime.flattened_offsets("CUSTOMER")["CUSTOMER.ID"], 0)
        self.assertEqual(runtime.flattened_offsets("CUSTOMER")["CUSTOMER.NAME"], 4)
        self.assertEqual(runtime.flattened_offsets("CUSTOMER")["CUSTOMER.ADDRESS.ZIP"], 24)

    def test_runtime_visitor_executes_structure_field_assignments(self):
        source = (
            "DCL 1 CUSTOMER, 2 ID FIXED BIN(31), 2 ADDRESS, 3 ZIP FIXED BIN(31); "
            "CUSTOMER.ID = 1001; CUSTOMER.ADDRESS.ZIP = CUSTOMER.ID + 1;"
        )
        visitor = RuntimeExecutionVisitor()

        visitor.visit(Parser(Lexer(source).tokenize()).parse())

        customer = visitor.variables["CUSTOMER"]
        self.assertEqual(customer.get_field("ID").value, 1001)
        self.assertEqual(customer.get_field("ADDRESS.ZIP").value, 1002)

    def test_runtime_visitor_executes_based_structure_through_pointer(self):
        source = (
            "DCL POINTER BUILTIN; DCL P POINTER; "
            "DCL 1 REC BASED(P), 2 ID FIXED BIN(31), 2 ADDRESS, 3 ZIP FIXED BIN(31); "
            "P = POINTER(100); "
            "P->REC.ID = 1001; "
            "P->REC.ADDRESS.ZIP = P->REC.ID + 1; "
            "REC.ID = 2002; "
            "TOTAL = P->REC.ID + REC.ADDRESS.ZIP;"
        )
        visitor = RuntimeExecutionVisitor()

        visitor.visit(normalize_calls(Parser(Lexer(source).tokenize()).parse()))

        self.assertEqual(visitor.variables["P"], PointerValue(100, 0))
        self.assertEqual(visitor.based_structures.get_field(PointerValue(100, 0), "REC", "ID").value, 2002)
        self.assertEqual(visitor.based_structures.get_field(PointerValue(100, 0), "REC", "ADDRESS.ZIP").value, 1002)
        self.assertEqual(visitor.variables["TOTAL"].value, 3004)

    def test_parses_labelled_procedure(self):
        program = Parser(
            Lexer("HELLO: PROC OPTIONS(MAIN); DCL TOTAL FIXED BIN(31); END HELLO;").tokenize()
        ).parse()

        self.assertIsInstance(program.statements[0], LabelledStatement)
        self.assertIsInstance(program.statements[0].statement, Procedure)

    def test_parses_if_then_else(self):
        program = Parser(Lexer("IF TOTAL = 0 THEN CALL ZERO(); ELSE CALL NONZERO();").tokenize()).parse()

        self.assertIsInstance(program.statements[0], IfStatement)

    def test_parses_file_io_statements(self):
        program = Parser(Lexer("OPEN FILE(F); READ FILE(F) KEY(KEYVAR) INTO(BUF); WRITE FILE(F) FROM(BUF); CLOSE FILE(F);").tokenize()).parse()

        self.assertEqual([statement.operation for statement in program.statements], ["OPEN", "READ", "WRITE", "CLOSE"])
        self.assertTrue(all(isinstance(statement, IOStatement) for statement in program.statements))
        self.assertEqual(program.statements[1].file_name, "F")
        self.assertEqual(program.statements[1].target, "BUF")
        self.assertEqual(program.statements[1].options["key"].name, "KEYVAR")
        self.assertEqual(program.statements[2].source.name, "BUF")

    def test_parses_do_while_and_do_until_groups(self):
        source = "DO WHILE TOTAL < 3; TOTAL = TOTAL + 1; END; DO; TOTAL = TOTAL + 1; UNTIL TOTAL = 5; END;"
        program = Parser(Lexer(source).tokenize()).parse()
        first = program.statements[0]
        second = program.statements[1]

        self.assertIsInstance(first, DoGroup)
        self.assertIsNotNone(first.while_condition)
        self.assertIsInstance(second, DoGroup)
        self.assertIsNotNone(second.until_condition)

    def test_parses_select_when_otherwise(self):
        source = "SELECT(TOTAL); WHEN(1) CALL DISPLAY('ONE'); WHEN(2,3) CALL DISPLAY('MANY'); OTHERWISE CALL DISPLAY('OTHER'); END;"
        statement = Parser(Lexer(source).tokenize()).parse().statements[0]

        self.assertIsInstance(statement, SelectStatement)
        self.assertEqual(len(statement.when_branches), 2)
        self.assertEqual(len(statement.when_branches[1].expressions), 2)
        self.assertIsNotNone(statement.otherwise)

    def test_parses_goto_labels_and_preprocessor_commands(self):
        source = "%DECLARE FEATURE FIXED; GOTO SKIP; GO TO DONE; SKIP: CALL DISPLAY('SKIP');"
        program = Parser(Lexer(source).tokenize()).parse()

        self.assertIsInstance(program.statements[0], PreprocessorStatement)
        self.assertEqual(program.statements[0].command, "DECLARE")
        self.assertEqual(program.statements[0].arguments, ["FEATURE", "FIXED"])
        self.assertIsInstance(program.statements[1], GotoStatement)
        self.assertEqual(program.statements[1].label, "SKIP")
        self.assertIsInstance(program.statements[2], GotoStatement)
        self.assertEqual(program.statements[2].label, "DONE")
        self.assertIsInstance(program.statements[3], LabelledStatement)
        self.assertEqual(program.statements[3].label, "SKIP")

    def test_goto_lowers_to_jump_mnemonic(self):
        source = "GOTO DONE; DONE: CALL DISPLAY('DONE');"
        mnemonics, _, _ = lower_program(Parser(Lexer(source).tokenize()).parse())

        self.assertEqual(mnemonics[0].op, "JMP")
        self.assertEqual(mnemonics[0].args, ("DONE",))
        self.assertIn(type(mnemonics[0])("LABEL", ("DONE",)), mnemonics)

    def test_preprocessor_emits_as_python_source_comment(self):
        output = compile_source("%INCLUDE 'COMMON.PLI';", target="python-source")

        self.assertIn("# preprocessor INCLUDE COMMON.PLI", output)

    def test_ast_accept_uses_visitor_pattern(self):
        class StatementCountingVisitor(AstVisitor):
            def visit_Program(self, node):
                return sum(1 for statement in node.statements if self.visit(statement))

            def visit_Declaration(self, node):
                return True

            def visit_Assignment(self, node):
                return True

        program = Parser(Lexer("DCL X FIXED BIN(31); X = 1;").tokenize()).parse()

        self.assertEqual(program.accept(StatementCountingVisitor()), 2)

    def test_condition_aliases_parse_and_execute_with_runtime_visitor(self):
        source = "DCL X FIXED BIN(31); X = 1; IF X ~= 2 THEN X = X + 1; IF X => 2 THEN X = X + 1;"
        visitor = RuntimeExecutionVisitor()

        visitor.visit(Parser(Lexer(source).tokenize()).parse())

        self.assertEqual(visitor.variables["X"].value, 3)

    def test_expression_parser_uses_pl1_operator_precedence(self):
        expression = Parser(Lexer("RESULT = A OR B AND C = D || E + F * G ** H;").tokenize()).parse().statements[0].expression
        table = {info.symbol: info.precedence for info in operator_precedence_table() if info.category != "prefix"}

        self.assertLess(table["OR"], table["AND"])
        self.assertLess(table["AND"], table["="])
        self.assertLess(table["="], table["||"])
        self.assertLess(table["||"], table["+"])
        self.assertLess(table["+"], table["*"])
        self.assertLess(table["*"], table["**"])
        self.assertIsInstance(expression, BinaryExpression)
        self.assertEqual(expression.operator, "OR")
        self.assertEqual(expression.right.operator, "AND")
        self.assertEqual(expression.right.right.operator, "=")
        self.assertEqual(expression.right.right.right.operator, "||")
        self.assertEqual(expression.right.right.right.right.operator, "+")
        self.assertEqual(expression.right.right.right.right.right.operator, "*")
        self.assertEqual(expression.right.right.right.right.right.right.operator, "**")

    def test_pli_type_parser_and_symbol_table_prepare_debugger_records(self):
        parser = PliTypeParser()
        fixed = parser.parse("FIXED DECIMAL(31,2)")
        character = parser.parse("CHAR(80) VARYING")
        pointer = parser.parse("POINTER")
        program = Parser(
            Lexer(
                "DCL P POINTER; DCL 1 REC BASED(P), 2 ID FIXED BIN(31), 2 NAME CHAR(80) VARYING; "
                "MAIN: PROC OPTIONS(MAIN); DCL TOTAL FIXED DECIMAL(31,2); END MAIN;"
            ).tokenize()
        ).parse()
        symbols = build_symbol_table(program)

        self.assertEqual(fixed.canonical(), "FIXED DECIMAL(31,2)")
        self.assertEqual(character.canonical(), "CHARACTER(80) VARYING")
        self.assertTrue(pointer.locator)
        self.assertEqual(TYPE_MAPPINGS["FIXED DECIMAL"].python, "decimal.Decimal / FixedDecimal")
        self.assertEqual(symbols.lookup("P").pli_type.canonical(), "POINTER")
        self.assertEqual(symbols.lookup("REC").storage, StorageClass.BASED)
        self.assertEqual(symbols.lookup("REC.ID").kind, SymbolKind.FIELD)
        self.assertEqual(symbols.lookup("TOTAL", "MAIN").pli_type.canonical(), "FIXED DECIMAL")
        self.assertEqual(symbols.lookup("MAIN").kind, SymbolKind.PROCEDURE)
        self.assertIn("scope", symbols.lookup("TOTAL", "MAIN").debugger_record())

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

    def test_emits_x86_64_windows_assignment_control_and_io(self):
        source = "DCL TOTAL FIXED BIN(31); TOTAL = 40 + 2; IF TOTAL = 42 THEN CALL DISPLAY(TOTAL);"
        assembly = compile_source(source, target="x86_64-windows")

        self.assertIn("bits 64", assembly)
        self.assertIn("global main", assembly)
        self.assertIn("TOTAL dq 0", assembly)
        self.assertIn("add rax, rbx", assembly)
        self.assertIn("cmp rax, rbx", assembly)
        self.assertIn("call printf", assembly)

    def test_creates_windows_x586_exe_container(self):
        binary = compile_binary("pe32-x586-windows")

        self.assertEqual(binary[:2], b"MZ")
        self.assertIn(b"PE\0\0", binary[:256])

    def test_creates_windows_x86_64_pe32_plus_container(self):
        binary = compile_binary("pe64-x86_64-windows", "DCL TOTAL FIXED BIN(31); TOTAL = 40 + 2;")
        pe_offset = struct.unpack_from("<I", binary, 0x3C)[0]

        self.assertEqual(binary[:2], b"MZ")
        self.assertEqual(binary[pe_offset : pe_offset + 4], b"PE\0\0")
        self.assertEqual(struct.unpack_from("<H", binary, pe_offset + 4)[0], 0x8664)
        self.assertEqual(struct.unpack_from("<H", binary, pe_offset + 24)[0], 0x020B)
        self.assertIn(b"\xB8\x28\x00\x00\x00", binary[0x200:0x240])

    def test_creates_elf_for_intel_and_arm(self):
        self.assertEqual(compile_binary("elf64-x86_64")[:4], b"\x7fELF")
        self.assertEqual(compile_binary("elf64-aarch64")[:4], b"\x7fELF")

    def test_creates_macho_for_apple_intel_and_m2(self):
        self.assertEqual(compile_binary("macho64-x86_64-macos")[:4], b"\xcf\xfa\xed\xfe")
        self.assertEqual(compile_binary("macho64-arm64-macos")[:4], b"\xcf\xfa\xed\xfe")

    def test_creates_static_and_shared_library_artifacts(self):
        source = "MAIN: PROC OPTIONS(MAIN); END MAIN;"

        self.assertTrue(compile_library("static-ar", source).startswith(b"!<arch>\n"))
        self.assertTrue(compile_library("static-lib-windows", source).startswith(b"!<arch>\n"))
        self.assertEqual(compile_library("shared-elf64", source)[:4], b"\x7fELF")
        self.assertEqual(compile_library("shared-macho64", source)[:4], b"\xcf\xfa\xed\xfe")
        self.assertEqual(compile_library("shared-pe64", source)[:2], b"MZ")

    def test_library_artifacts_embed_module_and_runtime_manifest(self):
        library = compile_library("static-ar", "MAIN: PROC OPTIONS(MAIN); END MAIN;", module_name="accounts")

        self.assertIn(b"module=accounts", library)
        self.assertIn(b"main=MAIN", library)
        self.assertIn(b"PL1RTLINK", library)

    def test_cli_emits_library_from_multiple_sources_and_include_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "decls.pli").write_text("DCL VALUE FIXED BIN(31);\n", encoding="utf-8")
            main = root / "main.pl1"
            helper = root / "helper.pl1"
            output = root / "libsample.a"
            main.write_text("%INCLUDE 'decls';\nMAIN: PROC OPTIONS(MAIN); CALL HELPER(); END MAIN;\n", encoding="utf-8")
            helper.write_text("HELPER: PROC; VALUE = 1; END HELPER;\n", encoding="utf-8")

            result = cli_main([str(main), str(helper), "-I", str(root), "--emit", "library", "--library-format", "static-ar", "-o", str(output)])

            self.assertEqual(result, 0)
            self.assertTrue(output.read_bytes().startswith(b"!<arch>\n"))

    def test_linkers_expose_pe_elf_and_macho_formats(self):
        pe64 = PELinker().link_pe64_x86_64_windows()
        elf = ELFLinker().link_elf64_x86_64()
        macho = MachOLinker().link_macho64_x86_64_macos()

        pe_offset = struct.unpack_from("<I", pe64, 0x3C)[0]
        self.assertEqual(struct.unpack_from("<H", pe64, pe_offset + 4)[0], 0x8664)
        self.assertEqual(elf[:4], b"\x7fELF")
        self.assertEqual(struct.unpack_from("<H", elf, 18)[0], 0x3E)
        self.assertEqual(macho[:4], b"\xcf\xfa\xed\xfe")
        self.assertEqual(struct.unpack_from("<I", macho, 4)[0], 0x01000007)

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

    def test_lowers_structured_control_blocks_to_branch_mnemonics(self):
        source = (
            "DCL TOTAL FIXED BIN(31); TOTAL = 0; "
            "DO WHILE TOTAL < 2; TOTAL = TOTAL + 1; END; "
            "DO; TOTAL = TOTAL + 1; UNTIL TOTAL = 4; END; "
            "SELECT(TOTAL); WHEN(4) TOTAL = 10; OTHERWISE TOTAL = 20; END;"
        )
        mnemonics, _, _ = lower_program(Parser(Lexer(source).tokenize()).parse())
        ops = [mnemonic.op for mnemonic in mnemonics]
        labels = [mnemonic.args[0] for mnemonic in mnemonics if mnemonic.op == "LABEL"]

        self.assertIn("JFALSE", ops)
        self.assertIn("JMP", ops)
        self.assertTrue(any(str(label).startswith("do_") for label in labels))
        self.assertTrue(any(str(label).startswith("select_") for label in labels))

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

    def test_dynamic_function_table_registers_user_procedures(self):
        program = Parser(Lexer("P: PROC(A,B) RETURNS(FIXED); END P;").tokenize()).parse()
        table = build_dynamic_function_table(program)
        descriptor = table.get("P")

        self.assertEqual(descriptor.source, "dynamic")
        self.assertEqual(descriptor.returns, "FIXED")
        self.assertEqual([parameter.name for parameter in descriptor.parameters], ["A", "B"])
        self.assertIsNotNone(descriptor.pointer)

    def test_runtime_function_table_contains_io_alloc_tcpip_and_socket_entries(self):
        for name in ["ALLOC", "FREE", "OPEN", "READ", "WRITE", "CLOSE", "TCPIP", "TCPIP_SEND", "SSL_SOCKET", "TLS_SOCKET"]:
            self.assertEqual(RUNTIME_FUNCTION_TABLE.get(name).source, "runtime")

    def test_static_table_contains_declared_pl1_builtins(self):
        descriptor = RUNTIME_FUNCTION_TABLE.get("SUBSTR")

        self.assertEqual(descriptor.source, "builtin")
        self.assertTrue(descriptor.requires_declaration)
        self.assertEqual([parameter.name for parameter in descriptor.parameters], ["S", "START", "COUNT"])

        pointer = RUNTIME_FUNCTION_TABLE.get("POINTER")
        self.assertEqual(pointer.source, "builtin")
        self.assertTrue(pointer.requires_declaration)
        self.assertEqual(pointer.returns, "POINTER")
        self.assertEqual([parameter.name for parameter in pointer.parameters], ["VALUE", "OFFSET"])
        self.assertTrue(all(parameter.optional for parameter in pointer.parameters))

    def test_builtin_declaration_enables_static_builtin_call(self):
        source = "DCL SUBSTR BUILTIN; CALL SUBSTR(S, START, COUNT);"
        program = Parser(Lexer(source).tokenize()).parse()
        normalized = normalize_calls(program)

        self.assertEqual(declared_builtins(program), {"SUBSTR"})
        self.assertIsInstance(normalized.statements[1], Call)

    def test_static_builtin_call_requires_builtin_declaration(self):
        program = Parser(Lexer("CALL SUBSTR(S, START, COUNT);").tokenize()).parse()

        with self.assertRaises(Exception) as context:
            normalize_calls(program)
        self.assertIn("must be declared with BUILTIN", str(context.exception))

    def test_builtin_by_name_normalizes_after_declaration(self):
        source = "DCL SUBSTR BUILTIN; CALL SUBSTR(COUNT, S, START) BY NAME;"
        program = normalize_calls(Parser(Lexer(source).tokenize()).parse())
        call = program.statements[1]

        self.assertIsInstance(call, Call)
        self.assertEqual(call.mode, "reference")
        self.assertEqual([argument.name for argument in call.arguments], ["S", "START", "COUNT"])

    def test_pointer_builtin_keyword_declaration_enables_call(self):
        source = "DCL POINTER BUILTIN; CALL POINTER(VALUE, OFFSET) BY NAME;"
        program = normalize_calls(Parser(Lexer(source).tokenize()).parse())

        self.assertEqual(declared_builtins(program), {"POINTER"})
        self.assertEqual(program.statements[1].name, "POINTER")
        self.assertEqual([argument.name for argument in program.statements[1].arguments], ["VALUE", "OFFSET"])

    def test_runtime_execution_visitor_uses_function_table_and_control_blocks(self):
        source = (
            "DCL LENGTH BUILTIN; DCL X FIXED BIN(31); DCL TEXT CHARACTER; "
            "TEXT = 'HELLO'; X = 0; "
            "DO WHILE X < 2; X = X + 1; END; "
            "DO; X = X + 1; UNTIL X = 4; END; "
            "SELECT(X); WHEN(4) CALL DISPLAY('FOUR'); OTHERWISE CALL DISPLAY('OTHER'); END; "
            "CALL LENGTH(TEXT);"
        )
        program = normalize_calls(Parser(Lexer(source).tokenize()).parse())
        visitor = RuntimeExecutionVisitor()

        visitor.visit(program)

        self.assertEqual(visitor.variables["X"].value, 4)
        self.assertEqual(visitor.output, ["FOUR"])

    def test_function_table_validates_call_descriptions(self):
        table = FunctionTable()
        table.add_function(
            FunctionDescriptor(
                "ADD",
                lambda left, right: left + right,
                (
                    ParameterDescriptor("LEFT", "FIXED BIN"),
                    ParameterDescriptor("RIGHT", "FIXED BIN"),
                ),
                returns="FIXED BIN",
            )
        )

        self.assertEqual(table.call("ADD", 2, 3), 5)
        with self.assertRaises(FunctionTableError):
            table.validate_call(Call("ADD", [Identifier("LEFT")]))

    def test_normalize_calls_checks_unknown_functions(self):
        program = Parser(Lexer("CALL DOES_NOT_EXIST();").tokenize()).parse()

        with self.assertRaises(Exception):
            normalize_calls(program)

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

    def test_unlabelled_proc_options_main_uses_main_entry_name(self):
        source = "PROC OPTIONS(MAIN); END;"
        program = Parser(Lexer(source).tokenize()).parse()
        mnemonics, _, _ = lower_program(program)

        self.assertEqual(main_procedure_name(program), "MAIN")
        self.assertIn(type(mnemonics[0])("LABEL", ("MAIN",)), mnemonics)
        self.assertIn(type(mnemonics[0])("CALL_PROC", ("MAIN", 0)), mnemonics)

    def test_main_procedure_command_parameter_reaches_python_entry(self):
        source = "MAIN: PROC(PARM) OPTIONS(MAIN); CALL DISPLAY(PARM); END MAIN;"
        output = compile_source(source, target="python-source")

        self.assertIn("import sys", output)
        self.assertIn("def MAIN(PARM):", output)
        self.assertIn('MAIN(" ".join(sys.argv[1:]))', output)

    def test_command_line_runtime_binds_pl1_main_parameters(self):
        runtime = CommandLineRuntime.from_argv(["prog", "ONE", "TWO"])

        self.assertEqual(runtime.command(), "ONE TWO")
        self.assertEqual(runtime.argc(), 2)
        self.assertEqual(runtime.argv_value(1), "ONE")
        self.assertEqual(runtime.bind_main_parameters(["PARM", "COUNT", "ARGS"]), ["ONE TWO", 2, ["ONE", "TWO"]])

    def test_runtime_function_table_exposes_command_line_services(self):
        for name in ("COMMAND", "ARGC", "ARGV"):
            descriptor = RUNTIME_FUNCTION_TABLE.get(name)
            self.assertEqual(descriptor.source, "runtime")
            self.assertFalse(descriptor.requires_declaration)

    def test_dynamic_load_runtime_and_function_table_services(self):
        runtime = DynamicLoadRuntime()
        java_request = runtime.java_class("pl1compinpy.runtime.PL1Runtime", ["pl1rt.jar"])
        dotnet_request = runtime.dotnet_assembly("PL1CompInPy.Runtime.dll", "PL1Runtime")

        self.assertEqual(java_request.class_name, "pl1compinpy.runtime.PL1Runtime")
        self.assertEqual(java_request.classpath, ("pl1rt.jar",))
        self.assertEqual(dotnet_request.assembly_name, "PL1CompInPy.Runtime.dll")
        for name in ("DYNLOAD", "DYNSYM", "JAVA_LOAD_CLASS", "DOTNET_LOAD_ASSEMBLY"):
            self.assertEqual(RUNTIME_FUNCTION_TABLE.get(name).source, "runtime")

    def test_runtime_visitor_dispatches_managed_dynamic_load_helpers(self):
        visitor = RuntimeExecutionVisitor()
        java_result = visitor.visit(Parser(Lexer("CALL JAVA_LOAD_CLASS('pl1compinpy.runtime.PL1Runtime');").tokenize()).parse())
        dotnet_result = visitor.visit(Parser(Lexer("CALL DOTNET_LOAD_ASSEMBLY('PL1CompInPy.Runtime.dll');").tokenize()).parse())

        self.assertEqual(java_result.class_name, "pl1compinpy.runtime.PL1Runtime")
        self.assertEqual(dotnet_result.assembly_name, "PL1CompInPy.Runtime.dll")

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

    def test_python_source_backend_emits_file_io_loops_and_select(self):
        source = (
            "OPEN FILE(F); READ FILE(F) INTO(BUF); WRITE FILE(F) FROM(BUF); CLOSE FILE(F); "
            "DO WHILE TOTAL < 3; TOTAL = TOTAL + 1; END; "
            "DO; TOTAL = TOTAL + 1; UNTIL TOTAL = 5; END; "
            "SELECT(TOTAL); WHEN(1) CALL DISPLAY('ONE'); OTHERWISE CALL DISPLAY('OTHER'); END;"
        )
        output = compile_source(source, target="python-source")

        self.assertIn("runtime.open(F)", output)
        self.assertIn("BUF = runtime.read_record(F)", output)
        self.assertIn("runtime.write_record(F, BUF)", output)
        self.assertIn("runtime.close(F)", output)
        self.assertIn("while (TOTAL < 3):", output)
        self.assertIn("if (TOTAL == 5):", output)
        self.assertIn("if TOTAL == 1:", output)
        self.assertIn("else:", output)

    def test_runtime_linkage_plans_cover_native_and_managed_targets(self):
        windows = runtime_linkage("pe64-x86_64-windows")
        elf = runtime_linkage("elf64-x86_64")
        arm64_windows = runtime_linkage("arm64-windows")
        jvm = runtime_linkage("jvm-bytecode")
        dotnet = runtime_linkage("dotnet-il")

        self.assertIn("LIBCMT.lib", windows.static_libraries)
        self.assertIn("MSVCRT.lib", windows.import_libraries)
        self.assertIn("libpl1rt_x86_64.a", elf.static_libraries)
        self.assertIn("pl1rt_arm64_windows.lib", arm64_windows.static_libraries)
        self.assertEqual(jvm.managed_type, "pl1compinpy/runtime/PL1Runtime")
        self.assertEqual(dotnet.managed_type, "PL1CompInPy.Runtime.PL1Runtime")

    def test_native_assembly_links_pl1_runtime_symbols(self):
        source = "DCL TOTAL FIXED BIN(31); TOTAL = 1;"
        x86_64_windows = compile_source(source, target="x86_64-windows")
        arm64_macos = compile_source(source, target="arm64-macos")

        self.assertIn("extern pl1rt_init", x86_64_windows)
        self.assertIn("call pl1rt_init", x86_64_windows)
        self.assertIn(".extern _pl1rt_init", arm64_macos)
        self.assertIn("bl _pl1rt_shutdown", arm64_macos)

    def test_native_binary_embeds_runtime_link_manifest(self):
        binary = compile_binary("elf64-x86_64", "CALL DISPLAY('RUNTIME');")

        self.assertIn(b"PL1RTLINK\0", binary)
        self.assertIn(b"libpl1rt_x86_64.a", binary)
        self.assertIn(b"DISPLAY", binary)

    def test_jvm_bytecode_backend_emits_main_and_return_descriptor(self):
        source = "MAIN: PROC OPTIONS(MAIN) RETURNS(FIXED); RETURN 0; END MAIN;"
        output = compile_source(source, target="jvm-bytecode")

        self.assertIn(".class public PL1Program", output)
        self.assertIn(".method public static MAIN()I", output)
        self.assertIn(".method public static main([Ljava/lang/String;)V", output)
        self.assertIn("invokestatic pl1compinpy/runtime/PL1Runtime/init()V", output)
        self.assertIn("invokestatic PL1Program/MAIN()I", output)
        self.assertIn("invokestatic pl1compinpy/runtime/PL1Runtime/shutdown()V", output)

    def test_dotnet_il_backend_emits_entrypoint_and_console_output(self):
        source = "MAIN: PROC OPTIONS(MAIN) RETURNS(FIXED); DCL TOTAL FIXED BIN(31); TOTAL = 40 + 2; CALL DISPLAY(TOTAL); RETURN TOTAL; END MAIN;"
        output = compile_source(source, target="dotnet-il")

        self.assertIn(".assembly extern mscorlib", output)
        self.assertIn(".assembly extern PL1CompInPy.Runtime {}", output)
        self.assertIn(".module PL1Program.exe", output)
        self.assertIn(".entrypoint", output)
        self.assertIn("PL1CompInPy.Runtime.PL1Runtime::Init()", output)
        self.assertIn("call int32 PL1Program::MAIN()", output)
        self.assertIn("PL1CompInPy.Runtime.PL1Runtime::Shutdown()", output)
        self.assertIn("call void [mscorlib]System.Console::WriteLine(int32)", output)

    def test_dotnet_il_backend_copies_parameters_to_locals(self):
        output = compile_source("ADD1: PROC(N) RETURNS(FIXED); RETURN N; END ADD1;", target="dotnet-il")

        self.assertIn(".method public hidebysig static int32 ADD1(int32 N)", output)
        self.assertIn("ldarg 0", output)
        self.assertIn("stloc 0", output)
        self.assertIn("ldloc 0", output)

    def test_dotnet_executable_builder_reports_missing_ilasm(self):
        program = Parser(Lexer("CALL DISPLAY('HELLO');").tokenize()).parse()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(DotNetExecutableError):
                from pl1compinpy.codegen.dotnet_executable import emit_dotnet_executable

                emit_dotnet_executable(program, Path(tmp) / "hello.exe", ilasm="/missing/ilasm")

    def test_jvm_classfile_backend_emits_java_17_class(self):
        source = "MAIN: PROC OPTIONS(MAIN) RETURNS(FIXED); RETURN 0; END MAIN;"
        classes = compile_jvm_classes(source)
        classfile = classes["PL1Program.class"]

        self.assertEqual(classfile[:4], b"\xca\xfe\xba\xbe")
        self.assertEqual(int.from_bytes(classfile[4:6], "big"), 0)
        self.assertEqual(int.from_bytes(classfile[6:8], "big"), JAVA_17_MAJOR_VERSION)
        self.assertIn(b"pl1compinpy/runtime/PL1Runtime", classfile)
        self.assertIn(b"PL1Program", classfile)
        self.assertIn(b"MAIN", classfile)
        self.assertIn(b"main", classfile)

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

    def test_runtime_executes_parsed_file_io_statements(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = FileDescriptor("F", Path(tmp) / "io.dat", mode="OUTPUT", recfm="V")
            program = Parser(Lexer("OPEN FILE(F); WRITE FILE(F) FROM(BUF); CLOSE FILE(F);").tokenize()).parse()
            runtime = StdioRuntime()
            variables = {"BUF": b"PAYLOAD"}

            for statement in program.statements:
                runtime.execute(statement, {"F": output}, variables)

            input_descriptor = FileDescriptor("F", Path(tmp) / "io.dat", mode="INPUT", recfm="V")
            read_program = Parser(Lexer("OPEN FILE(F); READ FILE(F) INTO(BUF); CLOSE FILE(F);").tokenize()).parse()
            for statement in read_program.statements:
                runtime.execute(statement, {"F": input_descriptor}, variables)

            self.assertEqual(variables["BUF"], b"PAYLOAD")

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

    def test_string_runtime_uses_two_byte_length_prefix(self):
        runtime = StringRuntime()
        value = runtime.allocate("HELLO")

        self.assertEqual(value.storage[:2], b"\x00\x05")
        self.assertEqual(value.payload, b"HELLO")
        self.assertEqual(value.text(), "HELLO")

    def test_string_runtime_substr_is_one_based(self):
        runtime = StringRuntime()
        value = runtime.allocate("HELLO")
        result = runtime.substr(value, 2, 3)

        self.assertEqual(result.storage[:2], b"\x00\x03")
        self.assertEqual(result.text(), "ELL")

    def test_string_runtime_length_index_and_assignment_use_two_byte_storage(self):
        runtime = StringRuntime()
        value = runtime.allocate("HELLO")

        runtime.assign(value, "HELLO WORLD")

        self.assertEqual(value.storage[:2], b"\x00\x0b")
        self.assertEqual(runtime.length(value), 11)
        self.assertEqual(runtime.index(value, "WORLD"), 7)

    def test_fixed_decimal_packed_and_zoned_codecs_round_trip(self):
        fixed = FixedDecimal.from_string("-123.45", precision=5, scale=2)
        packed = PackedDecimalCodec.encode(fixed)
        zoned = ZonedDecimalCodec.encode(fixed)

        self.assertEqual(packed, bytes.fromhex("12345d"))
        self.assertEqual(zoned, "1234N")
        self.assertEqual(PackedDecimalCodec.decode(packed, 5, 2), Decimal("-123.45"))
        self.assertEqual(ZonedDecimalCodec.decode(zoned, 5, 2), Decimal("-123.45"))

    def test_decimal_runtime_conversions_are_accessible(self):
        packed = DecimalRuntime.convert("42.50", "STRING", "PACKED", precision=4, scale=2)
        zoned = DecimalRuntime.convert(packed, "PACKED", "ZONED", precision=4, scale=2)

        self.assertEqual(packed, bytes.fromhex("04250c"))
        self.assertEqual(zoned, "425{")
        self.assertEqual(DecimalRuntime.convert(zoned, "ZONED", "STRING", precision=4, scale=2), "42.50")

    def test_picture_runtime_formats_and_parses_fixed_and_float_values(self):
        runtime = PictureRuntime()

        self.assertEqual(runtime.fixed_to_picture(42, "ZZZ9"), "  42")
        self.assertEqual(runtime.float_to_picture(12.345, "Z9.99"), "12.35")
        self.assertEqual(runtime.picture_to_fixed("  42", "ZZZ9"), Decimal("42"))
        self.assertEqual(runtime.picture_to_float("12.35", "Z9.99"), 12.35)

    def test_calculation_engine_promotes_numeric_tower_and_precedence(self):
        expression = Parser(Lexer("RESULT = 2 + 3 * 4 ** 2;").tokenize()).parse().statements[0].expression
        result = CalculationEngine().evaluate(expression)

        self.assertEqual(result.value, 50)
        self.assertEqual(result.type, PL1Type.FIXED_BIN)

    def test_calculation_engine_casts_and_converts_numeric_types(self):
        engine = CalculationEngine({"A": PL1Value(Decimal("2.5"), PL1Type.FIXED_DEC), "B": PL1Value(4, PL1Type.FIXED_BIN)})
        value = engine.evaluate(Parser(Lexer("RESULT = A + B;").tokenize()).parse().statements[0].expression)

        self.assertEqual(value.value, Decimal("6.5"))
        self.assertEqual(value.type, PL1Type.FIXED_DEC)
        self.assertEqual(engine.cast(PL1Value("42.9", PL1Type.CHARACTER), PL1Type.FIXED_BIN).value, 42)
        self.assertEqual(engine.cast(PL1Value(1, PL1Type.FIXED_BIN), PL1Type.FLOAT).value, 1.0)

    def test_calculation_builtins_handle_fixed_decimal_and_strings(self):
        builtins = CalculationBuiltinRuntime()
        fixed = builtins.FIXED_DECIMAL("10.25", 4, 2)
        text = StringRuntime().allocate("ABCDEFG")

        self.assertEqual(builtins.ROUND(fixed, 1), Decimal("10.3"))
        self.assertEqual(builtins.TRUNC(fixed, 1), Decimal("10.2"))
        self.assertEqual(builtins.LENGTH(text), 7)
        self.assertEqual(builtins.SUBSTR(text, 2, 3), "BCD")
        self.assertEqual(builtins.INDEX(text, "DE"), 4)

    def test_pointer_builtin_runtime_normalizes_handles_offsets_and_nulls(self):
        builtins = PointerBuiltinRuntime()

        self.assertEqual(builtins.POINTER(42), PointerValue(42, 0))
        self.assertEqual(builtins.POINTER(42, 8), PointerValue(42, 8))
        self.assertEqual(builtins.POINTER(PointerValue(42, 4), 8), PointerValue(42, 12))
        self.assertEqual(builtins.POINTER(None), PointerValue(None, 0))

    def test_runtime_visitor_dispatches_pointer_builtin(self):
        program = normalize_calls(Parser(Lexer("DCL POINTER BUILTIN; CALL POINTER(); CALL POINTER(42, 8);").tokenize()).parse())
        result = RuntimeExecutionVisitor().visit(program)

        self.assertEqual(result, PointerValue(42, 8))

    def test_runtime_function_table_exposes_decimal_conversion_builtins(self):
        for name in ("FIXED_DECIMAL", "DECIMAL_TO_PACKED", "DECIMAL_FROM_PACKED", "DECIMAL_TO_ZONED", "DECIMAL_FROM_ZONED"):
            descriptor = RUNTIME_FUNCTION_TABLE.get(name)
            self.assertEqual(descriptor.source, "builtin")
            self.assertTrue(descriptor.requires_declaration)

    def test_calculation_engine_handles_float_character_and_bit_operators(self):
        engine = CalculationEngine({"X": PL1Value(1.5, PL1Type.FLOAT), "FLAG": PL1Value(True, PL1Type.BIT)})

        float_value = engine.evaluate(Parser(Lexer("RESULT = X + 2;").tokenize()).parse().statements[0].expression)
        text_value = engine.evaluate(Parser(Lexer("RESULT = 'A' || 'B';").tokenize()).parse().statements[0].expression)
        bit_value = engine.evaluate(Parser(Lexer("RESULT = ^FLAG OR 0;").tokenize()).parse().statements[0].expression)

        self.assertEqual(float_value.type, PL1Type.FLOAT)
        self.assertEqual(float_value.value, 3.5)
        self.assertEqual(text_value.value, "AB")
        self.assertEqual(bit_value.value, False)

    def test_complex_attribute_builtins_and_compute_engine(self):
        declaration = Parser(Lexer("DCL (COMPLEX, REAL, IMAG, CONJG, ABS, SQRT) BUILTIN; DCL Z COMPLEX FLOAT;").tokenize()).parse().statements[0]
        builtins = CalculationBuiltinRuntime()
        complex_runtime = ComplexRuntime()
        z = builtins.COMPLEX(3, 4)
        expression = Parser(Lexer("RESULT = Z * Z;").tokenize()).parse().statements[0].expression
        result = CalculationEngine({"Z": PL1Value(z, PL1Type.COMPLEX)}).evaluate(expression)
        sqrt_negative = builtins.SQRT(ComplexValue(-1, 0))

        self.assertEqual(declaration.names, ["COMPLEX", "REAL", "IMAG", "CONJG", "ABS", "SQRT"])
        self.assertEqual(PliTypeParser().parse("COMPLEX FLOAT(53)").canonical(), "COMPLEX FLOAT BINARY(53)")
        self.assertEqual(TYPE_MAPPINGS["COMPLEX FLOAT BINARY"].python, "ComplexValue[float,float]")
        self.assertEqual(builtins.REAL(z), 3)
        self.assertEqual(builtins.IMAG(z), 4)
        self.assertEqual(builtins.ABS(z), 5.0)
        self.assertEqual(builtins.IMAG(builtins.CONJG(z)), -4)
        self.assertEqual(complex_runtime.mul(z, z), result.value)
        self.assertEqual(result.type, PL1Type.COMPLEX)
        self.assertEqual(result.value.real, -7)
        self.assertEqual(result.value.imag, 24)
        self.assertEqual(sqrt_negative.real, 0)
        self.assertEqual(sqrt_negative.imag, 1)

    def test_complex_builtins_run_through_runtime_function_table(self):
        program = normalize_calls(
            Parser(
                Lexer(
                    "DCL (COMPLEX, REAL, IMAG, CONJG, ABS) BUILTIN; "
                    "DCL Z COMPLEX FLOAT; "
                    "Z = COMPLEX(3,4); "
                    "CALL DISPLAY(REAL(Z)); "
                    "CALL DISPLAY(IMAG(Z)); "
                    "CALL DISPLAY(ABS(Z)); "
                    "CALL DISPLAY(IMAG(CONJG(Z)));"
                ).tokenize()
            ).parse()
        )
        visitor = RuntimeExecutionVisitor()

        visitor.visit(program)

        self.assertEqual(visitor.output, [3, 4, 5.0, -4])
        self.assertEqual(RUNTIME_FUNCTION_TABLE.get("COMPLEX").returns, "COMPLEX")
        self.assertTrue(RUNTIME_FUNCTION_TABLE.get("REAL").requires_declaration)

    def test_socket_runtime_sends_and_receives_plain_tcp(self):
        runtime = SocketRuntime()
        left, right = socket.socketpair()
        try:
            left.settimeout(1.0)
            right.settimeout(1.0)
            runtime.adopt("LEFT", left)
            runtime.adopt("RIGHT", right)

            runtime.send("LEFT", "PING")
            self.assertEqual(runtime.receive("RIGHT", 4), b"PING")
            runtime.send("RIGHT", b"PONG")
            self.assertEqual(runtime.receive("LEFT", 4), b"PONG")
        finally:
            runtime.close_all()

    def test_socket_runtime_builds_ssl_and_tls_descriptors(self):
        ssl_descriptor = SocketDescriptor.ssl_client("SSL", "localhost", 443, verify=False)
        tls_descriptor = SocketDescriptor.tls_client("TLS", "localhost", 443)

        self.assertEqual(ssl_descriptor.secure, SocketSecureMode.SSL)
        self.assertEqual(tls_descriptor.secure, SocketSecureMode.TLS)
        self.assertEqual(ssl_descriptor.server_hostname, "localhost")
        self.assertTrue(tls_descriptor.verify)

    def test_socket_stream_runtime_handles_variable_text_records(self):
        runtime = SocketStreamRuntime()
        left, right = socket.socketpair()
        try:
            left.settimeout(1.0)
            right.settimeout(1.0)
            runtime.adopt("LEFT", left)
            runtime.adopt("RIGHT", right)
            sender = SocketFileDescriptor("LEFT", recfm="V", text=True)
            receiver = SocketFileDescriptor("RIGHT", recfm="V", text=True)

            runtime.write_payload(sender, "HELLO SOCKET")

            self.assertEqual(runtime.read_payload(receiver), "HELLO SOCKET")
        finally:
            runtime.close_all()

    def test_socket_stream_runtime_handles_fixed_binary_records(self):
        runtime = SocketStreamRuntime()
        left, right = socket.socketpair()
        try:
            left.settimeout(1.0)
            right.settimeout(1.0)
            runtime.adopt("LEFT", left)
            runtime.adopt("RIGHT", right)
            sender = SocketFileDescriptor("LEFT", recfm="F", lrecl=6)
            receiver = SocketFileDescriptor("RIGHT", recfm="F", lrecl=6)

            runtime.write_record(sender, b"ABC")

            self.assertEqual(runtime.read_record(receiver), b"ABC\0\0\0")
        finally:
            runtime.close_all()

    def test_based_runtime_binds_records_to_pointer_storage(self):
        runtime = BasedRuntime()
        runtime.declare_pointer("P")
        runtime.declare_based_record("REC", size=4, pointer_name="P")
        pointer = runtime.allocate_based("REC")

        runtime.write_record("REC", b"ABCD")
        self.assertEqual(runtime.read_record("REC"), b"ABCD")

        runtime.declare_pointer("Q")
        runtime.set_pointer("Q", pointer.handle or 0)
        self.assertEqual(runtime.read_record("REC", pointer_name="Q"), b"ABCD")

    def test_parses_generic_declaration(self):
        source = "DCL SELECTOR GENERIC(PFIXED WHEN(FIXED), PCHAR WHEN(CHARACTER));"
        declaration = Parser(Lexer(source).tokenize()).parse().statements[0]

        self.assertEqual(declaration.names, ["SELECTOR"])
        alternatives = declaration.generic_options["SELECTOR"]
        self.assertEqual([(alt.procedure, alt.parameter_types) for alt in alternatives], [
            ("PFIXED", ["FIXED"]),
            ("PCHAR", ["CHARACTER"]),
        ])

    def test_generic_runtime_dispatches_with_lambdas_by_type(self):
        runtime = GenericRuntime()
        runtime.define("SELECTOR").when(["FIXED"], lambda value: value + 1).when(["CHARACTER"], lambda value: value.lower())

        self.assertEqual(runtime.call("SELECTOR", 41), 42)
        self.assertEqual(runtime.call("SELECTOR", "HELLO"), "hello")

    def test_vsam_ksds_catalog_and_data_components(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog = VSAMCatalog.define(Path(tmp), "CUSTOMER", VSAMType.KSDS, key_offset=0, key_length=4)
            catalog.write(b"KEY1payload")

            self.assertTrue((Path(tmp) / "catalog.json").exists())
            self.assertTrue((Path(tmp) / "data.bin").exists())
            self.assertEqual(catalog.read(key=b"KEY1"), b"KEY1payload")

    def test_vsam_esds_reads_by_rba(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog = VSAMCatalog.define(Path(tmp), "EVENTS", VSAMType.ESDS)
            rba = catalog.write(b"first")

            self.assertEqual(catalog.read(rba=rba), b"first")

    def test_vsam_rrds_reads_by_relative_record_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog = VSAMCatalog.define(Path(tmp), "SLOTS", VSAMType.RRDS, record_length=6)
            catalog.write(b"ABC", rrn=7)

            self.assertEqual(catalog.read(rrn=7), b"ABC\0\0\0")

    def test_vsam_lds_reads_by_relative_byte_address(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog = VSAMCatalog.define(Path(tmp), "LINEAR", VSAMType.LDS)
            catalog.write(b"0123456789", rba=0)

            self.assertEqual(catalog.read(rba=3, length=4), b"3456")

    def test_parses_vsam_file_options(self):
        source = "DCL CUSTOMER_FILE FILE RECORD UPDATE ENVIRONMENT(VSAM(KSDS), KEYOFFSET(0), KEYLENGTH(4), PATH('customer.ksds')) BINARY;"
        declaration = Parser(Lexer(source).tokenize()).parse().statements[0]

        self.assertEqual(declaration.file_options["vsam"], "KSDS")
        self.assertEqual(declaration.file_options["keyoffset"], "0")
        self.assertEqual(declaration.file_options["keylength"], "4")

    def test_vsam_descriptor_from_pl1_file_declaration(self):
        source = "DCL CUSTOMER_FILE FILE RECORD UPDATE ENVIRONMENT(VSAM(KSDS), KEYOFFSET(0), KEYLENGTH(4), PATH('customer.ksds')) BINARY;"
        declaration = Parser(Lexer(source).tokenize()).parse().statements[0]
        descriptor = VSAMFileDescriptor.from_declaration(declaration, Path("/tmp"))

        self.assertEqual(descriptor.name, "CUSTOMER_FILE")
        self.assertEqual(descriptor.organization, VSAMType.KSDS)
        self.assertEqual(descriptor.key_offset, 0)
        self.assertEqual(descriptor.key_length, 4)
        self.assertEqual(descriptor.path, Path("/tmp/customer.ksds"))

    def test_vsam_runtime_executes_parsed_open_write_read_close(self):
        with tempfile.TemporaryDirectory() as tmp:
            declaration = Parser(
                Lexer("DCL CUSTOMER FILE RECORD UPDATE ENVIRONMENT(VSAM(KSDS), KEYOFFSET(0), KEYLENGTH(4), PATH('customer.ksds')) BINARY;").tokenize()
            ).parse().statements[0]
            output_descriptor = VSAMFileDescriptor.from_declaration(declaration, Path(tmp))
            write_program = Parser(Lexer("OPEN FILE(CUSTOMER); WRITE FILE(CUSTOMER) FROM(RECORD); CLOSE FILE(CUSTOMER);").tokenize()).parse()
            runtime = VSAMRuntime()
            variables = {"RECORD": b"KEY1payload"}

            for statement in write_program.statements:
                runtime.execute(statement, {"CUSTOMER": output_descriptor}, variables)

            input_descriptor = VSAMFileDescriptor(
                output_descriptor.name,
                output_descriptor.path,
                output_descriptor.organization,
                mode="INPUT",
                key_offset=output_descriptor.key_offset,
                key_length=output_descriptor.key_length,
            )
            read_program = Parser(Lexer("OPEN FILE(CUSTOMER); READ FILE(CUSTOMER) KEY(KEY) INTO(RECORD); CLOSE FILE(CUSTOMER);").tokenize()).parse()
            variables["KEY"] = "KEY1"
            for statement in read_program.statements:
                runtime.execute(statement, {"CUSTOMER": input_descriptor}, variables)

            self.assertEqual(variables["RECORD"], b"KEY1payload")

    def test_vsam_runtime_executes_esds_io_by_rba(self):
        with tempfile.TemporaryDirectory() as tmp:
            declaration = Parser(
                Lexer("DCL EVENTS FILE RECORD UPDATE ENVIRONMENT(VSAM(ESDS), PATH('events.esds')) BINARY;").tokenize()
            ).parse().statements[0]
            descriptor = VSAMFileDescriptor.from_declaration(declaration, Path(tmp))
            runtime = VSAMRuntime()
            variables = {"RECORD": b"first-event", "RBA": 0}

            write_program = Parser(Lexer("OPEN FILE(EVENTS); WRITE FILE(EVENTS) FROM(RECORD); CLOSE FILE(EVENTS);").tokenize()).parse()
            for statement in write_program.statements:
                runtime.execute(statement, {"EVENTS": descriptor}, variables)

            read_program = Parser(Lexer("OPEN FILE(EVENTS); READ FILE(EVENTS) RBA(RBA) INTO(RECORD); CLOSE FILE(EVENTS);").tokenize()).parse()
            for statement in read_program.statements:
                runtime.execute(statement, {"EVENTS": descriptor}, variables)

            self.assertEqual(variables["RECORD"], b"first-event")

    def test_vsam_runtime_executes_rrds_io_by_rrn(self):
        with tempfile.TemporaryDirectory() as tmp:
            declaration = Parser(
                Lexer("DCL SLOTS FILE RECORD UPDATE ENVIRONMENT(VSAM(RRDS), RECORDLENGTH(6), PATH('slots.rrds')) BINARY;").tokenize()
            ).parse().statements[0]
            descriptor = VSAMFileDescriptor.from_declaration(declaration, Path(tmp))
            runtime = VSAMRuntime()
            variables = {"RECORD": b"ABC", "RRN": 7}

            write_program = Parser(Lexer("OPEN FILE(SLOTS); WRITE FILE(SLOTS) RRN(RRN) FROM(RECORD); CLOSE FILE(SLOTS);").tokenize()).parse()
            for statement in write_program.statements:
                runtime.execute(statement, {"SLOTS": descriptor}, variables)

            read_program = Parser(Lexer("OPEN FILE(SLOTS); READ FILE(SLOTS) RRN(RRN) INTO(RECORD); CLOSE FILE(SLOTS);").tokenize()).parse()
            for statement in read_program.statements:
                runtime.execute(statement, {"SLOTS": descriptor}, variables)

            self.assertEqual(variables["RECORD"], b"ABC\0\0\0")

    def test_vsam_runtime_executes_lds_io_by_rba_and_length(self):
        with tempfile.TemporaryDirectory() as tmp:
            declaration = Parser(
                Lexer("DCL LINEAR FILE RECORD UPDATE ENVIRONMENT(VSAM(LDS), PATH('linear.lds')) BINARY;").tokenize()
            ).parse().statements[0]
            descriptor = VSAMFileDescriptor.from_declaration(declaration, Path(tmp))
            runtime = VSAMRuntime()
            variables = {"PAYLOAD": b"0123456789", "RBA": 0, "READ_RBA": 3, "LEN": 4}

            write_program = Parser(Lexer("OPEN FILE(LINEAR); WRITE FILE(LINEAR) RBA(RBA) FROM(PAYLOAD); CLOSE FILE(LINEAR);").tokenize()).parse()
            for statement in write_program.statements:
                runtime.execute(statement, {"LINEAR": descriptor}, variables)

            read_program = Parser(Lexer("OPEN FILE(LINEAR); READ FILE(LINEAR) RBA(READ_RBA) LENGTH(LEN) INTO(PAYLOAD); CLOSE FILE(LINEAR);").tokenize()).parse()
            for statement in read_program.statements:
                runtime.execute(statement, {"LINEAR": descriptor}, variables)

            self.assertEqual(variables["PAYLOAD"], b"3456")

    def test_builtin_loader_reads_substr_pl1_source(self):
        source = BuiltinLibrary().source("SUBSTR")

        self.assertIn("SUBSTR: PROC", source)
        self.assertIn("RETURNS(CHARACTER)", source)

    def test_compiler_can_include_substr_builtin_source(self):
        output = compile_source("DCL X FIXED BIN(31);", builtins=["SUBSTR"])

        self.assertIn("def SUBSTR", output)
        self.assertIn("X = 0", output)


if __name__ == "__main__":
    unittest.main()
