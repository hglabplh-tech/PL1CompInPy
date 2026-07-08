from pl1compinpy.frontend import Lexer, Parser, operator_precedence_table
from pl1compinpy.runtime import TYPE_MAPPINGS, PliTypeParser, build_symbol_table


source = """
DCL P POINTER;
DCL 1 REC BASED(P),
      2 ID FIXED BIN(31),
      2 NAME CHAR(80) VARYING;
MAIN: PROC OPTIONS(MAIN);
   DCL TOTAL FIXED DECIMAL(31,2);
END MAIN;
"""
program = Parser(Lexer(source).tokenize()).parse()
symbols = build_symbol_table(program)
type_parser = PliTypeParser()

print(type_parser.parse("FIXED DECIMAL(31,2)").canonical())
print(TYPE_MAPPINGS["FIXED DECIMAL"].python)
print([info.symbol for info in operator_precedence_table() if info.category == "logical-or"])
for record in symbols.debugger_records():
    print(record["scope"], record["kind"], record["name"], record["type"])
