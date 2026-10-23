"""Complete denominators, manual samples, and reproducible research tables."""

import csv
import json
from dataclasses import replace
from pathlib import Path

import pytest

from gitskills.analysis.family_models import Artifact
from gitskills.analysis.family import FamilyAnalyzer
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
    rows[0].update({
        "review_phase": "adjudicated", "review_status": "complete", "reviewer": "team",
        "review_date": "2026-10-23", "manual_relatedness": "related",
        "direction_basis_review": "supported", "scanner_rule_review": "correct",
        "manual_change_review": "correct", "sibling_coverage_review": "complete",
        "indicator_review_scope": "all_assessed", "manual_supported_indicator_ids": "RI-006",
    })
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


def test_cluster_requires_explicit_pair_observations():
    # Keep old analyzer implementations from silently emitting missing all-pairs data.
    from gitskills.analysis.family_risk_models import ClusterRiskAnalysis

    with pytest.raises(TypeError, match="pair_observations"):
        ClusterRiskAnalysis(cluster_number=1, pairs_analyzed=1, flagged_pairs=())


def _write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _adjudicated_row(row: dict) -> dict:
    return {**row, "reviewer": "team", "review_phase": "adjudicated",
            "review_status": "complete", "review_date": "2026-10-23",
            "manual_relatedness": "related", "direction_basis_review": "supported",
            "scanner_rule_review": "correct", "manual_change_review": "correct",
            "sibling_coverage_review": "complete", "indicator_review_scope": "all_assessed"}


def test_review_requires_explicit_assessment_not_blank_implied_negative(tmp_path: Path):
    path = tmp_path / "report.json"
    path.write_text(json.dumps(_report()), encoding="utf-8")
    out = tmp_path / "out"
    summarize([path], out, per_stratum=8)
    rows = list(csv.DictReader((out / "validation_annotations_template.csv").open()))
    rows[0] = _adjudicated_row(rows[0])
    rows[0]["indicator_review_scope"] = ""
    annotations = tmp_path / "annotations.csv"
    _write_rows(annotations, rows)
    with pytest.raises(ResearchInputError, match="indicator_review_scope"):
        summarize([path], out, per_stratum=8, annotations=annotations)


def test_unassessable_coverage_is_excluded_from_indicator_metrics(tmp_path: Path):
    report = _report()
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    out = tmp_path / "out"
    summarize([path], out, per_stratum=8)
    rows = list(csv.DictReader((out / "validation_annotations_template.csv").open()))
    rows[0] = _adjudicated_row(rows[0])
    rows[0]["manual_relatedness"] = "uncertain"
    annotations = tmp_path / "annotations.csv"
    _write_rows(annotations, rows)
    metrics = summarize([path], out, per_stratum=8, annotations=annotations)["manual_validation"]
    assert metrics["reviewed_pairs"] == 1
    assert metrics["assessable_pairs"] == 0
    assert metrics["excluded_pairs"]["unrelated_or_uncertain"] == 1
    assert metrics["micro"]["tn"] == 0


def test_metrics_reject_unselected_and_independent_reviews(tmp_path: Path):
    path = tmp_path / "report.json"
    path.write_text(json.dumps(_report()), encoding="utf-8")
    out = tmp_path / "out"
    summarize([path], out, per_stratum=1)
    rows = list(csv.DictReader((out / "validation_annotations_template.csv").open()))
    assert rows
    annotations = tmp_path / "annotations.csv"
    rows[0] = _adjudicated_row(rows[0])
    rows[0]["review_phase"] = "independent"
    _write_rows(annotations, rows)
    with pytest.raises(ResearchInputError, match="review_phase=adjudicated"):
        summarize([path], out, per_stratum=1, annotations=annotations)
    rows[0]["review_phase"] = "adjudicated"
    rows[0]["base_artifact_id"] = "9999"
    _write_rows(annotations, rows)
    with pytest.raises(ResearchInputError, match="unsampled"):
        summarize([path], out, per_stratum=1, annotations=annotations)


def _relationship_report():
    phrase = "alpha beta gamma delta eta theta iota kappa lambda mu nu xi omicron pi rho sigma " * 8
    unrelated = "one two three four five six seven eight nine ten eleven twelve thirteen " * 8
    records = [
        Artifact(artifact_id=identifier, group_id=identifier, repo_id=identifier,
                 name="phase10-test", normalized_description="demo", file_sha=f"sha-{identifier}",
                 content=content, first_commit_at=None, repo_created_at=None,
                 sibling_file_count=0, sibling_content_sha="empty")
        for identifier, content in [(1, phrase), (2, phrase + " one"),
                                    (3, unrelated), (4, phrase)]
    ]
    return FamilyAnalyzer().analyze(records).to_dict(verbose=True)


def test_relationship_sample_includes_ambiguous_equivalent_and_no_edge(tmp_path: Path):
    scan = tmp_path / "scan.json"
    scan.write_text(json.dumps(_report()), encoding="utf-8")
    family = tmp_path / "family.json"
    family.write_text(json.dumps(_relationship_report()), encoding="utf-8")
    first = tmp_path / "first"
    second = tmp_path / "second"
    a = summarize([scan], first, per_stratum=2, seed=580, family_reports=[family])
    b = summarize([scan], second, per_stratum=2, seed=580, family_reports=[family])
    assert a == b
    assert a["relationship_sampling"]["sampled_pairs"] == 5
    rows = list(csv.DictReader((first / "relationship_validation_sample.csv").open()))
    assert {row["sampling_stratum"] for row in rows} == {"ambiguous", "equivalent", "no-related-edge"}
    assert all(row["direction_basis"] == "not_applicable" for row in rows
               if row["sampling_stratum"] == "no-related-edge")
    assert (first / "relationship_validation_sample.csv").read_bytes() == (
        second / "relationship_validation_sample.csv").read_bytes()
    assert (first / "relationship_validation_annotations_template.csv").is_file()
    review = list(csv.DictReader((first / "relationship_validation_annotations_template.csv").open()))
    review[0].update({"reviewer": "team", "review_phase": "adjudicated",
                      "review_status": "complete", "review_date": "2026-10-23",
                      "manual_relatedness": "related", "direction_basis_review": "uncertain"})
    annotated = tmp_path / "relationship-reviewed.csv"
    _write_rows(annotated, review)
    metrics = summarize([scan], first, per_stratum=2, seed=580, family_reports=[family],
                        relationship_annotations=annotated)["relationship_validation"]
    assert metrics["reviewed_pairs"] == 1
    assert metrics["relatedness_agree"] == 1


def test_relationship_reports_require_matching_policy_and_complete_data(tmp_path: Path):
    path = tmp_path / "scan.json"
    path.write_text(json.dumps(_report()), encoding="utf-8")
    report = _relationship_report()
    family = tmp_path / "family.json"
    report.pop("similarities")
    family.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ResearchInputError, match="complete analyze_family report"):
        summarize([path], tmp_path / "out", per_stratum=1, family_reports=[family])
    report = _relationship_report()
    report["policy"]["min_jaccard"] = 0.9
    family.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ResearchInputError, match="policy differs"):
        summarize([path], tmp_path / "out", per_stratum=1, family_reports=[family])


def test_uncertain_indicator_excluded_without_becoming_negative(tmp_path: Path):
    scan = tmp_path / "scan.json"
    scan.write_text(json.dumps(_report()), encoding="utf-8")
    output = tmp_path / "out"
    summarize([scan], output, per_stratum=5)
    rows = list(csv.DictReader((output / "validation_annotations_template.csv").open()))
    rows[0] = _adjudicated_row(rows[0])
    rows[0]["manual_uncertain_indicator_ids"] = "RI-006"
    reviewed = tmp_path / "reviewed.csv"
    _write_rows(reviewed, rows)
    metrics = summarize([scan], output, per_stratum=5, annotations=reviewed)["manual_validation"]
    assert metrics["uncertain_indicator_judgments"] == 1
    assert metrics["by_indicator"]["RI-006"] == {
        "tp": 0, "fp": 0, "fn": 0, "tn": 0, "precision": None, "recall": None,
    }
    assert metrics["assessable_pairs"] == 1


def test_conflicting_manual_indicator_labels_are_rejected(tmp_path: Path):
    scan = tmp_path / "scan.json"
    scan.write_text(json.dumps(_report()), encoding="utf-8")
    output = tmp_path / "out"
    summarize([scan], output, per_stratum=5)
    rows = list(csv.DictReader((output / "validation_annotations_template.csv").open()))
    rows[0] = _adjudicated_row(rows[0])
    rows[0]["manual_supported_indicator_ids"] = "RI-002"
    rows[0]["manual_uncertain_indicator_ids"] = "RI-002"
    reviewed = tmp_path / "reviewed.csv"
    _write_rows(reviewed, rows)
    with pytest.raises(ResearchInputError, match="overlapping supported and uncertain"):
        summarize([scan], output, per_stratum=5, annotations=reviewed)
