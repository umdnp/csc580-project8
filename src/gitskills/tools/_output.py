"""Shared helpers for writing tool JSON output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("output")


class OutputError(RuntimeError):
    """Raised when a tool cannot prepare or write its output."""


def add_output_argument(parser: argparse.ArgumentParser) -> None:
    """Add the shared optional output-directory argument to a parser."""

    parser.add_argument(
        "--output",
        nargs="?",
        const=DEFAULT_OUTPUT_DIR,
        type=Path,
        metavar="DIR",
        help=(
            "Write JSON output to DIR. If DIR is omitted, use ./output. "
            "Existing directories are reused."
        ),
    )


def prepare_output_directory(output: Path | None) -> Path | None:
    """Create and validate the requested output directory."""

    if output is None:
        return None

    if output.exists():
        if not output.is_dir():
            raise OutputError(
                f"Output path exists and is not a directory: {output}"
            )
        return output

    try:
        output.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OutputError(
            f"Unable to create output directory '{output}': {exc}"
        ) from exc

    return output


def write_json_output(
    output_dir: Path,
    file_stem: str,
    payload: Any,
) -> Path:
    """Write a JSON payload to <output_dir>/<file_stem>.json."""

    output_path = output_dir / f"{file_stem}.json"
    try:
        output_path.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise OutputError(
            f"Unable to write JSON output '{output_path}': {exc}"
        ) from exc

    return output_path


def scan_diff_file_stem(derived: Path) -> str:
    """Derive the scan_diff output file stem from the derived artifact path."""

    if derived.name.lower() == "skill.md":
        # Resolve without requiring the path to exist so a relative SKILL.md
        # still maps to the actual containing directory name.
        stem = derived.resolve(strict=False).parent.name
    else:
        stem = derived.stem

    if not stem:
        raise OutputError(
            f"Unable to derive an output file name from: {derived}"
        )

    return stem
