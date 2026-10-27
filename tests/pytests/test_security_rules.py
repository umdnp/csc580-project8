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


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_shell_code_fences_match_regardless_of_line_endings(newline):
    text = newline.join(["# Example", "```bash", "echo hello", "```", ""])
    matches = RULES["CMD-001"].evaluate(text)

    assert len(matches) == 1
    assert matches[0].line_number == 2
    assert matches[0].matched_text == "```bash"
    assert text[matches[0].start_offset:matches[0].end_offset] == "```bash"


@pytest.mark.parametrize("command", [
    "service nginx restart",
    "service ssh start",
    "service networking stop",
    "service nginx reload",
    "service nginx force-reload",
])
def test_service_modification_requires_service_name_and_action(command):
    assert len(RULES["SYS-002"].evaluate(command)) == 1


@pytest.mark.parametrize("text", [
    "- Direct DB calls in service layer (Flow broken)",
    "Service layer is reaching into controllers (ControllerGhost detected).",
    "Service health is a measure of application behavior.",
    "service nginx status",
])
def test_service_prose_and_read_only_status_are_not_system_modifications(text):
    assert RULES["SYS-002"].evaluate(text) == ()

@pytest.mark.parametrize('text', [
    'Python environment compatibility',
    'npm + OpenAI API | npm + Google Account | All setups |',
    "bash + data formats don't |",
    'bash script) and wasted passes.',
    'Python conventions from',
    'npm installability is important',
])
def test_command_rule_does_not_match_descriptive_prose_or_markdown_tables(text):
    assert RULES['CMD-002'].evaluate(text) == ()


@pytest.mark.parametrize('text', [
    'bash /tmp/config/b8ff-ransomware.sh',
    'python3 scripts/main.py',
    'python3 plugins/saga/scripts/evidence_ledger.py --repo-root .',
    'npm install radon',
    'subprocess.run(["bash", "./install.sh"])',
    'subprocess.Popen(["python", "script.py"])',
    'os.system("echo test")',
    'exec /tmp/run.sh',
    'bash -lc "echo hi"',
    'npx skills add mattpocock/skills --skill=code-review',
])
def test_command_rule_preserves_actual_invocations_and_execution_apis(text):
    assert RULES['CMD-002'].evaluate(text)


def test_touch_prose_is_not_a_file_modification():
    assert RULES['FS-001'].evaluate('If you touch any wiring or entry-point code, the review fails.') == ()
    assert len(RULES['FS-001'].evaluate('touch report')) == 1
    assert len(RULES['FS-001'].evaluate('Run `touch ./report.txt`')) == 1


@pytest.mark.parametrize("fence", (
    "~~~bash", "````bash", "   ~~~~powershell", "~~~sh\r",
))
def test_markdown_fence_extensions_are_detected(fence):
    assert len(RULES["CMD-001"].evaluate(fence + "\n")) == 1


@pytest.mark.parametrize("text", (
    "systemctl status nginx", "systemctl show nginx", "systemctl is-active nginx",
    "crontab -l", "crontab -u alice -l",
))
def test_read_only_system_commands_are_not_modifications(text):
    assert RULES["SYS-002"].evaluate(text) == ()


@pytest.mark.parametrize("text", (
    "systemctl --user enable nginx", "systemctl restart nginx", "crontab -e",
    "crontab -r", "crontab file.cron",
))
def test_system_modification_commands_remain_detected(text):
    assert len(RULES["SYS-002"].evaluate(text)) == 1


@pytest.mark.parametrize("text", (
    "pnpm add package", "yarn add package", "bun add package",
))
def test_additional_package_managers_are_installs(text):
    assert len(RULES["EXT-002"].evaluate(text)) == 1


@pytest.mark.parametrize("text", (
    'fetch("/api/data")', 'axios.get("/api/data")',
    'axios("/api/data")', 'httpx.get("https://example.test/api")',
))
def test_extended_network_clients_are_detected(text):
    assert len(RULES["NET-002"].evaluate(text)) == 1


@pytest.mark.parametrize("text", (
    'response.write("OK")', 'buffer.write("bytes")', 'file.write("bytes")',
))
def test_ambiguous_stream_writes_are_not_file_write_findings(text):
    assert RULES["FS-002"].evaluate(text) == ()


@pytest.mark.parametrize("text", (
    'Path("report.txt").write_text("done")',
    'fs.promises.writeFile("report.txt", "done")',
    'open("report.txt", "w").write("done")',
))
def test_explicit_file_write_apis_are_still_detected(text):
    assert RULES["FS-002"].evaluate(text)


@pytest.mark.parametrize("text", (
    "systemctl status nginx", "systemctl show nginx", "crontab -l",
    "crontab -u alice -l", "service nginx status",
))
def test_read_only_management_operations_keep_command_evidence(text):
    assert len(RULES["CMD-002"].evaluate(text)) == 1
    assert RULES["SYS-002"].evaluate(text) == ()
