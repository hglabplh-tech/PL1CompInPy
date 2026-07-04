from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ApiItem:
    kind: str
    name: str
    signature: str
    description: str
    line: int
    children: tuple["ApiItem", ...] = ()


@dataclass(frozen=True)
class ModuleDocs:
    module: str
    path: Path
    description: str
    classes: tuple[ApiItem, ...] = ()
    functions: tuple[ApiItem, ...] = ()


@dataclass(frozen=True)
class ApiDocs:
    modules: tuple[ModuleDocs, ...] = field(default_factory=tuple)

    @property
    def class_count(self) -> int:
        return sum(len(module.classes) for module in self.modules)

    @property
    def function_count(self) -> int:
        module_functions = sum(len(module.functions) for module in self.modules)
        methods = sum(len(api_class.children) for module in self.modules for api_class in module.classes)
        return module_functions + methods


def collect_api_docs(source_root: Path) -> ApiDocs:
    modules: list[ModuleDocs] = []
    for path in sorted(source_root.rglob("*.py")):
        module = _module_name(source_root, path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        description = ast.get_docstring(tree) or _generated_module_description(module)
        classes: list[ApiItem] = []
        functions: list[ApiItem] = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes.append(_class_item(node, module))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(_function_item(node, module, None))
        modules.append(ModuleDocs(module, path, description, tuple(classes), tuple(functions)))
    return ApiDocs(tuple(modules))


def render_markdown(docs: ApiDocs, source_root: Path) -> str:
    lines = [
        "# PL1CompInPy API Reference",
        "",
        "This file is generated from the Python source tree. Regenerate it with `python scripts/generate_api_docs.py`.",
        "",
        "## Summary",
        "",
        f"- Modules: {len(docs.modules)}",
        f"- Classes: {docs.class_count}",
        f"- Functions and methods: {docs.function_count}",
        "",
    ]
    for module in docs.modules:
        relative = module.path.relative_to(source_root.parent)
        lines.extend([f"## `{module.module}`", "", f"Source: `{relative}`", "", module.description.strip(), ""])
        if module.classes:
            lines.extend(["### Classes", ""])
            for api_class in module.classes:
                lines.extend(_render_item(api_class, level=4))
                if api_class.children:
                    lines.extend(["Methods:", ""])
                    for child in api_class.children:
                        lines.extend(_render_item(child, level=5))
        if module.functions:
            lines.extend(["### Functions", ""])
            for function in module.functions:
                lines.extend(_render_item(function, level=4))
    return "\n".join(lines).rstrip() + "\n"


def write_api_docs(source_root: Path, output: Path) -> ApiDocs:
    docs = collect_api_docs(source_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(docs, source_root), encoding="utf-8")
    return docs


def _class_item(node: ast.ClassDef, module: str) -> ApiItem:
    methods = tuple(
        _function_item(child, module, node.name)
        for child in node.body
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    signature = _class_signature(node)
    return ApiItem(
        "class",
        node.name,
        signature,
        ast.get_docstring(node) or _generated_class_description(node),
        node.lineno,
        methods,
    )


def _function_item(node: ast.FunctionDef | ast.AsyncFunctionDef, module: str, class_name: str | None) -> ApiItem:
    name = node.name if class_name is None else f"{class_name}.{node.name}"
    return ApiItem(
        "method" if class_name else "function",
        name,
        _function_signature(node),
        ast.get_docstring(node) or _generated_function_description(node.name, module, class_name),
        node.lineno,
    )


def _class_signature(node: ast.ClassDef) -> str:
    bases = [ast.unparse(base) for base in node.bases]
    return f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}"


def _function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    args = _arguments_signature(node.args)
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"{prefix} {node.name}({args}){returns}"


def _arguments_signature(args: ast.arguments) -> str:
    parts: list[str] = []
    positional = list(args.posonlyargs) + list(args.args)
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    for index, (argument, default) in enumerate(zip(positional, defaults)):
        if index == len(args.posonlyargs) and args.posonlyargs:
            parts.append("/")
        parts.append(_argument_text(argument, default))
    if args.vararg:
        parts.append("*" + _annotation(args.vararg))
    elif args.kwonlyargs:
        parts.append("*")
    for argument, default in zip(args.kwonlyargs, args.kw_defaults):
        parts.append(_argument_text(argument, default))
    if args.kwarg:
        parts.append("**" + _annotation(args.kwarg))
    return ", ".join(parts)


def _argument_text(argument: ast.arg, default: ast.expr | None) -> str:
    text = _annotation(argument)
    if default is not None:
        text += f" = {ast.unparse(default)}"
    return text


def _annotation(argument: ast.arg) -> str:
    return f"{argument.arg}: {ast.unparse(argument.annotation)}" if argument.annotation else argument.arg


def _render_item(item: ApiItem, level: int) -> list[str]:
    heading = "#" * level
    return [
        f"{heading} `{item.name}`",
        "",
        f"```python\n{item.signature}\n```",
        "",
        item.description.strip(),
        "",
        f"Defined at line {item.line}.",
        "",
    ]


def _module_name(source_root: Path, path: Path) -> str:
    relative = path.relative_to(source_root).with_suffix("")
    parts = [source_root.name] + list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _generated_module_description(module: str) -> str:
    name = module.split(".")[-1].strip("_") or "package entry point"
    return f"Module containing {name.replace('_', ' ')} support for the PL/I compiler."


def _generated_class_description(node: ast.ClassDef) -> str:
    words = _words(node.name)
    if node.name.endswith("Error"):
        return f"Exception type raised for {' '.join(words[:-1]) or 'compiler'} errors."
    if _has_decorator(node, "dataclass"):
        return f"Data container describing {' '.join(words)} values used by the compiler."
    return f"Class implementing {' '.join(words)} behavior in the PL/I compiler."


def _generated_function_description(name: str, module: str, class_name: str | None) -> str:
    readable = " ".join(_words(name))
    owner = f"`{class_name}`" if class_name else f"`{module}`"
    if name == "__init__":
        return f"Initializes an instance of {owner}."
    if name.startswith("_"):
        return f"Internal helper in {owner} for {readable.lstrip('_')}."
    if name.startswith("emit_"):
        return f"Emits {readable.removeprefix('emit ')} output for the compiler."
    if name.startswith("compile_"):
        return f"Compiles PL/I input into {readable.removeprefix('compile ')} output."
    if name.startswith("parse"):
        return "Parses lexer tokens into the compiler's AST representation."
    if name.startswith("tokenize"):
        return "Tokenizes PL/I source text for the parser."
    return f"Performs {readable} behavior in {owner}."


def _words(name: str) -> list[str]:
    cleaned = name.strip("_").replace("_", " ")
    words: list[str] = []
    current = ""
    for char in cleaned:
        if char.isupper() and current and not current[-1].isupper():
            words.append(current.lower())
            current = char
        else:
            current += char
    if current:
        words.append(current.lower())
    return " ".join(words).split()


def _has_decorator(node: ast.ClassDef, name: str) -> bool:
    return any(ast.unparse(decorator).split("(")[0].endswith(name) for decorator in node.decorator_list)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the PL1CompInPy API reference.")
    parser.add_argument("--source", type=Path, default=Path("src/pl1compinpy"))
    parser.add_argument("--output", type=Path, default=Path("docs/API.md"))
    args = parser.parse_args()
    docs = write_api_docs(args.source, args.output)
    print(f"Wrote {args.output} with {docs.class_count} classes and {docs.function_count} functions/methods.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
