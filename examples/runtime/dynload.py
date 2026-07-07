from pl1compinpy.runtime import DynamicLoadRuntime


runtime = DynamicLoadRuntime()

java = runtime.java_class("pl1compinpy.runtime.PL1Runtime", ["pl1rt.jar"])
dotnet = runtime.dotnet_assembly("PL1CompInPy.Runtime.dll", "PL1CompInPy.Runtime.PL1Runtime")

print(java.class_name)
print(dotnet.assembly_name)
