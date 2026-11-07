"""Produce reproducible research summaries for one or more GitSkills families."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from gitskills.pipelines.cohort import summarize_cohort
from gitskills.reporting.cohort_summary import ResearchInputError
from ._family_input import read_family_names
from ._family_args import add_family_input, add_similarity_options, similarity_policy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_family_input(
        parser, name_help="Exact candidate-family name",
        input_help="UTF-8 list of names, one per line; blank lines and # comments ignored",
        limit_help="With --input, process at most N families", input_metavar=None,
    )
    parser.add_argument("--db", type=Path, help="Prepared DuckDB (default: $GITSKILLS_DB)")
    parser.add_argument("--output", required=True, type=Path, help="Research results directory")
    parser.add_argument("--scan-cache", type=Path,
                        help="Scan cache directory (default: <output>/.scans)")
    parser.add_argument("--edges", choices=("primary", "all"), default="all",
                        help="Directed scan scope (default: all)")
    parser.add_argument("--rescan", action="store_true",
                        help="Regenerate scans even when the cache is compatible")
    parser.add_argument("--per-stratum", type=int, default=5,
                        help="Up to N manual-review pairs per stratum across the whole cohort (default: 5)")
    parser.add_argument("--no-sampling", action="store_true",
                        help="Skip manual-review sampling and full similarity recomputation for cached scans")
    parser.add_argument("--seed", type=int, default=580)
    parser.add_argument("--annotations", type=Path,
                        help="Adjudicated directed-pair review CSV (a copy of the template)")
    parser.add_argument("--relationship-annotations", type=Path,
                        help="Adjudicated relationship review CSV (a copy of the template)")
    parser.add_argument("--approval-reference", help="Reference to cohort selection approval")
    add_similarity_options(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.limit is not None and (args.input is None or args.limit < 1):
        parser.error("--limit requires --input and a positive integer")
    if args.per_stratum < 1:
        parser.error("--per-stratum must be positive")
    if args.no_sampling and (args.annotations or args.relationship_annotations):
        parser.error("--no-sampling cannot be used with review annotations")
    db = args.db or (Path(os.environ["GITSKILLS_DB"]) if os.environ.get("GITSKILLS_DB") else None)
    if db is None:
        print("Database path required: pass --db or set GITSKILLS_DB.", file=sys.stderr)
        return 2
    try:
        names = read_family_names(args.input, args.limit) if args.input else [args.name]
        policy = similarity_policy(args)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    try:
        outcome = summarize_cohort(
            names, database=db, results=args.output, scan_cache=args.scan_cache,
            policy=policy, edges=args.edges,
            rescan=args.rescan, per_stratum=None if args.no_sampling else args.per_stratum,
            seed=args.seed, directed_annotations=args.annotations,
            relationship_annotations=args.relationship_annotations,
            approval_reference=args.approval_reference, progress=print,
        )
    except (OSError, KeyError, TypeError, ValueError, ResearchInputError) as exc:
        print(f"Unable to summarize cohort: {exc}", file=sys.stderr)
        return 1
    print(f"Families: {outcome['family_count']}; directed pairs: {outcome['directed_pairs_analyzed']}; "
          f"artifacts loaded: {outcome['artifacts_loaded']}")
    print(f"Research outputs: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
