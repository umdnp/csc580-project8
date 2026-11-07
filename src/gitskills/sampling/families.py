"""Stratified family sampling with optional exclusions and primary-edge validation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import random
import secrets

import duckdb

from gitskills.analysis.family import FamilyAnalyzer
from gitskills.analysis.family_models import SimilarityPolicy
from gitskills.data.families import DuckDBFamilyRepository


DEFAULT_OUTPUT = Path("output")
DEFAULT_SAMPLE_SIZE = 100
# Bounds are inclusive; None denotes an unbounded upper limit.
STRATA = (
    ("Low", 2, 2, 20),
    ("Medium", 3, 15, 55),
    ("Large", 16, 100, 20),
    ("X-Large", 101, 500, 4),
    ("Extreme", 501, None, 1),
)


@dataclass(frozen=True)
class FamilySample:
    """Selected names and evidence needed to reproduce the selection."""

    seed: int
    sample_size: int
    families: list[dict]
    groups: list[dict]
    candidate_count: int
    excluded_count: int
    policy: SimilarityPolicy

    @property
    def names(self) -> list[str]:
        return [family["name"] for family in self.families]


def allocate_groups(size: int) -> list[int]:
    """Apply largest-remainder allocation with ties in stratum order."""
    if type(size) is not int or size < 1:
        raise ValueError("sample_size must be a positive integer")
    quotients = [divmod(size * percent, 100) for _, _, _, percent in STRATA]
    counts = [whole for whole, _ in quotients]
    remaining = size - sum(counts)
    order = sorted(range(len(STRATA)), key=lambda index: quotients[index][1], reverse=True)
    for index in order[:remaining]:
        counts[index] += 1
    return counts


def _representable(name: str) -> bool:
    """Ensure one name round-trips through the shared families.txt reader."""
    return name == name.strip() and len(name.splitlines()) == 1 and not name.startswith("#")


def load_candidates(database: Path | str) -> list[dict]:
    """Find names with at least two distinct primary-and-sibling hash states."""
    connection = duckdb.connect(str(database), read_only=True)
    try:
        rows = connection.execute("""
            WITH variants AS (
                SELECT DISTINCT g.name, a.file_sha, g.sibling_content_sha
                FROM artifact_groupings AS g
                JOIN artifacts AS a ON a.id = g.artifact_id
                WHERE g.name IS NOT NULL AND TRIM(g.name) <> ''
                  AND a.file_sha IS NOT NULL AND TRIM(a.file_sha) <> ''
            ), variant_counts AS (
                SELECT name, COUNT(*) AS unique_variants
                FROM variants GROUP BY name HAVING COUNT(*) >= 2
            ), family_sizes AS (
                SELECT name, COUNT(*) AS artifact_count
                FROM artifact_groupings
                WHERE name IS NOT NULL AND TRIM(name) <> ''
                GROUP BY name
            )
            SELECT v.name, v.unique_variants, f.artifact_count
            FROM variant_counts v JOIN family_sizes f USING (name)
            ORDER BY v.name
        """).fetchall()
    finally:
        connection.close()
    return [
        {"name": name, "unique_variants": variants, "artifact_count": count}
        for name, variants, count in rows if _representable(name)
    ]


def _hash_pair_counts(connection: duckdb.DuckDBPyConnection, name: str) -> dict:
    """Count all usable unordered pairs without building ID-based IN clauses."""
    rows = connection.execute("""
        SELECT a.file_sha, g.sibling_content_sha, COUNT(*)
        FROM artifact_groupings g
        JOIN artifacts a ON a.id = g.artifact_id
        WHERE g.name = ?
          AND a.file_sha IS NOT NULL AND TRIM(a.file_sha) <> ''
          AND a.content IS NOT NULL AND TRIM(a.content) <> ''
        GROUP BY a.file_sha, g.sibling_content_sha
    """, [name]).fetchall()
    primary_groups = defaultdict(list)
    for primary, sibling, count in rows:
        primary_groups[primary].append((sibling, count))
    n = sum(count for _, _, count in rows)
    pairs = n * (n - 1) // 2
    sibling_pairs = 0
    # Same-primary pairs qualify only when both sibling hashes are known and differ.
    for siblings in primary_groups.values():
        total = sum(count for _, count in siblings)
        known = sum(count for sibling, count in siblings if sibling is not None)
        equal = sum(count * (count - 1) // 2 for sibling, count in siblings if sibling is not None)
        different = known * (known - 1) // 2 - equal
        pairs -= total * (total - 1) // 2 - different
        sibling_pairs += different
    return {
        "usable_artifact_count": n,
        "usable_pair_count": pairs,
        "sibling_qualified_pair_count": sibling_pairs,
    }


def validate_family(database: Path | str, family: dict, *,
                    policy: SimilarityPolicy | None = None,
                    connection: duckdb.DuckDBPyConnection | None = None) -> dict:
    """Require at least one usable pair on a primary inferred directed edge."""
    own_connection = connection is None
    if own_connection:
        connection = duckdb.connect(str(database), read_only=True)
    try:
        counts = _hash_pair_counts(connection, family["name"])
    finally:
        if own_connection:
            connection.close()
    result = {**family, **counts, "primary_directed_relationships": 0}
    if counts["usable_pair_count"] < 1:
        return result

    loaded = DuckDBFamilyRepository(database).load_available(family["name"])
    if len(loaded.artifacts) < 2:
        return result
    analysis = FamilyAnalyzer(policy=policy).analyze(loaded.artifacts)
    edges = (
        edge for cluster in analysis.family.clusters
        for edge in cluster.evolution.directed_edges
    )
    result["primary_directed_relationships"] = sum(
        1 for edge in edges
        if edge.source.file_sha != edge.target.file_sha
        or (edge.source.sibling_content_sha is not None
            and edge.target.sibling_content_sha is not None
            and edge.source.sibling_content_sha != edge.target.sibling_content_sha)
    )
    return result


def pick_families(*, database: Path | str, sample_size: int = DEFAULT_SAMPLE_SIZE,
                  seed: int | None = None, exclude_names: Collection[str] = (),
                  policy: SimilarityPolicy | None = None,
                  progress: Callable[[str], None] | None = None,
                  verbose: bool = False) -> FamilySample:
    """Draw a seeded, quota-preserving sample of names with usable primary edges."""
    database = Path(database)
    if not database.is_file():
        raise FileNotFoundError(f"Prepared DuckDB database not found: {database}")
    quotas = allocate_groups(sample_size)
    if seed is None:
        seed = secrets.randbits(128)
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    policy = policy or SimilarityPolicy()
    if progress:
        progress("Loading hash-distinct candidate families from DuckDB...")
    candidates = load_candidates(database)
    # Removing excluded names before drawing preserves unbiased within-stratum sampling.
    excludes = set(exclude_names)
    excluded_count = sum(family["name"] in excludes for family in candidates)
    eligible = [family for family in candidates if family["name"] not in excludes]
    if progress:
        progress(f"Found {len(candidates):,} eligible-by-hash families; "
                 f"excluded {excluded_count:,} previously selected names.")
    pools = [
        [family for family in eligible
         if low <= family["artifact_count"]
         and (high is None or family["artifact_count"] <= high)]
        for _, low, high, _ in STRATA
    ]
    for (name, _, _, _), quota, pool in zip(STRATA, quotas, pools):
        if len(pool) < quota:
            raise ValueError(f"{name}: requested {quota} families but only {len(pool)} "
                             "hash-distinct candidates remain after exclusions")

    rng = random.Random(seed)
    selected: list[dict] = []
    groups: list[dict] = []
    attempted = 0
    rejected_total = 0
    connection = duckdb.connect(str(database), read_only=True)
    try:
        for (name, low, high, percentage), quota, pool in zip(STRATA, quotas, pools):
            if progress:
                progress(f"{name}: selecting {quota} of {len(pool):,} candidates")
            chosen: list[dict] = []
            rejected: list[dict] = []
            remaining = list(pool)  # DuckDB already orders candidates by name.
            while len(chosen) < quota and remaining:
                index = rng.randrange(len(remaining))
                candidate = remaining.pop(index)
                attempted += 1
                if progress:
                    progress(f"Checking candidate {attempted}: {candidate['name']} "
                             f"({name}, {candidate['artifact_count']:,} artifacts; "
                             f"{len(selected) + len(chosen)}/{sample_size} selected)...")
                checked = validate_family(database, candidate, policy=policy, connection=connection)
                if checked["primary_directed_relationships"] < 1:
                    reason = ("no_usable_pairs" if checked["usable_pair_count"] == 0
                              else "no_usable_primary_edge")
                    rejected.append({"name": checked["name"], "reason": reason})
                    rejected_total += 1
                    if progress and verbose:
                        progress(f"  Rejected: {reason} "
                                 f"({checked['usable_pair_count']} usable pairs)")
                    continue
                chosen.append({**checked, "group": name})
                if progress and (verbose or (len(selected) + len(chosen)) % 10 == 0
                                 or len(chosen) == quota):
                    progress(f"[{len(selected) + len(chosen)}/{sample_size}] selected | "
                             f"{attempted} checked | "
                             f"{rejected_total} rejected")
                if progress and verbose:
                    progress(f"  Accepted: {checked['primary_directed_relationships']} "
                             "usable primary directed relationship(s)")
            if len(chosen) < quota:
                raise ValueError(f"{name}: requested {quota}, only {len(chosen)} passed "
                                 f"validation; {len(pool)} candidates after exclusions, "
                                 f"{len(rejected)} rejected")
            groups.append({"name": name, "min_artifacts": low, "max_artifacts": high,
                           "percentage": percentage, "candidate_families": len(pool),
                           "selected_families": len(chosen), "rejected_families": rejected})
            selected.extend(chosen)
    finally:
        connection.close()
    return FamilySample(seed, sample_size, selected, groups, len(candidates), excluded_count, policy)


def save_sample(sample: FamilySample, *, output: Path | str, database: Path | str,
                exclude_files: Sequence[Path | str] = ()) -> Path:
    """Write both sample files into one directory, refusing existing outputs."""
    output = Path(output)
    database = Path(database)
    families_file = output / "families.txt"
    manifest_file = output / "sample.json"
    if families_file.exists() or manifest_file.exists():
        raise FileExistsError(f"Sample files already exist in {output}; archive or remove "
                              "them before creating a new sample")
    stat = database.stat()
    exclusions = []
    for filename in exclude_files:
        path = Path(filename)
        exclusions.append({"path": str(path.resolve()),
                           "sha256": sha256(path.read_bytes()).hexdigest()})
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": sample.seed,
        "sample_size": sample.sample_size,
        "database": {"path": str(database.resolve()), "size_bytes": stat.st_size,
                     "modified_time_ns": stat.st_mtime_ns},
        "eligibility": "At least two distinct primary/sibling hash states and one usable primary directed edge",
        "pair_definition": "Different primary file hashes, or two known and different sibling hashes",
        "similarity_policy": sample.policy.to_dict(),
        "allocation_method": "largest_remainder",
        "candidate_families": sample.candidate_count,
        "excluded_families": sample.excluded_count,
        "exclusion_files": exclusions,
        "groups": sample.groups,
        "families": sample.families,
    }
    output.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents silent overwrite even if another process starts meanwhile.
    with families_file.open("x", encoding="utf-8") as stream:
        stream.write("".join(name + "\n" for name in sample.names))
    try:
        with manifest_file.open("x", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
    except BaseException:
        families_file.unlink()
        raise
    return output
