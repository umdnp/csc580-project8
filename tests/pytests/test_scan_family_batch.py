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
    rows = _rows(benchmarked / "benchmarks.csv")
    assert rows[0]["status"] == "ok"
    assert list(rows[0]) == [
        "family", "seconds", "load_s", "family_load_s", "sibling_load_s",
        "analysis_s", "scan_s", "other_s", "peak_python_memory_mib", "status",
    ]
    assert rows[0]["peak_python_memory_mib"] == ""
    assert all(float(rows[0][phase]) >= 0 for phase in
               ("load_s", "family_load_s", "sibling_load_s", "analysis_s", "scan_s", "other_s"))
    assert abs(float(rows[0]["family_load_s"]) + float(rows[0]["sibling_load_s"])
               - float(rows[0]["load_s"])) <= 0.002
    assert abs(sum(float(rows[0][phase]) for phase in
                   ("load_s", "analysis_s", "scan_s", "other_s"))
               - float(rows[0]["seconds"])) <= 0.002


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
    rows = _rows(output / "benchmarks.csv")
    assert [r["status"] for r in rows] == ["failed", "ok"]
    assert all(rows[0][phase] == "" for phase in
               ("load_s", "family_load_s", "sibling_load_s", "analysis_s", "scan_s", "other_s"))
    assert all(rows[1][phase] != "" for phase in
               ("load_s", "family_load_s", "sibling_load_s", "analysis_s", "scan_s", "other_s"))
    assert not (output / "missing.json").exists()
    assert (output / "alpha.json").is_file()
    assert "not found" in capsys.readouterr().err


def test_batch_input_preflight_rejects_stale_and_duplicate(mock_repos, tmp_path):
    inputs = tmp_path / "names.txt"
    output = tmp_path / "reports"
    for text in ("alpha\nalpha\n",):
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


def test_batch_accepts_exact_names_with_filename_special_characters(mock_repos, tmp_path):
    from gitskills.reporting.files import report_stem

    families = ["A/B Test Setup", "A:B Test Setup", "A_B Test Setup", "CON", "../escape"]
    source = tmp_path / "families.txt"
    source.write_text("\n".join(families) + "\n", encoding="utf-8")
    output = tmp_path / "output"
    assert scan_family.main(["--input", str(source), "--db", str(mock_repos),
                             "--output", str(output)]) == 0
    files = list(output.glob("*.json"))
    assert len(files) == len(families)
    for name in families:
        path = output / f"{report_stem(name)}.json"
        assert path.is_file()
        assert json.loads(path.read_text(encoding="utf-8"))["candidate_family"] == name
    assert all(path.parent == output for path in files)


def test_batch_resolves_case_insensitive_filename_collisions(mock_repos, tmp_path):
    source = tmp_path / "families.txt"
    source.write_text("alpha\nALPHA\n", encoding="utf-8")
    output = tmp_path / "output"
    assert scan_family.main(["--input", str(source), "--db", str(mock_repos),
                             "--output", str(output)]) == 0
    names = [path.name.casefold() for path in output.glob("*.json")]
    assert len(names) == 2 and len(set(names)) == 2
    assert {json.loads(path.read_text())["candidate_family"]
            for path in output.glob("*.json")} == {"alpha", "ALPHA"}


def test_edge_selection_option_in_single_and_batch_modes(mock_repos, tmp_path, capsys):
    single = tmp_path / "single"
    assert scan_family.main(["alpha", "--db", str(mock_repos), "--edges", "all",
                             "--json", "--output", str(single)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["edge_selection"] == "all"
    assert (single / "alpha.json").is_file()

    source = tmp_path / "names.txt"
    source.write_text("alpha\n", encoding="utf-8")
    batch = tmp_path / "batch"
    assert scan_family.main(["--input", str(source), "--db", str(mock_repos),
                             "--edges", "all", "--output", str(batch)]) == 0
    assert json.loads((batch / "alpha.json").read_text())["edge_selection"] == "all"

    default = tmp_path / "default"
    assert scan_family.main(["alpha", "--db", str(mock_repos), "--json",
                             "--output", str(default)]) == 0
    assert json.loads((default / "alpha.json").read_text())["edge_selection"] == "all"

    primary = tmp_path / "primary"
    assert scan_family.main(["alpha", "--db", str(mock_repos), "--edges", "primary",
                             "--json", "--output", str(primary)]) == 0
    assert json.loads((primary / "alpha.json").read_text())["edge_selection"] == "primary"

    with pytest.raises(SystemExit, match="2"):
        scan_family.main(["alpha", "--db", str(mock_repos), "--edges", "ambiguous"])


@pytest.mark.parametrize("edge_mode", ["primary", "all"])
def test_benchmark_preserves_report_for_each_edge_mode(mock_repos, tmp_path, capsys, edge_mode):
    baseline = tmp_path / "baseline"
    assert scan_family.main(["alpha", "--db", str(mock_repos), "--edges", edge_mode,
                             "--json", "--output", str(baseline)]) == 0
    baseline_payload = json.loads(capsys.readouterr().out)

    benchmarked = tmp_path / "benchmarked"
    assert scan_family.main(["alpha", "--db", str(mock_repos), "--edges", edge_mode,
                             "--json", "--benchmark", "--output", str(benchmarked)]) == 0
    assert json.loads(capsys.readouterr().out) == baseline_payload
    row = _rows(benchmarked / "benchmarks.csv")[0]
    assert row["status"] == "ok"
    assert all(row[phase] != "" for phase in ("load_s", "analysis_s", "scan_s", "other_s"))


def test_timed_phase_accumulates_and_ignores_failed_phases(monkeypatch):
    times = iter([1.0, 2.0, 3.0, 5.0, 6.0])
    monkeypatch.setattr(scan_family.time, "perf_counter", lambda: next(times))
    timings = {}

    with scan_family._timed_phase(timings, "load_s"):
        pass
    with scan_family._timed_phase(timings, "load_s"):
        pass
    assert timings == {"load_s": 3.0}

    with pytest.raises(ValueError, match="failed"):
        with scan_family._timed_phase(timings, "scan_s"):
            raise ValueError("failed")
    assert "scan_s" not in timings

    with scan_family._timed_phase(None, "scan_s"):
        pass
