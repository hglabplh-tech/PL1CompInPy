from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


class IncludeError(ValueError):
    pass


@dataclass
class IncludeExpander:
    include_dirs: list[Path] = field(default_factory=list)
    suffixes: tuple[str, ...] = ("", ".pl1", ".pli", ".inc")
    included_once: set[Path] = field(default_factory=set)
    strict: bool = False

    def expand(self, source: str, *, base_dir: Path | None = None) -> str:
        base = base_dir or Path.cwd()
        return self._expand_source(source, base.resolve(), stack=[])

    def expand_file(self, path: Path) -> str:
        resolved = path.resolve()
        return self._expand_source(resolved.read_text(encoding="utf-8"), resolved.parent, [resolved])

    def _expand_source(self, source: str, base_dir: Path, stack: list[Path]) -> str:
        lines: list[str] = []
        for line in source.splitlines():
            directive = self._include_directive(line)
            if directive is None:
                lines.append(line)
                continue
            command, member = directive
            include_path = self._resolve_member(member, base_dir)
            if include_path is None:
                lines.append(line)
                continue
            if command in {"XINCLUDE", "XINSCAN"} and include_path in self.included_once:
                continue
            if include_path in stack:
                chain = " -> ".join(str(path) for path in stack + [include_path])
                raise IncludeError(f"Recursive include detected: {chain}")
            self.included_once.add(include_path)
            nested = include_path.read_text(encoding="utf-8")
            lines.append(self._expand_source(nested, include_path.parent, stack + [include_path]))
        return "\n".join(lines) + ("\n" if source.endswith("\n") or lines else "")

    def _include_directive(self, line: str) -> tuple[str, str] | None:
        match = re.match(r"^\s*%\s*(INCLUDE|XINCLUDE|INSCAN|XINSCAN)\s+(.+?)\s*;\s*(?:/\*.*\*/\s*)?$", line, re.IGNORECASE)
        if not match:
            return None
        command = match.group(1).upper()
        member = match.group(2).strip()
        if (member.startswith("'") and member.endswith("'")) or (member.startswith('"') and member.endswith('"')):
            member = member[1:-1]
        elif member.startswith("(") and member.endswith(")"):
            member = member[1:-1].strip()
        if not member:
            raise IncludeError(f"Empty %{command} member name")
        return command, member

    def _resolve_member(self, member: str, base_dir: Path) -> Path | None:
        candidate = Path(member)
        search_dirs = [base_dir] + [path.resolve() for path in self.include_dirs]
        if candidate.is_absolute():
            search_dirs = [Path("/")]
        for directory in search_dirs:
            for suffix in self.suffixes:
                path = candidate if candidate.is_absolute() else directory / (member + suffix)
                if path.exists() and path.is_file():
                    return path.resolve()
        if self.strict:
            raise IncludeError(f"Could not resolve include member: {member}")
        return None


def expand_includes(source: str, include_dirs: list[str | Path] | None = None, *, base_dir: str | Path | None = None) -> str:
    expander = IncludeExpander([Path(path) for path in include_dirs or []])
    return expander.expand(source, base_dir=Path(base_dir) if base_dir is not None else None)


def expand_include_file(path: str | Path, include_dirs: list[str | Path] | None = None) -> str:
    expander = IncludeExpander([Path(directory) for directory in include_dirs or []], strict=True)
    return expander.expand_file(Path(path))


__all__ = ["IncludeError", "IncludeExpander", "expand_include_file", "expand_includes"]
