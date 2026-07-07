from pl1compinpy.ast import StructureField
from pl1compinpy.runtime import BasedStructureRuntime, PL1Type, PL1Value, PointerValue


record = StructureField(
    1,
    "REC",
    children=[
        StructureField(2, "ID", ["FIXED", "BIN", "31"]),
        StructureField(2, "VALUE", ["FIXED", "BIN", "31"]),
    ],
)
runtime = BasedStructureRuntime()
pointer = PointerValue(100)

runtime.declare_based_structure(record, "P")
runtime.set_field(pointer, "REC", "ID", PL1Value(7, PL1Type.FIXED_BIN))
runtime.set_field(pointer, "REC", "VALUE", PL1Value(42, PL1Type.FIXED_BIN))

print(runtime.get_field(pointer, "REC", "ID"))
print(runtime.get_field(pointer, "REC", "VALUE"))
