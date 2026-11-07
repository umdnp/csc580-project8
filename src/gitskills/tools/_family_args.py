"""Common command-line arguments for candidate-family workflows."""

from __future__ import annotations

import argparse
from pathlib import Path

from gitskills.analysis.family_models import SimilarityPolicy


def add_family_input(parser: argparse.ArgumentParser, *,
                     name_help: str, input_help: str, limit_help: str,
                     input_metavar: str | None = "FILE") -> None:
    family = parser.add_mutually_exclusive_group(required=True)
    family.add_argument("name", nargs="?", help=name_help)
    options = {"type": Path, "help": input_help}
    if input_metavar is not None:
        options["metavar"] = input_metavar
    family.add_argument("--input", **options)
    parser.add_argument("--limit", type=int, metavar="N" if input_metavar else None,
                        help=limit_help)


def add_similarity_options(parser: argparse.ArgumentParser, *,
                           help_text: dict[str, str] | None = None) -> None:
    defaults = (
        ("--shingle-size", int, 5),
        ("--min-containment", float, 0.80),
        ("--min-jaccard", float, 0.30),
        ("--min-shared-shingles", int, 5),
        ("--direction-margin", float, 0.10),
    )
    for option, value_type, default in defaults:
        kwargs = {"type": value_type, "default": default}
        if help_text and option in help_text:
            kwargs["help"] = help_text[option]
        parser.add_argument(option, **kwargs)


def similarity_policy(args: argparse.Namespace) -> SimilarityPolicy:
    return SimilarityPolicy(
        shingle_size=args.shingle_size,
        min_containment=args.min_containment,
        min_jaccard=args.min_jaccard,
        min_shared_shingles=args.min_shared_shingles,
        direction_containment_margin=args.direction_margin,
    )
