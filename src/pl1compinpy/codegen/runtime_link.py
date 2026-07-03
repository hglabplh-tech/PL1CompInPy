from __future__ import annotations

from dataclasses import dataclass, field
import json

from ..core.ast import Call, DoGroup, IfStatement, LabelledStatement, Procedure, Program, SelectStatement, Statement


@dataclass(frozen=True)
class RuntimeLinkage:
    target: str
    runtime_kind: str
    startup_symbol: str
    shutdown_symbol: str
    static_objects: tuple[str, ...] = ()
    static_libraries: tuple[str, ...] = ()
    import_libraries: tuple[str, ...] = ()
    dynamic_libraries: tuple[str, ...] = ()
    managed_references: tuple[str, ...] = ()
    managed_type: str | None = None
    c_runtime: str | None = None
    notes: tuple[str, ...] = ()

    def symbol(self, name: str, prefix: str = "") -> str:
        if self.runtime_kind == "native":
            return f"{prefix}{name}"
        return name


@dataclass(frozen=True)
class RuntimeLinkManifest:
    linkage: RuntimeLinkage
    used_runtime_calls: tuple[str, ...] = field(default_factory=tuple)

    def to_bytes(self) -> bytes:
        payload = {
            "target": self.linkage.target,
            "runtime_kind": self.linkage.runtime_kind,
            "startup_symbol": self.linkage.startup_symbol,
            "shutdown_symbol": self.linkage.shutdown_symbol,
            "static_objects": self.linkage.static_objects,
            "static_libraries": self.linkage.static_libraries,
            "import_libraries": self.linkage.import_libraries,
            "dynamic_libraries": self.linkage.dynamic_libraries,
            "managed_references": self.linkage.managed_references,
            "managed_type": self.linkage.managed_type,
            "c_runtime": self.linkage.c_runtime,
            "used_runtime_calls": self.used_runtime_calls,
        }
        return b"PL1RTLINK\0" + json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\0"


NATIVE_RUNTIME_LINKAGES: dict[str, RuntimeLinkage] = {
    "pe32-x586-windows": RuntimeLinkage(
        "pe32-x586-windows",
        "native",
        "pl1rt_init",
        "pl1rt_shutdown",
        static_objects=("pl1rt_x586_windows.obj",),
        static_libraries=("pl1rt_x586_windows.lib", "LIBCMT.lib"),
        import_libraries=("pl1rt.lib", "MSVCRT.lib"),
        dynamic_libraries=("pl1rt.dll", "ucrtbase.dll"),
        c_runtime="MSVC /MT static or /MD DLL CRT",
        notes=("All modules should use the same CRT linkage option.",),
    ),
    "pe64-x86_64-windows": RuntimeLinkage(
        "pe64-x86_64-windows",
        "native",
        "pl1rt_init",
        "pl1rt_shutdown",
        static_objects=("pl1rt_x86_64_windows.obj",),
        static_libraries=("pl1rt_x86_64_windows.lib", "LIBCMT.lib"),
        import_libraries=("pl1rt.lib", "MSVCRT.lib"),
        dynamic_libraries=("pl1rt.dll", "ucrtbase.dll"),
        c_runtime="MSVC /MT static or /MD DLL CRT",
        notes=("All modules should use the same CRT linkage option.",),
    ),
    "pe64-arm64-windows": RuntimeLinkage(
        "pe64-arm64-windows",
        "native",
        "pl1rt_init",
        "pl1rt_shutdown",
        static_objects=("pl1rt_arm64_windows.obj",),
        static_libraries=("pl1rt_arm64_windows.lib", "LIBCMT.lib"),
        import_libraries=("pl1rt.lib", "MSVCRT.lib"),
        dynamic_libraries=("pl1rt.dll", "ucrtbase.dll"),
        c_runtime="MSVC /MT static or /MD DLL CRT",
        notes=("All modules should use the same CRT linkage option.",),
    ),
    "elf64-x86_64": RuntimeLinkage(
        "elf64-x86_64",
        "native",
        "pl1rt_init",
        "pl1rt_shutdown",
        static_objects=("pl1rt_x86_64_linux.o",),
        static_libraries=("libpl1rt_x86_64.a", "libc.a"),
        dynamic_libraries=("libpl1rt.so", "libc.so"),
        c_runtime="libc linked by the C driver or explicit -lc",
        notes=("Runtime archive should appear after PL/I object files on the link command line.",),
    ),
    "elf64-aarch64": RuntimeLinkage(
        "elf64-aarch64",
        "native",
        "pl1rt_init",
        "pl1rt_shutdown",
        static_objects=("pl1rt_aarch64_linux.o",),
        static_libraries=("libpl1rt_aarch64.a", "libc.a"),
        dynamic_libraries=("libpl1rt.so", "libc.so"),
        c_runtime="libc linked by the C driver or explicit -lc",
        notes=("Runtime archive should appear after PL/I object files on the link command line.",),
    ),
    "macho64-x86_64-macos": RuntimeLinkage(
        "macho64-x86_64-macos",
        "native",
        "pl1rt_init",
        "pl1rt_shutdown",
        static_objects=("pl1rt_x86_64_macos.o",),
        static_libraries=("libpl1rt_x86_64_macos.a", "libSystem.tbd"),
        dynamic_libraries=("libpl1rt.dylib", "libSystem.B.dylib"),
        c_runtime="Apple libSystem C runtime",
        notes=("Mach-O links through Apple's ld and dyld-compatible libraries.",),
    ),
    "macho64-arm64-macos": RuntimeLinkage(
        "macho64-arm64-macos",
        "native",
        "pl1rt_init",
        "pl1rt_shutdown",
        static_objects=("pl1rt_arm64_macos.o",),
        static_libraries=("libpl1rt_arm64_macos.a", "libSystem.tbd"),
        dynamic_libraries=("libpl1rt.dylib", "libSystem.B.dylib"),
        c_runtime="Apple libSystem C runtime",
        notes=("Mach-O links through Apple's ld and dyld-compatible libraries.",),
    ),
    "macho32-x586-macos": RuntimeLinkage(
        "macho32-x586-macos",
        "native",
        "pl1rt_init",
        "pl1rt_shutdown",
        static_objects=("pl1rt_x586_macos.o",),
        static_libraries=("libpl1rt_x586_macos.a", "libSystem.tbd"),
        dynamic_libraries=("libpl1rt.dylib", "libSystem.B.dylib"),
        c_runtime="Apple libSystem C runtime",
        notes=("This is an assembly linkage plan; modern macOS executable emission is 64-bit only.",),
    ),
}

ASSEMBLY_RUNTIME_TARGETS = {
    "x586-windows": "pe32-x586-windows",
    "x586-macos": "macho32-x586-macos",
    "x86_64-windows": "pe64-x86_64-windows",
    "arm64-macos": "macho64-arm64-macos",
    "arm64-windows": "pe64-arm64-windows",
}

JVM_RUNTIME_LINKAGE = RuntimeLinkage(
    "jvm-bytecode",
    "jvm",
    "init",
    "shutdown",
    managed_references=("pl1rt.jar",),
    managed_type="pl1compinpy/runtime/PL1Runtime",
    notes=("The runtime is resolved from the JVM classpath like any other class dependency.",),
)

DOTNET_RUNTIME_LINKAGE = RuntimeLinkage(
    "dotnet-il",
    "dotnet",
    "Init",
    "Shutdown",
    managed_references=("PL1CompInPy.Runtime.dll",),
    managed_type="PL1CompInPy.Runtime.PL1Runtime",
    notes=("The runtime is resolved as a managed assembly reference.",),
)


def runtime_linkage(target: str) -> RuntimeLinkage:
    if target == "jvm-bytecode":
        return JVM_RUNTIME_LINKAGE
    if target == "dotnet-il":
        return DOTNET_RUNTIME_LINKAGE
    native_target = ASSEMBLY_RUNTIME_TARGETS.get(target, target)
    try:
        return NATIVE_RUNTIME_LINKAGES[native_target]
    except KeyError as exc:
        raise ValueError(f"Unsupported runtime linkage target: {target}") from exc


def runtime_manifest(target: str, program: Program | None = None) -> RuntimeLinkManifest:
    return RuntimeLinkManifest(runtime_linkage(target), tuple(sorted(_runtime_calls(program))))


def encoded_runtime_manifest(target: str, program: Program | None = None) -> bytes:
    return runtime_manifest(target, program).to_bytes()


def _runtime_calls(program: Program | None) -> set[str]:
    if program is None:
        return set()
    calls: set[str] = set()
    for statement in program.statements:
        _collect_runtime_calls(statement, calls)
    return calls


def _collect_runtime_calls(statement: Statement | None, calls: set[str]) -> None:
    if statement is None:
        return
    if isinstance(statement, Call):
        calls.add(statement.name.upper())
    elif isinstance(statement, Procedure):
        for child in statement.body:
            _collect_runtime_calls(child, calls)
    elif isinstance(statement, LabelledStatement):
        _collect_runtime_calls(statement.statement, calls)
    elif isinstance(statement, DoGroup):
        for child in statement.body:
            _collect_runtime_calls(child, calls)
    elif isinstance(statement, IfStatement):
        _collect_runtime_calls(statement.then_branch, calls)
        _collect_runtime_calls(statement.else_branch, calls)
    elif isinstance(statement, SelectStatement):
        for branch in statement.when_branches:
            _collect_runtime_calls(branch.statement, calls)
        _collect_runtime_calls(statement.otherwise, calls)


__all__ = [
    "DOTNET_RUNTIME_LINKAGE",
    "JVM_RUNTIME_LINKAGE",
    "RuntimeLinkage",
    "RuntimeLinkManifest",
    "encoded_runtime_manifest",
    "runtime_linkage",
    "runtime_manifest",
]
