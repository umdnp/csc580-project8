"""Behavioral contracts for shared family, reporting, and CLI helpers."""

import pytest

from gitskills.analysis.family_models import Artifact, SimilarityPolicy
from gitskills.analysis.family_reporting import source_records
from gitskills.analysis.source_fields import SOURCE_FIELDS
from gitskills.data.families import FamilyLoad
from gitskills.pipelines.provenance import compatible_family
from gitskills.reporting.cohort_records import (
    ResearchInputError, read_scan_report, sample_directed_pairs,
)
from gitskills.reporting.redaction import safe_rule_excerpt
from gitskills.analysis.models import RiskCategory, RuleMatch
from gitskills.tools import analyze_family, scan_family, summarize_cohort
from gitskills.tools._family_args import similarity_policy


@pytest.mark.parametrize("module,options", [
    (analyze_family, []),
    (scan_family, []),
    (summarize_cohort, ["--output", "results"]),
])
def test_family_clis_share_similarity_defaults_and_explicit_options(module, options):
    parser = module.build_parser()
    args = parser.parse_args(["example-family", *options])
    assert similarity_policy(args) == SimilarityPolicy()

    args = parser.parse_args([
        "example-family", *options, "--shingle-size", "7",
        "--min-containment", "0.9", "--min-jaccard", "0.4",
        "--min-shared-shingles", "8", "--direction-margin", "0.2",
    ])
    policy = similarity_policy(args)
    assert policy == SimilarityPolicy(
        shingle_size=7, min_containment=0.9, min_jaccard=0.4,
        min_shared_shingles=8, direction_containment_margin=0.2,
    )


def test_source_record_fields_match_provenance_validation():
    artifact = Artifact(
        artifact_id=5, group_id=3, repo_id=2, name="example",
        normalized_description="example", file_sha="test-sha", content="hello",
        first_commit_at=None, repo_created_at=None, sibling_file_count=0,
        sibling_content_sha="empty", repo_full_name="team/example",
        path="SKILL.md",
    )
    records = source_records(FamilyLoad((artifact,), ()))
    assert tuple(records[0]) == SOURCE_FIELDS
    report = {
        "name": "example", "policy": SimilarityPolicy().to_dict(),
        "artifacts": records, "family": {"clusters": []},
        "skipped_artifacts": [],
    }
    assert compatible_family(report, "example", SimilarityPolicy(), records, [])


def test_shared_excerpt_redacts_sensitive_matches():
    credential = RuleMatch(
        rule_id="CRED-001", category=RiskCategory.CREDENTIAL_ACCESS,
        message="secret", matched_text="API_KEY=private-value",
    )
    invocation = RuleMatch(
        rule_id="CMD-002", category=RiskCategory.COMMAND_EXECUTION,
        message="command", matched_text="npm install",
    )
    assert safe_rule_excerpt(credential) == "[credential-related content redacted]"
    assert safe_rule_excerpt(invocation) == "npm install"


def test_cohort_record_reader_preserves_input_validation():
    with pytest.raises(ResearchInputError, match="expected a scan_family report"):
        read_scan_report({"report_type": "other"})
    sample = [
        {"family": "test", "cluster": 1, "base_artifact_id": 1,
         "derived_artifact_id": 2, "flagged": 0, "indicator_ids": "",
         "uncertain_indicator_ids": "", "coverage_status": "complete",
         "change_type": "skill-only"},
    ]
    selected = sample_directed_pairs(sample, per_stratum=1, seed=580)
    assert selected == [{**sample[0], "sampling_stratum": "unflagged-directed"}]
