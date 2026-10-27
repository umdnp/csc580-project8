"""Standalone summarizer and scan-cache contracts; no DuckDB installation needed."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import pytest

from gitskills.analysis.family_models import Artifact
from gitskills.data.families import FamilyLoad
from gitskills.pipelines import cohort
from gitskills.tools import summarize_cohort as cli


BASE = "Review software changes and document test coverage accurately. " * 18


@pytest.fixture
def sources(monkeypatch, tmp_path):
    database = tmp_path / "prepared.duckdb"
    database.touch()

    class Families:
        def __init__(self, path):
            assert Path(path) == database

        def load_available(self, name):
            if name == "missing":
                return FamilyLoad((), ())
            return FamilyLoad(tuple(
                Artifact(
                    artifact_id=(1 if name == "alpha" else 101) + offset,
                    group_id=(1 if name == "alpha" else 101) + offset,
                    repo_id=offset + 1, name=name, normalized_description="test",
                    file_sha=f"{name}-{offset}",
                    content=BASE + ("\nUse curl https://example.test" if offset == 1 else
                                    "\nCheck security and permissions" if offset == 2 else ""),
                    first_commit_at=f"2026-01-{offset+1:02d}", repo_created_at=None,
                    sibling_file_count=0, sibling_content_sha="empty",
                ) for offset in range(3)
            ), ())

    class Siblings:
        def __init__(self, path):
            assert Path(path) == database

        def load(self, ids):
            return ()

    monkeypatch.setattr(cohort, "DuckDBFamilyRepository", Families)
    monkeypatch.setattr(cohort, "DuckDBSiblingRepository", Siblings)
    return database


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_independent_cohort_writes_cache_and_outputs(sources, tmp_path):
    results = tmp_path / "results"
    outcome = cohort.summarize_cohort(["alpha", "beta"], database=sources, results=results)
    assert outcome["family_count"] == 2
    assert outcome["artifacts_loaded"] == 6
    assert (results / ".scans" / "alpha.json").is_file()
    assert (results / ".scans" / "beta.json").is_file()
    manifest = _json(results / ".scans" / ".metadata" / "scan-manifest.json")
    assert set(manifest["families"]) == {"alpha", "beta"}
    assert manifest["version"] == 1
    assert "implementation_fingerprint" not in _json(results / ".scans" / "alpha.json")
    assert (results / "review" / "directed_pairs.csv").is_file()
    assert (results / "manual-review" / "directed-pairs" / "annotations_template.csv").is_file()
    assert (results / "manual-review" / "relationship-pairs" / "relationship_validation_sample.csv").is_file()
    assert (results / "figures" / "indicator_frequency.svg").is_file()
    assert (results / "audit" / "processing_summary.csv").is_file()
    assert (results / "sample_manifest.json").is_file()


def test_reuses_valid_scans_and_rescan_forces_recomputation(sources, tmp_path, monkeypatch):
    results = tmp_path / "results"
    original = cohort.scan_family_report
    scans = []

    def count(*args, **kwargs):
        scans.append(args[0])
        return original(*args, **kwargs)

    monkeypatch.setattr(cohort, "scan_family_report", count)
    cohort.summarize_cohort(["alpha"], database=sources, results=results)
    first = (results / ".scans" / "alpha.json").read_bytes()
    assert scans == ["alpha"]
    cohort.summarize_cohort(["alpha"], database=sources, results=results)
    assert scans == ["alpha"]
    assert (results / ".scans" / "alpha.json").read_bytes() == first
    cohort.summarize_cohort(["alpha"], database=sources, results=results, rescan=True)
    assert scans == ["alpha", "alpha"]
    assert (results / ".scans" / "alpha.json").read_bytes() == first


def test_stale_manifest_and_altered_file_regenerate(sources, tmp_path, monkeypatch):
    results = tmp_path / "results"
    cohort.summarize_cohort(["alpha"], database=sources, results=results)
    scan_path = results / ".scans" / "alpha.json"
    calls = []
    original = cohort.scan_family_report

    def count(*args, **kwargs):
        calls.append(args[0])
        return original(*args, **kwargs)

    monkeypatch.setattr(cohort, "scan_family_report", count)
    scan_path.write_text("{}", encoding="utf-8")
    cohort.summarize_cohort(["alpha"], database=sources, results=results)
    assert calls == ["alpha"]
    # A configuration change invalidates the cache, but no research algorithm changes.
    cohort.summarize_cohort(["alpha"], database=sources, results=results, edges="primary")
    assert calls == ["alpha", "alpha"]


def test_adopts_independent_scan_family_output(sources, tmp_path, monkeypatch):
    """Cache manifest is optional when a standalone scan meets current contracts."""
    from gitskills.analysis.family_reporting import scan_family_report
    from gitskills.analysis.family_models import SimilarityPolicy
    from gitskills.reporting.files import write_json

    results = tmp_path / "results"
    loaded = cohort.DuckDBFamilyRepository(sources).load_available("alpha")
    _, report = scan_family_report("alpha", loaded, policy=SimilarityPolicy(), edges="all")
    folder = results / ".scans"
    folder.mkdir(parents=True)
    write_json(folder, "alpha", report)
    def forbidden(*args, **kwargs):
        raise AssertionError("compatible standalone scan must be reused")
    monkeypatch.setattr(cohort, "scan_family_report", forbidden)
    cohort.summarize_cohort(["alpha"], database=sources, results=results)
    assert "alpha" in _json(folder / ".metadata" / "scan-manifest.json")["families"]


def test_review_snapshot_protected_against_changed_families(sources, tmp_path):
    results = tmp_path / "results"
    cohort.summarize_cohort(["alpha"], database=sources, results=results)
    folder = results / "manual-review" / "adjudicated"
    folder.mkdir(parents=True)
    (folder / "completed.csv").write_text("approved", encoding="utf-8")
    with pytest.raises(ValueError, match="archive the previous results"):
        cohort.summarize_cohort(["alpha", "beta"], database=sources, results=results)


def test_command_line_can_run_one_or_multiple_families(sources, tmp_path, capsys):
    results = tmp_path / "results"
    assert cli.main(["alpha", "--db", str(sources), "--output", str(results)]) == 0
    assert "Families: 1" in capsys.readouterr().out
    families = tmp_path / "families.txt"
    families.write_text("# tests\nalpha\nbeta\n", encoding="utf-8")
    assert cli.main(["--input", str(families), "--db", str(sources),
                     "--output", str(results), "--rescan"]) == 0
    assert (results / ".scans" / "beta.json").is_file()


def test_seeded_relationship_validation_stable_across_family_order(sources, tmp_path):
    first = tmp_path / "a"
    second = tmp_path / "b"
    cohort.summarize_cohort(["alpha", "beta"], database=sources, results=first)
    cohort.summarize_cohort(["beta", "alpha"], database=sources, results=second)
    path = Path("manual-review/relationship-pairs/relationship_validation_sample.csv")
    assert (first / path).read_bytes() == (second / path).read_bytes()


def test_review_metrics_use_saved_samples_without_loading_or_scanning(sources, tmp_path, monkeypatch):
    results = tmp_path / "results"
    cohort.summarize_cohort(["alpha", "beta"], database=sources, results=results)
    manual = results / "manual-review"
    adjudicated = manual / "adjudicated"
    adjudicated.mkdir()
    directed = adjudicated / "directed.csv"
    related = adjudicated / "relationships.csv"

    directed_rows = list(csv.DictReader((manual / "directed-pairs" / "annotations_template.csv").open()))
    relationship_rows = list(csv.DictReader((manual / "relationship-pairs" / "relationship_annotations_template.csv").open()))
    assert directed_rows and relationship_rows
    directed_rows[0].update({
        "reviewer": "team", "review_phase": "adjudicated", "review_status": "complete",
        "review_date": "2026-10-24", "manual_relatedness": "related",
        "direction_basis_review": "supported", "scanner_rule_review": "correct",
        "manual_change_review": "correct", "sibling_coverage_review": "complete",
        "indicator_review_scope": "all_assessed",
    })
    relationship_rows[0].update({
        "reviewer": "team", "review_phase": "adjudicated", "review_status": "complete",
        "review_date": "2026-10-24", "manual_relatedness": "related",
        "direction_basis_review": "uncertain",
    })
    for path, rows in ((directed, directed_rows), (related, relationship_rows)):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    original_scan = (results / ".scans" / "alpha.json").read_bytes()
    original_sample = (manual / "relationship-pairs" / "relationship_validation_sample.csv").read_bytes()
    original_manifest = (results / "sample_manifest.json").read_bytes()

    def forbid(*args, **kwargs):
        raise AssertionError("annotation processing must not load or reanalyze families")

    monkeypatch.setattr(cohort, "FamilyAnalyzer", forbid)
    monkeypatch.setattr(cohort, "DuckDBFamilyRepository", forbid)
    monkeypatch.setattr(cohort, "scan_family_report", forbid)
    outcome = cohort.summarize_cohort(
        ["alpha", "beta"], database=sources, results=results,
        directed_annotations=directed, relationship_annotations=related,
    )
    assert outcome["validation_status"] == "adjudicated results provided"
    summary = _json(results / "review" / "summary.json")
    assert summary["manual_validation"]["reviewed_pairs"] == 1
    assert summary["relationship_validation"]["reviewed_pairs"] == 1
    assert (results / ".scans" / "alpha.json").read_bytes() == original_scan
    assert (manual / "relationship-pairs" / "relationship_validation_sample.csv").read_bytes() == original_sample
    assert (results / "sample_manifest.json").read_bytes() == original_manifest
    assert "reviewed_pairs" in str(summary)
    # Repeat reviews from persisted evidence, with the same metrics.
    cohort.summarize_cohort(["alpha", "beta"], database=sources, results=results,
                            directed_annotations=directed, relationship_annotations=related)
    assert _json(results / "review" / "summary.json") == summary


def test_review_fast_path_fails_closed_if_samples_or_inputs_change(sources, tmp_path, monkeypatch):
    results = tmp_path / "results"
    cohort.summarize_cohort(["alpha"], database=sources, results=results)
    annotation = results / "manual-review" / "adjudicated" / "directed.csv"
    annotation.parent.mkdir()
    annotation.write_bytes((results / "manual-review" / "directed-pairs" /
                            "annotations_template.csv").read_bytes())
    relationship = results / "manual-review" / "relationship-pairs" / "relationship_validation_sample.csv"
    original = relationship.read_bytes()
    relationship.write_bytes(original + b"\n")
    def forbid(*args, **kwargs):
        raise AssertionError("should not silently fall back to an expensive recompute")
    monkeypatch.setattr(cohort, "FamilyAnalyzer", forbid)
    with pytest.raises(ValueError, match="saved research summary or validation samples have changed"):
        cohort.summarize_cohort(["alpha"], database=sources, results=results,
                                directed_annotations=annotation)
    relationship.write_bytes(original)
    with pytest.raises(ValueError, match="cohort sources, settings, or implementation do not match"):
        cohort.summarize_cohort(["alpha"], database=sources, results=results,
                                directed_annotations=annotation, seed=581)
    with pytest.raises(ValueError, match="cohort sources, settings, or implementation do not match"):
        cohort.summarize_cohort(["alpha", "beta"], database=sources, results=results,
                                directed_annotations=annotation)


def test_review_fast_path_rejects_unsampled_rows_and_keeps_summary(sources, tmp_path):
    results = tmp_path / "results"
    cohort.summarize_cohort(["alpha"], database=sources, results=results)
    annotation = results / "manual-review" / "adjudicated" / "directed.csv"
    annotation.parent.mkdir()
    with (results / "manual-review" / "directed-pairs" / "annotations_template.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    rows[0].update({"review_status": "complete", "review_phase": "adjudicated", "reviewer": "team",
                    "review_date": "2026-10-24", "base_artifact_id": "999999"})
    with annotation.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    old_summary = (results / "review" / "summary.json").read_bytes()
    with pytest.raises(ValueError, match="Unknown or unsampled reviewed pair"):
        cohort.summarize_cohort(["alpha"], database=sources, results=results,
                                directed_annotations=annotation)
    assert (results / "review" / "summary.json").read_bytes() == old_summary


def test_legacy_manifest_migrates_to_metadata(sources, tmp_path, monkeypatch):
    results = tmp_path / "results"
    cohort.summarize_cohort(["alpha"], database=sources, results=results)
    folder = results / ".scans"
    current = folder / ".metadata" / "scan-manifest.json"
    legacy = folder / ".scan_manifest.json"
    legacy.write_bytes(current.read_bytes())
    current.unlink()
    def forbid(*args, **kwargs):
        raise AssertionError("valid cached scan should not be regenerated")
    monkeypatch.setattr(cohort, "scan_family_report", forbid)
    cohort.summarize_cohort(["alpha"], database=sources, results=results)
    assert current.is_file()
    assert not legacy.exists()


def test_rescan_with_annotations_still_runs_scanner(sources, tmp_path, monkeypatch):
    results = tmp_path / "results"
    cohort.summarize_cohort(["alpha"], database=sources, results=results)
    annotation = results / "manual-review" / "adjudicated" / "directed.csv"
    annotation.parent.mkdir()
    annotation.write_bytes((results / "manual-review" / "directed-pairs" /
                            "annotations_template.csv").read_bytes())
    original = cohort.scan_family_report
    calls = []
    def counted(*args, **kwargs):
        calls.append(args[0])
        return original(*args, **kwargs)
    monkeypatch.setattr(cohort, "scan_family_report", counted)
    cohort.summarize_cohort(["alpha"], database=sources, results=results,
                            directed_annotations=annotation, rescan=True)
    assert calls == ["alpha"]
    assert "manual_validation" in _json(results / "review" / "summary.json")


def test_saved_review_rejects_outdated_cache_and_missing_initial_results(sources, tmp_path):
    results = tmp_path / "results"
    annotation = tmp_path / "reviewed.csv"
    annotation.write_text("review_status\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Cannot reuse saved validation evidence"):
        cohort.summarize_cohort(["alpha"], database=sources, results=results,
                                directed_annotations=annotation)
    cohort.summarize_cohort(["alpha"], database=sources, results=results)
    manifest = results / ".scans" / ".metadata" / "scan-manifest.json"
    manifest.unlink()
    with pytest.raises(ValueError, match="scan-manifest.json"):
        cohort.summarize_cohort(["alpha"], database=sources, results=results,
                                directed_annotations=annotation)
