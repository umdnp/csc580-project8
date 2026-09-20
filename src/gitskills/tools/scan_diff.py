"""Compare two text artifacts and report newly introduced capabilities."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Sequence

from gitskills.analysis.analyzer import SkillAnalyzer
from gitskills.analysis.comparator import compare_profiles
from gitskills.analysis.models import Finding


LOGGER = logging.getLogger("gitskills.scan_diff")


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Compare a derived GitSkills artifact against a base artifact "
            "and report newly introduced security-sensitive capabilities."
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
        "--show-profiles",
        action="store_true",
        help="Include base and derived profiles with the introduced capabilities.",
    )
    parser.add_argument(
        "--show-all-findings",
        action="store_true",
        help="Log all rule findings for both artifacts instead of only introduced categories.",
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
    comparison = compare_profiles(
        base=base_result.profile,
        derived=derived_result.profile,
    )

    if args.show_all_findings:
        _log_findings("base", base_result.findings)
        _log_findings("derived", derived_result.findings)
    else:
        introduced_findings = tuple(
            finding
            for finding in derived_result.findings
            if comparison.introduces(finding.category)
        )
        _log_findings("derived", introduced_findings)

    print(
        json.dumps(
            comparison.to_dict(include_profiles=args.show_profiles),
            indent=2,
        )
    )
    return 0


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _log_findings(label: str, findings: tuple[Finding, ...]) -> None:
    for finding in findings:
        location = (
            f" line {finding.line_number}"
            if finding.line_number is not None
            else ""
        )
        LOGGER.info(
            "[%s] %s%s: %s",
            finding.rule_id,
            label,
            location,
            finding.message,
        )


if __name__ == "__main__":
    raise SystemExit(main())
