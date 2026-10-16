"""Download checksum-pinned portable report tools for Windows x64."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import sys
import urllib.parse
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / ".cache/report-tools"


def download(spec: dict[str, str], target: Path) -> None:
    if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == spec["sha256"]:
        return
    request = urllib.request.Request(spec["url"], headers={"User-Agent": "csc580-report-setup"})
    temporary = target.with_name(target.name + ".download")
    with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    if hashlib.sha256(temporary.read_bytes()).hexdigest() != spec["sha256"]:
        raise RuntimeError(f"Checksum mismatch for {target.name}; download was not installed.")
    temporary.replace(target)


def archive_name(spec: dict[str, str]) -> str:
    return urllib.parse.unquote(Path(urllib.parse.urlparse(spec["url"]).path).name)


def main() -> int:
    if platform.system() != "Windows" or platform.machine().lower() not in {"amd64", "x86_64"}:
        print("This portable setup targets Windows x64. On other platforms use Pandoc 3.11+, Java 21, and the pinned PlantUML JAR; see report/README.md.", file=sys.stderr)
        return 1
    specs = json.loads((ROOT / "report/toolchain.json").read_text(encoding="utf-8"))
    TOOLS.mkdir(parents=True, exist_ok=True)
    download(specs["plantuml"], TOOLS / "plantuml.jar")
    pandoc_archive = TOOLS / archive_name(specs["pandoc"])
    download(specs["pandoc"], pandoc_archive)
    with zipfile.ZipFile(pandoc_archive) as package:
        member = next(name for name in package.namelist() if name.endswith("/pandoc.exe"))
        (TOOLS / "pandoc.exe").write_bytes(package.read(member))
    java_archive = TOOLS / archive_name(specs["java"])
    download(specs["java"], java_archive)
    java_root = (TOOLS / "java").resolve()
    with zipfile.ZipFile(java_archive) as package:
        for member in package.infolist():
            relative = Path(*Path(member.filename).parts[1:])
            if not relative.parts:
                continue
            destination = (java_root / relative).resolve()
            if not destination.is_relative_to(java_root):
                raise RuntimeError(f"Invalid archive path: {member.filename}")
            if member.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(package.read(member))
    print(f"Portable tools ready in {TOOLS}; no system installation or PATH changes.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile) as exc:
        print(f"Report setup failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
