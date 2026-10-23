"""Incremental family scanning and reproducible cohort review outputs."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Sequence

from gitskills.analysis.family_models import SimilarityPolicy
from gitskills.analysis.family_reporting import (
    analyze_family_report, scan_family_report, source_records,
    implementation_fingerprint,
)
from gitskills.data.families import DuckDBFamilyRepository
from gitskills.data.siblings import DuckDBSiblingRepository
from gitskills.tools._output import report_stems, write_json
from gitskills.tools.summarize_scans import summarize


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read report {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Report must be a JSON object: {path}")
    return value


def _git_revision(path: Path) -> str | None:
    """Identify an ordinary Git checkout without invoking external commands."""
    git = path / ".git"
    try:
        if git.is_file():
            git = (path / git.read_text(encoding="utf-8").strip().removeprefix("gitdir: ")).resolve()
        head = (git / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref: "):
            ref = git / head[5:]
            return ref.read_text(encoding="utf-8").strip() if ref.is_file() else None
        return head or None
    except OSError:
        return None


def _fingerprint(records: list[dict]) -> str:
    return hashlib.sha256(json.dumps(records, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _validate_names(names: Sequence[str]) -> tuple[list[str], dict[str, str]]:
    selected = list(names)
    if not selected or any(not isinstance(name, str) or not name.strip() for name in selected):
        raise ValueError("Choose at least one nonempty candidate family")
    if len(set(selected)) != len(selected):
        raise ValueError("Duplicate candidate family names are not allowed")
    return selected, report_stems(selected)


def _compatible_family(report: dict, name: str, policy: SimilarityPolicy,
                       records: list[dict], skipped: list[dict]) -> bool:
    if (report.get("name") != name or report.get("policy") != policy.to_dict()
            or report.get("implementation_fingerprint") != implementation_fingerprint()):
        return False
    if not isinstance(report.get("artifacts"), list) or not isinstance(report.get("similarities"), list):
        return False
    if not isinstance(report.get("family"), dict) or not isinstance(report["family"].get("clusters"), list):
        return False
    if not all(isinstance(item, dict) for item in report["artifacts"]):
        return False
    actual = [{key: item.get(key) for key in record} for item in report["artifacts"]
              for record in records if record["artifact_id"] == item.get("artifact_id")]
    return (len(actual) == len(records) and actual == records
            and report.get("skipped_artifacts") == skipped)


def run_family(name: str, *, database: Path, skilltrace_reports: Path,
               scans: Path, policy: SimilarityPolicy | None = None,
               edges: str = "all", force_family: bool = False) -> dict:
    """Analyze or reuse one SkillTrace report and write one current security scan.

    Scan reports are rebuilt when explicitly running a family; other families'
    reports remain untouched. The source database is always read-only.
    """
    policy = policy or SimilarityPolicy()
    _, stems = _validate_names([name])
    family_path = skilltrace_reports / f"{stems[name]}.json"
    scan_path = scans / f"{stems[name]}.json"
    loaded = DuckDBFamilyRepository(database).load_available(name)
    if not loaded.artifacts and not loaded.skipped_artifacts:
        raise ValueError(f"Candidate family not found in prepared DuckDB: {name}")
    records = source_records(loaded)
    skipped = [item.to_dict() for item in loaded.skipped_artifacts]

    existing = None
    if family_path.exists() and not force_family:
        try:
            existing = _read_json(family_path)
        except ValueError:
            pass  # Refresh a malformed report from source, rather than trusting it.
    refresh = force_family or existing is None or not _compatible_family(
        existing, name, policy, records, skipped)
    if refresh:
        _, family_report = analyze_family_report(name, loaded, policy=policy)
    else:
        family_report = existing

    siblings = DuckDBSiblingRepository(database).load(
        artifact.artifact_id for artifact in loaded.artifacts)
    _, scan_report = scan_family_report(
        name, loaded, siblings, policy=policy, edges=edges)
    adjudicated = scans.parent / "review" / "adjudicated"
    if adjudicated.exists() and any(adjudicated.glob("*.csv")):
        old_scan = _read_json(scan_path) if scan_path.is_file() else None
        if refresh or old_scan != scan_report:
            raise ValueError(
                f"{name}: completed review exists and reports would change; "
                "archive the existing run before rebuilding it"
            )

    if refresh:
        skilltrace_reports.mkdir(parents=True, exist_ok=True)
        write_json(skilltrace_reports, stems[name], family_report)
    scans.mkdir(parents=True, exist_ok=True)
    write_json(scans, stems[name], scan_report)
    return {
        "family": name, "family_report": str(family_path),
        "family_report_updated": refresh, "scan_report": str(scan_path),
        "artifacts_loaded": len(records), "artifacts_skipped": len(skipped),
        "pairs_analyzed": scan_report["summary"]["pairs_analyzed"],
        "pairs_incomplete": scan_report["summary"]["pairs_incomplete"],
        "source_fingerprint": _fingerprint(records),
    }


def _verify_pair_sources(family: dict, scan: dict, family_name: str) -> int:
    """Reject any scan pairs absent from the selected family relationship report."""
    artifact_ids = {a["artifact_id"] for a in family["artifacts"]}
    relationships = {
        (edge["source_artifact_id"], edge["target_artifact_id"])
        for cluster in family["family"]["clusters"]
        for edge in cluster["evolution"]["directed_edges"]
    }
    observed = [
        (pair["source_artifact_id"], pair["destination_artifact_id"])
        for cluster in scan["clusters"]
        for pair in cluster["pair_observations"]
    ]
    for source, destination in observed:
        if (source, destination) not in relationships or source not in artifact_ids or destination not in artifact_ids:
            raise ValueError(f"{family_name}: scan pair {source}->{destination} is not traceable to a family edge")
    if len(observed) != scan["summary"]["pairs_analyzed"] or len(set(observed)) != len(observed):
        raise ValueError(f"{family_name}: pair count mismatch or repeated source pair")
    return len(observed)


def summarize_cohort(names: Sequence[str], *, database: Path,
                     skilltrace_reports: Path, results: Path,
                     per_stratum: int = 5, seed: int = 580,
                     directed_annotations: Path | None = None,
                     relationship_annotations: Path | None = None,
                     approval_reference: str | None = None) -> dict:
    """Summarize only named families and write cohort/audit provenance.

    Does not regenerate missing reports: run_family must first complete for
    every selected family, possibly over independent notebook sessions.
    """
    selected, stems = _validate_names(names)
    if per_stratum < 1:
        raise ValueError("per_stratum must be positive")
    family_files = [skilltrace_reports / f"{stems[name]}.json" for name in selected]
    scan_files = [results / "scans" / f"{stems[name]}.json" for name in selected]
    missing = [str(path) for path in (*family_files, *scan_files) if not path.is_file()]
    if missing:
        raise FileNotFoundError("Run the missing candidate families before summarizing: " + ", ".join(missing))

    family_reports = [_read_json(path) for path in family_files]
    scans = [_read_json(path) for path in scan_files]
    audit = []
    snapshots = []
    for name, family, scan, family_path, scan_path in zip(
            selected, family_reports, scans, family_files, scan_files):
        if family.get("name") != name or scan.get("candidate_family") != name:
            raise ValueError(f"{name}: stored report has an unexpected family name")
        expected_implementation = implementation_fingerprint()
        if (family.get("implementation_fingerprint") != expected_implementation
                or scan.get("implementation_fingerprint") != expected_implementation):
            raise ValueError(f"{name}: report was built with a different implementation; rerun run_family")
        if not isinstance(family.get("artifacts"), list) or not isinstance(family.get("similarities"), list):
            raise ValueError(f"{name}: SkillTrace report lacks artifacts/similarities; rerun run_family")
        source = [
            {key: item.get(key) for key in (
                "artifact_id", "group_id", "repo_full_name", "path", "file_sha",
                "sibling_file_count", "sibling_content_sha")}
            for item in family["artifacts"]
        ]
        if sorted(source, key=lambda item: item["artifact_id"]) != scan.get("input_artifacts"):
            raise ValueError(f"{name}: scan inputs do not match the SkillTrace report; rerun run_family")
        if family.get("skipped_artifacts") != scan.get("skipped_artifacts"):
            raise ValueError(f"{name}: skipped input records disagree; rerun run_family")
        n_pairs = _verify_pair_sources(family, scan, name)
        snapshots.append({
            "name": name, "family_report": str(family_path), "scan_report": str(scan_path),
            "source_fingerprint": _fingerprint(source),
            "artifacts": source, "skipped_artifacts": scan["skipped_artifacts"],
            "groups": sorted({item["group_id"] for item in source}),
        })
        audit.append({
            "family": name, "artifacts_loaded": len(source),
            "artifacts_skipped": len(scan["skipped_artifacts"]),
            "pairs_analyzed": n_pairs,
            "pairs_incomplete": scan["summary"]["pairs_incomplete"],
            "ambiguous_edges_skipped": scan["summary"]["ambiguous_edges_skipped"],
            "source_fingerprint": _fingerprint(source),
        })

    database = Path(database)
    if not database.is_file():
        raise FileNotFoundError(f"Prepared DuckDB database not found: {database}")
    sample = {
        "sample_status": "approved" if approval_reference else "provisional",
        "approval_reference": approval_reference,
        "dataset": {"path": str(database.resolve()), "size_bytes": database.stat().st_size,
                    "kind": "prepared GitSkills DuckDB", "source": "GitSkills Zenodo record 21875637"},
        "selection": {"unit": "artifact_groupings.name candidate family",
                      "criterion": "exact names in candidate_families (artifact_groupings joined to artifacts)",
                      "invalid_inputs": "retain per-artifact skip reasons; exclude from comparison",
                      "population": "all prepared grouping rows matching each selected name; not manually picked pairs",
                      "upstream_filter": "sql/create_analysis_tables.sql: frontmatter_valid=1, body_chars>50, content/name/description non-NULL, skill name occurs at least twice; each normalized description remains a group",
                      "sibling_fingerprint": "sql/update_artifact_groupings.sql: file entries with available hashes; unknown when composition is incomplete",
                      "sibling_scan_scope": "artifact_siblings.entry_type=file only; directory entries are not executable content",
                      "comparison_scope": "direction-supported family edges; ambiguous relationships reviewed separately"},
        "family_names": selected,
        "similarity_policy": scans[0]["similarity_policy"],
        "active_rules": scans[0]["active_rules"],
        "implementation_fingerprint": scans[0]["implementation_fingerprint"],
        "code_revision": _git_revision(skilltrace_reports.parent.parent.parent),
        "python_version": sys.version.split()[0],
        "scanner_scope": scans[0]["scanner_scope"],
        "edge_selection": scans[0]["edge_selection"],
        "sampling": {"per_stratum": per_stratum, "seed": seed},
        "families": snapshots,
        "totals": {"families": len(selected),
                   "artifacts_loaded": sum(item["artifacts_loaded"] for item in audit),
                   "artifacts_skipped": sum(item["artifacts_skipped"] for item in audit)},
    }
    # Avoid silently changing a validation sample after adjudication starts.
    manifest_path = results / "sample_manifest.json"
    adjudication_dir = results / "review" / "adjudicated"
    if manifest_path.is_file() and adjudication_dir.exists() and any(adjudication_dir.glob("*.csv")):
        old = _read_json(manifest_path)
        if any(old.get(key) != sample.get(key) for key in (
                "family_names", "similarity_policy", "edge_selection", "sampling", "families", "active_rules")):
            raise ValueError("Selected sample changed after adjudication; archive the previous results first")

    summary = summarize(
        scan_files, results / "review", per_stratum=per_stratum, seed=seed,
        family_reports=family_files, annotations=directed_annotations,
        relationship_annotations=relationship_annotations)
    results.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(sample, indent=2) + "\n", encoding="utf-8")
    audit_dir = results / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    with (audit_dir / "processing_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit[0]))
        writer.writeheader()
        writer.writerows(audit)
    with (audit_dir / "skipped_artifacts.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("family", "artifact_id", "repo_full_name", "path", "reason"))
        writer.writeheader()
        writer.writerows({"family": item["name"], **skipped}
                         for item in snapshots for skipped in item["skipped_artifacts"])
    execution = {
        "status": "complete" if sum(item["artifacts_loaded"] for item in audit) > 0 else "incomplete",
        "input_coverage": "partial" if any(item["artifacts_skipped"] for item in audit) else "complete",
        "family_count": len(selected),
        "artifacts_loaded": sum(item["artifacts_loaded"] for item in audit),
        "artifacts_skipped": sum(item["artifacts_skipped"] for item in audit),
        "directed_pairs_analyzed": summary["directed_pairs_analyzed"],
        "pairs_incomplete": sum(item["pairs_incomplete"] for item in audit),
        "validation_status": "awaiting independent review/adjudication" if not directed_annotations and not relationship_annotations else "adjudicated results provided",
        "result_directory": str(results),
    }
    (results / "execution_summary.json").write_text(json.dumps(execution, indent=2) + "\n", encoding="utf-8")
    return execution
