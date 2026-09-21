import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("agent_skills_release.db")
OUTPUT_PATH = Path("same_name_different_sha.md")

db = sqlite3.connect(DB_PATH)
db.row_factory = sqlite3.Row

with OUTPUT_PATH.open("w", encoding="utf-8") as report:

    report.write("# Same-Name / Different-SHA Analysis\n\n")
    report.write(f"- **Database:** `{DB_PATH}`\n")
    report.write(
        f"- **Generated:** {datetime.now().isoformat(timespec='seconds')}\n\n"
    )

    # -------------------------------------------------------------
    # Overall counts
    # -------------------------------------------------------------

    summary = db.execute("""
        SELECT
            COUNT(*) AS named_artifacts,
            COUNT(DISTINCT LOWER(TRIM(name))) AS distinct_names
        FROM artifacts
        WHERE name IS NOT NULL
          AND TRIM(name) <> ''
    """).fetchone()

    candidate_count = db.execute("""
        SELECT COUNT(*) AS candidate_names
        FROM (
            SELECT LOWER(TRIM(name)) AS normalized_name
            FROM artifacts
            WHERE name IS NOT NULL
              AND TRIM(name) <> ''
              AND file_sha IS NOT NULL
            GROUP BY LOWER(TRIM(name))
            HAVING COUNT(DISTINCT file_sha) > 1
        )
    """).fetchone()["candidate_names"]

    report.write("## Summary\n\n")
    report.write("| Metric | Count |\n")
    report.write("|---|---:|\n")
    report.write(
        f"| Artifacts with a skill name | {summary['named_artifacts']} |\n"
    )
    report.write(
        f"| Distinct normalized skill names | {summary['distinct_names']} |\n"
    )
    report.write(
        f"| Names associated with multiple SHAs | {candidate_count} |\n\n"
    )

    # -------------------------------------------------------------
    # Largest same-name/different-SHA groups
    # -------------------------------------------------------------

    report.write("## Top Candidate Version Families\n\n")

    report.write(
        "| Skill Name | Artifacts | Distinct SHAs | Repositories | "
        "With Content | Earliest Commit | Latest Commit |\n"
    )
    report.write(
        "|---|---:|---:|---:|---:|---|---|\n"
    )

    rows = db.execute("""
        SELECT
            LOWER(TRIM(name)) AS normalized_name,
            COUNT(*) AS artifact_count,
            COUNT(DISTINCT file_sha) AS distinct_shas,
            COUNT(DISTINCT repo_full_name) AS repo_count,
            SUM(CASE WHEN content IS NOT NULL THEN 1 ELSE 0 END)
                AS with_content,
            MIN(first_commit_at) AS earliest_commit,
            MAX(first_commit_at) AS latest_commit
        FROM artifacts
        WHERE name IS NOT NULL
          AND TRIM(name) <> ''
          AND file_sha IS NOT NULL
        GROUP BY LOWER(TRIM(name))
        HAVING COUNT(DISTINCT file_sha) > 1
        ORDER BY repo_count DESC, distinct_shas DESC
        LIMIT 100
    """)

    candidate_names = []

    for row in rows:
        name = row["normalized_name"]
        candidate_names.append(name)

        safe_name = name.replace("|", "\\|")

        report.write(
            f"| {safe_name} "
            f"| {row['artifact_count']} "
            f"| {row['distinct_shas']} "
            f"| {row['repo_count']} "
            f"| {row['with_content']} "
            f"| {row['earliest_commit'] or 'N/A'} "
            f"| {row['latest_commit'] or 'N/A'} |\n"
        )

    report.write("\n")

    # -------------------------------------------------------------
    # Show individual artifacts for top candidates
    # -------------------------------------------------------------

    report.write("## Artifact Details for Top Candidates\n\n")

    for name in candidate_names[:25]:

        report.write(f"### `{name}`\n\n")

        rows = db.execute("""
            SELECT
                repo_full_name,
                path,
                file_sha,
                first_commit_at,
                last_commit_at,
                commit_count,
                CASE WHEN content IS NOT NULL THEN 1 ELSE 0 END
                    AS has_content
            FROM artifacts
            WHERE LOWER(TRIM(name)) = ?
            ORDER BY
                CASE WHEN first_commit_at IS NULL THEN 1 ELSE 0 END,
                first_commit_at,
                repo_full_name
            LIMIT 100
        """, (name,))

        report.write(
            "| Repository | Path | SHA | First Commit | "
            "Last Commit | Commits | Content |\n"
        )
        report.write(
            "|---|---|---|---|---|---:|---:|\n"
        )

        for row in rows:
            repo = row["repo_full_name"].replace("|", "\\|")
            path = row["path"].replace("|", "\\|")

            report.write(
                f"| {repo} "
                f"| `{path}` "
                f"| `{row['file_sha']}` "
                f"| {row['first_commit_at'] or 'N/A'} "
                f"| {row['last_commit_at'] or 'N/A'} "
                f"| {row['commit_count'] or 'N/A'} "
                f"| {row['has_content']} |\n"
            )

        report.write("\n")

db.close()

print("Analysis complete.")
print(f"Report written to: {OUTPUT_PATH.resolve()}")