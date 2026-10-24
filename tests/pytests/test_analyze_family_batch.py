"""Single and batch candidate-family report generation."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from gitskills.analysis.family_models import Artifact
from gitskills.reporting.files import report_stem
from gitskills.tools import analyze_family


BODY = "A documented skill compares source records and repository changes. " * 12


@pytest.fixture
def mock_repos(monkeypatch, tmp_path):
    database = tmp_path / "data.db"
    database.touch()

    class Families:
        def __init__(self, path):
            assert Path(path) == database

        def load_available(self, name):
            if name == "missing":
                return SimpleNamespace(artifacts=(), skipped_artifacts=())
            artifacts = tuple(
                Artifact(
                    artifact_id=i, group_id=1, repo_id=i, name=name,
                    normalized_description="example", file_sha=f"sha-{name}-{i}",
                    content=BODY + (" Additional guidance." if i == 2 else ""),
                    first_commit_at=f"2026-01-{i:02d}", repo_created_at=None,
                    sibling_file_count=0, sibling_content_sha="empty",
                )
                for i in (1, 2)
            )
            return SimpleNamespace(artifacts=artifacts, skipped_artifacts=())

    monkeypatch.setattr(analyze_family, "DuckDBFamilyRepository", Families)
    return database


def test_single_family_interface_unchanged(mock_repos, tmp_path, capsys):
    output = tmp_path / "reports"
    assert analyze_family.main(["alpha", "--db", str(mock_repos),
                                "--output", str(output), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["name"] == "alpha"
    assert payload == json.loads((output / "alpha.json").read_text(encoding="utf-8"))
    assert "similarities" in payload and "artifacts" in payload


def test_batch_writes_per_family_reports_and_progress(mock_repos, tmp_path, capsys):
    source = tmp_path / "families.txt"
    source.write_text("\ufeff# example\n\nalpha\nA/B Test Setup\nbeta\n", encoding="utf-8")
    output = tmp_path / "reports"
    assert analyze_family.main(["--input", str(source), "--db", str(mock_repos),
                                "--output", str(output), "--json"]) == 0
    stdout = capsys.readouterr().out
    assert stdout.splitlines() == [
        "[1/3] alpha: ok", "[2/3] A/B Test Setup: ok", "[3/3] beta: ok"
    ]
    for name in ("alpha", "A/B Test Setup", "beta"):
        path = output / f"{report_stem(name)}.json"
        assert path.is_file()
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["name"] == name
        assert "similarities" in payload and "artifacts" in payload


def test_limit_processes_first_n_only(mock_repos, tmp_path, capsys):
    source = tmp_path / "families.txt"
    source.write_text("alpha\nbeta\n", encoding="utf-8")
    output = tmp_path / "limited"
    assert analyze_family.main(["--input", str(source), "--db", str(mock_repos),
                                "--output", str(output), "--limit", "1"]) == 0
    assert list(p.name for p in output.glob("*.json")) == ["alpha.json"]
    assert capsys.readouterr().out.strip() == "[1/1] alpha: ok"


def test_invalid_batch_options(mock_repos, tmp_path):
    source = tmp_path / "families.txt"
    source.write_text("alpha\n", encoding="utf-8")
    cases = [
        ["--input", str(source)],
        ["alpha", "--limit", "1"],
        ["--input", str(source), "--limit", "0", "--output", str(tmp_path / "out")],
        ["--input", str(source), "--limit", "-1", "--output", str(tmp_path / "out")],
        ["alpha", "--input", str(source), "--output", str(tmp_path / "out")],
    ]
    for options in cases:
        with pytest.raises(SystemExit) as error:
            analyze_family.main([*options, "--db", str(mock_repos)])
        assert error.value.code == 2


def test_batch_rejects_duplicates_empty_and_existing_reports(mock_repos, tmp_path, capsys):
    source = tmp_path / "families.txt"
    output = tmp_path / "out"
    for text in ("alpha\nalpha\n", "# no names\n\n"):
        source.write_text(text, encoding="utf-8")
        assert analyze_family.main(["--input", str(source), "--db", str(mock_repos),
                                    "--output", str(output)]) == 2
    assert "Invalid analysis input" in capsys.readouterr().err

    source.write_text("alpha\n", encoding="utf-8")
    output.mkdir(exist_ok=True)
    (output / "old.json").write_text("{}", encoding="utf-8")
    assert analyze_family.main(["--input", str(source), "--db", str(mock_repos),
                                "--output", str(output)]) == 2
    assert (output / "old.json").read_text() == "{}"


def test_failed_family_does_not_stop_batch(mock_repos, tmp_path, capsys):
    source = tmp_path / "families.txt"
    source.write_text("alpha\nmissing\nbeta\n", encoding="utf-8")
    output = tmp_path / "reports"
    assert analyze_family.main(["--input", str(source), "--db", str(mock_repos),
                                "--output", str(output)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        "[1/3] alpha: ok", "[2/3] missing: failed", "[3/3] beta: ok"
    ]
    assert "Candidate family not found: missing" in captured.err
    assert sorted(p.name for p in output.glob("*.json")) == ["alpha.json", "beta.json"]


def test_case_insensitive_report_name_collision(mock_repos, tmp_path):
    source = tmp_path / "families.txt"
    source.write_text("alpha\nALPHA\n", encoding="utf-8")
    output = tmp_path / "reports"
    assert analyze_family.main(["--input", str(source), "--db", str(mock_repos),
                                "--output", str(output)]) == 0
    files = list(output.glob("*.json"))
    assert len(files) == 2
    assert len({file.name.casefold() for file in files}) == 2
    assert {json.loads(file.read_text())["name"] for file in files} == {
        "alpha", "ALPHA"
    }
