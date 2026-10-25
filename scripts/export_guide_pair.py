"""Export the two cometchat-core artifacts used in the project guide."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import duckdb


BASE_ID = 3498417
DERIVED_ID = 3602273
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPOSITORY_ROOT / "tests/temp"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, help="DuckDB path; defaults to GITSKILLS_DB.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Export directory (default: tests/temp under the repository root).",
    )
    args = parser.parse_args()
    configured = os.environ.get("GITSKILLS_DB")
    database = args.db or (Path(configured) if configured else None)
    if database is None or not database.is_file():
        parser.exit(1, "Set GITSKILLS_DB or pass --db pointing to the prepared DuckDB file.\n")

    try:
        with duckdb.connect(str(database), read_only=True) as connection:
            rows = connection.execute(
                "SELECT id, content FROM artifacts WHERE id IN (?, ?)",
                [BASE_ID, DERIVED_ID],
            ).fetchall()
        contents = dict(rows)
        for artifact_id in (BASE_ID, DERIVED_ID):
            if not isinstance(contents.get(artifact_id), str) or not contents[artifact_id].strip():
                parser.exit(1, f"Artifact {artifact_id} is missing or has no text content.\n")
        for label, artifact_id in (("Base", BASE_ID), ("Derived", DERIVED_ID)):
            destination = args.output / label.lower() / "cometchat-core" / "SKILL.md"
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(contents[artifact_id].encode("utf-8"))
            print(f"{label} {artifact_id}: {destination}")
    except (duckdb.Error, OSError) as exc:
        parser.exit(1, f"Unable to export example pair: {exc}\n")
    print("Exported stored text only. The database was opened read-only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
