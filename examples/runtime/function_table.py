from pl1compinpy.frontend import Lexer, Parser
from pl1compinpy.runtime import RUNTIME_FUNCTION_TABLE, build_dynamic_function_table


source = "ADD: PROC(LEFT,RIGHT) RETURNS(FIXED); RETURN LEFT; END ADD;"
program = Parser(Lexer(source).tokenize()).parse()

dynamic_table = build_dynamic_function_table(program)
descriptor = dynamic_table.get("ADD")

print(descriptor.name, descriptor.returns)
print(RUNTIME_FUNCTION_TABLE.get("TCPIP_SEND").name)
