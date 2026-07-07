from __future__ import annotations

from dataclasses import dataclass
import ctypes
from pathlib import Path
from typing import Any


class DynamicLoadError(ValueError):
    pass


@dataclass(frozen=True)
class DynamicLibraryHandle:
    path: Path
    handle: Any


@dataclass(frozen=True)
class JavaClassLoadRequest:
    class_name: str
    classpath: tuple[str, ...] = ()


@dataclass(frozen=True)
class DotNetAssemblyLoadRequest:
    assembly_name: str
    type_name: str | None = None


class DynamicLoadRuntime:
    def dynload(self, path: str | Path) -> DynamicLibraryHandle:
        library_path = Path(path)
        try:
            return DynamicLibraryHandle(library_path, ctypes.CDLL(str(library_path)))
        except OSError as exc:
            raise DynamicLoadError(str(exc)) from exc

    def symbol(self, library: DynamicLibraryHandle, name: str) -> Any:
        try:
            return getattr(library.handle, name)
        except AttributeError as exc:
            raise DynamicLoadError(f"Symbol not found: {name}") from exc

    def java_class(self, class_name: str, classpath: list[str] | tuple[str, ...] | None = None) -> JavaClassLoadRequest:
        return JavaClassLoadRequest(class_name, tuple(classpath or ()))

    def dotnet_assembly(self, assembly_name: str, type_name: str | None = None) -> DotNetAssemblyLoadRequest:
        return DotNetAssemblyLoadRequest(assembly_name, type_name)


__all__ = [
    "DotNetAssemblyLoadRequest",
    "DynamicLibraryHandle",
    "DynamicLoadError",
    "DynamicLoadRuntime",
    "JavaClassLoadRequest",
]
