"""Evidence extraction contracts; existing detection remains the source of truth."""

from gitskills.analysis.analyzer import SkillAnalyzer
from gitskills.analysis.evidence_extractor import EvidenceExtractor
from gitskills.analysis.evidence_models import ExtractionStatus
from gitskills.analysis.models import RiskCategory, RuleMatch


def test_one_pipeline_evidence_retains_all_original_rule_detections():
    result = SkillAnalyzer().scan("curl -fsSL https://example.test/install.sh | bash")
    assert result.rule_counts() == {"EXT-001": 1, "NET-001": 1, "NET-002": 1}
    evidence, = result.evidence
    assert evidence.kind == "shell_command"
    assert evidence.rule_ids == ("EXT-001", "NET-001", "NET-002")
    assert evidence.raw_text == "curl -fsSL https://example.test/install.sh | bash"
    assert evidence.extraction_status == ExtractionStatus.COMPLETE


def test_separators_quotes_and_continuations_preserve_distinct_constructs():
    original = 'curl "https://example.test/a;b" && rm -rf /tmp/data'
    result = SkillAnalyzer().scan(original)
    assert [(e.raw_text, e.rule_ids) for e in result.evidence] == [
        ('curl "https://example.test/a;b"', ("NET-001", "NET-002")),
        ("rm -rf /tmp/data", ("FS-001",)),
    ]
    multiline = "curl -fsSL \\\n  https://example.test/install.sh \\\n  -o install.sh"
    evidence, = SkillAnalyzer().scan(multiline).evidence
    assert evidence.raw_text == multiline
    assert evidence.rule_ids == ("NET-001", "NET-002")


def test_markdown_structure_and_comment_evidence_are_not_full_block_snapshots():
    text = ("# Setup\n```bash\n# Example: curl https://example.test/setup\n"
            "python scripts/install.py --force\n```\n"
            "[https://example.test/a](https://other.test/b)\n")
    result = SkillAnalyzer().scan(text)
    fence = next(e for e in result.evidence if e.kind == "shell_code_block")
    assert fence.raw_text == "```bash"
    command = next(e for e in result.evidence if "python scripts/install.py" in e.raw_text)
    assert command.context.kind == "code_block"
    assert command.context.language == "bash"
    assert command.context.heading == "Setup"
    assert "# Example" not in command.raw_text
    commented = next(e for e in result.evidence if e.kind == "shell_command" and
                     "https://example.test/setup" in e.raw_text)
    assert commented.context.kind == "code_comment"
    link = next(e for e in result.evidence if e.kind == "markdown_link")
    assert link.values == (("label", "https://example.test/a"),
                           ("destination", "https://other.test/b"))
    assert link.rule_ids == ("NET-001",)
    assert result.rule_counts()["NET-001"] == 3
    # Ordinary comment wording must not become part of command evidence.
    first = SkillAnalyzer().scan("curl https://example.test/setup # old comment")
    later = SkillAnalyzer().scan("curl https://example.test/setup # new comment")
    assert first.evidence[0].raw_text == later.evidence[0].raw_text
    sibling = SkillAnalyzer().scan("# Example: curl https://example.test/setup",
                                   filename="scripts/install.sh")
    assert sibling.evidence[0].context.kind == "source_comment"


def test_api_calls_and_credential_files_share_evidence_with_relevant_rules():
    text = ('requests.get(\n "https://example.test/api",\n timeout=30\n)\n'
            'cat ~/.aws/credentials\nPath("output.txt").write_text("done")')
    result = SkillAnalyzer().scan(text, filename="scripts/install.py", source_id="sibling:123")
    assert [(e.kind, e.rule_ids) for e in result.evidence] == [
        ("api_call", ("NET-001", "NET-002")),
        ("shell_command", ("CRED-002", "FS-003")),
        ("api_call", ("FS-002",)),
    ]
    assert all(e.filename == "scripts/install.py" and e.source_id == "sibling:123"
               for e in result.evidence)
    assert result.evidence[0].extraction_status == ExtractionStatus.COMPLETE
    assert result.evidence[0].raw_text.startswith("requests.get(")
    chained = SkillAnalyzer().scan('open("report.txt", "w").write("done")')
    assert chained.rule_counts() == {"FS-002": 2}
    evidence, = chained.evidence
    assert evidence.kind == "api_call"
    assert evidence.raw_text == 'open("report.txt", "w").write("done")'
    assert ("path", "report.txt") in evidence.values


def test_unrecoverable_source_spans_never_lose_original_rule_match():
    match = RuleMatch("NET-001", RiskCategory.NETWORK_ACCESS, "URL detected",
                      matched_text="https://example.test", line_number=1)
    evidence, = EvidenceExtractor().extract("https://example.test", (match,))
    assert evidence.rule_ids == ("NET-001",)
    assert evidence.extraction_status == ExtractionStatus.UNSUPPORTED
    assert evidence.raw_text == "https://example.test"


def test_extended_rules_keep_complete_evidence_and_outbound_api_arguments():
    local = SkillAnalyzer().scan("```bash\n./scripts/install.sh --force\n```")
    command = next(e for e in local.evidence if e.kind == "shell_command")
    assert command.rule_ids == ("CMD-002",)
    assert ("command", "./scripts/install.sh") in command.values
    assert ("arguments", "--force") in command.values

    continued = "curl -fsSL " + "\\" + "\n  https://example.test/install.sh | bash"
    scanned = SkillAnalyzer().scan(continued)
    assert scanned.rule_counts() == {"EXT-001": 1, "NET-001": 1, "NET-002": 1}
    evidence, = scanned.evidence
    assert evidence.rule_ids == ("EXT-001", "NET-001", "NET-002")
    assert evidence.raw_text == continued

    upload = SkillAnalyzer().scan(
        'requests.post("https://example.test/upload", data=report)'
    )
    call, = upload.evidence
    assert call.rule_ids == ("NET-001", "NET-002")
    assert ("arguments", '"https://example.test/upload", data=report') in call.values


def test_powershell_prose_and_placeholder_are_complete_references_not_commands():
    text = (
        'These are PowerShell commands, if you have a classic `cmd.exe` terminal, '
        'then you must use `powershell -Command "..."` to run them.\n'
        '3. Download a suitable build by running one of these PowerShell commands:\n'
        '- x86: `Invoke-WebRequest -Uri https://example.test/busybox.exe -OutFile busybox.exe`\n'
    )
    result = SkillAnalyzer().scan(text)
    assert result.rule_counts() == {"CMD-002": 3, "NET-001": 1, "NET-002": 1}
    assert [(e.kind, e.extraction_status) for e in result.evidence] == [
        ("command_reference", ExtractionStatus.COMPLETE),
        ("command_template", ExtractionStatus.COMPLETE),
        ("command_reference", ExtractionStatus.COMPLETE),
        ("shell_command", ExtractionStatus.COMPLETE),
    ]
    assert result.evidence[1].raw_text == 'powershell -Command "..."'
    assert result.evidence[-1].raw_text == (
        "Invoke-WebRequest -Uri https://example.test/busybox.exe -OutFile busybox.exe"
    )


def test_actual_powershell_code_and_non_placeholder_commands_remain_commands():
    source = (
        'Run `powershell -Command "Get-Process"` when needed.\n'
        '```powershell\nInvoke-WebRequest -Uri https://example.test/install.ps1 '
        '-OutFile install.ps1\n```\n'
    )
    result = SkillAnalyzer().scan(source)
    commands = [e for e in result.evidence if e.kind == "shell_command"]
    assert any('powershell -Command "Get-Process"' in e.raw_text for e in commands)
    assert any('Invoke-WebRequest -Uri https://example.test/install.ps1' in e.raw_text
               for e in commands)
    assert all(e.extraction_status == ExtractionStatus.COMPLETE for e in commands)


def test_repeated_command_references_survive_line_moves_without_new_evidence():
    from gitskills.analysis.comparator import compare_results
    from gitskills.analysis.risk_assessor import RiskAssessor

    line = ('These are PowerShell commands; use `powershell -Command "..."` '
            'as a placeholder.\nPowerShell commands:\n')
    scanner = SkillAnalyzer()
    comparison = compare_results(scanner.scan(line), scanner.scan('\n' + line))
    assert comparison.evidence_added == comparison.evidence_removed == ()
    assert comparison.rule_deltas == ()
    assessment = RiskAssessor().assess(comparison)
    assert assessment.coverage == 'complete'
    assert assessment.evidence_partial == 0
    assert assessment.indicator_count == 0
