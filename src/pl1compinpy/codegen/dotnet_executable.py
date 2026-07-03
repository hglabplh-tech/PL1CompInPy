from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile

from ..core.ast import Program
from .dotnet_il import emit_dotnet_il


class DotNetExecutableError(RuntimeError):
    pass


def emit_dotnet_executable(program: Program, output: Path, ilasm: str | None = None) -> Path:
    tool = ilasm or shutil.which("ilasm") or shutil.which("ilasm.exe")
    if tool is None:
        raise DotNetExecutableError("ILAsm was not found. Install the .NET Framework SDK or run from a Visual Studio Developer shell.")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        il_path = Path(tmp) / "PL1Program.il"
        il_path.write_text(emit_dotnet_il(program), encoding="utf-8")
        try:
            result = subprocess.run(
                [tool, str(il_path), "/exe", f"/output:{output}"],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            raise DotNetExecutableError(f"ILAsm could not be started: {tool}") from exc
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise DotNetExecutableError(f"ILAsm failed with exit code {result.returncode}: {detail}")
    return output


__all__ = ["DotNetExecutableError", "emit_dotnet_executable"]
