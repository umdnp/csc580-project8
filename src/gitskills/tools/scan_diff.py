"""Compare two artifacts and report security-sensitive changes."""

from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Sequence

from gitskills.analysis.analyzer import SkillAnalyzer
from gitskills.analysis.comparator import compare_results
from gitskills.analysis.models import (
    AnalysisComparison,
    RiskCategory,
    RuleMatch,
)


LOGGER = logging.getLogger("gitskills.scan_diff")
MAX_EXCERPT_LENGTH = 120


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Compare a derived GitSkills artifact against a base artifact "
            "and report security-sensitive changes."
        )
    )
    parser.add_argument(
        "base",
        type=Path,
        help="Base or earlier artifact.",
    )
    parser.add_argument(
        "derived",
        type=Path,
        help="Derived or later artifact.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include source profiles and individual rule matches.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the artifact comparison command."""

    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        base_text = _read_text(args.base)
        derived_text = _read_text(args.derived)
    except (OSError, UnicodeError) as exc:
        LOGGER.error("Unable to read input file: %s", exc)
        return 1

    analyzer = SkillAnalyzer()
    base_result = analyzer.scan(base_text)
    derived_result = analyzer.scan(derived_text)
    comparison = compare_results(base_result, derived_result)

    _log_rule_changes(comparison, verbose=args.verbose)

    print(json.dumps(comparison.to_dict(verbose=args.verbose), indent=2))
    return 0


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _log_rule_changes(
    comparison: AnalysisComparison,
    *,
    verbose: bool,
) -> None:
    matches_by_rule: dict[str, list[RuleMatch]] = defaultdict(list)

    for rule_match in comparison.derived.rule_matches:
        matches_by_rule[rule_match.rule_id].append(rule_match)

    for rule_delta in comparison.rule_deltas:
        rule_matches = matches_by_rule.get(rule_delta.rule_id, [])
        description = _rule_description(
            rule_delta.rule_id,
            comparison,
        )

        LOGGER.info(
            "[%s] %d matches (base=%d, delta=%+d): %s",
            rule_delta.rule_id,
            rule_delta.derived,
            rule_delta.base,
            rule_delta.delta,
            description,
        )

        if verbose:
            for rule_match in rule_matches:
                LOGGER.info(
                    "  line %s: %s",
                    rule_match.line_number or "?",
                    _safe_excerpt(rule_match),
                )


def _rule_description(
    rule_id: str,
    comparison: AnalysisComparison,
) -> str:
    for result in (comparison.derived, comparison.base):
        for rule_match in result.rule_matches:
            if rule_match.rule_id == rule_id:
                return rule_match.message

    return "Rule match count changed"


def _safe_excerpt(rule_match: RuleMatch) -> str:
    if rule_match.category is RiskCategory.CREDENTIAL_ACCESS:
        return "[credential-related content redacted]"

    text = " ".join((rule_match.matched_text or "").split())
    if len(text) <= MAX_EXCERPT_LENGTH:
        return text

    return f"{text[:MAX_EXCERPT_LENGTH - 3]}..."


if __name__ == "__main__":
    raise SystemExit(main())
