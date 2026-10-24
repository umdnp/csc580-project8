"""Regression checks for the scanner's rule-count comparison contract."""

import pytest

from gitskills.analysis.analyzer import SkillAnalyzer
from gitskills.analysis.comparator import compare_results
from gitskills.analysis.models import RiskCategory


def test_changed_url_preserves_rule_counts_without_a_rule_delta():
    analyzer = SkillAnalyzer()
    base = analyzer.scan("See https://example.test/learning/page1")
    derived = analyzer.scan("See https://example.test/learning/page2")

    comparison = compare_results(base, derived)

    assert base.rule_counts() == derived.rule_counts() == {"NET-001": 1}
    assert comparison.rule_deltas == ()
    assert comparison.rule_match_delta == 0
    assert not any(comparison.introduced.to_dict().values())


def test_new_file_operation_preserves_existing_rule_deltas_and_capabilities():
    analyzer = SkillAnalyzer()
    base = analyzer.scan("curl https://example.test/data")
    derived = analyzer.scan("curl https://example.test/data\nrm -rf /tmp/build")

    comparison = compare_results(base, derived)

    assert base.rule_counts() == {"NET-001": 1, "NET-002": 1}
    assert derived.rule_counts() == {"FS-001": 1, "NET-001": 1, "NET-002": 1}
    assert comparison.introduces(RiskCategory.FILESYSTEM_ACCESS)
    assert {delta.rule_id: delta.to_dict() for delta in comparison.rule_deltas} == {
        "FS-001": {"base": 0, "derived": 1, "delta": 1},
    }


@pytest.mark.parametrize("text", ["", "curl https://example.test/data\nrm -rf /tmp/build"])
def test_identical_scans_have_no_changes_even_with_different_source_ids(text):
    analyzer = SkillAnalyzer()
    base = analyzer.scan(text, source_id="artifact:before")
    derived = analyzer.scan(text, source_id="artifact:after")
    comparison = compare_results(base, derived)

    assert not comparison.introduced.capabilities
    assert comparison.rule_deltas == ()
    assert comparison.rule_match_delta == 0
    assert comparison.evidence_added == comparison.evidence_removed == ()
    assert comparison.base is base
    assert comparison.derived is derived


def test_complete_removal_preserves_negative_deltas_and_all_removed_evidence():
    analyzer = SkillAnalyzer()
    base = analyzer.scan("https://example.test/data\nrm -rf /tmp/build")
    comparison = compare_results(base, analyzer.scan(""))

    assert not comparison.introduced.capabilities
    assert comparison.rule_match_delta == -2
    assert comparison.to_dict()["rule_deltas"] == {
        "FS-001": {"base": 1, "derived": 0, "delta": -1},
        "NET-001": {"base": 1, "derived": 0, "delta": -1},
    }
    assert comparison.evidence_added == ()
    assert comparison.evidence_removed == base.evidence
    assert len(comparison.evidence_removed) == 2


def test_more_matches_within_an_existing_category_are_not_a_category_introduction():
    analyzer = SkillAnalyzer()
    comparison = compare_results(
        analyzer.scan("https://example.test/one"),
        analyzer.scan("https://example.test/one\nhttps://example.test/two"),
    )

    assert not comparison.introduces(RiskCategory.NETWORK_ACCESS)
    assert not comparison.introduced.capabilities
    assert comparison.to_dict()["rule_deltas"] == {
        "NET-001": {"base": 1, "derived": 2, "delta": 1},
    }
    assert comparison.rule_match_delta == 1
    assert comparison.evidence_removed == ()
    assert [item.raw_text for item in comparison.evidence_added] == ["https://example.test/two"]


def test_removing_one_rule_does_not_remove_the_remaining_category_signal():
    analyzer = SkillAnalyzer()
    comparison = compare_results(
        analyzer.scan("curl https://example.test/data"),
        analyzer.scan("https://example.test/data"),
    )

    assert comparison.base.profile.capabilities == comparison.derived.profile.capabilities == frozenset({RiskCategory.NETWORK_ACCESS})
    assert not comparison.introduced.capabilities
    assert comparison.to_dict()["rule_deltas"] == {
        "NET-002": {"base": 1, "derived": 0, "delta": -1},
    }
    assert comparison.rule_match_delta == -1
    assert comparison.derived.rule_counts() == {"NET-001": 1}


def test_equal_total_counts_do_not_cancel_changes_in_different_rules():
    analyzer = SkillAnalyzer()
    comparison = compare_results(
        analyzer.scan("rm -rf /tmp/build"),
        analyzer.scan("https://example.test/data"),
    )

    assert comparison.rule_match_delta == 0
    assert comparison.to_dict()["rule_match_count"] == {"base": 1, "derived": 1, "delta": 0}
    assert comparison.to_dict()["rule_deltas"] == {
        "FS-001": {"base": 1, "derived": 0, "delta": -1},
        "NET-001": {"base": 0, "derived": 1, "delta": 1},
    }
    assert comparison.introduced.capabilities == frozenset({RiskCategory.NETWORK_ACCESS})
    assert [item.raw_text for item in comparison.evidence_removed] == ["rm -rf /tmp/build"]
    assert [item.raw_text for item in comparison.evidence_added] == ["https://example.test/data"]


def test_reversing_comparison_swaps_added_removed_evidence_and_negates_deltas():
    analyzer = SkillAnalyzer()
    base = analyzer.scan("rm -rf /tmp/build\nhttps://example.test/retained", source_id="artifact:before")
    derived = analyzer.scan("https://example.test/retained\nhttps://example.test/new\nhttps://example.test/new", source_id="artifact:after")
    forward = compare_results(base, derived)
    reverse = compare_results(derived, base)

    assert len(forward.evidence_added) == 2  # Repeated occurrences are not a set.
    assert len(forward.evidence_removed) == 1
    assert reverse.evidence_added == forward.evidence_removed
    assert reverse.evidence_removed == forward.evidence_added
    assert reverse.rule_match_delta == -forward.rule_match_delta
    assert reverse.to_dict()["rule_deltas"] == {
        rule_id: {"base": counts["derived"], "derived": counts["base"], "delta": -counts["delta"]}
        for rule_id, counts in forward.to_dict()["rule_deltas"].items()
    }
    assert not forward.introduced.capabilities  # Network was already present.
    assert reverse.introduced.capabilities == frozenset({RiskCategory.FILESYSTEM_ACCESS})
