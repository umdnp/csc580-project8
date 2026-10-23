"""Incremental pipeline contract without requiring the large GitSkills database."""

import csv
import json
from pathlib import Path

import pytest

from gitskills.analysis.family_models import Artifact, SimilarityPolicy
from gitskills.data.families import FamilyLoad, SkippedArtifact
from gitskills.pipeline import run_family, summarize_cohort


BASE = ("Read and document the available source project configuration. " * 18)


def make_artifact(name, artifact_id, content):
    return Artifact(
        artifact_id=artifact_id, group_id=artifact_id // 100,
        repo_id=artifact_id, name=name, normalized_description="example",
        file_sha=f"sha-{artifact_id}", content=content,
        first_commit_at=f"2026-01-{artifact_id % 20 + 1:02d}", repo_created_at=None,
        repo_full_name=f"test/repo-{artifact_id}", path=".agents/skills/SKILL.md",
        sibling_file_count=0, sibling_content_sha="empty",
    )


@pytest.fixture
def repositories(monkeypatch, tmp_path):
    from gitskills import pipeline

    class FakeFamilies:
        def __init__(self, database):
            pass

        def load_available(self, name):
            if name not in {"alpha", "beta"}:
                return FamilyLoad((), ())
            offset = 100 if name == "alpha" else 200
            return FamilyLoad((
                make_artifact(name, offset + 1, BASE),
                make_artifact(name, offset + 2, BASE + "\nUse curl https://example.org/a.\n"),
            ), (SkippedArtifact(offset + 3, "test/empty", "SKILL.md", "missing_content"),))

    class FakeSiblings:
        def __init__(self, database):
            pass

        def load(self, ids):
            return ()

    monkeypatch.setattr(pipeline, "DuckDBFamilyRepository", FakeFamilies)
    monkeypatch.setattr(pipeline, "DuckDBSiblingRepository", FakeSiblings)
    db = tmp_path / "prepared.duckdb"
    db.touch()
    return db, tmp_path / "apps" / "skilltrace" / "reports", tmp_path / "results"


def test_incremental_cohort_filters_old_scans_and_preserves_sources(repositories):
    db, reports, results = repositories
    for name in ("alpha", "beta"):
        outcome = run_family(name, database=db, skilltrace_reports=reports, scans=results / "scans")
        assert outcome["artifacts_loaded"] == 2
        assert outcome["artifacts_skipped"] == 1
        assert json.loads((reports / f"{name}.json").read_text())["artifacts"]

    first = summarize_cohort(["alpha"], database=db, skilltrace_reports=reports, results=results)
    assert first["family_count"] == 1
    assert first["artifacts_skipped"] == 1
    assert first["status"] == "complete"
    assert (results / "review" / "relationship_validation_annotations_template.csv").exists()
    assert (results / "review" / "validation_annotations_template.csv").exists()
    cohort = json.loads((results / "sample_manifest.json").read_text())
    assert cohort["family_names"] == ["alpha"]
    assert len(cohort["families"][0]["artifacts"]) == 2
    with (results / "audit" / "skipped_artifacts.csv").open() as handle:
        exclusions = list(csv.DictReader(handle))
    assert [(row["artifact_id"], row["reason"]) for row in exclusions] == [("103", "missing_content")]

    second = summarize_cohort(["alpha", "beta"], database=db, skilltrace_reports=reports,
                              results=results)
    assert second["family_count"] == 2
    assert second["artifacts_loaded"] == 4


def test_old_compact_family_report_is_refreshed(repositories):
    db, reports, results = repositories
    run_family("alpha", database=db, skilltrace_reports=reports, scans=results / "scans")
    path = reports / "alpha.json"
    old = json.loads(path.read_text())
    old.pop("similarities")
    old.pop("artifacts")
    path.write_text(json.dumps(old))
    refreshed = run_family("alpha", database=db, skilltrace_reports=reports,
                           scans=results / "scans")
    assert refreshed["family_report_updated"] is True
    assert len(json.loads(path.read_text())["artifacts"]) == 2
    again = run_family("alpha", database=db, skilltrace_reports=reports,
                       scans=results / "scans")
    assert again["family_report_updated"] is False


def test_missing_and_mismatched_source_reports_are_rejected(repositories):
    db, reports, results = repositories
    with pytest.raises(FileNotFoundError, match="missing candidate families"):
        summarize_cohort(["alpha"], database=db, skilltrace_reports=reports, results=results)
    with pytest.raises(ValueError, match="not found"):
        run_family("missing", database=db, skilltrace_reports=reports, scans=results / "scans")
    run_family("alpha", database=db, skilltrace_reports=reports, scans=results / "scans")
    path = results / "scans" / "alpha.json"
    report = json.loads(path.read_text())
    report["input_artifacts"][0]["file_sha"] = "unrelated"
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="do not match"):
        summarize_cohort(["alpha"], database=db, skilltrace_reports=reports, results=results)


def test_default_family_output_supplies_relationship_analysis(repositories):
    db, reports, results = repositories
    run_family("alpha", database=db, skilltrace_reports=reports, scans=results / "scans")
    report = json.loads((reports / "alpha.json").read_text())
    assert isinstance(report["similarities"], list)
    assert "artifacts" in report
    assert "groups" not in report  # Optional verbose diagnostics.
    assert "directed_edges" in report["family"]["clusters"][0]["evolution"]
    assert report["skipped_artifacts"][0]["reason"] == "missing_content"


def test_reviewer_snapshot_is_not_silently_replaced(repositories):
    db, reports, results = repositories
    for name in ("alpha", "beta"):
        run_family(name, database=db, skilltrace_reports=reports, scans=results / "scans")
    summarize_cohort(["alpha"], database=db, skilltrace_reports=reports, results=results)
    adjudicated = results / "review" / "adjudicated"
    adjudicated.mkdir()
    (adjudicated / "directed.csv").write_text("original review", encoding="utf-8")
    with pytest.raises(ValueError, match="archive the previous results"):
        summarize_cohort(["alpha", "beta"], database=db,
                         skilltrace_reports=reports, results=results)


def test_all_invalid_inputs_reported_but_not_marked_negative():
    from gitskills.analysis.family_reporting import analyze_family_report, scan_family_report

    loaded = FamilyLoad((), (SkippedArtifact(42, "test/repo", "SKILL.md", "empty_content"),))
    analyzed, family_report = analyze_family_report("unavailable", loaded)
    scanned, scan_report = scan_family_report("unavailable", loaded, edges="all")
    assert family_report["summary"]["artifact_count"] == 0
    assert family_report["skipped_artifacts"][0]["reason"] == "empty_content"
    assert scan_report["input_summary"]["incomplete"] is True
    assert scan_report["summary"]["pairs_analyzed"] == 0
    assert scanned.pairs_analyzed == 0


def test_do_not_replace_scans_after_adjudication(repositories):
    db, reports, results = repositories
    run_family("alpha", database=db, skilltrace_reports=reports, scans=results / "scans")
    adjudicated = results / "review" / "adjudicated"
    adjudicated.mkdir(parents=True)
    (adjudicated / "directed.csv").write_text("completed independent review", encoding="utf-8")
    # An identical rerun is safe.
    run_family("alpha", database=db, skilltrace_reports=reports, scans=results / "scans")
    # Different scan inputs cannot overwrite a reviewed snapshot.
    with pytest.raises(ValueError, match="archive the existing run"):
        run_family("alpha", database=db, skilltrace_reports=reports,
                   scans=results / "scans", edges="primary")


def test_stale_analysis_implementation_is_refreshed(repositories):
    db, reports, results = repositories
    run_family("alpha", database=db, skilltrace_reports=reports, scans=results / "scans")
    family_path = reports / "alpha.json"
    outdated = json.loads(family_path.read_text())
    outdated["implementation_fingerprint"] = "old-version"
    family_path.write_text(json.dumps(outdated))
    refreshed = run_family("alpha", database=db, skilltrace_reports=reports,
                           scans=results / "scans")
    assert refreshed["family_report_updated"] is True
    assert json.loads(family_path.read_text())["implementation_fingerprint"] != "old-version"
