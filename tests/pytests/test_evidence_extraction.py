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
    assert chained.rule_counts() == {"FS-002": 1}
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


def test_balanced_makefile_and_shell_substitutions_are_complete_source_evidence():
    source = (
        "# Phase 2: Create root files\n"
        "```makefile\n"
        "@mkdir -p $(GOCACHE) $(GOMODCACHE)\n"
        "@mkdir -p $(CACHE_DIR)\n"
        "@mkdir -p $(shell pwd)\n"
        "```\n"
        "```bash\n"
        "mkdir -p $(CACHE_DIR)\n"
        "```\n"
    )
    result = SkillAnalyzer().scan(source)
    records = [e for e in result.evidence if e.kind == "shell_command"]
    assert result.rule_counts() == {"CMD-001": 1, "FS-001": 4}
    assert len(records) == 4
    assert [r.extraction_status for r in records] == [
        ExtractionStatus.COMPLETE, ExtractionStatus.COMPLETE,
        ExtractionStatus.COMPLETE, ExtractionStatus.COMPLETE,
    ]
    assert records[0].raw_text == "mkdir -p $(GOCACHE) $(GOMODCACHE)"
    assert records[0].context.language == "makefile"


def test_markdown_inline_commands_are_separate_even_with_long_prose_and_apostrophes():
    """Do not merge two backtick commands with the prose between them."""
    from gitskills.analysis.comparator import compare_results
    from gitskills.analysis.risk_assessor import RiskAssessor

    base = (
        '2. Clear caches and reinstall dependencies: reset Metro cache, '
        '`watchman watch-del-all`, remove `node_modules` + lockfile, '
        '`npm install`, then '
        '`cd ios && rm -rf build Pods Podfile.lock && pod install --repo-update`'
    )
    derived = (
        '2. Clear caches and reinstall dependencies **without deleting lockfiles**: '
        'reset Metro cache, `watchman watch-del-all`, remove `node_modules`, '
        "reinstall from the lockfile (`npm ci`, or the package manager's "
        'frozen/immutable install), then '
        '`cd ios && rm -rf build Pods && pod install` — keep `Podfile.lock`. '
        'Deleting lockfiles re-resolves dependency versions and changes the build; '
        'do it only as a last resort with explicit user approval.'
    )
    analyzer = SkillAnalyzer()
    initial = analyzer.scan(base)
    later = analyzer.scan(derived)
    assert initial.rule_counts() == {'CMD-002': 1, 'EXT-002': 1, 'FS-001': 1}
    assert later.rule_counts() == {'CMD-002': 1, 'FS-001': 1}
    assert [(e.raw_text, e.rule_ids) for e in initial.evidence] == [
        ('npm install', ('CMD-002', 'EXT-002')),
        ('rm -rf build Pods Podfile.lock', ('FS-001',)),
    ]
    assert [(e.raw_text, e.rule_ids) for e in later.evidence] == [
        ('npm ci', ('CMD-002',)),
        ('rm -rf build Pods', ('FS-001',)),
    ]
    assert all(e.extraction_status == ExtractionStatus.COMPLETE
               and e.context.kind == 'inline_code'
               for e in (*initial.evidence, *later.evidence))

    comparison = compare_results(initial, later)
    assert [e.raw_text for e in comparison.evidence_removed] == [
        'npm install', 'rm -rf build Pods Podfile.lock',
    ]
    assert [e.raw_text for e in comparison.evidence_added] == [
        'npm ci', 'rm -rf build Pods',
    ]
    assessment = RiskAssessor().assess(comparison)
    assert assessment.coverage == 'complete'
    assert not any(indicator.indicator_id == 'RI-006' for indicator in assessment.supported)


def test_separate_markdown_inline_code_spans_and_fenced_code_remain_distinct():
    source = (
        'Use `npm ci`, then `rm -rf build Pods`; the manager\'s note is prose.\n'
        'Or use ``rm -rf ./cache`` without deleting dependencies.\n'
        '```bash\nrm -rf /tmp/cache\n```\n'
    )
    result = SkillAnalyzer().scan(source)
    assert [(item.raw_text, item.context.kind) for item in result.evidence
            if item.kind == 'shell_command'] == [
        ('npm ci', 'inline_code'),
        ('rm -rf build Pods', 'inline_code'),
        ('rm -rf ./cache', 'inline_code'),
        ('rm -rf /tmp/cache', 'code_block'),
    ]
    assert all(item.extraction_status == ExtractionStatus.COMPLETE
               for item in result.evidence)


def test_markdown_backticks_do_not_turn_urls_into_partial_unresolved_evidence():
    source = (
        "> Read `https://www.cometchat.com/docs/mcp` for details.\n"
        "Download from `https://preview.cometchat.com/downloads/cometchat-builder-react.zip`.\n"
    )
    result = SkillAnalyzer().scan(source)
    assert result.rule_counts() == {"NET-001": 2}
    assert [(e.kind, e.extraction_status, e.raw_text) for e in result.evidence] == [
        ("url_reference", ExtractionStatus.COMPLETE, "https://www.cometchat.com/docs/mcp"),
        ("url_reference", ExtractionStatus.COMPLETE,
         "https://preview.cometchat.com/downloads/cometchat-builder-react.zip"),
    ]


def test_pinned_install_command_stays_inside_inline_markdown_not_surrounding_prose():
    source = (
        "> Use `npm install @cometchat/chat-uikit-react@6.4.3 "
        "@cometchat/calls-sdk-javascript@4.2.5` — **pinned versions from the "
        "canonical repo's README**. Older/newer versions may drift."
    )
    result = SkillAnalyzer().scan(source)
    assert result.rule_counts() == {"CMD-002": 1, "EXT-002": 1}
    commands = [e for e in result.evidence if e.kind == "shell_command"]
    assert len(commands) == 1
    assert commands[0].raw_text == (
        "npm install @cometchat/chat-uikit-react@6.4.3 "
        "@cometchat/calls-sdk-javascript@4.2.5"
    )
    assert commands[0].extraction_status == ExtractionStatus.COMPLETE


def test_complex_shell_command_is_complete_if_source_construct_is_captured():
    from gitskills.analysis.comparator import compare_results
    from gitskills.analysis.risk_assessor import RiskAssessor

    source = 'mkdir -p "$(dirname "$REPORT_PATH")"'
    analyzed = SkillAnalyzer().scan(source)
    command, = analyzed.evidence
    assert command.raw_text == source
    assert command.extraction_status == ExtractionStatus.COMPLETE
    assert "FS-001" in command.rule_ids
    result = RiskAssessor().assess(compare_results(SkillAnalyzer().scan(""), analyzed))
    assert result.coverage == "complete"

    truncated = SkillAnalyzer().scan('mkdir -p "$(dirname "$REPORT_PATH"')
    assert any(e.extraction_status == ExtractionStatus.PARTIAL for e in truncated.evidence)


def test_extended_network_clients_are_balanced_api_evidence():
    from gitskills.analysis.comparator import compare_results
    from gitskills.analysis.risk_assessor import RiskAssessor

    scanner = SkillAnalyzer()
    for code in (
        'fetch("https://example.test/api")',
        'axios.get("https://example.test/api")',
        'axios("https://example.test/api")',
        'httpx.post("https://example.test/api", json=payload)',
    ):
        scanned = scanner.scan(code, filename="scripts/client.js")
        call, = scanned.evidence
        assert call.kind == "api_call" and call.raw_text == code
        assert call.rule_ids == ("NET-001", "NET-002")
        assert call.extraction_status == ExtractionStatus.COMPLETE
        assert ("url", "https://example.test/api") in call.values
        assessment = RiskAssessor().assess(compare_results(scanner.scan(""), scanned))
        assert any(i.indicator_id == "RI-003" for i in assessment.supported)


def test_long_and_tilde_fences_keep_same_normalized_evidence():
    scanner = SkillAnalyzer()
    results = [scanner.scan(f'{marker}bash\necho hello\n{marker}\n')
               for marker in ('```', '````', '~~~', '~~~~')]
    evidence = [next(e for e in r.evidence if e.kind == "shell_code_block") for r in results]
    assert all(e.extraction_status == ExtractionStatus.COMPLETE for e in evidence)
    assert all(dict(e.values)["language"] == "bash" for e in evidence)
    assert len({e.normalized_text for e in evidence}) == 1


def test_exec_extraction_tracks_interpreter_and_script_path():
    command, = SkillAnalyzer().scan('exec ./runner.sh').evidence
    assert ("command", "exec") in command.values
    assert ("arguments", "./runner.sh") in command.values
