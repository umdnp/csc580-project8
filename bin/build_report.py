"""Build the report using installed Pandoc or the project's portable copy."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("html", "docx", "pdf", "latex"), default="html")
    parser.add_argument("--cached-only", action="store_true", help="Require cached diagram images without invoking Java.")
    args = parser.parse_args()
    portable = ROOT / ".cache/report-tools/pandoc.exe"
    executable = os.environ.get("PANDOC_BIN") or shutil.which("pandoc")
    if not executable and portable.is_file():
        executable = str(portable)
    if not executable:
        parser.error("Pandoc 3.11+ is required. See report/README.md for installed and portable setup.")
    command = [executable, "--defaults", "report/pandoc.yaml"]
    suffix = "tex" if args.format == "latex" else args.format
    destination = ROOT / "report/generated-report" / f"final.{suffix}"
    if args.format == "pdf":
        if not shutil.which("xelatex"):
            parser.error("PDF builds require XeLaTeX (MiKTeX or TeX Live). HTML, Word, and LaTeX source builds do not.")
        command.append("--pdf-engine=xelatex")
        destination = ROOT / "report/final.pdf"
    destination.parent.mkdir(parents=True, exist_ok=True)
    command.extend(["-o", str(destination)])
    environment = os.environ.copy()
    java = ROOT / ".cache/report-tools/java/bin/java.exe"
    if java.is_file():
        environment.setdefault("PLANTUML_JAVA", str(java))
    environment.setdefault("PLANTUML_JAR", str(ROOT / ".cache/report-tools/plantuml.jar"))
    if args.cached_only:
        environment["PLANTUML_CACHED_ONLY"] = "1"
    result = subprocess.run(command, cwd=ROOT, env=environment, check=False)
    if result.returncode == 0:
        print(f"Built {destination}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
