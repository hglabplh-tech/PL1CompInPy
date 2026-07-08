from pl1compinpy.frontend import Lexer, Parser
from pl1compinpy.runtime import CalculationBuiltinRuntime, CalculationEngine, ComplexRuntime, ComplexValue, PL1Type, PL1Value


builtins = CalculationBuiltinRuntime()
runtime = ComplexRuntime()
z = builtins.COMPLEX(3, 4)
expression = Parser(Lexer("RESULT = Z * Z + ONE;").tokenize()).parse().statements[0].expression
result = CalculationEngine({"Z": PL1Value(z, PL1Type.COMPLEX), "ONE": PL1Value(ComplexValue(1, 0), PL1Type.COMPLEX)}).evaluate(expression)

print(runtime.mul(z, z))
print(result.value)
print(builtins.REAL(z), builtins.IMAG(z), builtins.ABS(z))
print(builtins.CONJG(z))
print(builtins.SQRT(ComplexValue(-1, 0)))
