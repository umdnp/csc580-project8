"""Regression checks for the scanner's rule-count comparison contract."""

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
