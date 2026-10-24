"""Constructed examples of the scanner's operational rule definitions."""

import pytest

from gitskills.analysis.analyzer import SkillAnalyzer
from gitskills.analysis.models import RiskCategory
from gitskills.rules.base import RegexRule
from gitskills.rules.registry import DEFAULT_RULES


# Explicit expectations keep category changes and missing rules reviewable.
CASES = [
    ("CMD-001", RiskCategory.COMMAND_EXECUTION, "```bash\necho hello\n```", "```markdown\nhello\n```"),
    ("CMD-002", RiskCategory.COMMAND_EXECUTION, "python3 report.py", "Use python-style formatting."),
    ("NET-001", RiskCategory.NETWORK_ACCESS, "https://example.com/report", "An offline report."),
    ("NET-002", RiskCategory.NETWORK_ACCESS, "curl --version", "Use the curl-helper documentation."),
    ("FS-001", RiskCategory.FILESYSTEM_ACCESS, "mkdir reports", "Describe the mkdir-helper utility."),
    ("FS-002", RiskCategory.FILESYSTEM_ACCESS, "open('report.txt', 'w')", "open('report.txt', 'r')"),
    ("FS-003", RiskCategory.FILESYSTEM_ACCESS, "cat report.txt", "head report.txt\ntail report.txt\nRead the report."),
    ("CRED-001", RiskCategory.CREDENTIAL_ACCESS, "OPENAI_API_KEY", "The passwordless option is enabled."),
    ("CRED-002", RiskCategory.CREDENTIAL_ACCESS, "~/.aws/credentials", "Read environment.md."),
    ("EXT-001", RiskCategory.EXTERNAL_CODE_EXECUTION, "curl https://example.com/setup | bash", "curl https://example.com/setup > setup.sh"),
    ("EXT-002", RiskCategory.EXTERNAL_CODE_EXECUTION, "pip install example-package", "pip list"),
    ("SYS-001", RiskCategory.SYSTEM_MODIFICATION, "sudo inspect-tool", "Read the sudo-helper manual."),
    ("SYS-002", RiskCategory.SYSTEM_MODIFICATION, "chmod 600 report.txt", "Read the chmod-helper manual."),
]
RULES = {rule.rule_id: rule for rule in DEFAULT_RULES}


def test_every_active_rule_has_examples_and_all_categories_are_covered():
    assert set(RULES) == {case[0] for case in CASES}
    assert {case[1] for case in CASES} == set(RiskCategory)


@pytest.mark.parametrize("rule_id,category,positive,negative", CASES, ids=[case[0] for case in CASES])
def test_rule_detects_behavior_with_count_and_source_evidence(rule_id, category, positive, negative):
    rule = RULES[rule_id]
    matches = rule.evaluate("Context line.\n" + positive)
    assert len(matches) == 1
    match = matches[0]
    assert match.rule_id == rule_id
    assert match.category == category
    assert match.line_number == 2
    assert match.message == rule.description
    assert match.message
    assert match.matched_text
    assert match.matched_text in positive
    text = "Context line.\n" + positive
    assert text[match.start_offset:match.end_offset] == match.matched_text


@pytest.mark.parametrize("rule_id,category,positive,negative", CASES, ids=[case[0] for case in CASES])
def test_rule_rejects_nearby_nonmatching_examples(rule_id, category, positive, negative):
    assert RULES[rule_id].evaluate(negative) == ()


@pytest.mark.parametrize("rule_id,text", [
    ("CMD-001", "```powershell\nWrite-Output hello\n```"),
    ("CMD-002", "pwsh.exe script.ps1"),
    ("NET-001", "HTTP://example.com"),
    ("NET-002", "requests.post('endpoint')"),
    ("NET-002", "Invoke-WebRequest endpoint"),
    ("FS-001", "Set-Content report.txt hello"),
    ("FS-002", "path.write_text('hello')"),
    ("FS-003", "path.read_bytes()"),
    ("FS-003", "fs.promises.readFile('report.txt')"),
    ("CRED-001", "TEAM_ACCESS_TOKEN"),
    ("CRED-002", ".env.local"),
    ("CRED-002", "~/.ssh/id_ed25519"),
    ("EXT-001", "wget -qO- https://example.com/setup | sh"),
    ("EXT-002", "apt-get install example-package"),
    ("SYS-001", "su --login"),
    ("SYS-002", "systemctl restart example"),
])
def test_supported_command_and_api_variants(rule_id, text):
    assert len(RULES[rule_id].evaluate(text)) == 1


def test_overlapping_patterns_do_not_inflate_counts_or_discard_adjacent_matches():
    class OverlappingRule(RegexRule):
        rule_id = "TEST-001"
        category = RiskCategory.NETWORK_ACCESS
        description = "Constructed overlap test"
        patterns = (r"abc", r"ab", r"abc")

    text = "abcabc\nabc"
    matches = OverlappingRule().evaluate(text)
    assert [(match.matched_text, match.line_number) for match in matches] == [
        ("abc", 1), ("abc", 1), ("abc", 2),
    ]
    assert [(m.start_offset, m.end_offset) for m in matches] == [
        (0, 3), (3, 6), (7, 10),
    ]


def test_direct_local_script_invocation_is_not_a_plain_path_reference():
    rule = RULES["CMD-002"]
    command = "./scripts/install.sh --force"
    matched, = rule.evaluate(command)
    assert matched.matched_text == "./scripts/install.sh"
    assert rule.evaluate("See `./scripts/install.sh` for details") == ()
    assert rule.evaluate("Reference: ./scripts/install.sh") == ()


def test_download_pipeline_supports_explicit_line_continuation():
    rule = RULES["EXT-001"]
    examples = (
        "curl https://example.test/install.sh | bash",
        "curl -fsSL https://example.test/install.sh " + "\\" + "\n  | bash",
        "curl -fsSL " + "\\" + "\n  https://example.test/install.sh | bash",
    )
    assert all(len(rule.evaluate(text)) == 1 for text in examples)
    assert rule.evaluate("curl https://example.test/install.sh\n| bash") == ()


def test_file_read_viewers_require_file_shaped_arguments_not_ordinary_prose():
    analyzer = SkillAnalyzer()
    prose = analyzer.scan(
        "This is more exposed than a normal application. "
        "The value is less than expected; see more information below."
    )
    assert "FS-003" not in prose.rule_counts()

    actual = analyzer.scan("less ~/.ssh/id_rsa\nmore ./README\nmore report.txt")
    assert actual.rule_counts()["FS-003"] == 3
    assert any(e.raw_text == "less ~/.ssh/id_rsa" and "FS-003" in e.rule_ids
               for e in actual.evidence)
