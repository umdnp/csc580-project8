"""CLI for aggregating family scans into reproducible research results."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gitskills.reporting.scan_summary import ResearchInputError, summarize, _sample


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path,
                        help="scan_family JSON files, or directories containing those files")
    parser.add_argument("--output", required=True, type=Path, help="Output directory")
    parser.add_argument("--per-stratum", type=int,
                        help="Optionally select up to N pairs per manual-review stratum")
    parser.add_argument("--seed", type=int, default=580)
    parser.add_argument("--annotations", type=Path,
                        help="Optional completed validation_annotations.csv for sample-only metrics")
    parser.add_argument("--family-reports", nargs="+", type=Path,
                        help="Matching analyze_family JSON files or directories for relationship review")
    parser.add_argument("--relationship-annotations", type=Path,
                        help="Adjudicated relationship validation CSV for descriptive relationship metrics")
    args = parser.parse_args(argv)
    if args.per_stratum is not None and args.per_stratum < 1:
        parser.error("--per-stratum must be at least 1")
    if args.annotations is not None and args.per_stratum is None:
        parser.error("--annotations requires --per-stratum to select a review sample")
    if args.family_reports and args.per_stratum is None:
        parser.error("--family-reports requires --per-stratum")
    if args.relationship_annotations and not args.family_reports:
        parser.error("--relationship-annotations requires --family-reports")
    paths = []
    for path in args.reports:
        paths.extend(sorted(path.glob("*.json")) if path.is_dir() else [path])
    family_paths = []
    for path in args.family_reports or []:
        family_paths.extend(sorted(path.glob("*.json")) if path.is_dir() else [path])
    if args.family_reports and not family_paths:
        parser.error("--family-reports did not contain any JSON reports")
    try:
        result = summarize(paths, args.output, per_stratum=args.per_stratum,
                           seed=args.seed, annotations=args.annotations,
                           family_reports=family_paths,
                           relationship_annotations=args.relationship_annotations)
    except (OSError, KeyError, TypeError, ResearchInputError) as exc:
        print(f"Unable to summarize reports: {exc}", file=sys.stderr)
        return 1
    print(f"Families: {result['family_count']}; directed pairs: {result['directed_pairs_analyzed']}; "
          f"pairs with indicators: {result['pairs_with_supported_indicators']}")
    print(f"Research outputs: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
