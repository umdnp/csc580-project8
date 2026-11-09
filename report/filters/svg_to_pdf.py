"""Convert a report SVG to a vector PDF for XeLaTeX; do not alter the SVG.

Usage: python report/filters/svg_to_pdf.py input.svg output.pdf

Generated PDFs belong in .cache/, not in Git. Install an SVG renderer once
with `uv add --dev svglib` if neither CairoSVG nor Inkscape is available.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def convert_svg(source: Path, target: Path) -> None:
    # CairoSVG preserves SVG paths, text, and arrows when its native Cairo
    # dependency is available. On Windows that library may not be installed.
    failures: list[str] = []
    try:
        import cairosvg
        cairosvg.svg2pdf(url=str(source), write_to=str(target))
        return
    except (ImportError, OSError) as exc:
        failures.append(f"CairoSVG unavailable: {exc}")

    # Use the SVG-native Inkscape export if available locally.
    inkscape = shutil.which("inkscape")
    if inkscape:
        result = subprocess.run(
            [inkscape, str(source), "--export-type=pdf", f"--export-filename={target}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if result.returncode == 0 and target.exists():
            return
        failures.append(f"Inkscape export failed: {result.stderr.strip()}")

    # Pure-Python fallback with Windows wheels for ReportLab.
    try:
        from reportlab.graphics import renderPDF
        from svglib.svglib import svg2rlg
    except ImportError as exc:
        failures.append(f"svglib unavailable: {exc}")
    else:
        drawing = svg2rlg(str(source))
        if drawing is not None:
            renderPDF.drawToFile(drawing, str(target))
            return
        failures.append("svglib could not parse the SVG")

    raise RuntimeError(
        "No usable SVG-to-PDF converter is installed. "
        "On Windows, run `uv add --dev svglib` once, then rebuild. "
        "Alternatively install Inkscape or CairoSVG with its native libraries.\n"
        + "\n".join(failures)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    args.target.parent.mkdir(parents=True, exist_ok=True)
    convert_svg(args.source, args.target)
    if not args.target.is_file() or not args.target.read_bytes().startswith(b"%PDF-"):
        raise RuntimeError(f"SVG conversion did not generate a valid PDF: {args.target}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
