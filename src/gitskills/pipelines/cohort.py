"""Independent cohort analysis, reusable scan cache, and research audit records."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Callable, Sequence

from gitskills.analysis.family_models import SimilarityPolicy
from gitskills.analysis.family import FamilyAnalyzer
from gitskills.analysis.family_reporting import analyze_family_report, scan_family_report, source_records
from gitskills.analysis.family_risk import FamilyRiskAnalyzer
from gitskills.data.families import DuckDBFamilyRepository
from gitskills.data.siblings import DuckDBSiblingRepository
from gitskills.reporting.cohort_summary import (
    RelationshipSampler, ResearchInputError, _read_report, _rows, _sample,
    apply_adjudications, summarize,
)

from .provenance import (
    cohort_manifest, fingerprint, implementation_fingerprint, protect_snapshot,
    read_json, validate_names, write_audit,
)

_CACHE_VERSION = 1


def _atomic_json(path: Path, payload: dict) -> None:
    """Replace a file only after its complete JSON has been written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".pending-", suffix=".json", delete=False) as handle:
            temp_path = Path(handle.name)
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _database_stamp(path: Path) -> dict:
    stats = path.stat()
    return {"path": str(path.resolve()), "size_bytes": stats.st_size,
            "mtime_ns": stats.st_mtime_ns}


def _scan_matches(scan: dict, name: str, records: list[dict], skipped: list[dict],
                  policy: SimilarityPolicy, edges: str, active_rules: list[dict]) -> bool:
    if (scan.get("candidate_family") != name or scan.get("edge_selection") != edges
            or scan.get("similarity_policy") != policy.to_dict()
            or scan.get("active_rules") != active_rules
            or scan.get("scanner_scope") != "skill-body-and-changed-siblings"
            or scan.get("input_artifacts") != records
            or scan.get("skipped_artifacts") != skipped):
        return False
    try:
        _read_report(scan)
        _rows(scan)  # Validate recorded directed pairs and aggregate counts.
    except (KeyError, TypeError, ValueError, ResearchInputError):
        return False
    return True


def _cached_scan(path: Path, manifest_entry: dict | None, *, name: str,
                 records: list[dict], skipped: list[dict], policy: SimilarityPolicy,
                 edges: str, active_rules: list[dict], db_stamp: dict,
                 implementation: str) -> dict | None:
    if not path.is_file():
        return None
    if manifest_entry is not None:
        expected = {
            "filename": path.name, "source_fingerprint": fingerprint(records),
            "skipped_fingerprint": fingerprint(skipped), "database": db_stamp,
            "implementation_fingerprint": implementation,
            "policy": policy.to_dict(), "edges": edges, "active_rules": active_rules,
        }
        if any(manifest_entry.get(key) != value for key, value in expected.items()):
            return None
        if manifest_entry.get("sha256") != _file_sha(path):
            return None
    try:
        scan = read_json(path)
    except ValueError:
        return None
    return scan if _scan_matches(scan, name, records, skipped, policy, edges, active_rules) else None


def _verify_lineage(analysis, scan: dict) -> None:
    """Ensure every scanned pair corresponds to the inferred family graph."""
    relationships = {}
    for cluster in analysis.family.clusters:
        for edge in cluster.evolution.related_edges:
            relationships[(cluster.number, edge.source_artifact_id, edge.target_artifact_id)] = "additional"
        for edge in cluster.evolution.directed_edges:
            relationships[(cluster.number, edge.source_artifact_id, edge.target_artifact_id)] = "primary"
    observed = set()
    for cluster in scan["clusters"]:
        for pair in cluster["pair_observations"]:
            key = (cluster["cluster"], pair["source_artifact_id"], pair["destination_artifact_id"])
            kind = relationships.get(key)
            if (kind is None or kind != pair.get("edge_type") or
                    (scan["edge_selection"] == "primary" and kind != "primary") or key in observed):
                raise ResearchInputError(f"{analysis.name}: scan pair is not traceable to inferred lineage: {key}")
            observed.add(key)
    if len(observed) != scan["summary"]["pairs_analyzed"]:
        raise ResearchInputError(f"{analysis.name}: scanned pair count does not match inferred lineage")



def _entry(path: Path, records: list[dict], skipped: list[dict], stamp: dict,
           implementation: str, policy: SimilarityPolicy, edges: str,
           active_rules: list[dict]) -> dict:
    return {
        "filename": path.name, "sha256": _file_sha(path),
        "source_fingerprint": fingerprint(records), "skipped_fingerprint": fingerprint(skipped),
        "database": stamp, "implementation_fingerprint": implementation,
        "policy": policy.to_dict(), "edges": edges, "active_rules": active_rules,
    }


def _review_exists(results: Path) -> bool:
    return any(folder.exists() and any(folder.glob("*.csv"))
               for folder in (results / "manual-review" / "adjudicated",
                              results / "review" / "adjudicated"))


def _research_fingerprint() -> str:
    """Fingerprint the orchestration and summarization logic used for this cohort."""
    digest = hashlib.sha256()
    for path in (Path(__file__), Path(__file__).resolve().parents[1] / "reporting" / "cohort_summary.py"):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _summary_fingerprint(summary: dict) -> str:
    """Ignore adjudication metrics, which legitimately change after manual review."""
    return fingerprint({key: value for key, value in summary.items()
                        if key not in ("manual_validation", "relationship_validation")})


def _sample_checksums(results: Path) -> dict:
    paths = ("manual-review/directed-pairs/validation_sample.csv",
             "manual-review/relationship-pairs/relationship_validation_sample.csv")
    return {name: _file_sha(results / name) for name in paths}


def _apply_saved_reviews(*, selected: list[str], database: Path, results: Path,
                         policy: SimilarityPolicy, edges: str, per_stratum: int,
                         seed: int, directed_annotations: Path | None,
                         relationship_annotations: Path | None, active_rules: list[dict],
                         stamp: dict, implementation: str,
                         approval_reference: str | None) -> dict:
    """Verify persisted cohort evidence before applying manual-review metrics."""
    def invalid(reason: str):
        raise ValueError(f"Cannot reuse saved validation evidence: {reason}. "
                         "Archive the previous results and generate a new cohort "
                         "without annotations if the inputs have changed")

    manifest_path = results / "sample_manifest.json"
    scan_manifest_path = results / ".scans" / ".metadata" / "scan-manifest.json"
    execution_path = results / "execution_summary.json"
    try:
        saved = read_json(manifest_path)
        scan_manifest = read_json(scan_manifest_path)
        prior = read_json(execution_path)
        summary = read_json(results / "review" / "summary.json")
    except ValueError as exc:
        invalid(str(exc))
    if (sorted(saved.get("family_names", [])) != sorted(selected) or
            saved.get("dataset", {}).get("path") != str(database.resolve()) or
            saved.get("dataset", {}).get("size_bytes") != stamp["size_bytes"] or
            saved.get("similarity_policy") != policy.to_dict() or
            saved.get("edge_selection") != edges or
            saved.get("active_rules") != active_rules or
            saved.get("implementation_fingerprint") != implementation or
            saved.get("cohort_implementation_fingerprint") != _research_fingerprint() or
            saved.get("sampling", {}).get("seed") != seed or
            saved.get("sampling", {}).get("per_stratum") != per_stratum or
            (approval_reference is not None and saved.get("approval_reference") != approval_reference)):
        invalid("cohort sources, settings, or implementation do not match")

    entries = scan_manifest.get("families", {})
    if scan_manifest.get("version") != _CACHE_VERSION or not isinstance(entries, dict):
        invalid("scan cache manifest is missing or incompatible")
    snapshots = {entry["name"]: entry for entry in saved.get("families", [])}
    if set(snapshots) != set(selected):
        invalid("cohort family source snapshots are incomplete")
    for name in selected:
        entry = entries.get(name, {})
        source = snapshots[name]
        filename = entry.get("filename")
        if not isinstance(filename, str) or Path(filename).name != filename:
            invalid(f"scan cache filename for {name} is invalid")
        scan_file = results / ".scans" / filename
        if (not isinstance(source.get("scan_report"), str) or
                Path(source["scan_report"]).resolve() != scan_file.resolve() or
                entry.get("database") != stamp or
                entry.get("implementation_fingerprint") != implementation or
                entry.get("policy") != policy.to_dict() or
                entry.get("edges") != edges or
                entry.get("active_rules") != active_rules or
                entry.get("source_fingerprint") != source.get("source_fingerprint") or
                entry.get("source_fingerprint") != fingerprint(source.get("artifacts", [])) or
                entry.get("skipped_fingerprint") != fingerprint(source.get("skipped_artifacts", [])) or
                not scan_file.is_file() or entry.get("sha256") != _file_sha(scan_file)):
            invalid(f"scan cache for {name} is stale or inconsistent")

    if saved.get("validation_sample_checksums") is None or saved.get("review_summary_fingerprint") is None:
        invalid("saved evidence predates validation caching")
    try:
        hashes = _sample_checksums(results)
    except OSError as exc:
        invalid(f"validation sample is missing: {exc}")
    if (hashes != saved["validation_sample_checksums"] or
            saved["review_summary_fingerprint"] != _summary_fingerprint(summary) or
            summary.get("similarity_policy") != policy.to_dict() or
            summary.get("edge_selection") != edges or
            summary.get("family_count") != len(selected) or
            prior.get("family_count") != len(selected) or
            prior.get("directed_pairs_analyzed") != summary.get("directed_pairs_analyzed")):
        invalid("saved research summary or validation samples have changed")

    # Validate both supplied annotation files before writing either result.
    updated = apply_adjudications(
        results, directed_annotations=directed_annotations,
        relationship_annotations=relationship_annotations,
    )
    _atomic_json(results / "review" / "summary.json", updated)
    prior["validation_status"] = "adjudicated results provided"
    _atomic_json(execution_path, prior)
    return prior


def summarize_cohort(names: Sequence[str], *, database: Path, results: Path,
                     skilltrace_reports: Path | None = None,
                     policy: SimilarityPolicy | None = None, edges: str = "all",
                     rescan: bool = False, per_stratum: int | None = 5, seed: int = 580,
                     directed_annotations: Path | None = None,
                     relationship_annotations: Path | None = None,
                     approval_reference: str | None = None,
                     progress: Callable[[str], None] | None = None) -> dict:
    """Analyze selected families without requiring saved family or scan reports.

    Reuse valid ``results/.scans/<family>.json`` files. Complete similarity
    analyses remain in memory only for relationship validation. A normal scan
    can be produced independently by scan_family with the same configuration.
    """
    selected, stems = validate_names(names)
    database, results = Path(database), Path(results)
    if not database.is_file():
        raise FileNotFoundError(f"Prepared DuckDB database not found: {database}")
    if edges not in ("primary", "all"):
        raise ValueError("edges must be primary or all")
    if per_stratum is not None and per_stratum < 1:
        raise ValueError("per_stratum must be positive")
    if (directed_annotations or relationship_annotations) and per_stratum is None:
        raise ValueError("Review annotations require --per-stratum")
    policy = policy or SimilarityPolicy()
    stamp, implementation = _database_stamp(database), implementation_fingerprint()
    active_rules = [rule.to_dict() for rule in FamilyRiskAnalyzer(policy=policy, edges=edges).active_rules]
    folder = results / ".scans"
    cache_manifest = folder / ".metadata" / "scan-manifest.json"
    legacy_manifest = folder / ".scan_manifest.json"
    if (directed_annotations or relationship_annotations) and not rescan:
        if progress is not None:
            progress("Verifying saved cohort and updating adjudication metrics")
        return _apply_saved_reviews(
            selected=selected, database=database, results=results, policy=policy,
            edges=edges, per_stratum=per_stratum, seed=seed,
            directed_annotations=directed_annotations,
            relationship_annotations=relationship_annotations,
            active_rules=active_rules, stamp=stamp, implementation=implementation,
            approval_reference=approval_reference,
        )
    try:
        manifest_source = cache_manifest if cache_manifest.is_file() else legacy_manifest
        stored = read_json(manifest_source) if manifest_source.is_file() else {}
    except ValueError:
        stored = {}
    entries = dict(stored.get("families", {})) if stored.get("version") == _CACHE_VERSION else {}
    if _review_exists(results) and (results / "sample_manifest.json").is_file():
        previous = read_json(results / "sample_manifest.json")
        expected_samples = previous.get("validation_sample_checksums")
        if expected_samples is not None:
            try:
                if expected_samples != _sample_checksums(results):
                    raise ValueError("Saved validation samples changed after adjudication; "
                                     "archive the previous results first")
            except OSError as exc:
                raise ValueError("Saved validation sample missing after adjudication; "
                                 "archive the previous results first") from exc
    if legacy_manifest.is_file() and not cache_manifest.is_file() and stored.get("version") == _CACHE_VERSION:
        _atomic_json(cache_manifest, stored)
        legacy_manifest.unlink()
    family_repository = DuckDBFamilyRepository(database)
    sibling_repository = DuckDBSiblingRepository(database)
    snapshots, audit, scans = [], [], []
    sampler = RelationshipSampler(per_stratum, seed) if per_stratum is not None else None
    # Sorting means a different order in --input cannot change seeded review selections.
    for index, name in enumerate(sorted(selected), 1):
        if progress is not None:
            progress(f"[{index}/{len(selected)}] {name}: loading source artifacts")
        loaded = family_repository.load_available(name)
        if not loaded.artifacts and not loaded.skipped_artifacts:
            raise ValueError(f"Candidate family not found: {name}")
        records = source_records(loaded)
        skipped = [item.to_dict() for item in loaded.skipped_artifacts]
        path = folder / f"{stems[name]}.json"
        cached = None if rescan else _cached_scan(
            path, entries.get(name), name=name, records=records, skipped=skipped,
            policy=policy, edges=edges, active_rules=active_rules,
            db_stamp=stamp, implementation=implementation,
        )
        # Recalculate similarities only when needed for relationship validation
        # or for a missing/stale/forced security scan; never serialize verbose JSON.
        family_analysis = None
        if sampler is not None or cached is None:
            if progress is not None:
                progress(f"[{index}/{len(selected)}] {name}: computing similarities")
            if loaded.artifacts:
                family_analysis = FamilyAnalyzer(policy).analyze(loaded.artifacts)
            else:
                family_analysis, _ = analyze_family_report(name, loaded, policy=policy)
        if sampler is not None:
            sampler.add_family(family_analysis)
        if cached is None:
            if progress is not None:
                progress(f"[{index}/{len(selected)}] {name}: scanning directed edges")
            siblings = sibling_repository.load(artifact.artifact_id for artifact in loaded.artifacts)
            _, scan = scan_family_report(name, loaded, siblings, policy=policy,
                                         edges=edges, family_analysis=family_analysis)
            if family_analysis is not None:
                _verify_lineage(family_analysis, scan)
            if _review_exists(results) and path.is_file():
                if read_json(path) != scan:
                    raise ValueError(f"{name}: completed review exists and scans would change; "
                                     "archive the previous results first")
            _atomic_json(path, scan)
            entries[name] = _entry(path, records, skipped, stamp, implementation,
                                   policy, edges, active_rules)
            _atomic_json(cache_manifest, {"version": _CACHE_VERSION, "families": entries})
        else:
            if progress is not None:
                progress(f"[{index}/{len(selected)}] {name}: reusing compatible scan")
            scan = cached
            if name not in entries:
                entries[name] = _entry(path, records, skipped, stamp, implementation,
                                       policy, edges, active_rules)
                _atomic_json(cache_manifest, {"version": _CACHE_VERSION, "families": entries})
        if cached is not None and family_analysis is not None:
            _verify_lineage(family_analysis, scan)
        _rows(scan)  # Reject internally inconsistent results before research outputs.
        scans.append(scan)
        snapshots.append({
            "name": name, "scan_report": str(path),
            "source_fingerprint": fingerprint(records), "artifacts": records,
            "skipped_artifacts": skipped,
            "groups": sorted({item["group_id"] for item in records}),
        })
        audit.append({
            "family": name, "artifacts_loaded": len(records),
            "artifacts_skipped": len(skipped),
            "pairs_analyzed": scan["summary"]["pairs_analyzed"],
            "pairs_incomplete": scan["summary"]["pairs_incomplete"],
            "ambiguous_edges_skipped": scan["summary"]["ambiguous_edges_skipped"],
            "source_fingerprint": fingerprint(records),
        })
        del family_analysis, loaded
        if progress is not None:
            progress(f"[{index}/{len(selected)}] {name}: complete")

    # Reorder source metadata as requested; the sampling population is independent
    # of this display order.
    by_name = {row["name"]: (row, audit[index], scans[index])
               for index, row in enumerate(snapshots)}
    snapshots = [by_name[name][0] for name in selected]
    audit = [by_name[name][1] for name in selected]
    scans = [by_name[name][2] for name in selected]
    selected_relationships = sampler.selected() if sampler is not None else None
    sample = cohort_manifest(selected, database, scans, snapshots, audit,
                             Path(__file__).resolve().parents[3], per_stratum, seed,
                             approval_reference)
    sample["cohort_implementation_fingerprint"] = _research_fingerprint()
    if per_stratum is not None:
        rows = sorted((item for scan in scans for item in _rows(scan)),
                      key=lambda row: (row["family"], row["cluster"], row["base_artifact_id"],
                                       row["derived_artifact_id"]))
        # Prevent silent replacement of independently adjudicated sampled pairs.
        sample["review_sample_fingerprint"] = fingerprint({
            "directed": _sample(rows, per_stratum, seed),
            "relationships": selected_relationships,
        })
    protect_snapshot(results / "sample_manifest.json", sample)
    summary = summarize(
        scans, results / "review", per_stratum=per_stratum, seed=seed,
        relationship_selected=selected_relationships,
        manual_review=results / "manual-review", figures=results / "figures",
        annotations=directed_annotations,
        relationship_annotations=relationship_annotations,
    )
    results.mkdir(parents=True, exist_ok=True)
    if per_stratum is not None:
        sample["validation_sample_checksums"] = _sample_checksums(results)
    sample["review_summary_fingerprint"] = _summary_fingerprint(summary)
    _atomic_json(results / "sample_manifest.json", sample)
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
    (results / "execution_summary.json").write_text(json.dumps(execution, indent=2) + "\n", encoding="utf-8")
    return execution
