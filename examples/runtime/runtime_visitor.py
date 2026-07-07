from pl1compinpy.frontend.lexer import Lexer
from pl1compinpy.frontend.parser import Parser
from pl1compinpy.runtime import RuntimeExecutionVisitor, normalize_calls


source = """
DCL LENGTH BUILTIN;
DCL TOTAL FIXED BIN(31);
DCL TEXT CHARACTER;

TEXT = 'VISITOR';
TOTAL = 0;

DO WHILE TOTAL < 2;
  TOTAL = TOTAL + 1;
END;

SELECT(TOTAL);
  WHEN(2) CALL DISPLAY('VISITOR CONTROL FLOW');
  OTHERWISE CALL DISPLAY('UNREACHED');
END;

CALL LENGTH(TEXT);
"""

program = normalize_calls(Parser(Lexer(source).tokenize()).parse())
visitor = RuntimeExecutionVisitor()
visitor.visit(program)

print(visitor.variables["TOTAL"].value)
print(visitor.output)
