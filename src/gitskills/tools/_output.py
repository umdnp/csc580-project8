"""Command-line options for report output (file handling is shared)."""

from __future__ import annotations

import argparse
from pathlib import Path

from gitskills.reporting.files import (
    DEFAULT_OUTPUT_DIR, OutputError, prepare_directory,
    report_stems, write_json,
)


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
