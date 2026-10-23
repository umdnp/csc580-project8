"""Complete denominators, manual samples, and reproducible research tables."""

import csv
import json
from dataclasses import replace
from pathlib import Path

import pytest

from gitskills.analysis.family_models import Artifact
from gitskills.analysis.family_risk import FamilyRiskAnalyzer
from gitskills.tools.summarize_scans import ResearchInputError, summarize


PREFIX = "The agent skill performs safe and documented analysis of software artifacts and security patterns. " * 15 + "\n"


def _a(artifact_id: int, content: str):
    return Artifact(
        artifact_id=artifact_id, group_id=1, repo_id=artifact_id,
        name="phase10-test", normalized_description="demo",
        file_sha=f"sha-{artifact_id}", content=content,
        first_commit_at=f"2026-01-{artifact_id:02d}", repo_created_at=None,
        sibling_file_count=0, sibling_content_sha="empty",
    )


def _report():
    # One unchanged pair and one changed pair; both must appear in the denominator.
    artifacts = [
        _a(1, PREFIX + "This is a preparatory step for the user.\n"),
        _a(2, PREFIX + "This is a revised preparatory step for the user.\n"),
        _a(3, PREFIX + "This is a revised preparatory step for the user.\n```bash\ncurl https://example.com/b\n```"),
    ]
    return FamilyRiskAnalyzer().analyze(artifacts).to_dict()


def test_every_directed_edge_including_unflagged_is_serialized():
    report = _report()
    all_pairs = [p for cluster in report["clusters"] for p in cluster["pair_observations"]]
    assert report["report_type"] == "gitskills-family-scan"
    assert "report_schema_version" not in report
    assert "indicator_policy_version" not in report
    assert len(all_pairs) == report["summary"]["pairs_analyzed"]
    assert any(not p["flagged"] for p in all_pairs)
    assert any(p["flagged"] for p in all_pairs)
    assert all("coverage" in p for p in all_pairs)


def test_reproducible_tables_and_sample_including_nonflagged(tmp_path: Path):
    path = tmp_path / "phase10-test.json"
    path.write_text(json.dumps(_report()), encoding="utf-8")
    first = tmp_path / "first"
    second = tmp_path / "second"
    a = summarize([path], first, per_stratum=2, seed=42)
    b = summarize([path], second, per_stratum=2, seed=42)
    assert a == b
    assert a["directed_pairs_analyzed"] > a["flagged_pairs"]
    assert all((first / filename).read_bytes() == (second / filename).read_bytes()
               for filename in ("summary.json", "families.csv", "directed_pairs.csv",
                                "validation_sample.csv", "indicator_frequency.csv",
                                "indicator_frequency.svg", "direction_basis.csv"))
    rows = list(csv.DictReader((first / "validation_sample.csv").open(encoding="utf-8")))
    assert any(row["sampling_stratum"] == "unflagged-directed" for row in rows)
    assert (first / "validation_annotations_template.csv").is_file()


def test_reconcile_catches_summary_mismatch(tmp_path: Path):
    result = _report()
    path = tmp_path / "input.json"
    result["summary"]["pairs_analyzed"] += 1
    path.write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(ResearchInputError, match="family pair count mismatch"):
        summarize([path], tmp_path / "out")


def test_rejects_non_scan_reports_and_missing_required_pair_data(tmp_path: Path):
    path = tmp_path / "input.json"
    report = _report()
    report.pop("report_type")
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ResearchInputError, match="expected a scan_family report"):
        summarize([path], tmp_path / "out")

    report = _report()
    report["clusters"][0].pop("pair_observations")
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ResearchInputError, match="missing pair_observations"):
        summarize([path], tmp_path / "out")


def test_annotation_metrics_count_only_completed_reviews(tmp_path: Path):
    path = tmp_path / "input.json"
    path.write_text(json.dumps(_report()), encoding="utf-8")
    out = tmp_path / "results"
    summarize([path], out, per_stratum=8)
    template = out / "validation_annotations_template.csv"
    rows = list(csv.DictReader(template.open(encoding="utf-8")))
    assert rows
    rows[0]["review_status"] = "complete"
    rows[0]["manual_supported_indicator_ids"] = "RI-006"
    annotations = tmp_path / "reviewed.csv"
    with annotations.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    metrics = summarize([path], out, per_stratum=8, annotations=annotations)["manual_validation"]
    assert metrics["reviewed_pairs"] == 1
    assert metrics["micro"]["fn"] == 1
    assert metrics["micro"]["recall"] == 0.0


def test_duplicate_family_reports_not_silently_double_counted(tmp_path: Path):
    report = _report()
    paths = [tmp_path / "a.json", tmp_path / "b.json"]
    for path in paths:
        path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ResearchInputError, match="Duplicate family"):
        summarize(paths, tmp_path / "out")


def test_default_research_summary_does_not_select_review_sample(tmp_path: Path):
    path = tmp_path / "family.json"
    path.write_text(json.dumps(_report()), encoding="utf-8")
    output = tmp_path / "research"
    summary = summarize([path], output)
    assert summary["directed_pairs_analyzed"] > 0
    assert "sampling" not in summary
    assert (output / "directed_pairs.csv").is_file()
    assert (output / "indicator_frequency.svg").is_file()
    assert not (output / "validation_sample.csv").exists()
    assert not (output / "validation_annotations_template.csv").exists()


def test_serializing_cluster_with_missing_observations_fails_at_source():
    analysis = FamilyRiskAnalyzer().analyze([
        _a(1, PREFIX + "One step.\n"),
        _a(2, PREFIX + "Two steps.\n"),
    ])
    cluster = analysis.clusters[0]
    incomplete = replace(cluster, pairs_analyzed=cluster.pairs_analyzed + 1)
    with pytest.raises(ValueError, match=r"pairs_analyzed=2, pair_observations=1"):
        incomplete.to_dict()


def test_pair_mismatch_message_gives_counts_and_remediation(tmp_path: Path):
    report = _report()
    cluster = report["clusters"][0]
    cluster["pairs_analyzed"] += 1
    input_path = tmp_path / "report.json"
    input_path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ResearchInputError, match=r"pairs_analyzed=\d+, pair_observations=\d+.*regenerate"):
        summarize([input_path], tmp_path / "summary")
