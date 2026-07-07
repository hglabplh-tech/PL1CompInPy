from pathlib import Path

from pl1compinpy.compiler import compile_library


ROOT = Path(__file__).resolve().parents[1]
main_source = (ROOT / "language" / "multi_source_main.pl1").read_text(encoding="utf-8")
helper_source = (ROOT / "language" / "module_helper.pl1").read_text(encoding="utf-8")
source = main_source + "\n" + helper_source

static_archive = compile_library("static-ar", source, module_name="multi_source")
shared_elf = compile_library("shared-elf64", source, module_name="multi_source")

print(static_archive[:8])
print(shared_elf[:4])
