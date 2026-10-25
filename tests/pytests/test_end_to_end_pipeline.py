"""Incremental pipeline contract without requiring the large GitSkills database."""

import csv
from hashlib import sha1, sha256
import json
from pathlib import Path

import pytest
import duckdb

from gitskills.analysis.family_models import Artifact, SimilarityPolicy
from gitskills.data.families import FamilyLoad, SkippedArtifact
from gitskills.pipelines.family import run_family
from gitskills.pipelines.cohort import summarize_cohort


BASE = ("Read and document the available source project configuration. " * 18)


@pytest.mark.parametrize("missing_sibling_content", [False, True])
def test_prepared_duckdb_flows_through_real_loaders_scanning_and_saved_reports(tmp_path, missing_sibling_content):
    """No repository mocks: exercise the prepared-table-to-cohort boundary."""
    db = tmp_path / "prepared.duckdb"
    reports = tmp_path / "reports"
    results = tmp_path / "results"
    derived = BASE + "\nSee https://example.test/data\n"
    script = "rm -rf /tmp/cache"
    contents = {1: BASE, 2: derived, 3: None, 4: BASE, 5: BASE}
    hashes = {artifact_id: sha1(content.encode()).hexdigest() if content is not None else "missing"
              for artifact_id, content in contents.items()}
    script_hash = sha1(script.encode()).hexdigest()
    notes = None if missing_sibling_content else "Summarize the project."
    with duckdb.connect(str(db)) as connection:
        connection.execute("""
            CREATE TABLE artifacts (
                id BIGINT, file_sha VARCHAR, content VARCHAR,
                repo_full_name VARCHAR, path VARCHAR, first_commit_at VARCHAR
            );
            CREATE TABLE artifact_groupings (
                id BIGINT, artifact_id BIGINT, repo_id BIGINT, name VARCHAR,
                normalized_description VARCHAR, sibling_file_count BIGINT,
                sibling_content_sha VARCHAR
            );
            CREATE TABLE repos (id BIGINT, created_at VARCHAR);
            CREATE TABLE artifact_siblings (
                id BIGINT, artifact_id BIGINT, entry_name VARCHAR, entry_sha VARCHAR,
                content VARCHAR, skipped_reason VARCHAR, entry_type VARCHAR
            );
        """)
        for artifact_id, content in contents.items():
            connection.execute(
                "INSERT INTO artifacts VALUES (?, ?, ?, ?, 'skills/demo/SKILL.md', ?)",
                [artifact_id, hashes[artifact_id], content, f"test/repo-{artifact_id}", f"2026-01-{artifact_id:02d}"],
            )
            connection.execute(
                "INSERT INTO artifact_groupings VALUES (?, ?, ?, ?, 'demo', ?, ?)",
                [artifact_id, artifact_id, artifact_id,
                 "database-demo" if artifact_id <= 3 else "other-family",
                 2 if artifact_id == 2 else 0,
                 "changed" if artifact_id == 2 else "empty"],
            )
            connection.execute("INSERT INTO repos VALUES (?, '2025-01-01')", [artifact_id])
        connection.executemany("INSERT INTO artifact_siblings VALUES (?, 2, ?, ?, ?, ?, 'file')", [
            (20, "scripts/cleanup.sh", script_hash, script, None),
            (21, "notes.txt", "notes-hash", notes, "not-fetched" if notes is None else None),
        ])
    original_database_hash = sha256(db.read_bytes()).hexdigest()

    outcome = run_family("database-demo", database=db, skilltrace_reports=reports,
                         scans=results / "scans")
    assert outcome["artifacts_loaded"] == 2
    assert outcome["artifacts_skipped"] == 1
    assert outcome["pairs_analyzed"] == 1
    assert outcome["pairs_incomplete"] == int(missing_sibling_content)
    family = json.loads((reports / "database-demo.json").read_text(encoding="utf-8"))
    scan_path = results / "scans" / "database-demo.json"
    scan = json.loads(scan_path.read_text(encoding="utf-8"))
    assert "implementation_fingerprint" not in family
    assert "implementation_fingerprint" not in scan
    assert {item["artifact_id"] for item in family["artifacts"]} == {1, 2}
    assert {item["artifact_id"] for item in scan["input_artifacts"]} == {1, 2}
    for item in scan["input_artifacts"]:
        assert item["file_sha"] == hashes[item["artifact_id"]]
        assert item["path"] == "skills/demo/SKILL.md"
        assert item["repo_full_name"] == f"test/repo-{item['artifact_id']}"
    assert scan["skipped_artifacts"] == [{
        "artifact_id": 3, "repo_full_name": "test/repo-3",
        "path": "skills/demo/SKILL.md", "reason": "missing_content",
    }]
    edge, = family["family"]["clusters"][0]["evolution"]["directed_edges"]
    assert (edge["source_artifact_id"], edge["target_artifact_id"]) == (1, 2)
    pair, = scan["clusters"][0]["flagged_pairs"]
    assert (pair["source_artifact_id"], pair["destination_artifact_id"]) == (1, 2)
    assert pair["direction_basis"] == "chronology"
    assert {(rule["rule_id"], rule["surface"]) for rule in pair["flagged_rules"]} == {
        ("NET-001", "skill"), ("FS-001", "sibling"),
    }
    sibling_evidence, = pair["evidence_comparison"]["siblings"]["added"]
    assert sibling_evidence["source"]["source_id"] == "sibling:20"
    assert sibling_evidence["source"]["filename"] == "scripts/cleanup.sh"
    assert sibling_evidence["excerpt"] == script
    assert pair["sibling_scan"]["incomplete"] == missing_sibling_content
    assert pair["sibling_scan"]["unavailable_destination_ids"] == ([21] if missing_sibling_content else [])

    saved_scan = scan_path.read_bytes()
    repeated = run_family("database-demo", database=db, skilltrace_reports=reports,
                          scans=results / "scans")
    assert repeated["family_report_updated"] is False
    assert scan_path.read_bytes() == saved_scan
    execution = summarize_cohort(["database-demo"], database=db,
                                 skilltrace_reports=reports, results=results)
    assert execution["directed_pairs_analyzed"] == 1
    assert execution["artifacts_skipped"] == 1
    assert execution["pairs_incomplete"] == int(missing_sibling_content)
    manifest = json.loads((results / "sample_manifest.json").read_text(encoding="utf-8"))
    assert manifest["family_names"] == ["database-demo"]
    from gitskills.pipelines.provenance import implementation_fingerprint
    assert manifest["implementation_fingerprint"] == implementation_fingerprint()
    with (results / "audit" / "skipped_artifacts.csv").open(encoding="utf-8", newline="") as handle:
        exclusions = list(csv.DictReader(handle))
    assert [(row["artifact_id"], row["reason"]) for row in exclusions] == [("3", "missing_content")]
    assert sha256(db.read_bytes()).hexdigest() == original_database_hash


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
    from gitskills.pipelines import family as pipeline, cohort as summarizer

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
    monkeypatch.setattr(summarizer, "DuckDBFamilyRepository", FakeFamilies)
    monkeypatch.setattr(summarizer, "DuckDBSiblingRepository", FakeSiblings)
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
    assert (results / "manual-review" / "relationship-pairs" / "relationship_annotations_template.csv").exists()
    assert (results / "manual-review" / "directed-pairs" / "annotations_template.csv").exists()
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


def test_cohort_generates_missing_reports_and_refreshes_mismatched_scans(repositories):
    db, reports, results = repositories
    assert summarize_cohort(["alpha"], database=db, results=results)["family_count"] == 1
    with pytest.raises(ValueError, match="not found"):
        run_family("missing", database=db, skilltrace_reports=reports, scans=results / "scans")
    run_family("alpha", database=db, skilltrace_reports=reports, scans=results / "scans")
    path = results / ".scans" / "alpha.json"
    report = json.loads(path.read_text())
    report["input_artifacts"][0]["file_sha"] = "unrelated"
    path.write_text(json.dumps(report))
    summarize_cohort(["alpha"], database=db, results=results)
    assert json.loads(path.read_text())["input_artifacts"][0]["file_sha"] != "unrelated"


def test_default_family_output_supplies_relationship_analysis(repositories):
    db, reports, results = repositories
    run_family("alpha", database=db, skilltrace_reports=reports, scans=results / "scans")
    report = json.loads((reports / "alpha.json").read_text())
    assert "similarities" not in report
    assert "artifacts" in report
    assert "groups" not in report  # Optional verbose diagnostics.
    assert "directed_edges" in report["family"]["clusters"][0]["evolution"]
    assert report["skipped_artifacts"][0]["reason"] == "missing_content"


def test_reviewer_snapshot_is_not_silently_replaced(repositories):
    db, reports, results = repositories
    for name in ("alpha", "beta"):
        run_family(name, database=db, skilltrace_reports=reports, scans=results / "scans")
    summarize_cohort(["alpha"], database=db, skilltrace_reports=reports, results=results)
    adjudicated = results / "manual-review" / "adjudicated"
    adjudicated.mkdir(parents=True)
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


def test_legacy_fingerprint_is_removed_without_rebuilding_family(repositories):
    db, reports, results = repositories
    run_family("alpha", database=db, skilltrace_reports=reports, scans=results / "scans")
    family_path = reports / "alpha.json"
    original = json.loads(family_path.read_text())
    outdated = {**original, "implementation_fingerprint": "old-version"}
    family_path.write_text(json.dumps(outdated))

    migrated = run_family("alpha", database=db, skilltrace_reports=reports,
                          scans=results / "scans")
    assert migrated["family_report_updated"] is True
    assert json.loads(family_path.read_text()) == original
    assert run_family("alpha", database=db, skilltrace_reports=reports,
                      scans=results / "scans")["family_report_updated"] is False


def test_fingerprint_change_only_affects_cohort_manifest(repositories, monkeypatch):
    from gitskills.pipelines import provenance

    db, reports, results = repositories
    run_family("alpha", database=db, skilltrace_reports=reports, scans=results / "scans")
    family_path = reports / "alpha.json"
    scan_path = results / "scans" / "alpha.json"
    original_family = family_path.read_bytes()
    original_scan = scan_path.read_bytes()

    # Simulate a rules/source change: only the manifest records the new code hash.
    monkeypatch.setattr(provenance, "implementation_fingerprint", lambda: "new-source-revision")
    repeated = run_family("alpha", database=db, skilltrace_reports=reports,
                          scans=results / "scans")
    assert repeated["family_report_updated"] is False
    assert family_path.read_bytes() == original_family
    assert scan_path.read_bytes() == original_scan

    summarize_cohort(["alpha"], database=db, skilltrace_reports=reports, results=results)
    manifest = json.loads((results / "sample_manifest.json").read_text())
    assert manifest["implementation_fingerprint"] == "new-source-revision"
    assert "implementation_fingerprint" not in json.loads(family_path.read_text())
    assert "implementation_fingerprint" not in json.loads(scan_path.read_text())


def test_legacy_scan_fingerprint_does_not_invalidate_completed_review(repositories):
    db, reports, results = repositories
    run_family("alpha", database=db, skilltrace_reports=reports, scans=results / "scans")
    family_path = reports / "alpha.json"
    scan_path = results / "scans" / "alpha.json"
    for path in (family_path, scan_path):
        report = json.loads(path.read_text())
        report["implementation_fingerprint"] = "old-version"
        path.write_text(json.dumps(report))

    reviewed = results / "review" / "adjudicated"
    reviewed.mkdir(parents=True)
    (reviewed / "directed.csv").write_text("completed independent review")
    run_family("alpha", database=db, skilltrace_reports=reports, scans=results / "scans")
    assert "implementation_fingerprint" not in json.loads(family_path.read_text())
    assert "implementation_fingerprint" not in json.loads(scan_path.read_text())


def test_all_edges_are_traceable_to_primary_and_related_family_edges(monkeypatch, tmp_path):
    """Regression: all must accept valid additional edges, not just primary."""
    from gitskills.data.families import FamilyLoad
    from gitskills.pipelines import family as module, cohort as summarizer

    prefix = ("The agent skill performs safe and documented analysis of software artifacts "
              "and security patterns. " * 15) + "\n"
    suffixes = (
        "Prepare the project.",
        "Prepare the project.\nmkdir cache",
        "Prepare the project.\nmkdir cache\nrm -rf cache",
        "Prepare the project.\nmkdir cache\nrm -rf cache\ncat ~/.ssh/id_rsa",
    )
    artifacts = tuple(make_artifact("edges", 101 + i, prefix + suffix)
                      for i, suffix in enumerate(suffixes))

    class Families:
        def __init__(self, database):
            pass

        def load_available(self, name):
            return FamilyLoad(artifacts, ())

    class Siblings:
        def __init__(self, database):
            pass

        def load(self, ids):
            return ()

    monkeypatch.setattr(module, "DuckDBFamilyRepository", Families)
    monkeypatch.setattr(module, "DuckDBSiblingRepository", Siblings)
    monkeypatch.setattr(summarizer, "DuckDBFamilyRepository", Families)
    monkeypatch.setattr(summarizer, "DuckDBSiblingRepository", Siblings)
    db = tmp_path / "prepared.duckdb"
    db.touch()
    reports = tmp_path / "apps" / "skilltrace" / "reports"
    results = tmp_path / "results"
    run_family("edges", database=db, skilltrace_reports=reports, scans=results / "scans")
    result = summarize_cohort(["edges"], database=db, skilltrace_reports=reports, results=results)
    assert result["directed_pairs_analyzed"] == 6
    scan_file = results / ".scans" / "edges.json"
    scan = json.loads(scan_file.read_text())
    additional = [pair for cluster in scan["clusters"] for pair in cluster["pair_observations"]
                  if pair["edge_type"] == "additional"]
    assert len(additional) == 3

    # A modified cache must be rejected and recreated, never accepted on mere existence.
    additional[0]["edge_type"] = "primary"
    scan_file.write_text(json.dumps(scan))
    summarize_cohort(["edges"], database=db, results=results)
    repaired = json.loads(scan_file.read_text())
    assert repaired["clusters"][0]["pair_observations"] != scan["clusters"][0]["pair_observations"]


def test_fresh_family_analysis_is_reused_for_security_scan(repositories, monkeypatch):
    """Avoid calculating similarities twice when a new family report is built."""
    from gitskills.analysis.family import FamilyAnalyzer

    db, reports, results = repositories
    original = FamilyAnalyzer.analyze
    calls = []

    def count(self, artifacts):
        calls.append(1)
        return original(self, artifacts)

    monkeypatch.setattr(FamilyAnalyzer, "analyze", count)
    run_family("alpha", database=db, skilltrace_reports=reports, scans=results / "scans")
    assert len(calls) == 1
    run_family("alpha", database=db, skilltrace_reports=reports, scans=results / "scans")
    assert len(calls) == 2  # Cached JSON cannot supply the full in-memory analysis.
