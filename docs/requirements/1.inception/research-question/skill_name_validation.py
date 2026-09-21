import sqlite3
import re
from pathlib import Path
from datetime import datetime

DB_PATH = Path("agent_skills_release.db")
OUTPUT_PATH = Path("skill_name_validation.md")

SAMPLE_SIZE = 500


def normalize_name(value):
    if value is None:
        return None

    value = value.strip().strip('"').strip("'")
    return value.casefold()


def extract_frontmatter_name(content):
    """
    Extract the `name:` field from YAML-style frontmatter.

    Expected general structure:

    ---
    name: writing-plans
    description: ...
    ---

    Returns:
        extracted name string, or None
    """

    if not content:
        return None

    # Normalize line endings
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    lines = content.splitlines()

    if not lines:
        return None

    # Ignore leading blank lines
    start_index = 0

    while start_index < len(lines) and not lines[start_index].strip():
        start_index += 1

    # Require YAML frontmatter opening delimiter
    if (
        start_index >= len(lines)
        or lines[start_index].strip() != "---"
    ):
        return None

    # Search only inside frontmatter
    for line in lines[start_index + 1:]:

        stripped = line.strip()

        # End of frontmatter
        if stripped == "---":
            break

        match = re.match(
            r"^\s*name\s*:\s*(.+?)\s*$",
            line,
            flags=re.IGNORECASE
        )

        if match:
            value = match.group(1).strip()

            # Remove simple inline comments when unquoted
            if (
                not value.startswith('"')
                and not value.startswith("'")
            ):
                value = value.split("#", 1)[0].strip()

            # Remove surrounding quotes
            if (
                len(value) >= 2
                and (
                    (value[0] == '"' and value[-1] == '"')
                    or
                    (value[0] == "'" and value[-1] == "'")
                )
            ):
                value = value[1:-1]

            return value.strip()

    return None


def md_escape(value):
    if value is None:
        return "N/A"

    return str(value).replace("|", "\\|")


# ---------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------

db = sqlite3.connect(DB_PATH)
db.row_factory = sqlite3.Row

print(f"Selecting random sample of {SAMPLE_SIZE} artifacts...")

rows = db.execute("""
    SELECT
        repo_full_name,
        path,
        name,
        content,
        file_sha
    FROM artifacts
    WHERE name IS NOT NULL
      AND TRIM(name) <> ''
      AND content IS NOT NULL
    ORDER BY RANDOM()
    LIMIT ?
""", (SAMPLE_SIZE,)).fetchall()

print(f"Sample selected: {len(rows)} artifacts")


# ---------------------------------------------------------------------
# Analyze
# ---------------------------------------------------------------------

results = []

match_count = 0
mismatch_count = 0
missing_frontmatter_name_count = 0

for index, row in enumerate(rows, start=1):

    db_name = row["name"]
    header_name = extract_frontmatter_name(row["content"])

    db_normalized = normalize_name(db_name)
    header_normalized = normalize_name(header_name)

    if header_name is None:
        status = "NO_HEADER_NAME"
        missing_frontmatter_name_count += 1

    elif db_normalized == header_normalized:
        status = "MATCH"
        match_count += 1

    else:
        status = "MISMATCH"
        mismatch_count += 1

    results.append({
        "repo": row["repo_full_name"],
        "path": row["path"],
        "sha": row["file_sha"],
        "db_name": db_name,
        "header_name": header_name,
        "status": status,
    })

    if index % 50 == 0 or index == len(rows):
        print(
            f"Processed {index}/{len(rows)} "
            f"(matches={match_count}, "
            f"mismatches={mismatch_count}, "
            f"missing={missing_frontmatter_name_count})"
        )


# ---------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------

with OUTPUT_PATH.open("w", encoding="utf-8") as report:

    report.write("# GitSkills Name Validation\n\n")

    report.write(f"- **Database:** `{DB_PATH}`\n")
    report.write(
        f"- **Generated:** "
        f"{datetime.now().isoformat(timespec='seconds')}\n"
    )
    report.write(f"- **Random sample size:** {len(rows)}\n\n")

    report.write(
        "This report compares the `artifacts.name` database field "
        "against the `name:` value extracted from YAML-style frontmatter "
        "in the stored SKILL.md content.\n\n"
    )

    # Summary
    report.write("## Summary\n\n")

    report.write("| Result | Count | Percent |\n")
    report.write("|---|---:|---:|\n")

    total = len(rows)

    def pct(count):
        if total == 0:
            return 0
        return (count / total) * 100

    report.write(
        f"| Match | {match_count} | {pct(match_count):.2f}% |\n"
    )
    report.write(
        f"| Mismatch | {mismatch_count} | "
        f"{pct(mismatch_count):.2f}% |\n"
    )
    report.write(
        f"| No frontmatter name found | "
        f"{missing_frontmatter_name_count} | "
        f"{pct(missing_frontmatter_name_count):.2f}% |\n"
    )

    report.write("\n")

    # Mismatches
    report.write("## Mismatches\n\n")

    mismatches = [
        r for r in results
        if r["status"] == "MISMATCH"
    ]

    if not mismatches:
        report.write("No mismatches found.\n\n")
    else:
        report.write(
            "| Repository | Path | Database Name | "
            "Header Name | SHA |\n"
        )
        report.write(
            "|---|---|---|---|---|\n"
        )

        for result in mismatches:
            report.write(
                f"| {md_escape(result['repo'])} "
                f"| `{md_escape(result['path'])}` "
                f"| `{md_escape(result['db_name'])}` "
                f"| `{md_escape(result['header_name'])}` "
                f"| `{md_escape(result['sha'])}` |\n"
            )

        report.write("\n")

    # Missing names
    report.write("## No Frontmatter Name Found\n\n")

    missing = [
        r for r in results
        if r["status"] == "NO_HEADER_NAME"
    ]

    if not missing:
        report.write(
            "All sampled artifacts contained a readable "
            "`name:` field in YAML frontmatter.\n\n"
        )
    else:
        report.write(
            "| Repository | Path | Database Name | SHA |\n"
        )
        report.write(
            "|---|---|---|---|\n"
        )

        for result in missing:
            report.write(
                f"| {md_escape(result['repo'])} "
                f"| `{md_escape(result['path'])}` "
                f"| `{md_escape(result['db_name'])}` "
                f"| `{md_escape(result['sha'])}` |\n"
            )

        report.write("\n")

    # Optional sample records
    report.write("## First 25 Sampled Records\n\n")

    report.write(
        "| Repository | Database Name | Header Name | Status |\n"
    )
    report.write(
        "|---|---|---|---|\n"
    )

    for result in results[:25]:
        report.write(
            f"| {md_escape(result['repo'])} "
            f"| `{md_escape(result['db_name'])}` "
            f"| `{md_escape(result['header_name'])}` "
            f"| {result['status']} |\n"
        )

    report.write("\n---\n\n")
    report.write("Validation complete.\n")


db.close()

print()
print("=" * 70)
print("DONE")
print("=" * 70)
print(f"Matches: {match_count}")
print(f"Mismatches: {mismatch_count}")
print(
    f"No frontmatter name found: "
    f"{missing_frontmatter_name_count}"
)
print(f"Report written to: {OUTPUT_PATH.resolve()}")