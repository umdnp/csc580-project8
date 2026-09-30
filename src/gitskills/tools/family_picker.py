"""Interactive family picker for GitSkills analyze_family."""

from __future__ import annotations

import os
import random
import subprocess
import sys
from pathlib import Path

import duckdb


DB_ENV_VAR = "GITSKILLS_DB"
TOOLS_PACKAGE = "gitskills.tools"
REPORT_OUTPUT = "apps/skilltrace/reports"
RANDOM_FAMILY_COUNT = 10


def get_database_path() -> Path:
    """Return the GitSkills database path from the environment."""

    value = os.getenv(DB_ENV_VAR)

    if not value:
        raise RuntimeError(
            f"{DB_ENV_VAR} is not set. "
            f"Set it to the GitSkills DuckDB database before running this tool."
        )

    path = Path(value)

    if not path.exists():
        raise RuntimeError(f"Database not found: {path}")

    return path


def load_family_counts(database: Path) -> dict[str, int]:
    """Load candidate-family names and artifact counts."""

    connection = duckdb.connect(str(database), read_only=True)

    try:
        rows = connection.execute(
            """
            SELECT
                name,
                COUNT(*) AS artifact_count
            FROM artifact_groupings
            WHERE name IS NOT NULL
              AND trim(name) <> ''
            GROUP BY name
            ORDER BY lower(name), name
            """
        ).fetchall()
    finally:
        connection.close()

    return {
        name: artifact_count
        for name, artifact_count in rows
    }


def resolve_family_name(
    entered_name: str,
    family_counts: dict[str, int],
) -> str | None:
    """Resolve a family name case-insensitively."""

    normalized = entered_name.strip().lower()

    for family in family_counts:
        if family.lower() == normalized:
            return family

    return None


def choose_random_families(
    family_counts: dict[str, int],
) -> list[str]:
    """Return up to RANDOM_FAMILY_COUNT randomly selected family names."""

    names = list(family_counts)

    count = min(RANDOM_FAMILY_COUNT, len(names))

    return random.sample(names, count)


def run_analyze_family(family: str) -> None:
    """Run analyze_family for the selected candidate family."""

    print()
    print("=" * 72)
    print(f"Analyzing family: {family}")
    print("=" * 72)
    print()

    command = [
        sys.executable,
        "-m",
        f"{TOOLS_PACKAGE}.analyze_family",
        family,
        "--output",
        "apps/skilltrace/reports",
    ]

    result = subprocess.run(command, check=False)

    print()

    if result.returncode == 0:
        print(f"Analysis complete: {family}")
    else:
        print(
            f"analyze_family exited with status "
            f"{result.returncode}: {family}"
        )

    print()


def family_picker(family_counts: dict[str, int]) -> None:
    """Repeatedly show random families and allow manual selection."""

    while True:
        random_families = choose_random_families(family_counts)

        print("=" * 72)
        print("GitSkills Family Analyzer")
        print("=" * 72)
        print()
        print(
            f"Candidate families available: "
            f"{len(family_counts):,}"
        )
        print()
        print("Random candidate families:")
        print()

        for index, family in enumerate(random_families, start=1):
            artifact_count = family_counts[family]

            artifact_label = (
                "artifact"
                if artifact_count == 1
                else "artifacts"
            )

            print(
                f"  [{index:2}] "
                f"{family} "
                f"({artifact_count:,} {artifact_label})"
            )

        print()
        print("  [R] Refresh random families")
        print("  [Q] Quit")
        print()
        print(
            "Enter a number above, or type an exact family name."
        )
        print()

        choice = input("Selection: ").strip()

        if not choice:
            continue

        if choice.lower() == "q":
            return

        if choice.lower() == "r":
            print()
            continue

        if choice.isdigit():
            selection = int(choice)

            if 1 <= selection <= len(random_families):
                family = random_families[selection - 1]
                run_analyze_family(family)
                continue

            print()
            print(f"Invalid selection: {choice}")
            print()
            continue

        family = resolve_family_name(
            choice,
            family_counts,
        )

        if family is None:
            print()
            print(f"Candidate family not found: {choice}")
            print()
            continue

        run_analyze_family(family)


def main() -> int:
    """Run the interactive family-analysis picker."""

    try:
        database = get_database_path()
        family_counts = load_family_counts(database)

        if not family_counts:
            print("No candidate families found in artifact_groupings.")
            return 1

        family_picker(family_counts)

    except KeyboardInterrupt:
        print()
        print()
        print("Exiting GitSkills Family Analyzer.")
        return 0

    except (OSError, RuntimeError, duckdb.Error) as exc:
        print(
            f"Unable to start family analyzer: {exc}",
            file=sys.stderr,
        )
        return 1

    print()
    print("Exiting GitSkills Family Analyzer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())