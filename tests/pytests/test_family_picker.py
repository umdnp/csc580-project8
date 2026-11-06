"""Sampling quotas, eligibility, and reproducible pipeline handoff."""

from itertools import combinations
import json

import duckdb
import pytest

from gitskills.tools import family_picker as picker
from gitskills.tools._family_input import read_family_names


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "families.db"
    connection = duckdb.connect(str(path))
    connection.execute("CREATE TABLE artifact_groupings(name VARCHAR, artifact_id BIGINT, sibling_content_sha VARCHAR)")
    connection.execute("CREATE TABLE artifacts(id BIGINT, content VARCHAR, file_sha VARCHAR)")
    records = [
        ("siblings", "same", "a", "text"),
        ("siblings", "same", "b", "text"),
        ("identical", "same", "a", "text"),
        ("identical", "same", "a", "text"),
        ("unknown", "same", None, "text"),
        ("unknown", "same", "b", "text"),
        ("mixed", "one", None, "text"),
        ("mixed", "one", "a", "text"),
        ("mixed", "one", "a", "text"),
        ("mixed", "one", "b", "text"),
        ("mixed", "two", None, "text"),
        ("mixed", "two", "c", "text"),
    ]
    for identifier, (name, sha, sibling, content) in enumerate(records):
        connection.execute("INSERT INTO artifacts VALUES (?, ?, ?)", [identifier, content, sha])
        connection.execute("INSERT INTO artifact_groupings VALUES (?, ?, ?)", [name, identifier, sibling])
    connection.close()
    return path, records


def test_selected_hash_counts_match_explicit_pairs(database):
    path, records = database
    with duckdb.connect(str(path), read_only=True) as connection:
        result = {f["name"]: picker.validate_family(connection, f)
                  for f in picker.load_candidates(path)}
    for name, family in result.items():
        members = [(sha, sibling) for n, sha, sibling, content in records
                   if n == name and content is not None and content.strip() and sha.strip()]
        expected = sum(a != b or (s is not None and t is not None and s != t)
                       for (a, s), (b, t) in combinations(members, 2))
        assert family["usable_pair_count"] == expected
        assert family["usable_artifact_count"] == len(members)
    assert result["siblings"]["usable_pair_count"] == 1
    assert result["identical"]["usable_pair_count"] == 0
    assert result["unknown"]["usable_pair_count"] == 0


def test_candidate_pool_does_not_read_content(database):
    path, _ = database
    with duckdb.connect(str(path)) as connection:
        connection.execute("ALTER TABLE artifacts DROP COLUMN content")
    candidates = {f["name"]: f for f in picker.load_candidates(path)}
    assert candidates["siblings"]["potential_pair_count"] == 1
    assert candidates["unknown"]["potential_pair_count"] == 1


def test_fixed_snapshot_exclusions_are_applied(database):
    path, _ = database
    exclusions = json.loads(picker.DEFAULT_EXCLUSIONS.read_text(encoding="utf-8"))["families"]
    assert len(exclusions) == len(set(exclusions)) == 617
    with duckdb.connect(str(path)) as connection:
        connection.execute("INSERT INTO artifact_groupings VALUES (?, 999, NULL), (?, 1000, NULL)",
                           [exclusions[0], exclusions[0]])
    assert exclusions[0] not in {f["name"] for f in picker.load_candidates(path)}


def test_failed_candidates_are_replaced_in_the_same_group():
    config = {"sampling": {"sample_size": 2}, "eligibility": {"min_usable_pairs": 1},
              "groups": [{"name": "Low", "min_artifacts": 2, "percentage": 100}]}
    candidates = [{"name": str(n), "artifact_count": 2, "usable_pair_count": 1} for n in range(4)]
    checked = []

    def validate(family):
        checked.append(family["name"])
        return {**family, "usable_pair_count": 0 if len(checked) == 1 else 1}

    selected, summaries = picker.select_sample(candidates, config, 580, validate)
    assert len(selected) == 2
    assert len(checked) == len(set(checked)) == 3
    assert summaries[0]["rejected_families"] == checked[:1]
    assert checked[0] not in {f["name"] for f in selected}


@pytest.mark.parametrize("size, expected", [(10, [2, 6, 1, 1, 0]), (100, [20, 60, 14, 5, 1])])
def test_agreed_allocations(size, expected):
    config = {"sampling": {"sample_size": size}, "groups": [
        {"percentage": percentage} for percentage in [20, 60, 14, 5, 1]]}
    assert picker.allocate_groups(config) == expected


def test_remainder_ties_follow_group_order_and_zero_stays_zero():
    config = {"sampling": {"sample_size": 1}, "groups": [
        {"percentage": 0}, {"percentage": 50}, {"percentage": 50}]}
    assert picker.allocate_groups(config) == [0, 1, 0]


@pytest.mark.parametrize("before, after", [
    ("sample_size = 10", "sample_size = 0"),
    ('seed = ""', 'seed = "abc"'),
    ("percentage = 20", "percentage = 21"),
    ("min_artifacts = 3", "min_artifacts = 2"),
    ("min_usable_pairs = 1", "min_usable_pairs = 0"),
])
def test_invalid_config_rejected(tmp_path, before, after):
    path = tmp_path / "bad.toml"
    text = '''[sampling]
sample_size = 10
seed = ""
allocation_method = "largest_remainder"
[eligibility]
min_usable_pairs = 1
[[groups]]
name = "Low"
min_artifacts = 2
max_artifacts = 2
percentage = 20
[[groups]]
name = "Other"
min_artifacts = 3
percentage = 80
'''
    path.write_text(text.replace(before, after), encoding="utf-8")
    with pytest.raises(ValueError):
        picker.load_config(path)


def test_sampling_is_order_independent_and_without_replacement():
    config = {"sampling": {"sample_size": 5}, "eligibility": {"min_usable_pairs": 1},
              "groups": [{"name": "Low", "min_artifacts": 2, "percentage": 100}]}
    candidates = [{"name": str(n), "artifact_count": 2, "usable_pair_count": 1} for n in range(20)]
    first, _ = picker.select_sample(candidates, config, 999999999999999999999999)
    again, _ = picker.select_sample(list(reversed(candidates)), config, 999999999999999999999999)
    assert first == again
    assert len({f["name"] for f in first}) == 5
    with pytest.raises(ValueError, match="only 2 are eligible"):
        picker.select_sample(candidates[:2], config, 580)


def test_headless_handoff_and_saved_seed_replay(database, tmp_path, monkeypatch, capsys):
    path, _ = database
    config = tmp_path / "picker.toml"
    config.write_text('''[sampling]
sample_size = 2
seed = ""
allocation_method = "largest_remainder"
[eligibility]
min_usable_pairs = 1
[[groups]]
name = "All"
min_artifacts = 2
percentage = 100
''', encoding="utf-8")
    output = tmp_path / "samples"
    monkeypatch.setattr(picker.secrets, "randbits", lambda _: 123456789)
    argv = ["--config", str(config), "--db", str(path), "--output", str(output)]
    assert picker.main(argv) == 0
    printed = capsys.readouterr()
    assert "Seed: 123456789" in printed.err
    run = next(output.iterdir())
    names = read_family_names(run / "families.txt")
    assert printed.out.splitlines() == names
    assert set(names) == {"siblings", "mixed"}
    manifest = json.loads((run / "sample.json").read_text(encoding="utf-8"))
    assert manifest["seed"] == 123456789
    config.write_text(config.read_text().replace('seed = ""', 'seed = 123456789'))
    assert picker.main(argv) == 0
    assert capsys.readouterr().out.splitlines() == names
    assert len(list(output.iterdir())) == 2


def test_shortage_creates_no_sample(database, tmp_path, capsys):
    path, _ = database
    output = tmp_path / "samples"
    assert picker.main(["--db", str(path), "--output", str(output)]) == 1
    assert "only" in capsys.readouterr().err
    assert not output.exists()
