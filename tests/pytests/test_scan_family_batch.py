"""Single/batch CLI reporting and optional benchmarking."""

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from gitskills.analysis.family_models import Artifact
from gitskills.tools import scan_family


BODY = ("A documented agent skill compares repository content without executing scripts. " * 15)


def _artifact(artifact_id, name):
    return Artifact(
        artifact_id=artifact_id, group_id=1, repo_id=artifact_id,
        name=name, normalized_description="example", file_sha=f"sha{artifact_id}",
        content=BODY + (" Read https://example.org/data." if artifact_id % 2 == 0 else ""),
        first_commit_at=f"2026-01-{artifact_id:02d}", repo_created_at=None,
        sibling_file_count=0, sibling_content_sha="empty",
    )


@pytest.fixture
def mock_repos(monkeypatch, tmp_path):
    db = tmp_path / "data.db"
    db.touch()

    class Families:
        def __init__(self, path):
            assert Path(path) == db

        def load_available(self, name):
            if name == "missing":
                return SimpleNamespace(artifacts=(), skipped_artifacts=())
            ids = (1, 2) if name == "alpha" else (3, 4)
            return SimpleNamespace(artifacts=tuple(_artifact(i, name) for i in ids),
                                   skipped_artifacts=())

    class Siblings:
        def __init__(self, path):
            assert Path(path) == db

        def load(self, ids):
            return ()

    monkeypatch.setattr(scan_family, "DuckDBFamilyRepository", Families)
    monkeypatch.setattr(scan_family, "DuckDBSiblingRepository", Siblings)
    return db


def _rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_single_scan_benchmark_is_opt_in(mock_repos, tmp_path, capsys):
    output = tmp_path / "single"
    args = ["alpha", "--db", str(mock_repos), "--json", "--output", str(output)]
    assert scan_family.main(args) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["candidate_family"] == "alpha"
    assert (output / "alpha.json").is_file()
    assert not (output / "benchmarks.csv").exists()

    benchmarked = tmp_path / "benchmarked"
    assert scan_family.main(["alpha", "--db", str(mock_repos), "--json", "--benchmark",
                             "--output", str(benchmarked)]) == 0
    assert json.loads(capsys.readouterr().out)["candidate_family"] == "alpha"
    assert _rows(benchmarked / "benchmarks.csv")[0]["status"] == "ok"


def test_batch_writes_individual_reports_and_uses_custom_policy(mock_repos, tmp_path, capsys):
    inputs = tmp_path / "names.txt"
    inputs.write_text("# research cohort\nalpha\n\nbeta\n", encoding="utf-8")
    output = tmp_path / "reports"
    assert scan_family.main(["--input", str(inputs), "--db", str(mock_repos),
                             "--output", str(output), "--min-containment", "0.65",
                             "--benchmark"]) == 0
    progress = capsys.readouterr().out
    assert "[1/2] alpha: ok" in progress and "[2/2] beta: ok" in progress
    assert len(_rows(output / "benchmarks.csv")) == 2
    assert json.loads((output / "alpha.json").read_text())["similarity_policy"]["min_containment"] == 0.65
    assert json.loads((output / "beta.json").read_text())["candidate_family"] == "beta"


def test_batch_failure_is_recorded_and_remaining_scans_continue(mock_repos, tmp_path, capsys):
    inputs = tmp_path / "names.txt"
    inputs.write_text("missing\nalpha\n", encoding="utf-8")
    output = tmp_path / "results"
    assert scan_family.main(["--input", str(inputs), "--db", str(mock_repos),
                             "--output", str(output), "--benchmark"]) == 1
    assert [r["status"] for r in _rows(output / "benchmarks.csv")] == ["failed", "ok"]
    assert not (output / "missing.json").exists()
    assert (output / "alpha.json").is_file()
    assert "not found" in capsys.readouterr().err


def test_batch_input_preflight_rejects_stale_duplicate_and_traversal(mock_repos, tmp_path):
    inputs = tmp_path / "names.txt"
    output = tmp_path / "reports"
    for text in ("alpha\nalpha\n", "../escape\n", "alpha/beta\n"):
        inputs.write_text(text, encoding="utf-8")
        assert scan_family.main(["--input", str(inputs), "--db", str(mock_repos),
                                 "--output", str(output)]) == 2
    inputs.write_text("alpha\n", encoding="utf-8")
    output.mkdir(exist_ok=True)
    (output / "alpha.json").write_text("{}", encoding="utf-8")
    assert scan_family.main(["--input", str(inputs), "--db", str(mock_repos),
                             "--output", str(output)]) == 2


def test_batch_limit_and_traced_memory(mock_repos, tmp_path):
    inputs = tmp_path / "names.txt"
    inputs.write_text("alpha\nbeta\n", encoding="utf-8")
    output = tmp_path / "pilot"
    assert scan_family.main(["--input", str(inputs), "--db", str(mock_repos),
                             "--output", str(output), "--limit", "1",
                             "--benchmark", "--tracemalloc"]) == 0
    rows = _rows(output / "benchmarks.csv")
    assert len(rows) == 1 and rows[0]["family"] == "alpha"
    assert float(rows[0]["peak_python_memory_mib"]) >= 0
    assert not (output / "beta.json").exists()


def test_batch_requires_output_and_tracemalloc_requires_benchmark(mock_repos, tmp_path):
    inputs = tmp_path / "names.txt"
    inputs.write_text("alpha\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="2"):
        scan_family.main(["--input", str(inputs), "--db", str(mock_repos)])
    with pytest.raises(SystemExit, match="2"):
        scan_family.main(["alpha", "--db", str(mock_repos), "--tracemalloc"])
