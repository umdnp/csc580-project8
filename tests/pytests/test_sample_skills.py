import json
from pathlib import Path

import pytest

from gitskills.tools.scan_diff import main


PYTEST_DIR = Path(__file__).resolve().parent
TESTS_DIR = PYTEST_DIR.parent
CONFIG_DIR = PYTEST_DIR / "test_configs"


def load_test_configs():
    """Load all sample-skill test configurations."""

    test_cases = []

    for config_path in sorted(CONFIG_DIR.glob("*.json")):
        with config_path.open("r", encoding="utf-8") as file:
            config = json.load(file)

        test_cases.append(
            pytest.param(
                config_path,
                config,
                id=config_path.stem,
            )
        )

    return test_cases


@pytest.mark.parametrize(
    "config_path, expected",
    load_test_configs(),
)
def test_sample_skill(config_path, expected, capsys):
    """Verify a sample skill produces the expected analyzer changes."""

    skill_name = config_path.stem

    base_skill = (
        TESTS_DIR
        / "sample_skills"
        / "base"
        / skill_name
        / "SKILL.md"
    )

    derived_skill = (
        TESTS_DIR
        / "sample_skills"
        / "derived"
        / skill_name
        / "SKILL.md"
    )

    assert base_skill.exists(), (
        f"Missing base skill: {base_skill}"
    )

    assert derived_skill.exists(), (
        f"Missing derived skill: {derived_skill}"
    )

    exit_code = main(
        [
            str(base_skill),
            str(derived_skill),
        ]
    )

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert exit_code == 0

    actual_introduced = {
        capability
        for capability, introduced
        in result["introduced"].items()
        if introduced
    }

    expected_introduced = set(
        expected["introduced"]
    )

    assert actual_introduced == expected_introduced

    assert (
        result["rule_match_count"]
        == expected["rule_match_count"]
    )

    assert (
        result["rule_deltas"]
        == expected["rule_deltas"]
    )