import unittest
from decimal import Decimal
from pathlib import Path
import sys
import struct
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pl1compinpy import compile_source
from pl1compinpy.builtins import BuiltinLibrary
from pl1compinpy.compiler import compile_binary, compile_jvm_classes
from pl1compinpy.codegen.dotnet_executable import DotNetExecutableError
from pl1compinpy.codegen.jvm_classfile import JAVA_17_MAJOR_VERSION
from pl1compinpy.codegen.executable_pipeline import lower_program
from pl1compinpy.codegen.linkers import ELFLinker, MachOLinker, PELinker
from pl1compinpy.ast import Call, Declaration, DoGroup, IOStatement, IfStatement, LabelledStatement, Procedure, SelectStatement
from pl1compinpy.frontend.lexer import Lexer, TokenType
from pl1compinpy.frontend.parser import Parser
from pl1compinpy.runtime import (
    ArrayRuntime,
    BasedRuntime,
    FileDescriptor,
    GenericRuntime,
    PictureRuntime,
    StdioRuntime,
    StringRuntime,
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

    def test_jvm_bytecode_backend_emits_main_and_return_descriptor(self):
        source = "MAIN: PROC OPTIONS(MAIN) RETURNS(FIXED); RETURN 0; END MAIN;"
        output = compile_source(source, target="jvm-bytecode")

        self.assertIn(".class public PL1Program", output)
        self.assertIn(".method public static MAIN()I", output)
        self.assertIn(".method public static main([Ljava/lang/String;)V", output)
        self.assertIn("invokestatic PL1Program/MAIN()I", output)

    def test_dotnet_il_backend_emits_entrypoint_and_console_output(self):
        source = "MAIN: PROC OPTIONS(MAIN) RETURNS(FIXED); DCL TOTAL FIXED BIN(31); TOTAL = 40 + 2; CALL DISPLAY(TOTAL); RETURN TOTAL; END MAIN;"
        output = compile_source(source, target="dotnet-il")

        self.assertIn(".assembly extern mscorlib", output)
        self.assertIn(".module PL1Program.exe", output)
        self.assertIn(".entrypoint", output)
        self.assertIn("call int32 PL1Program::MAIN()", output)
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

    def test_picture_runtime_formats_and_parses_fixed_and_float_values(self):
        runtime = PictureRuntime()

        self.assertEqual(runtime.fixed_to_picture(42, "ZZZ9"), "  42")
        self.assertEqual(runtime.float_to_picture(12.345, "Z9.99"), "12.35")
        self.assertEqual(runtime.picture_to_fixed("  42", "ZZZ9"), Decimal("42"))
        self.assertEqual(runtime.picture_to_float("12.35", "Z9.99"), 12.35)

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
