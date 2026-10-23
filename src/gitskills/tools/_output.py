"""Shared helpers for tool JSON output."""

from __future__ import annotations

import argparse
import json
import hashlib
import re
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("output")
_WINDOWS_RESERVED = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    | {f"COM{number}" for number in range(1, 10)}
    | {f"LPT{number}" for number in range(1, 10)}
)
_SAFE_STEM = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,119}\Z")


def report_stem(name: str, *, force_suffix: bool = False) -> str:
    """Make a stable Windows-safe output stem without changing the source name."""

    if not name:
        raise OutputError("Cannot create a report for an empty name")
    safe = (bool(_SAFE_STEM.fullmatch(name)) and not name.endswith((".", " "))
            and name.split(".", 1)[0].upper() not in _WINDOWS_RESERVED)
    if safe and not force_suffix:
        return name
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._-")[:90].rstrip("._-")
    if not slug or slug.split(".", 1)[0].upper() in _WINDOWS_RESERVED:
        slug = "family"
    suffix = hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]
    return f"{slug}-{suffix}"


def report_stems(names: list[str]) -> dict[str, str]:
    """Resolve Windows case-insensitive collisions in a family cohort."""

    stems = {name: report_stem(name) for name in names}
    from collections import Counter
    counts = Counter(stem.casefold() for stem in stems.values())
    for name, stem in tuple(stems.items()):
        if counts[stem.casefold()] > 1:
            stems[name] = report_stem(name, force_suffix=True)
    if len({stem.casefold() for stem in stems.values()}) != len(stems):
        raise OutputError("Family names could not be mapped to unique output filenames")
    return stems


class OutputError(RuntimeError):
    """Raised when output cannot be prepared or written."""


def add_argument(parser: argparse.ArgumentParser) -> None:
    """Add the optional output-directory argument."""

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


def prepare_directory(output: Path | None) -> Path | None:
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


def write_json(
    output_dir: Path,
    file_stem: str,
    payload: Any,
) -> Path:
    """Write a JSON payload to <output_dir>/<file_stem>.json."""

    output_path = output_dir / f"{report_stem(file_stem)}.json"

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
