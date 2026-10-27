"""Source identity, report consistency, and cohort audit artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Sequence

from gitskills.analysis.family_models import SimilarityPolicy
from gitskills.reporting.files import report_stems


SOURCE_FIELDS = (
    "artifact_id", "group_id", "repo_full_name", "path", "file_sha",
    "sibling_file_count", "sibling_content_sha",
)


def read_json(path: Path) -> dict:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read report {path}: {exc}") from exc
    if not isinstance(report, dict):
        raise ValueError(f"Report must be a JSON object: {path}")
    return report


def implementation_fingerprint() -> str:
    """Record the implementation used for a cohort run, not per-family output."""
    root = Path(__file__).resolve().parents[1]
    files = sorted((*root.glob("analysis/*.py"), *root.glob("rules/*.py"),
                    root / "reporting" / "redaction.py"))
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def fingerprint(records: list[dict]) -> str:
    """Hash a stable JSON description of the source artifacts."""
    payload = json.dumps(records, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_names(names: Sequence[str]) -> tuple[list[str], dict[str, str]]:
    selected = list(names)
    if not selected or any(not isinstance(name, str) or not name.strip() for name in selected):
        raise ValueError("Choose at least one nonempty candidate family")
    if len(set(selected)) != len(selected):
        raise ValueError("Duplicate candidate family names are not allowed")
    return selected, report_stems(selected)


def compatible_family(report: dict, name: str, policy: SimilarityPolicy,
                      records: list[dict], skipped: list[dict]) -> bool:
    """Reuse only complete family reports built from the same inputs and policy."""
    if report.get("name") != name or report.get("policy") != policy.to_dict():
        return False
    artifacts = report.get("artifacts")
    if (not isinstance(artifacts, list)
            or not isinstance(report.get("family"), dict)
            or not isinstance(report["family"].get("clusters"), list)
            or not all(isinstance(item, dict) for item in artifacts)):
        return False
    reference = {item["artifact_id"]: item for item in records}
    actual = {
        item.get("artifact_id"): {field: item.get(field) for field in SOURCE_FIELDS}
        for item in artifacts
    }
    return (len(actual) == len(artifacts) == len(reference)
            and actual == reference and report.get("skipped_artifacts") == skipped)


def verify_pair_sources(family: dict, scan: dict, name: str) -> int:
    """Verify every scanned primary/additional pair against its source cluster."""
    artifact_ids = {artifact["artifact_id"] for artifact in family["artifacts"]}
    relationships = {}
    for cluster in family["family"]["clusters"]:
        number = cluster["cluster"]
        evolution = cluster["evolution"]
        for kind, key in (("primary", "directed_edges"), ("additional", "related_edges")):
            for edge in evolution[key]:
                pair = (number, edge["source_artifact_id"], edge["target_artifact_id"])
                # Primary classification prevails if a related edge appears in both lists.
                if pair not in relationships or kind == "primary":
                    relationships[pair] = kind

    observed = []
    for cluster in scan["clusters"]:
        for pair in cluster["pair_observations"]:
            source, target = pair["source_artifact_id"], pair["destination_artifact_id"]
            key = (cluster["cluster"], source, target)
            kind = relationships.get(key)
            if (source not in artifact_ids or target not in artifact_ids
                    or kind != pair.get("edge_type")
                    or (scan["edge_selection"] == "primary" and kind != "primary")):
                raise ValueError(f"{name}: scan pair {source}->{target} is not traceable to a family edge")
            observed.append(key)
    if len(observed) != scan["summary"]["pairs_analyzed"] or len(set(observed)) != len(observed):
        raise ValueError(f"{name}: pair count mismatch or repeated source pair")
    return len(observed)


def check_reports(name: str, family: dict, scan: dict) -> tuple[list[dict], int]:
    """Validate identity and return traceable source references and pair count."""
    if family.get("name") != name or scan.get("candidate_family") != name:
        raise ValueError(f"{name}: stored report has an unexpected family name")
    if scan.get("similarity_policy") != family.get("policy"):
        raise ValueError(f"{name}: scan and family similarity policies disagree; rerun run_family")
    if not isinstance(family.get("artifacts"), list):
        raise ValueError(f"{name}: SkillTrace report lacks artifacts; rerun analyze_family")
    sources = [{field: item.get(field) for field in SOURCE_FIELDS} for item in family["artifacts"]]
    if sorted(sources, key=lambda item: item["artifact_id"]) != scan.get("input_artifacts"):
        raise ValueError(f"{name}: scan inputs do not match the SkillTrace report; rerun run_family")
    if family.get("skipped_artifacts") != scan.get("skipped_artifacts"):
        raise ValueError(f"{name}: skipped input records disagree; rerun run_family")
    return sources, verify_pair_sources(family, scan, name)


def git_revision(root: Path) -> str | None:
    """Read a normal Git checkout's HEAD without external commands."""
    git = root / ".git"
    try:
        if git.is_file():
            git = (root / git.read_text(encoding="utf-8").strip().removeprefix("gitdir: ")).resolve()
        head = (git / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref: "):
            ref = git / head[5:]
            return ref.read_text(encoding="utf-8").strip() if ref.is_file() else None
        return head or None
    except OSError:
        return None


def cohort_manifest(names: list[str], database: Path, scans: list[dict],
                    snapshots: list[dict], audit: list[dict],
                    project_root: Path, per_stratum: int | None, seed: int,
                    approval_reference: str | None) -> dict:
    if not database.is_file():
        raise FileNotFoundError(f"Prepared DuckDB database not found: {database}")
    return {
        "sample_status": "approved" if approval_reference else "provisional",
        "approval_reference": approval_reference,
        "dataset": {"path": str(database.resolve()), "size_bytes": database.stat().st_size,
                    "kind": "prepared GitSkills DuckDB", "source": "GitSkills Zenodo record 21875637"},
        "selection": {
            "unit": "artifact_groupings.name candidate family",
            "criterion": "exact names in candidate_families (artifact_groupings joined to artifacts)",
            "invalid_inputs": "retain per-artifact skip reasons; exclude from comparison",
            "population": "all prepared grouping rows matching each selected name; not manually picked pairs",
            "upstream_filter": "sql/create_analysis_tables.sql: frontmatter_valid=1, body_chars>50, content/name/description non-NULL, skill name occurs at least twice; each normalized description remains a group",
            "sibling_fingerprint": "sql/update_artifact_groupings.sql: file entries with available hashes; unknown when composition is incomplete",
            "sibling_scan_scope": "artifact_siblings.entry_type=file only; directory entries are not executable content",
            "comparison_scope": "direction-supported family edges; ambiguous relationships reviewed separately",
        },
        "family_names": names,
        "similarity_policy": scans[0]["similarity_policy"],
        "active_rules": scans[0]["active_rules"],
        "implementation_fingerprint": implementation_fingerprint(),
        "code_revision": git_revision(project_root),
        "python_version": sys.version.split()[0],
        "scanner_scope": scans[0]["scanner_scope"],
        "edge_selection": scans[0]["edge_selection"],
        "sampling": {
            "per_stratum": per_stratum, "seed": seed, "unit": "selected cohort",
            "directed_selection": "seeded shuffle without replacement",
            "relationship_selection": "bounded seeded reservoir without replacement",
        },
        "families": snapshots,
        "totals": {"families": len(names),
                   "artifacts_loaded": sum(row["artifacts_loaded"] for row in audit),
                   "artifacts_skipped": sum(row["artifacts_skipped"] for row in audit)},
    }


def protect_snapshot(manifest_path: Path, sample: dict) -> None:
    """Do not silently change a cohort with completed adjudication files."""
    adjudications = (manifest_path.parent / "manual-review" / "adjudicated",
                     manifest_path.parent / "review" / "adjudicated")
    if manifest_path.is_file() and any(folder.exists() and any(folder.glob("*.csv"))
                                      for folder in adjudications):
        previous = read_json(manifest_path)
        frozen = ("family_names", "similarity_policy", "edge_selection", "sampling",
                  "families", "active_rules")
        if (any(previous.get(key) != sample.get(key) for key in frozen)
                or previous.get("review_sample_fingerprint") != sample.get("review_sample_fingerprint")):
            raise ValueError("Selected sample changed after adjudication; archive the previous results first")


def write_audit(results: Path, rows: list[dict], snapshots: list[dict]) -> None:
    folder = results / "audit"
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "processing_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (folder / "skipped_artifacts.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("family", "artifact_id", "repo_full_name", "path", "reason"))
        writer.writeheader()
        writer.writerows({"family": item["name"], **skipped}
                         for item in snapshots for skipped in item["skipped_artifacts"])
