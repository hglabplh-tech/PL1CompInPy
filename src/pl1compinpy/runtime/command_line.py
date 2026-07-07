from __future__ import annotations

from dataclasses import dataclass
import sys


@dataclass(frozen=True)
class CommandLineRuntime:
    argv: tuple[str, ...]

    @classmethod
    def from_argv(cls, argv: list[str] | tuple[str, ...] | None = None) -> "CommandLineRuntime":
        return cls(tuple(sys.argv if argv is None else argv))

    @property
    def program_name(self) -> str:
        return self.argv[0] if self.argv else ""

    @property
    def arguments(self) -> tuple[str, ...]:
        return self.argv[1:]

    def command(self) -> str:
        return " ".join(self.arguments)

    def argc(self) -> int:
        return len(self.arguments)

    def argv_value(self, index: int) -> str:
        if index == 0:
            return self.program_name
        try:
            return self.arguments[index - 1]
        except IndexError as exc:
            raise IndexError(f"Command-line argument index out of range: {index}") from exc

    def bind_main_parameters(self, parameter_names: list[str]) -> list[object]:
        if not parameter_names:
            return []
        values: list[object] = [self.command()]
        if len(parameter_names) > 1:
            values.append(self.argc())
        if len(parameter_names) > 2:
            values.append(list(self.arguments))
        while len(values) < len(parameter_names):
            values.append(None)
        return values


__all__ = ["CommandLineRuntime"]
