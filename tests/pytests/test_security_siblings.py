"""In-memory family scans exercise sibling scope and evidence reporting."""

import json

import pytest

from gitskills.analysis.family_models import Artifact
from gitskills.analysis.family_risk import FamilyRiskAnalyzer
from gitskills.analysis.family_risk_models import SiblingFile


def artifact(artifact_id, sibling_count, sibling_sha):
    return Artifact(
        artifact_id=artifact_id, group_id=artifact_id, repo_id=artifact_id,
        name="constructed-example", normalized_description="",
        file_sha="identical-skill", content="Review the project configuration and summarize the current status.",
        first_commit_at=f"2026-01-{artifact_id:02d}", repo_created_at=None,
        sibling_file_count=sibling_count, sibling_content_sha=sibling_sha,
    )


@pytest.mark.parametrize("entry_name", ["setup.py", "config.json", "instructions.md", "run", "data.uncommon"])
def test_added_sibling_scan_is_extension_independent_and_traceable(entry_name):
    result = FamilyRiskAnalyzer().analyze(
        [artifact(1, 0, "empty"), artifact(2, 1, "added")],
        sibling_files=[SiblingFile(20, 2, entry_name, "new-file", "https://example.com/report")],
    )
    assert result.pairs_analyzed == 1
    assert result.pairs_flagged == 1
    pair, = result.to_dict(verbose=True)["clusters"][0]["flagged_pairs"]
    assert (pair["source_artifact_id"], pair["destination_artifact_id"]) == (1, 2)
    rule, = pair["flagged_rules"]
    assert (rule["rule_id"], rule["category"], rule["surface"]) == ("NET-001", "network_access", "sibling")
    assert (rule["source"], rule["destination"]) == (0, 1)
    source, = rule["finding_sources"]
    assert source == {
        "surface": "sibling", "id": 20, "entry_name": entry_name,
        "matches": [{"line_number": 1, "matched_text": "https://example.com/report"}],
    }


def test_unchanged_sibling_is_not_reported_as_new_evidence():
    result = FamilyRiskAnalyzer().analyze(
        [artifact(1, 1, "before"), artifact(2, 2, "after")],
        sibling_files=[
            SiblingFile(10, 1, "old.md", "same-file", "https://example.com/retained"),
            SiblingFile(20, 2, "renamed.md", "same-file", "https://example.com/retained"),
            SiblingFile(21, 2, "notes.txt", "new-file", "Summarize the project."),
        ],
    )
    assert result.pairs_analyzed == 1
    assert result.pairs_flagged == 0
    assert result.pairs_incomplete == 0


def test_unavailable_sibling_does_not_suppress_available_findings():
    result = FamilyRiskAnalyzer().analyze(
        [artifact(1, 0, "empty"), artifact(2, 2, "added")],
        sibling_files=[
            SiblingFile(20, 2, "missing.py", "missing-file", None),
            SiblingFile(21, 2, "available.md", "new-file", "https://example.com/report"),
        ],
    )
    assert result.pairs_flagged == 1
    assert result.pairs_incomplete == 1
    coverage = result.to_dict()["clusters"][0]["incomplete_pairs"][0]["sibling_scan"]
    assert coverage["unavailable_destination_ids"] == [20]
    assert coverage["incomplete"] is True


def test_verbose_credential_evidence_is_redacted():
    result = FamilyRiskAnalyzer().analyze(
        [artifact(1, 0, "empty"), artifact(2, 1, "added")],
        sibling_files=[SiblingFile(20, 2, "config.txt", "new-file", "OPENAI_API_KEY")],
    )
    payload = result.to_dict(verbose=True)
    rule, = payload["clusters"][0]["flagged_pairs"][0]["flagged_rules"]
    assert rule["rule_id"] == "CRED-001"
    assert rule["finding_sources"][0]["matches"] == [
        {"line_number": 1, "matched_text": "[credential-related content redacted]"},
    ]
    assert "OPENAI_API_KEY" not in json.dumps(payload)
