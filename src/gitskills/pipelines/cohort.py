"""Selected-cohort review summaries and reproducibility records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from gitskills.reporting.scan_summary import summarize

from .provenance import (
    check_reports, cohort_manifest, fingerprint, protect_snapshot,
    read_json, validate_names, write_audit,
)


def summarize_cohort(names: Sequence[str], *, database: Path,
                     skilltrace_reports: Path, results: Path,
                     per_stratum: int = 5, seed: int = 580,
                     directed_annotations: Path | None = None,
                     relationship_annotations: Path | None = None,
                     approval_reference: str | None = None) -> dict:
    """Summarize only selected families and preserve source/audit information.

    Generate each family's reports with run_family first (possibly across sessions).
    """
    selected, stems = validate_names(names)
    if per_stratum < 1:
        raise ValueError("per_stratum must be positive")
    family_files = [skilltrace_reports / f"{stems[name]}.json" for name in selected]
    scan_files = [results / "scans" / f"{stems[name]}.json" for name in selected]
    missing = [str(path) for path in (*family_files, *scan_files) if not path.is_file()]
    if missing:
        raise FileNotFoundError("Run the missing candidate families before summarizing: " + ", ".join(missing))

    family_reports = [read_json(path) for path in family_files]
    scans = [read_json(path) for path in scan_files]
    snapshots, audit = [], []
    for name, family, scan, family_path, scan_path in zip(
            selected, family_reports, scans, family_files, scan_files):
        sources, pair_count = check_reports(name, family, scan)
        snapshots.append({
            "name": name, "family_report": str(family_path), "scan_report": str(scan_path),
            "source_fingerprint": fingerprint(sources), "artifacts": sources,
            "skipped_artifacts": scan["skipped_artifacts"],
            "groups": sorted({item["group_id"] for item in sources}),
        })
        audit.append({
            "family": name, "artifacts_loaded": len(sources),
            "artifacts_skipped": len(scan["skipped_artifacts"]),
            "pairs_analyzed": pair_count,
            "pairs_incomplete": scan["summary"]["pairs_incomplete"],
            "ambiguous_edges_skipped": scan["summary"]["ambiguous_edges_skipped"],
            "source_fingerprint": fingerprint(sources),
        })

    sample = cohort_manifest(selected, Path(database), scans, snapshots, audit,
                             skilltrace_reports, per_stratum, seed, approval_reference)
    manifest_path = results / "sample_manifest.json"
    protect_snapshot(manifest_path, sample)

    summary = summarize(
        scan_files, results / "review", per_stratum=per_stratum, seed=seed,
        family_reports=family_files, annotations=directed_annotations,
        relationship_annotations=relationship_annotations,
    )
    results.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(sample, indent=2) + "\n", encoding="utf-8")
    write_audit(results, audit, snapshots)

    execution = {
        "status": "complete" if sum(row["artifacts_loaded"] for row in audit) > 0 else "incomplete",
        "input_coverage": "partial" if any(row["artifacts_skipped"] for row in audit) else "complete",
        "family_count": len(selected),
        "artifacts_loaded": sum(row["artifacts_loaded"] for row in audit),
        "artifacts_skipped": sum(row["artifacts_skipped"] for row in audit),
        "directed_pairs_analyzed": summary["directed_pairs_analyzed"],
        "pairs_incomplete": sum(row["pairs_incomplete"] for row in audit),
        "validation_status": ("awaiting independent review/adjudication"
                              if not directed_annotations and not relationship_annotations
                              else "adjudicated results provided"),
        "result_directory": str(results),
    }
    (results / "execution_summary.json").write_text(
        json.dumps(execution, indent=2) + "\n", encoding="utf-8")
    return execution
