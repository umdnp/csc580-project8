"""Avoid misclassifying explanatory Markdown as JavaScript network calls."""

import pytest

from gitskills.analysis.analyzer import SkillAnalyzer
from gitskills.analysis.comparator import compare_results
from gitskills.analysis.models import RiskCategory


@pytest.mark.parametrize("prose", [
    "fetch (slower — use only when freshness matters)",
    "fetch (slower than other options)",
    "- fetch (requires extra time and resources)",
])
def test_explanatory_fetch_in_markdown_is_not_network_evidence(prose):
    result = SkillAnalyzer().scan(prose, filename="SKILL.md")
    assert not any(match.rule_id == "NET-002" for match in result.rule_matches)
    assert not result.profile.has(RiskCategory.NETWORK_ACCESS)
    assert not any("NET-002" in evidence.rule_ids for evidence in result.evidence)


@pytest.mark.parametrize("source,filename", [
    ('fetch("/api/users")', "src/client.js"),
    ('fetch (url)', "SKILL.md"),
    ('fetch (url, options)', "SKILL.md"),
    ('`fetch (url, options)`', "SKILL.md"),
    ('```javascript\nfetch (url, options)\n```', "SKILL.md"),
    ('```javascript\nfetch (slower — use only when freshness matters)\n```', "SKILL.md"),
    ('fetch (await getUrl())', "src/client.ts"),
])
def test_valid_fetch_calls_and_explicit_code_remain_detectable(source, filename):
    result = SkillAnalyzer().scan(source, filename=filename)
    assert sum(match.rule_id == "NET-002" for match in result.rule_matches) == 1
    assert result.profile.has(RiskCategory.NETWORK_ACCESS)
    assert any("NET-002" in evidence.rule_ids for evidence in result.evidence)


def test_prose_parenthetical_cannot_introduce_a_network_capability():
    analyzer = SkillAnalyzer()
    base = analyzer.scan("Use fetch for occasional updates.")
    derived = analyzer.scan("Use fetch (slower — use only when freshness matters).")
    comparison = compare_results(base, derived)
    assert not comparison.introduces(RiskCategory.NETWORK_ACCESS)
    assert comparison.rule_deltas == ()
    assert comparison.evidence_added == ()
