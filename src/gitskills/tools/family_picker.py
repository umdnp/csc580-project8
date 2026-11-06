"""Generate a reproducible, stratified family sample without running analysis."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import random
import secrets
import sys
import tempfile
import tomllib

import duckdb

DEFAULT_CONFIG = Path(__file__).with_suffix(".toml")
DEFAULT_EXCLUSIONS = Path(__file__).with_name("family_picker_exclusions.json")
DEFAULT_OUTPUT = Path("output/family_samples")


def load_config(path: Path) -> dict:
    """Read and validate sampling settings before accessing the database."""
    with path.open("rb") as stream:
        config = tomllib.load(stream)
    sampling = config.get("sampling", {})
    size = sampling.get("sample_size")
    if type(size) is not int or size < 1:
        raise ValueError("sampling.sample_size must be a positive integer")
    seed = sampling.get("seed", "")
    if seed != "" and type(seed) is not int:
        raise ValueError('sampling.seed must be an integer or ""')
    if sampling.get("allocation_method") != "largest_remainder":
        raise ValueError("sampling.allocation_method must be largest_remainder")
    minimum = config.get("eligibility", {}).get("min_usable_pairs")
    if type(minimum) is not int or minimum < 1:
        raise ValueError("eligibility.min_usable_pairs must be a positive integer")
    groups = config.get("groups")
    if not isinstance(groups, list) or not groups:
        raise ValueError("At least one group is required")
    names = set()
    previous_max = 1
    percentages = []
    for group in groups:
        name = group.get("name")
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError("Group names must be unique, nonempty strings")
        names.add(name)
        low, high = group.get("min_artifacts"), group.get("max_artifacts")
        if type(low) is not int or previous_max is None or low != previous_max + 1:
            raise ValueError("Groups must cover contiguous, ordered artifact counts starting at 2")
        if high is not None and (type(high) is not int or high < low):
            raise ValueError(f"Invalid max_artifacts for {name}")
        previous_max = high
        value = group.get("percentage")
        if type(value) not in (int, float):
            raise ValueError(f"Invalid percentage for {name}")
        try:
            percent = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError(f"Invalid percentage for {name}") from exc
        if not percent.is_finite() or not 0 <= percent <= 100:
            raise ValueError(f"Percentage for {name} must be between 0 and 100")
        percentages.append(percent)
    if previous_max is not None:
        raise ValueError("The final group must omit max_artifacts")
    if sum(percentages) != 100:
        raise ValueError("Group percentages must total 100")
    return config


def allocate_groups(config: dict) -> list[int]:
    """Allocate every slot, breaking equal remainders in configured group order."""
    size = config["sampling"]["sample_size"]
    quotas = [Decimal(str(g["percentage"])) * size / 100 for g in config["groups"]]
    counts = [int(q) for q in quotas]
    order = sorted(range(len(quotas)), key=lambda i: quotas[i] - counts[i], reverse=True)
    for i in order[:size - sum(counts)]:
        counts[i] += 1
    return counts


def load_candidates(database: Path) -> list[dict]:
    """Count families and exclude known failures from the fixed database snapshot."""
    excluded = set(json.loads(DEFAULT_EXCLUSIONS.read_text(encoding="utf-8"))["families"])
    connection = duckdb.connect(str(database), read_only=True)
    try:
        totals = connection.execute("""
            SELECT name, count(*) FROM artifact_groupings
            WHERE name IS NOT NULL AND trim(name) <> '' GROUP BY name
        """).fetchall()
    finally:
        connection.close()
    return sorted(({"name": name, "artifact_count": count,
                    "potential_pair_count": count * (count - 1) // 2}
                   for name, count in totals if name not in excluded),
                  key=lambda family: family["name"])


def count_pairs(totals: list[tuple], rows: list[tuple]) -> list[dict]:
    """Count differing primary or known sibling hashes without enumerating pairs."""
    families = {
        name: {"name": name, "artifact_count": count, "usable_artifact_count": 0,
               "usable_pair_count": 0, "sibling_qualified_pair_count": 0}
        for name, count in totals
    }
    primary_groups = defaultdict(list)
    for name, primary, sibling, count in rows:
        families[name]["usable_artifact_count"] += count
        primary_groups[name, primary].append((sibling, count))
    for family in families.values():
        n = family["usable_artifact_count"]
        family["usable_pair_count"] = n * (n - 1) // 2
    for (name, _), siblings in primary_groups.items():
        total = sum(count for _, count in siblings)
        known = sum(count for sha, count in siblings if sha is not None)
        equal = sum(count * (count - 1) // 2 for sha, count in siblings if sha is not None)
        different = known * (known - 1) // 2 - equal
        family = families[name]
        family["usable_pair_count"] -= total * (total - 1) // 2 - different
        family["sibling_qualified_pair_count"] += different
    return sorted(families.values(), key=lambda f: f["name"])


def validate_family(connection: duckdb.DuckDBPyConnection, family: dict) -> dict:
    """Count selected-family hashes; content is already verified in this snapshot."""
    members = connection.execute(
        "SELECT artifact_id, sibling_content_sha FROM artifact_groupings WHERE name = ?",
        [family["name"]],
    ).fetchall()
    siblings = dict(members)
    identifiers = list(siblings)
    if not identifiers:
        raise ValueError(f"Family disappeared during sampling: {family['name']}")
    placeholders = ",".join("?" for _ in identifiers)
    records = connection.execute(
        f"SELECT id, file_sha FROM artifacts WHERE id IN ({placeholders})",
        identifiers,
    ).fetchall()
    grouped = defaultdict(int)
    for identifier, primary in records:
        if isinstance(primary, str) and primary.strip():
            grouped[primary, siblings[identifier]] += 1
    rows = [(family["name"], primary, sibling, count)
            for (primary, sibling), count in grouped.items()]
    return count_pairs([(family["name"], family["artifact_count"])], rows)[0]


def select_sample(candidates: list[dict], config: dict, seed: int,
                  validate: Callable[[dict], dict] | None = None) -> tuple[list[dict], list[dict]]:
    """Sample uniformly within each group without silently changing quotas."""
    rng = random.Random(seed)
    selected, summaries = [], []
    minimum = config["eligibility"]["min_usable_pairs"]
    for group, count in zip(config["groups"], allocate_groups(config)):
        pool = sorted((f for f in candidates
                       if f.get("potential_pair_count", f.get("usable_pair_count", 0)) >= minimum
                       and group["min_artifacts"] <= f["artifact_count"]
                       and ("max_artifacts" not in group
                            or f["artifact_count"] <= group["max_artifacts"])),
                      key=lambda f: f["name"])
        if count > len(pool):
            raise ValueError(f"{group['name']}: requested {count} families, but only {len(pool)} are eligible")
        chosen, rejected = [], []
        # Drawing without replacement and rejecting failures is uniform among
        # eligible families, while checking hashes only for proposed families.
        remaining = list(pool)
        while len(chosen) < count and remaining:
            index = rng.randrange(len(remaining))
            candidate = remaining[index]
            remaining[index] = remaining[-1]
            remaining.pop()
            checked = validate(candidate) if validate is not None else candidate
            if checked["usable_pair_count"] < minimum:
                rejected.append(checked["name"])
                continue
            chosen.append({**checked, "group": group["name"]})
        if len(chosen) < count:
            raise ValueError(f"{group['name']}: requested {count} families, but only {len(chosen)} passed pair validation")
        summaries.append({**group, "candidate_families": len(pool),
                          "selected_families": count, "rejected_families": rejected})
        selected.extend(chosen)
    # Ensure the existing pipeline list reader can preserve every selected name.
    if any(f["name"] != f["name"].strip() or len(f["name"].splitlines()) != 1
           or f["name"].startswith("#") for f in selected):
        raise ValueError("A selected name cannot be represented in the pipeline's family-list format")
    return selected, summaries


def save_sample(output: Path, database: Path, config_path: Path, config: dict,
                seed: int, selected: list[dict], summaries: list[dict]) -> Path:
    """Save a new run directory so previous samples are preserved."""
    output.mkdir(parents=True, exist_ok=True)
    created = datetime.now(timezone.utc)
    run = Path(tempfile.mkdtemp(prefix=created.strftime("%Y%m%dT%H%M%SZ-"), dir=output))
    (run / "families.txt").write_text("".join(f["name"] + "\n" for f in selected), encoding="utf-8")
    stat = database.stat()
    manifest = {
        "created_at": created.isoformat(), "seed": seed,
        "database": {"path": str(database.resolve()), "size_bytes": stat.st_size,
                     "modified_time_ns": stat.st_mtime_ns},
        "config_path": str(config_path.resolve()), "config": config,
        "exclusions": json.loads(DEFAULT_EXCLUSIONS.read_text(encoding="utf-8")),
        "pair_definition": "Unordered pairs of loadable artifacts with different primary hashes, or both sibling hashes non-null and different; no repository filter.",
        "groups": summaries, "families": selected,
    }
    (run / "sample.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--db", type=Path, help="DuckDB path (default: GITSKILLS_DB)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Parent directory for saved sample runs")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        database = args.db or (Path(os.environ["GITSKILLS_DB"]) if os.getenv("GITSKILLS_DB") else None)
        if database is None or not database.is_file():
            raise ValueError("Set GITSKILLS_DB or pass --db with an existing DuckDB file")
        configured_seed = config["sampling"].get("seed", "")
        seed = secrets.randbits(128) if configured_seed == "" else configured_seed
        print("Loading family counts and applying the fixed exclusion list...", file=sys.stderr, flush=True)
        candidates = load_candidates(database)
        print("Counting hashes for selected families (without reading content)...", file=sys.stderr, flush=True)
        connection = duckdb.connect(str(database), read_only=True)
        try:
            selected, summaries = select_sample(
                candidates, config, seed, lambda family: validate_family(connection, family),
            )
        finally:
            connection.close()
        run = save_sample(args.output, database, args.config, config, seed, selected, summaries)
    except (OSError, ValueError, TypeError, duckdb.Error) as exc:
        print(f"Unable to generate family sample: {exc}", file=sys.stderr)
        return 1
    print(f"Seed: {seed}", file=sys.stderr)
    for group in summaries:
        print(f"{group['name']}: {group['selected_families']} selected / {group['candidate_families']:,} candidates", file=sys.stderr)
    print(f"Family list: {run / 'families.txt'}", file=sys.stderr)
    print(f"Sample record: {run / 'sample.json'}", file=sys.stderr)
    for family in selected:
        print(family["name"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
