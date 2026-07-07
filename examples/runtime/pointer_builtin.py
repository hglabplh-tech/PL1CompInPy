from pl1compinpy.runtime import PointerBuiltinRuntime, PointerValue


runtime = PointerBuiltinRuntime()

null_pointer = runtime.POINTER()
heap_pointer = runtime.POINTER(42)
field_pointer = runtime.POINTER(heap_pointer, 8)
explicit_offset = runtime.POINTER(4096, 16)

print(null_pointer)
print(heap_pointer)
print(field_pointer)
print(explicit_offset)
print(field_pointer == PointerValue(42, 8))
