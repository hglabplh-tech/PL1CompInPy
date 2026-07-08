from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
import re

from .include import IncludeExpander


PP_BUILTIN_NAMES = (
    "COLLATE",
    "COMMENT",
    "COMPILEDATE",
    "COMPILETIME",
    "COPY",
    "COUNTER",
    "INDEX",
    "LENGTH",
    "LOWERCASE",
    "MAX",
    "MIN",
    "PARMSET",
    "QUOTE",
    "REPEAT",
    "SUBSTR",
    "SYSPARM",
    "SYSTEM",
    "SYSVERSION",
    "TRANSLATE",
    "TRIM",
    "UPPERCASE",
    "VERIFY",
)

PP_DIRECTIVE_NAMES = (
    "ACTIVATE",
    "ANSWER",
    "DECLARE",
    "DCL",
    "DEACTIVATE",
    "DO",
    "END",
    "ELSE",
    "GO",
    "GOTO",
    "IF",
    "INCLUDE",
    "XINCLUDE",
    "INSCAN",
    "XINSCAN",
    "ITERATE",
    "LEAVE",
    "NOTE",
    "OTHERWISE",
    "PROCEDURE",
    "PROC",
    "REPLACE",
    "RETURN",
    "SELECT",
    "WHEN",
    "PRINT",
    "NOPRINT",
    "PAGE",
    "SKIP",
    "PUSH",
    "POP",
    "PROCESS",
    "OPTIONS",
)


class PreprocessorError(ValueError):
    pass


@dataclass
class CompileTimeSymbol:
    name: str
    datatype: str = "CHARACTER"
    value: Any = ""
    active: bool = False
    builtin: bool = False


@dataclass
class PreprocessorState:
    symbols: dict[str, CompileTimeSymbol] = field(default_factory=dict)
    replace_table: dict[str, str] = field(default_factory=dict)
    directive_table: dict[str, str] = field(default_factory=dict)
    builtin_table: dict[str, Callable[..., Any]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    sysp_arm: str = ""
    counter: int = 0

    def ensure_symbol(self, name: str, datatype: str = "CHARACTER") -> CompileTimeSymbol:
        key = name.upper()
        if key not in self.symbols:
            self.symbols[key] = CompileTimeSymbol(key, datatype)
        return self.symbols[key]


@dataclass
class _ConditionalFrame:
    parent_active: bool
    condition_true: bool
    active: bool


class IBMStylePreprocessor:
    """Small IBM PL/I-style compile-time layer used before lexing.

    The class intentionally keeps macro procedures hook-oriented, but it evaluates
    the common source-shaping directives that fit PL1CompInPy today: include
    expansion, compile-time declarations and assignments, activation flags,
    replacements, notes, and simple conditional blocks.
    """

    def __init__(
        self,
        include_dirs: list[str | Path] | None = None,
        *,
        strict: bool = False,
        sysp_arm: str = "",
        suffixes: tuple[str, ...] = ("", ".pl1", ".pli", ".inc"),
    ) -> None:
        self.state = PreprocessorState(sysp_arm=sysp_arm)
        self.include_expander = IncludeExpander([Path(path) for path in include_dirs or []], suffixes=suffixes, strict=strict)
        for directive in PP_DIRECTIVE_NAMES:
            self.state.directive_table[directive] = directive
        self._init_builtins()

    def preprocess(self, source: str, *, base_dir: str | Path | None = None) -> str:
        expanded = self.include_expander.expand(source, base_dir=Path(base_dir) if base_dir is not None else None)
        return self._process_lines(expanded.splitlines(keepends=True))

    def preprocess_file(self, path: str | Path) -> str:
        resolved = Path(path).resolve()
        expanded = self.include_expander.expand_file(resolved)
        return self._process_lines(expanded.splitlines(keepends=True))

    def compile_time_tables(self) -> dict[str, Any]:
        return {
            "directives": sorted(self.state.directive_table),
            "builtins": sorted(self.state.builtin_table),
            "symbols": {name: symbol.__dict__.copy() for name, symbol in self.state.symbols.items()},
            "replace_table": self.state.replace_table.copy(),
            "notes": list(self.state.notes),
        }

    def register_builtin(self, name: str, handler: Callable[..., Any]) -> None:
        key = name.upper()
        self.state.builtin_table[key] = handler
        symbol = self.state.ensure_symbol(key, "BUILTIN")
        symbol.active = True
        symbol.builtin = True

    def apply_source_replacements(self, text: str) -> str:
        return rewrite_identifiers_outside_literals(text, self.state.replace_table)

    def _init_builtins(self) -> None:
        builtins: dict[str, Callable[..., Any]] = {
            "COLLATE": lambda: "".join(chr(i) for i in range(256)),
            "COMMENT": lambda x: "/* " + str(x).replace("*/", "* /") + " */",
            "COMPILEDATE": lambda: datetime.now().strftime("%d %b %Y").upper(),
            "COMPILETIME": lambda: datetime.now().strftime("%H:%M:%S"),
            "COPY": lambda x, y: str(x) * int(y),
            "COUNTER": self._counter,
            "INDEX": lambda x, y, z=1: str(x).find(str(y), max(int(z) - 1, 0)) + 1,
            "LENGTH": lambda x: len(str(x)),
            "LOWERCASE": lambda x: str(x).lower(),
            "MAX": lambda *xs: max(xs),
            "MIN": lambda *xs: min(xs),
            "PARMSET": lambda x: str(x).upper() in self.state.sysp_arm.upper().split(),
            "QUOTE": lambda x: "'" + str(x).replace("'", "''") + "'",
            "REPEAT": lambda x, y: str(x) * int(y),
            "SUBSTR": lambda x, y, z=None: str(x)[int(y) - 1:] if z is None else str(x)[int(y) - 1:int(y) - 1 + int(z)],
            "SYSPARM": lambda: self.state.sysp_arm,
            "SYSTEM": lambda: "PL1COMPINPY",
            "SYSVERSION": lambda: "PL1COMPINPY 0.1",
            "TRANSLATE": self._translate,
            "TRIM": lambda x, y=" ": str(x).strip(str(y)),
            "UPPERCASE": lambda x: str(x).upper(),
            "VERIFY": lambda x, y: next((idx + 1 for idx, ch in enumerate(str(x)) if ch not in str(y)), 0),
        }
        for name, handler in builtins.items():
            self.register_builtin(name, handler)

    def _process_lines(self, lines: list[str]) -> str:
        output: list[str] = []
        stack: list[_ConditionalFrame] = []
        active = True
        for line in lines:
            directive = self._directive(line)
            if directive is None:
                if active:
                    output.append(self.apply_source_replacements(line))
                continue
            command, payload = directive
            if command in {"INCLUDE", "XINCLUDE", "INSCAN", "XINSCAN"}:
                if active:
                    output.append(line)
                continue
            if command == "IF":
                condition = self._condition_payload(payload)
                result = bool(self._eval_expr(condition))
                frame = _ConditionalFrame(active, result, active and result)
                stack.append(frame)
                active = frame.active
                continue
            if command == "ELSE":
                if not stack:
                    if active:
                        output.append(line)
                    continue
                frame = stack[-1]
                frame.active = frame.parent_active and not frame.condition_true
                active = frame.active
                continue
            if command in {"DO", "SELECT"}:
                frame = _ConditionalFrame(active, True, active)
                stack.append(frame)
                active = frame.active
                continue
            if command == "END":
                if stack:
                    stack.pop()
                    active = stack[-1].active if stack else True
                    continue
                if active:
                    output.append(line)
                continue
            if not active:
                continue
            if command in {"DECLARE", "DCL"}:
                self._declare(payload)
            elif command == "ACTIVATE":
                self._activate(payload, True)
            elif command == "DEACTIVATE":
                self._activate(payload, False)
            elif command == "REPLACE":
                self._replace(payload)
            elif command == "NOTE":
                self.state.notes.append(str(self._eval_expr(payload)))
            elif command in {"PRINT", "NOPRINT", "PAGE", "SKIP", "PUSH", "POP", "PROCESS", "OPTIONS"}:
                continue
            elif self._assignment(command, payload):
                continue
            else:
                output.append(line)
        if stack:
            raise PreprocessorError("Unclosed preprocessor conditional block")
        return "".join(output)

    def _directive(self, line: str) -> tuple[str, str] | None:
        match = re.match(r"^\s*%\s*([A-Za-z_#$@][A-Za-z0-9_#$@]*)\b(.*?)\s*;\s*$", line)
        if not match:
            return None
        return match.group(1).upper(), match.group(2).strip()

    def _condition_payload(self, payload: str) -> str:
        return re.sub(r"\s*%?THEN\s*$", "", payload, flags=re.IGNORECASE).strip()

    def _declare(self, payload: str) -> None:
        cleaned = payload.strip().rstrip(";")
        for item in split_top_level_commas(cleaned):
            parts = item.split()
            if not parts:
                continue
            name = parts[0]
            datatype = " ".join(parts[1:]) or "CHARACTER"
            self.state.ensure_symbol(name, datatype)

    def _activate(self, payload: str, active: bool) -> None:
        for name in split_top_level_commas(payload):
            if name:
                self.state.ensure_symbol(name).active = active

    def _replace(self, payload: str) -> None:
        match = re.match(r"(.+?)\s+(?:BY|=)\s+(.+)$", payload, flags=re.IGNORECASE)
        if not match:
            raise PreprocessorError(f"Invalid %REPLACE payload: {payload}")
        old = match.group(1).strip()
        new = match.group(2).strip()
        if is_quoted_literal(old):
            old = unquote_pli(old)
        if is_quoted_literal(new):
            new = unquote_pli(new)
        self.state.replace_table[old.upper()] = new

    def _assignment(self, command: str, payload: str) -> bool:
        if not payload.startswith("="):
            return False
        symbol = self.state.ensure_symbol(command)
        symbol.value = self._eval_expr(payload[1:].strip())
        symbol.active = True
        return True

    def _eval_expr(self, expr: str) -> Any:
        expr = expr.strip().rstrip(";")
        if not expr:
            return ""
        if is_quoted_literal(expr):
            return unquote_pli(expr)
        if re.fullmatch(r"[+-]?\d+", expr):
            return int(expr)
        call = re.match(r"^([A-Za-z_#$@][A-Za-z0-9_#$@]*)\s*\((.*)\)$", expr)
        if call:
            name = call.group(1).upper()
            args = [self._eval_expr(arg) for arg in split_top_level_commas(call.group(2))]
            if name not in self.state.builtin_table:
                raise PreprocessorError(f"Unknown preprocessor builtin {name}")
            return self.state.builtin_table[name](*args)
        comparison = re.match(r"^(.+?)\s*(=|\^=|<>|<=|>=|<|>)\s*(.+)$", expr)
        if comparison:
            left = self._eval_expr(comparison.group(1))
            op = comparison.group(2)
            right = self._eval_expr(comparison.group(3))
            if op == "=":
                return left == right
            if op in {"^=", "<>"}:
                return left != right
            if op == "<":
                return left < right
            if op == "<=":
                return left <= right
            if op == ">":
                return left > right
            if op == ">=":
                return left >= right
        key = expr.upper()
        if key in self.state.symbols:
            value = self.state.symbols[key].value
            if isinstance(value, str) and value == "":
                return self.state.symbols[key].active
            return value
        return expr

    def _counter(self) -> int:
        self.state.counter += 1
        return self.state.counter

    def _translate(self, value: Any, to: Any, from_: Any | None = None) -> str:
        text = str(value)
        target = str(to)
        source = str(from_) if from_ is not None else "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        table = {source[i]: target[i] for i in range(min(len(source), len(target)))}
        return "".join(table.get(ch, ch) for ch in text)


def preprocess_source(
    source: str,
    include_dirs: list[str | Path] | None = None,
    *,
    base_dir: str | Path | None = None,
    strict: bool = False,
    sysp_arm: str = "",
) -> str:
    return IBMStylePreprocessor(include_dirs, strict=strict, sysp_arm=sysp_arm).preprocess(source, base_dir=base_dir)


def rewrite_identifiers_outside_literals(text: str, mapping: dict[str, str]) -> str:
    if not mapping:
        return text
    result: list[str] = []
    i = 0
    quote: str | None = None
    while i < len(text):
        ch = text[i]
        if quote:
            result.append(ch)
            if ch == quote:
                if i + 1 < len(text) and text[i + 1] == quote:
                    result.append(text[i + 1])
                    i += 2
                    continue
                quote = None
            i += 1
            continue
        if ch in {"'", '"'}:
            quote = ch
            result.append(ch)
            i += 1
            continue
        if ch.isalpha() or ch in "_#$@":
            start = i
            while i < len(text) and (text[i].isalnum() or text[i] in "_#$@"):
                i += 1
            word = text[start:i]
            result.append(mapping.get(word.upper(), word))
            continue
        result.append(ch)
        i += 1
    return "".join(result)


def split_top_level_commas(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    quote: str | None = None
    for ch in text:
        if quote:
            current.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in {"'", '"'}:
            quote = ch
            current.append(ch)
            continue
        if ch == "(":
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def is_quoted_literal(text: str) -> bool:
    stripped = text.strip()
    return len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}


def unquote_pli(text: str) -> str:
    stripped = text.strip()
    if is_quoted_literal(stripped):
        quote = stripped[0]
        return stripped[1:-1].replace(quote + quote, quote)
    return stripped


__all__ = [
    "CompileTimeSymbol",
    "IBMStylePreprocessor",
    "PP_BUILTIN_NAMES",
    "PP_DIRECTIVE_NAMES",
    "PreprocessorError",
    "PreprocessorState",
    "preprocess_source",
    "rewrite_identifiers_outside_literals",
    "split_top_level_commas",
]
