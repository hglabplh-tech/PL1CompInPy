from pl1compinpy.runtime import CalculationBuiltinRuntime, DecimalRuntime, PackedDecimalCodec, StringRuntime, ZonedDecimalCodec


decimal_value = DecimalRuntime.fixed_decimal("-123.45", precision=5, scale=2)
packed = PackedDecimalCodec.encode(decimal_value)
zoned = ZonedDecimalCodec.encode(decimal_value)

print(decimal_value.string())
print(packed.hex())
print(zoned)

strings = StringRuntime()
name = strings.allocate("PL1COMP")
builtins = CalculationBuiltinRuntime()

print(strings.length(name))
print(strings.substr(name, 1, 3).text())
print(builtins.INDEX(name, "COMP"))
