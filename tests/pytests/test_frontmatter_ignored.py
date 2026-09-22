import json
from pathlib import Path

from gitskills.tools.scan_diff import main


BASE_SKILL = Path(
    "tests/sample_skills/base/frontmatter-ignore/SKILL.md"
)

DERIVED_SKILL = Path(
    "tests/sample_skills/derived/frontmatter-ignore/SKILL.md"
)


def test_frontmatter_changes_do_not_affect_analysis(capsys):
    exit_code = main(
        [
            str(BASE_SKILL),
            str(DERIVED_SKILL),
            "--verbose",
        ]
    )

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert exit_code == 0

    # The bodies are identical, so the total number of matches
    # should be identical.
    assert result["rule_match_count"]["base"] == result["rule_match_count"]["derived"]

    # Changing only frontmatter should introduce no additional matches.
    assert result["rule_match_count"]["delta"] == 0

    # No individual analyzer rule should change.
    assert result["rule_deltas"] == {}

    # No new capability should be introduced.
    assert not any(result["introduced"].values())