"""Sprint 3 notebook uses the reusable picker and persists non-overlapping lists."""

import json
from pathlib import Path

import pytest

from gitskills.analysis.family_models import SimilarityPolicy
from gitskills.sampling.families import FamilySample, save_sample
from gitskills.tools._family_input import read_family_names


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "notebooks/end_to_end_pipeline/end_to_end_pipeline.ipynb"


def _selection_cell():
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return "".join(notebook["cells"][10]["source"])


def _run(tmp_path, *, sprint, trial, picker, existing=None):
    notebook_dir = tmp_path / "notebooks" / "end_to_end_pipeline"
    sample_dir = notebook_dir / ("sprint2/samples" if sprint == 2 else f"sprint3/samples{trial}")
    sample_file = sample_dir / "families.txt"
    if existing is not None:
        sample_dir.mkdir(parents=True, exist_ok=True)
        sample_file.write_text("\n".join(existing) + "\n", encoding="utf-8")
    database = tmp_path / "database.duckdb"
    database.touch()
    namespace = {
        "Path": Path,
        "NOTEBOOK_DIR": notebook_dir,
        "SAMPLE_DIR": sample_dir,
        "FAMILY_FILE": sample_file,
        "DB_PATH": database,
        "SPRINT": sprint,
        "SAMPLE": trial,
        "SimilarityPolicy": SimilarityPolicy,
        "pick_families": picker,
        "save_sample": save_sample,
        "read_family_names": read_family_names,
    }
    exec(compile(_selection_cell(), str(NOTEBOOK), "exec"), namespace)
    return namespace


def _sample(seed, names):
    return FamilySample(seed=seed, sample_size=len(names),
                        families=[{"name": name, "artifact_count": 2, "group": "Low"}
                                  for name in names], groups=[], candidate_count=1000,
                        excluded_count=0, policy=SimilarityPolicy())


def test_sample_one_created_and_reused(tmp_path):
    calls = []

    def pick(**kwargs):
        calls.append(kwargs)
        return _sample(kwargs["seed"], ["trial-one"])

    result = _run(tmp_path, sprint=3, trial=1, picker=pick)
    assert result["candidate_families"] == ["trial-one"]
    assert calls[0]["seed"] == 5801
    assert calls[0]["sample_size"] == 100
    assert calls[0]["exclude_names"] == set()
    assert calls[0]["policy"].to_dict() == SimilarityPolicy().to_dict()
    assert (result["SAMPLE_DIR"] / "sampling_report.json").exists()
    result = _run(tmp_path, sprint=3, trial=1,
                  picker=lambda **kwargs: pytest.fail("Existing sample should be reused"))
    assert result["candidate_families"] == ["trial-one"]


def test_later_trials_exclude_previous_lists(tmp_path):
    sample_one = tmp_path / "notebooks/end_to_end_pipeline/sprint3/samples1"
    sample_one.mkdir(parents=True)
    (sample_one / "families.txt").write_text("first\nother\n", encoding="utf-8")
    calls = []

    def pick(**kwargs):
        calls.append(kwargs)
        return _sample(kwargs["seed"], ["second"])

    result = _run(tmp_path, sprint=3, trial=2, picker=pick)
    assert calls[0]["seed"] == 5802
    assert calls[0]["exclude_names"] == {"first", "other"}
    assert result["candidate_families"] == ["second"]
    manifest = json.loads((result["SAMPLE_DIR"] / "sampling_report.json").read_text())
    assert len(manifest["exclusion_files"]) == 1
    assert len(manifest["exclusion_files"][0]["sha256"]) == 64
    result = _run(tmp_path, sprint=3, trial=3,
                  picker=lambda **kwargs: _sample(kwargs["seed"], ["third"]) if
                  kwargs["exclude_names"] == {"first", "other", "second"} else
                  pytest.fail("Missing exclusions"))
    assert result["FAMILY_SEED"] == 5803
    assert result["candidate_families"] == ["third"]


def test_prior_sample_required_before_later_trial(tmp_path):
    with pytest.raises(FileNotFoundError, match="Run earlier Sprint 3 trials"):
        _run(tmp_path, sprint=3, trial=3, picker=lambda **kw: pytest.fail("Must not pick"))


def test_sprint_two_never_auto_generates(tmp_path):
    with pytest.raises(FileNotFoundError, match="approved family list"):
        _run(tmp_path, sprint=2, trial=1, picker=lambda **kw: pytest.fail("Must not pick"))
    result = _run(tmp_path, sprint=2, trial=1,
                  picker=lambda **kw: pytest.fail("Must not pick"), existing=["approved"])
    assert result["candidate_families"] == ["approved"]
    assert result["EDGES"] == "primary"
    assert result["SEED"] == 580
