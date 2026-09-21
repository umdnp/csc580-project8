import sqlite3
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
import re

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

DB_PATH = Path("agent_skills_release.db")
OUTPUT_PATH = Path("skill_similarity_pilot.md")

# Distinctive names that look more likely to represent copied/evolved skills
SKILL_NAMES = [
    "writing-plans",
    "systematic-debugging",
    "verification-before-completion",
    "subagent-driven-development",
    "using-git-worktrees",
    "dispatching-parallel-agents",
]

# Compare every artifact to this many of the earliest artifacts
ANCHOR_COUNT = 5

# Only include matches at or above this similarity in detailed results
REPORT_THRESHOLD = 0.75

# Maximum detailed matches written per skill
MAX_RESULTS_PER_SKILL = 100


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def normalize_text(text):
    """
    Light normalization intended to reduce meaningless formatting differences
    without destroying actual content differences.
    """
    if text is None:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove trailing whitespace
    lines = [line.rstrip() for line in text.splitlines()]

    # Collapse runs of 3+ blank lines to 2
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def similarity(text_a, text_b):
    """
    Return SequenceMatcher similarity from 0.0 to 1.0.
    """
    if not text_a or not text_b:
        return 0.0

    return SequenceMatcher(
        None,
        text_a,
        text_b,
        autojunk=False
    ).ratio()


def md_escape(value):
    if value is None:
        return "N/A"

    return str(value).replace("|", "\\|")


def classify_similarity(score):
    if score >= 0.95:
        return "Very strong"
    elif score >= 0.90:
        return "Strong"
    elif score >= 0.75:
        return "Possible"
    else:
        return "Weak"


# ---------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------

db = sqlite3.connect(DB_PATH)
db.row_factory = sqlite3.Row


# ---------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------

with OUTPUT_PATH.open("w", encoding="utf-8") as report:

    report.write("# GitSkills Same-Name Content Similarity Pilot\n\n")
    report.write(f"- **Database:** `{DB_PATH}`\n")
    report.write(
        f"- **Generated:** {datetime.now().isoformat(timespec='seconds')}\n"
    )
    report.write(f"- **Anchor artifacts per skill:** {ANCHOR_COUNT}\n")
    report.write(
        f"- **Detailed reporting threshold:** "
        f"{REPORT_THRESHOLD:.0%}\n\n"
    )

    report.write(
        "This exploratory analysis tests whether artifacts sharing the same "
        "skill name also contain highly similar content despite having "
        "different SHA values. Same-name and high-similarity results may "
        "indicate probable reuse, modification, or common origin, but do not "
        "by themselves establish genealogy.\n\n"
    )

    overall_pairs = 0
    overall_75 = 0
    overall_90 = 0
    overall_95 = 0

    # ================================================================
    # Process each candidate skill
    # ================================================================

    for skill_index, skill_name in enumerate(SKILL_NAMES, start=1):

        print("=" * 80)
        print(
            f"[{skill_index}/{len(SKILL_NAMES)}] "
            f"Loading: {skill_name}"
        )

        rows = db.execute("""
            SELECT
                repo_full_name,
                path,
                file_sha,
                first_commit_at,
                last_commit_at,
                commit_count,
                content
            FROM artifacts
            WHERE LOWER(TRIM(name)) = ?
              AND content IS NOT NULL
              AND file_sha IS NOT NULL
            ORDER BY
                CASE WHEN first_commit_at IS NULL THEN 1 ELSE 0 END,
                first_commit_at,
                repo_full_name,
                path
        """, (skill_name.lower(),)).fetchall()

        print(f"Artifacts with content: {len(rows)}")

        report.write(f"## `{skill_name}`\n\n")
        report.write(f"- **Artifacts with content:** {len(rows)}\n")

        if len(rows) < 2:
            report.write(
                "- Insufficient artifacts for comparison.\n\n"
            )
            continue

        # Pre-normalize once so we don't repeatedly process the same document.
        artifacts = []

        for row in rows:
            normalized = normalize_text(row["content"])

            artifacts.append({
                "repo": row["repo_full_name"],
                "path": row["path"],
                "sha": row["file_sha"],
                "first_commit": row["first_commit_at"],
                "last_commit": row["last_commit_at"],
                "commit_count": row["commit_count"],
                "content": normalized,
                "length": len(normalized),
            })

        # Earliest artifacts become candidate origin/reference anchors.
        anchors = artifacts[:min(ANCHOR_COUNT, len(artifacts))]

        report.write(
            f"- **Earliest artifacts used as anchors:** "
            f"{len(anchors)}\n\n"
        )

        comparisons = set()
        results = []

        # -------------------------------------------------------------
        # A. Compare every artifact to earliest anchors
        # -------------------------------------------------------------

        print("Comparing artifacts to earliest anchors...")

        for i, artifact in enumerate(artifacts):

            if i % 100 == 0 or i == len(artifacts) - 1:
                print(
                    f"  Anchor comparison progress: "
                    f"{i + 1}/{len(artifacts)}"
                )

            for anchor_index, anchor in enumerate(anchors):

                # Avoid comparing an artifact with itself.
                if artifact["sha"] == anchor["sha"]:
                    continue

                pair_key = tuple(sorted((
                    (artifact["repo"], artifact["path"], artifact["sha"]),
                    (anchor["repo"], anchor["path"], anchor["sha"])
                )))

                if pair_key in comparisons:
                    continue

                comparisons.add(pair_key)

                score = similarity(
                    artifact["content"],
                    anchor["content"]
                )

                results.append({
                    "type": f"Anchor {anchor_index + 1}",
                    "score": score,
                    "a": anchor,
                    "b": artifact,
                })

        # -------------------------------------------------------------
        # B. Compare chronologically adjacent artifacts
        # -------------------------------------------------------------

        print("Comparing chronologically adjacent artifacts...")

        for i in range(1, len(artifacts)):

            previous = artifacts[i - 1]
            current = artifacts[i]

            if previous["sha"] == current["sha"]:
                continue

            pair_key = tuple(sorted((
                (previous["repo"], previous["path"], previous["sha"]),
                (current["repo"], current["path"], current["sha"])
            )))

            if pair_key in comparisons:
                continue

            comparisons.add(pair_key)

            score = similarity(
                previous["content"],
                current["content"]
            )

            results.append({
                "type": "Chronological neighbor",
                "score": score,
                "a": previous,
                "b": current,
            })

        # -------------------------------------------------------------
        # Summaries
        # -------------------------------------------------------------

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        pair_count = len(results)
        count_75 = sum(r["score"] >= 0.75 for r in results)
        count_90 = sum(r["score"] >= 0.90 for r in results)
        count_95 = sum(r["score"] >= 0.95 for r in results)

        overall_pairs += pair_count
        overall_75 += count_75
        overall_90 += count_90
        overall_95 += count_95

        report.write("### Similarity Summary\n\n")
        report.write("| Metric | Count |\n")
        report.write("|---|---:|\n")
        report.write(f"| Comparisons performed | {pair_count} |\n")
        report.write(f"| Similarity ≥ 75% | {count_75} |\n")
        report.write(f"| Similarity ≥ 90% | {count_90} |\n")
        report.write(f"| Similarity ≥ 95% | {count_95} |\n")

        if pair_count:
            report.write(
                f"| Highest similarity | "
                f"{results[0]['score']:.2%} |\n"
            )

        report.write("\n")

        print(
            f"Completed {pair_count} comparisons: "
            f"{count_75} >=75%, "
            f"{count_90} >=90%, "
            f"{count_95} >=95%"
        )

        # -------------------------------------------------------------
        # Detailed results
        # -------------------------------------------------------------

        significant = [
            r for r in results
            if r["score"] >= REPORT_THRESHOLD
        ][:MAX_RESULTS_PER_SKILL]

        report.write(
            f"### Top Matches ≥ {REPORT_THRESHOLD:.0%}\n\n"
        )

        if not significant:
            report.write(
                "No comparisons met the reporting threshold.\n\n"
            )
            continue

        for result_index, result in enumerate(significant, start=1):

            a = result["a"]
            b = result["b"]
            score = result["score"]

            report.write(
                f"#### Match {result_index}: "
                f"{score:.2%} — "
                f"{classify_similarity(score)}\n\n"
            )

            report.write(
                f"- **Comparison type:** "
                f"{result['type']}\n"
            )
            report.write(
                f"- **Similarity:** {score:.2%}\n"
            )
            report.write(
                f"- **Length A:** {a['length']:,} characters\n"
            )
            report.write(
                f"- **Length B:** {b['length']:,} characters\n"
            )

            if a["length"]:
                length_change = (
                    (b["length"] - a["length"])
                    / a["length"]
                ) * 100

                report.write(
                    f"- **Length change:** "
                    f"{length_change:+.1f}%\n"
                )

            report.write("\n")

            report.write("**Artifact A**\n\n")
            report.write(
                f"- Repository: `{md_escape(a['repo'])}`\n"
            )
            report.write(
                f"- Path: `{md_escape(a['path'])}`\n"
            )
            report.write(
                f"- SHA: `{a['sha']}`\n"
            )
            report.write(
                f"- First commit: "
                f"{md_escape(a['first_commit'])}\n"
            )
            report.write(
                f"- Last commit: "
                f"{md_escape(a['last_commit'])}\n"
            )
            report.write(
                f"- Commit count: "
                f"{md_escape(a['commit_count'])}\n\n"
            )

            report.write("**Artifact B**\n\n")
            report.write(
                f"- Repository: `{md_escape(b['repo'])}`\n"
            )
            report.write(
                f"- Path: `{md_escape(b['path'])}`\n"
            )
            report.write(
                f"- SHA: `{b['sha']}`\n"
            )
            report.write(
                f"- First commit: "
                f"{md_escape(b['first_commit'])}\n"
            )
            report.write(
                f"- Last commit: "
                f"{md_escape(b['last_commit'])}\n"
            )
            report.write(
                f"- Commit count: "
                f"{md_escape(b['commit_count'])}\n\n"
            )

    # ================================================================
    # Overall summary
    # ================================================================

    report.write("# Overall Pilot Summary\n\n")
    report.write("| Metric | Count |\n")
    report.write("|---|---:|\n")
    report.write(
        f"| Skill names analyzed | {len(SKILL_NAMES)} |\n"
    )
    report.write(
        f"| Total comparisons | {overall_pairs} |\n"
    )
    report.write(
        f"| Similarity ≥ 75% | {overall_75} |\n"
    )
    report.write(
        f"| Similarity ≥ 90% | {overall_90} |\n"
    )
    report.write(
        f"| Similarity ≥ 95% | {overall_95} |\n"
    )

    report.write("\n---\n\n")
    report.write("Pilot analysis complete.\n")


db.close()

print()
print("=" * 80)
print("DONE")
print("=" * 80)
print(f"Report written to: {OUTPUT_PATH.resolve()}")