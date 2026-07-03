from __future__ import annotations

from dataclasses import dataclass
from importlib import resources


class BuiltinError(ValueError):
    pass


@dataclass(frozen=True)
class BuiltinLibrary:
    package: str = "pl1compinpy.builtins.pl1"

    def source(self, name: str) -> str:
        normalized = name.lower()
        if normalized != "substr":
            raise BuiltinError(f"Unknown builtin: {name}")
        return resources.files(self.package).joinpath(f"{normalized}.pl1").read_text(encoding="utf-8")

    def include(self, names: list[str]) -> str:
        return "\n".join(self.source(name) for name in names)


def include_builtins(source: str, names: list[str] | None = None) -> str:
    requested = names or []
    if not requested:
        return source
    return BuiltinLibrary().include(requested) + "\n" + source

