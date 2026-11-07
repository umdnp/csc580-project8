"""Generate reproducible stratified family samples with usable primary directed edges."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

import duckdb

from gitskills.sampling.families import DEFAULT_OUTPUT, DEFAULT_SAMPLE_SIZE, pick_families, save_sample
from gitskills.tools._family_input import read_family_names


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, help="DuckDB path (default: GITSKILLS_DB)")
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE,
                        help="Number of distinct families (default: 100)")
    parser.add_argument("--seed", type=int, help="Selection seed (default: generate and record one)")
    parser.add_argument("--exclude-files", "--exclusions", nargs="+", type=Path,
                        default=[], metavar="FILE", dest="exclude_files",
                        help="Previously generated families.txt files; separate paths by spaces")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Directory for families.txt and sample.json (default: output/)")
    parser.add_argument("--verbose", action="store_true", help="Report each candidate and validation result")
    args = parser.parse_args(argv)
    try:
        database = args.db or (Path(os.environ["GITSKILLS_DB"]) if os.getenv("GITSKILLS_DB") else None)
        if database is None or not database.is_file():
            raise ValueError("Set GITSKILLS_DB or pass --db with an existing DuckDB file")
        if (args.output / "families.txt").exists() or (args.output / "sample.json").exists():
            raise FileExistsError(f"Sample files already exist in {args.output}; move them before rerunning")
        exclude_names = set()
        for filename in args.exclude_files:
            exclude_names.update(read_family_names(filename))
        sample = pick_families(database=database, sample_size=args.sample_size,
                               seed=args.seed, exclude_names=exclude_names,
                               progress=lambda message: print(message, file=sys.stderr, flush=True),
                               verbose=args.verbose)
        save_sample(sample, output=args.output, database=database,
                    exclude_files=args.exclude_files)
    except (OSError, ValueError, duckdb.Error) as exc:
        print(f"Unable to generate family sample: {exc}", file=sys.stderr)
        return 1
    print(f"Seed: {sample.seed}", file=sys.stderr)
    print(f"Family list: {args.output / 'families.txt'}", file=sys.stderr)
    print(f"Sample record: {args.output / 'sample.json'}", file=sys.stderr)
    for name in sample.names:
        print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
