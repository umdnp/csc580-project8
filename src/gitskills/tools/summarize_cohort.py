"""Produce reproducible research summaries for one or more GitSkills families."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from gitskills.analysis.family_models import SimilarityPolicy
from gitskills.pipelines.cohort import summarize_cohort
from gitskills.reporting.cohort_summary import ResearchInputError
from ._family_input import read_family_names


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    families = parser.add_mutually_exclusive_group(required=True)
    families.add_argument("name", nargs="?", help="Exact candidate-family name")
    families.add_argument("--input", type=Path,
                          help="UTF-8 list of names, one per line; blank lines and # comments ignored")
    parser.add_argument("--limit", type=int, help="With --input, process at most N families")
    parser.add_argument("--db", type=Path, help="Prepared DuckDB (default: $GITSKILLS_DB)")
    parser.add_argument("--output", required=True, type=Path, help="Research results directory")
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
    parser.add_argument("--shingle-size", type=int, default=5)
    parser.add_argument("--min-containment", type=float, default=0.80)
    parser.add_argument("--min-jaccard", type=float, default=0.30)
    parser.add_argument("--min-shared-shingles", type=int, default=5)
    parser.add_argument("--direction-margin", type=float, default=0.10)
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
        policy = SimilarityPolicy(
            shingle_size=args.shingle_size, min_containment=args.min_containment,
            min_jaccard=args.min_jaccard, min_shared_shingles=args.min_shared_shingles,
            direction_containment_margin=args.direction_margin,
        )
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    try:
        outcome = summarize_cohort(
            names, database=db, results=args.output, policy=policy, edges=args.edges,
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
