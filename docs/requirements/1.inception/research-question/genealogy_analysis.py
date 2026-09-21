import sqlite3
from pathlib import Path
from datetime import datetime
import time

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

DB_PATH = Path("agent_skills_release.db")
OUTPUT_PATH = Path("genealogy_analysis.md")

# How often to print a heartbeat while SQLite is busy on a long query.
PROGRESS_INTERVAL_SECONDS = 5

script_started = time.monotonic()
current_task = "Starting"
last_progress_print = 0.0


def elapsed_time():
    """Return total script runtime as HH:MM:SS."""
    seconds = int(time.monotonic() - script_started)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def set_task(message):
    """Set and immediately display the current high-level task."""
    global current_task, last_progress_print
    current_task = message
    last_progress_print = time.monotonic()
    print(f"[{elapsed_time()}] {message}", flush=True)


def sqlite_progress():
    """
    SQLite calls this periodically while executing VM instructions.

    Returning 0 tells SQLite to continue.  We use it only to print a
    time-based heartbeat so long-running GROUP BY / COUNT queries do not
    appear frozen.
    """
    global last_progress_print

    now = time.monotonic()
    if now - last_progress_print >= PROGRESS_INTERVAL_SECONDS:
        print(
            f"[{elapsed_time()}] Still working: {current_task} ...",
            flush=True,
        )
        last_progress_print = now

    return 0


def task_done(message="Done"):
    """Print completion of the current task."""
    print(f"[{elapsed_time()}] {message}", flush=True)

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def md_safe(value):
    """Convert database values to readable Markdown-safe text."""
    if value is None:
        return "N/A"

    return str(value).replace("|", "\\|")


def write_code_block(report, value):
    """Write potentially multiline text safely as a Markdown code block."""
    if value is None:
        report.write("`N/A`\n\n")
        return

    report.write("```text\n")
    report.write(str(value).rstrip())
    report.write("\n```\n\n")


# ---------------------------------------------------------------------
# Connect
# ---------------------------------------------------------------------

set_task(f"Opening database: {DB_PATH}")
db = sqlite3.connect(DB_PATH)
db.row_factory = sqlite3.Row

# Invoke sqlite_progress every 100,000 SQLite virtual-machine instructions.
# The callback itself only prints once every PROGRESS_INTERVAL_SECONDS.
db.set_progress_handler(sqlite_progress, 100_000)

task_done("Database opened")

with OUTPUT_PATH.open("w", encoding="utf-8") as report:

    report.write("# GitSkills Genealogy Analysis\n\n")
    report.write(
        f"- **Database:** `{DB_PATH}`\n"
        f"- **Generated:** {datetime.now().isoformat(timespec='seconds')}\n\n"
    )

    # =================================================================
    # 1. HISTORY COVERAGE
    # =================================================================

    set_task("Section 1/6: Analyzing history coverage")
    report.write("## 1. History Coverage\n\n")

    row = db.execute("""
        SELECT
            COUNT(*) AS total_artifacts,
            SUM(CASE WHEN history_fetched = 1 THEN 1 ELSE 0 END) AS history_fetched,
            SUM(CASE WHEN commit_count > 1 THEN 1 ELSE 0 END) AS multiple_commits,
            MAX(commit_count) AS max_commit_count,
            AVG(commit_count) AS avg_commit_count
        FROM artifacts
    """).fetchone()

    report.write("| Metric | Value |\n")
    report.write("|---|---:|\n")

    for key in row.keys():
        value = row[key]

        if isinstance(value, float):
            value = f"{value:.2f}"

        report.write(f"| {key} | {md_safe(value)} |\n")

    report.write("\n### Top 25 Artifacts by Commit Count\n\n")

    rows = db.execute("""
        SELECT
            repo_full_name,
            path,
            first_commit_at,
            last_commit_at,
            commit_count,
            first_commit_message,
            last_commit_message
        FROM artifacts
        WHERE commit_count > 1
        ORDER BY commit_count DESC
        LIMIT 25
    """)

    for i, row in enumerate(rows, start=1):
        report.write(
            f"#### {i}. `{md_safe(row['repo_full_name'])}`\n\n"
        )

        report.write(f"- **Path:** `{md_safe(row['path'])}`\n")
        report.write(f"- **Commit count:** {md_safe(row['commit_count'])}\n")
        report.write(f"- **First commit:** {md_safe(row['first_commit_at'])}\n")
        report.write(f"- **Last commit:** {md_safe(row['last_commit_at'])}\n\n")

        report.write("**First commit message:**\n\n")
        write_code_block(report, row["first_commit_message"])

        report.write("**Last commit message:**\n\n")
        write_code_block(report, row["last_commit_message"])

    task_done("Section 1/6 complete")

    # =================================================================
    # 2. MULTIPLE ROWS FOR SAME REPOSITORY/PATH
    # =================================================================

    set_task("Section 2/6: Finding duplicate repository/path groups")
    report.write("## 2. Multiple Rows for the Same Repository and Path\n\n")

    duplicate_count = db.execute("""
        SELECT COUNT(*) AS duplicate_groups
        FROM (
            SELECT repo_full_name, path
            FROM artifacts
            GROUP BY repo_full_name, path
            HAVING COUNT(*) > 1
        )
    """).fetchone()["duplicate_groups"]

    report.write(
        f"**Duplicate repository/path groups found:** {duplicate_count}\n\n"
    )

    if duplicate_count > 0:
        report.write("### Top 25 Duplicate Repository/Path Groups\n\n")

        report.write("| Repository | Path | Records |\n")
        report.write("|---|---|---:|\n")

        rows = db.execute("""
            SELECT
                repo_full_name,
                path,
                COUNT(*) AS records
            FROM artifacts
            GROUP BY repo_full_name, path
            HAVING COUNT(*) > 1
            ORDER BY records DESC
            LIMIT 25
        """)

        for row in rows:
            report.write(
                f"| {md_safe(row['repo_full_name'])} "
                f"| {md_safe(row['path'])} "
                f"| {row['records']} |\n"
            )

        report.write("\n")

    task_done("Section 2/6 complete")

    # =================================================================
    # 3. EXACT CONTENT REUSE ACROSS REPOSITORIES
    # =================================================================

    set_task("Section 3/6: Finding exact content reuse across repositories")
    report.write("## 3. Exact Content Reuse Across Repositories\n\n")

    # Count ALL cross-repository duplicate SHA groups.
    reuse_group_count = db.execute("""
        SELECT COUNT(*) AS reuse_groups
        FROM (
            SELECT file_sha
            FROM artifacts
            WHERE file_sha IS NOT NULL
            GROUP BY file_sha
            HAVING COUNT(DISTINCT repo_full_name) > 1
        )
    """).fetchone()["reuse_groups"]

    report.write(
        f"**Total SHA groups appearing in multiple repositories:** "
        f"{reuse_group_count}\n\n"
    )

    report.write("### Top 50 Cross-Repository SHA Groups\n\n")

    report.write("| SHA | Artifacts | Repositories |\n")
    report.write("|---|---:|---:|\n")

    rows = db.execute("""
        SELECT
            file_sha,
            COUNT(*) AS artifact_count,
            COUNT(DISTINCT repo_full_name) AS repo_count
        FROM artifacts
        WHERE file_sha IS NOT NULL
        GROUP BY file_sha
        HAVING COUNT(DISTINCT repo_full_name) > 1
        ORDER BY repo_count DESC, artifact_count DESC
        LIMIT 50
    """)

    for row in rows:
        report.write(
            f"| `{md_safe(row['file_sha'])}` "
            f"| {row['artifact_count']} "
            f"| {row['repo_count']} |\n"
        )

    report.write("\n")

    task_done("Section 3/6 complete")

    # =================================================================
    # 4. DEDUP_PRIMARY DISTRIBUTION
    # =================================================================

    set_task("Section 4/6: Analyzing dedup_primary distribution")
    report.write("## 4. `dedup_primary` Distribution\n\n")

    report.write("| dedup_primary | Count |\n")
    report.write("|---:|---:|\n")

    rows = db.execute("""
        SELECT
            dedup_primary,
            COUNT(*) AS count
        FROM artifacts
        GROUP BY dedup_primary
        ORDER BY dedup_primary
    """)

    for row in rows:
        report.write(
            f"| {md_safe(row['dedup_primary'])} "
            f"| {row['count']} |\n"
        )

    report.write("\n### Top 25 Duplicate SHA Groups and Primary Counts\n\n")

    report.write("| SHA | Total | Primaries | Repositories |\n")
    report.write("|---|---:|---:|---:|\n")

    rows = db.execute("""
        SELECT
            file_sha,
            COUNT(*) AS total,
            SUM(CASE WHEN dedup_primary = 1 THEN 1 ELSE 0 END) AS primaries,
            COUNT(DISTINCT repo_full_name) AS repo_count
        FROM artifacts
        WHERE file_sha IS NOT NULL
        GROUP BY file_sha
        HAVING COUNT(*) > 1
        ORDER BY total DESC
        LIMIT 25
    """)

    for row in rows:
        report.write(
            f"| `{md_safe(row['file_sha'])}` "
            f"| {row['total']} "
            f"| {row['primaries']} "
            f"| {row['repo_count']} |\n"
        )

    report.write("\n")

    task_done("Section 4/6 complete")

    # =================================================================
    # 5. REPOSITORY FORKS
    # =================================================================

    set_task("Section 5/6: Analyzing repository forks")
    report.write("## 5. Repository Forks\n\n")

    row = db.execute("""
        SELECT
            COUNT(*) AS repositories,
            SUM(CASE WHEN is_fork = 1 THEN 1 ELSE 0 END) AS forks
        FROM repos
    """).fetchone()

    report.write(f"- **Repositories:** {row['repositories']}\n")
    report.write(f"- **Forks:** {row['forks'] or 0}\n\n")

    report.write("### Sample Artifacts from Forked Repositories\n\n")

    rows = db.execute("""
        SELECT
            a.repo_full_name,
            a.path,
            a.file_sha,
            a.commit_count,
            a.first_commit_at,
            a.last_commit_at
        FROM artifacts a
        JOIN repos r
            ON a.repo_full_name = r.full_name
        WHERE r.is_fork = 1
        LIMIT 25
    """)

    found_forks = False

    for i, row in enumerate(rows, start=1):
        found_forks = True

        report.write(f"#### {i}. `{md_safe(row['repo_full_name'])}`\n\n")
        report.write(f"- **Path:** `{md_safe(row['path'])}`\n")
        report.write(f"- **SHA:** `{md_safe(row['file_sha'])}`\n")
        report.write(f"- **Commit count:** {md_safe(row['commit_count'])}\n")
        report.write(f"- **First commit:** {md_safe(row['first_commit_at'])}\n")
        report.write(f"- **Last commit:** {md_safe(row['last_commit_at'])}\n\n")

    if not found_forks:
        report.write("No forked repositories were found.\n\n")

    task_done("Section 5/6 complete")

    # =================================================================
    # 6. SUMMARY COUNTS
    # =================================================================

    set_task("Section 6/6: Calculating summary counts")
    report.write("## 6. Summary Counts for Content and History\n\n")

    row = db.execute("""
        SELECT
            COUNT(*) AS total_artifacts,
            SUM(CASE WHEN content IS NOT NULL THEN 1 ELSE 0 END) AS with_content,
            SUM(CASE WHEN file_sha IS NOT NULL THEN 1 ELSE 0 END) AS with_sha,
            SUM(CASE WHEN commit_count IS NOT NULL THEN 1 ELSE 0 END) AS with_commit_count,
            SUM(CASE WHEN first_commit_at IS NOT NULL THEN 1 ELSE 0 END) AS with_first_commit,
            SUM(CASE WHEN last_commit_at IS NOT NULL THEN 1 ELSE 0 END) AS with_last_commit
        FROM artifacts
    """).fetchone()

    report.write("| Metric | Count |\n")
    report.write("|---|---:|\n")

    for key in row.keys():
        report.write(f"| {key} | {md_safe(row[key])} |\n")

    report.write("\n---\n\n")
    report.write("Analysis complete.\n")
    task_done("Section 6/6 complete")


db.close()

print(f"Analysis complete.")
print(f"Report written to: {OUTPUT_PATH.resolve()}")