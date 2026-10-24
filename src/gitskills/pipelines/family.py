"""Incremental analysis and security scanning of one candidate family."""

from __future__ import annotations

from pathlib import Path

from gitskills.analysis.family_models import SimilarityPolicy
from gitskills.analysis.family_reporting import analyze_family_report, scan_family_report, source_records
from gitskills.data.families import DuckDBFamilyRepository
from gitskills.data.siblings import DuckDBSiblingRepository
from gitskills.reporting.files import write_json

from .provenance import compatible_family, fingerprint, read_json, validate_names


def run_family(name: str, *, database: Path, skilltrace_reports: Path,
               scans: Path, policy: SimilarityPolicy | None = None,
               edges: str = "all", force_family: bool = False) -> dict:
    """Reuse/refresh one SkillTrace report and produce one current security scan.

    Does not touch other families. The source DuckDB is opened read-only.
    """
    policy = policy or SimilarityPolicy()
    _, stems = validate_names([name])
    family_path = skilltrace_reports / f"{stems[name]}.json"
    scan_path = scans / f"{stems[name]}.json"
    loaded = DuckDBFamilyRepository(database).load_available(name)
    if not loaded.artifacts and not loaded.skipped_artifacts:
        raise ValueError(f"Candidate family not found in prepared DuckDB: {name}")
    records = source_records(loaded)
    skipped = [item.to_dict() for item in loaded.skipped_artifacts]

    existing = None
    if family_path.is_file() and not force_family:
        try:
            existing = read_json(family_path)
        except ValueError:
            pass  # Malformed reports are rebuilt from source.
    refresh = (force_family or existing is None or
               not compatible_family(existing, name, policy, records, skipped))
    # Upgrade a valid older report without rebuilding similarities just to drop
    # the legacy per-report implementation hash.
    legacy_cleanup = False
    if not refresh and "implementation_fingerprint" in existing:
        existing.pop("implementation_fingerprint")
        legacy_cleanup = True
    family_analysis = None
    if refresh:
        family_analysis, family_report = analyze_family_report(name, loaded, policy=policy)
    else:
        family_report = existing

    siblings = DuckDBSiblingRepository(database).load(
        artifact.artifact_id for artifact in loaded.artifacts)
    _, scan_report = scan_family_report(
        name, loaded, siblings, policy=policy, edges=edges,
        family_analysis=family_analysis,
    )
    adjudicated = scans.parent / "review" / "adjudicated"
    if adjudicated.exists() and any(adjudicated.glob("*.csv")):
        old_scan = read_json(scan_path) if scan_path.is_file() else None
        if old_scan is not None:
            old_scan.pop("implementation_fingerprint", None)
        if refresh or old_scan != scan_report:
            raise ValueError(
                f"{name}: completed review exists and reports would change; "
                "archive the existing run before rebuilding it"
            )

    if refresh or legacy_cleanup:
        skilltrace_reports.mkdir(parents=True, exist_ok=True)
        write_json(skilltrace_reports, stems[name], family_report)
    scans.mkdir(parents=True, exist_ok=True)
    write_json(scans, stems[name], scan_report)
    return {
        "family": name, "family_report": str(family_path),
        "family_report_updated": refresh or legacy_cleanup, "scan_report": str(scan_path),
        "artifacts_loaded": len(records), "artifacts_skipped": len(skipped),
        "pairs_analyzed": scan_report["summary"]["pairs_analyzed"],
        "pairs_incomplete": scan_report["summary"]["pairs_incomplete"],
        "source_fingerprint": fingerprint(records),
    }
