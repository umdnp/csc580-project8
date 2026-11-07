"""Stratified family selection, directed eligibility, and reproducible outputs."""

from hashlib import sha1
import json

import duckdb
import pytest

from gitskills.analysis.family_models import SimilarityPolicy
from gitskills.sampling import families as sampling
from gitskills.tools import family_picker as picker
from gitskills.tools._family_input import read_family_names


BODY = "Read and document the available source project configuration. " * 18


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "families.duckdb"
    with duckdb.connect(str(path)) as connection:
        connection.execute("""
            CREATE TABLE artifacts (
                id BIGINT, file_sha VARCHAR, content VARCHAR,
                repo_full_name VARCHAR, path VARCHAR, first_commit_at VARCHAR
            );
            CREATE TABLE artifact_groupings (
                id BIGINT, artifact_id BIGINT, repo_id BIGINT, name VARCHAR,
                normalized_description VARCHAR, sibling_file_count BIGINT,
                sibling_content_sha VARCHAR
            );
            CREATE TABLE repos (id BIGINT, created_at VARCHAR);
        """)
        records = [
            ("eligible", BODY, "base", "2026-01-01"),
            ("eligible", BODY + "\nDocument the changed URL.\n", "derived", "2026-01-02"),
            ("identical", BODY, "same", "2026-01-01"),
            ("identical", BODY, "same", "2026-01-02"),
            ("unknown", BODY, None, "2026-01-01"),
            ("unknown", BODY, "known", "2026-01-02"),
            ("ambiguous", BODY, "base", None),
            ("ambiguous", BODY, "derived", None),
            ("#unrepresentable", BODY, "base", "2026-01-01"),
            ("#unrepresentable", BODY + "\nUpdate.\n", "derived", "2026-01-02"),
        ]
        for artifact_id, (name, content, sibling, timestamp) in enumerate(records, 1):
            connection.execute(
                "INSERT INTO artifacts VALUES (?, ?, ?, ?, 'skills/skill.md', ?)",
                [artifact_id, sha1(content.encode()).hexdigest(), content, f"team/repo{artifact_id}", timestamp],
            )
            connection.execute("INSERT INTO repos VALUES (?, '2025-01-01')", [artifact_id])
            connection.execute("INSERT INTO artifact_groupings VALUES (?, ?, ?, ?, 'desc', 0, ?)",
                               [artifact_id, artifact_id, artifact_id, name, sibling])
    return path


def test_hash_distinct_query_omits_exact_duplicates_and_bad_names(database):
    candidates = {row["name"]: row for row in sampling.load_candidates(database)}
    assert "eligible" in candidates
    assert candidates["eligible"]["unique_variants"] == 2
    assert "identical" not in candidates
    assert "#unrepresentable" not in candidates
    assert "unknown" in candidates  # Candidate, but not a usable pair.


def test_fast_pair_validation_rejects_unknown_sibling_state(database):
    with duckdb.connect(str(database), read_only=True) as connection:
        assert sampling._hash_pair_counts(connection, "identical")["usable_pair_count"] == 0
        assert sampling._hash_pair_counts(connection, "unknown")["usable_pair_count"] == 0
        assert sampling._hash_pair_counts(connection, "eligible")["usable_pair_count"] == 1


def test_relationship_check_requires_a_usable_primary_directed_edge(database):
    candidates = {row["name"]: row for row in sampling.load_candidates(database)}
    good = sampling.validate_family(database, candidates["eligible"])
    assert good["primary_directed_relationships"] >= 1
    assert good["usable_pair_count"] == 1
    unknown = sampling.validate_family(database, candidates["unknown"])
    assert unknown["primary_directed_relationships"] == 0
    assert unknown["usable_pair_count"] == 0
    ambiguous = sampling.validate_family(database, candidates["ambiguous"])
    assert ambiguous["usable_pair_count"] == 1
    assert ambiguous["primary_directed_relationships"] == 0


def test_stratum_quotas_and_remainder_ties():
    assert sampling.allocate_groups(100) == [20, 55, 20, 4, 1]
    assert sampling.allocate_groups(10) == [2, 6, 2, 0, 0]
    assert sum(sampling.allocate_groups(31)) == 31
    with pytest.raises(ValueError, match="sample_size"):
        sampling.allocate_groups(0)


def test_picker_replaces_failed_candidate_and_tracks_exclusions(tmp_path, monkeypatch):
    db = tmp_path / "unused.duckdb"
    db.touch()
    # A size-1 sample allocates the single slot to Medium.
    candidates = [
        {"name": f"test-{i}", "artifact_count": 3, "unique_variants": 2}
        for i in range(6)
    ]
    monkeypatch.setattr(sampling, "load_candidates", lambda _: candidates)
    checked = []

    class Connection:
        def close(self):
            pass

    monkeypatch.setattr(sampling.duckdb, "connect", lambda *a, **kw: Connection())

    def validate(_, candidate, **kwargs):
        checked.append(candidate["name"])
        return {**candidate, "usable_pair_count": 1,
                "primary_directed_relationships": int(len(checked) > 1)}

    monkeypatch.setattr(sampling, "validate_family", validate)
    sample = sampling.pick_families(database=db, sample_size=1, seed=5801,
                                   exclude_names={"test-0"})
    assert len(sample.names) == 1
    assert sample.names[0] != "test-0"
    assert len(checked) == 2
    assert sample.excluded_count == 1
    assert sample.groups[1]["rejected_families"][0]["reason"] == "no_usable_primary_edge"
    checked.clear()
    again = sampling.pick_families(database=db, sample_size=1, seed=5801,
                                   exclude_names={"test-0"})
    assert sample.names == again.names


def test_cli_writes_directly_and_never_overwrites(database, tmp_path, monkeypatch, capsys):
    # Exercise CLI integration with an actual FamilyAnalyzer on a small test database.
    monkeypatch.setattr(sampling, "STRATA", (("Any", 2, None, 100),))
    output = tmp_path / "selected"
    arguments = ["--db", str(database), "--sample-size", "1", "--seed", "5801", "--output", str(output)]
    # Remove the candidates which cannot pass validation, leaving the directed case.
    excluded = tmp_path / "prior.txt"
    excluded.write_text("ambiguous\nunknown\n", encoding="utf-8")
    arguments += ["--exclude-files", str(excluded), "--verbose"]
    assert picker.main(arguments) == 0
    messages = capsys.readouterr()
    assert messages.out.splitlines() == ["eligible"]
    assert "Checking" in messages.err
    assert read_family_names(output / "families.txt") == ["eligible"]
    manifest = json.loads((output / "sample.json").read_text(encoding="utf-8"))
    assert manifest["seed"] == 5801
    assert manifest["groups"][0]["percentage"] == 100
    assert manifest["similarity_policy"] == SimilarityPolicy().to_dict()
    assert manifest["exclusion_files"][0]["sha256"]
    assert manifest["excluded_families"] == 2
    before = (output / "families.txt").read_bytes()
    assert picker.main(arguments) == 1
    assert "already exist" in capsys.readouterr().err
    assert (output / "families.txt").read_bytes() == before


def test_shortage_does_not_write_files(database, tmp_path, capsys):
    output = tmp_path / "empty"
    assert picker.main(["--db", str(database), "--sample-size", "100", "--output", str(output)]) == 1
    assert "requested" in capsys.readouterr().err
    assert not output.exists()


def test_invalid_exclusion_file_fails_before_sampling(database, tmp_path, capsys):
    output = tmp_path / "out"
    assert picker.main(["--db", str(database), "--exclude-files", str(tmp_path / "missing.txt"),
                        "--output", str(output)]) == 1
    assert not output.exists()
    assert "Unable to generate" in capsys.readouterr().err


def test_name_representation_round_trips():
    assert sampling._representable("code-review; echo harmless")
    for name in ["#comment", " leading", "trailing ", "two\nlines", ""]:
        assert not sampling._representable(name)
