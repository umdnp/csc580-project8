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
    manifest = _json(results / ".scans" / ".scan_manifest.json")
    assert set(manifest["families"]) == {"alpha", "beta"}
    assert manifest["version"] == 1
    assert "implementation_fingerprint" not in _json(results / ".scans" / "alpha.json")
    assert (results / "review" / "directed_pairs.csv").is_file()
    assert (results / "manual-review" / "directed-pairs" / "validation_annotations_template.csv").is_file()
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
    assert "alpha" in _json(folder / ".scan_manifest.json")["families"]


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
