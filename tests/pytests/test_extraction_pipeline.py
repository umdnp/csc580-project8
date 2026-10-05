"""Story 2.3 regression tests for the notebook's loader and extraction cells."""

import json
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from gitskills import SkillAnalyzer, compare_results


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = (
    PROJECT_ROOT
    / "notebooks/extraction_pipeline/samples_extraction_and_exploration.ipynb"
)
SAFE_CONTENT = "Summarize the project status."
URL_CONTENT = "Read https://example.com/one and https://example.com/two."

# Run from the repository root: uv run pytest tests/pytests/test_extraction_pipeline.py -v
# Load the notebook's code cells once for reuse across the tests.
@pytest.fixture(scope="module")
def notebook_cells():
    """Read production code without importing Jupyter or running plot cells."""
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    return [
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    ]


# Find one notebook cell by its opening code and execute it in the test namespace.
def run_cell(cells, starts_with, namespace):
    """Select by code anchor so inserting notebook cells does not break tests."""
    matches = [source for source in cells if source.lstrip().startswith(starts_with)]
    assert len(matches) == 1, f"Expected one notebook cell starting with {starts_with!r}"
    exec(compile(matches[0], str(NOTEBOOK_PATH), "exec"), namespace)


# Create a temporary database with ordered artifacts, multiple groups, and missing metadata.
@pytest.fixture
def sample_database(tmp_path):
    """Small ordered view with interleaved groups and extra source metadata."""
    database = tmp_path / "sample.duckdb"
    with duckdb.connect(str(database)) as connection:
        connection.execute(
            """
            CREATE TABLE artifacts (
                view_order INTEGER, id INTEGER, name VARCHAR, file_sha VARCHAR,
                content VARCHAR, repo_name VARCHAR, first_commit_at VARCHAR
            )
            """
        )
        connection.executemany(
            "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (0, 10, "alpha", "sha-a1", SAFE_CONTENT, "team/alpha", None),
                (1, 20, "beta", "sha-b1", SAFE_CONTENT, "team/beta", "2026-01-01"),
                (2, 11, "alpha", "sha-a2", URL_CONTENT, "team/alpha", "2026-02-01"),
                (3, 30, "singleton", "sha-s1", SAFE_CONTENT, "team/solo", None),
                (4, 21, "beta", "sha-b2", SAFE_CONTENT, "team/beta", "2026-03-01"),
                (5, 12, "alpha", "sha-a3", URL_CONTENT, "team/alpha", "2026-04-01"),
            ],
        )
        connection.execute(
            "CREATE VIEW sample_artifacts AS "
            "SELECT * EXCLUDE (view_order) FROM artifacts ORDER BY view_order"
        )
    return database


# Run the notebook's connection, loader, and validation cells, then close the connection after use.
@pytest.fixture
def pipeline(notebook_cells, sample_database):
    namespace = {
        "json": json,
        "pd": pd,
        "duckdb": duckdb,
        "DB_PATH": sample_database,
        "analyzer": SkillAnalyzer(),
        "compare_results": compare_results,
    }
    run_cell(notebook_cells, "conn = duckdb.connect", namespace)
    try:
        run_cell(notebook_cells, "sample_artifacts = conn.sql", namespace)
        run_cell(notebook_cells, "def artifact_validation_reason", namespace)
        yield namespace
    finally:
        namespace["conn"].close()


# Check that loading preserves row order, source fields, and nulls through a read-only connection.
def test_loader_preserves_view_order_columns_and_null_metadata(pipeline):
    loaded = pipeline["sample_artifacts"]
    assert loaded["id"].tolist() == [10, 20, 11, 30, 21, 12]
    assert pipeline["SOURCE_COLUMNS"] == [
        "id", "name", "file_sha", "content", "repo_name", "first_commit_at"
    ]
    assert loaded.loc[2, "content"] == URL_CONTENT
    assert loaded.loc[2, "repo_name"] == "team/alpha"
    assert pd.isna(loaded.loc[0, "first_commit_at"])
    # Verify the actual notebook connection cannot modify the fixture database.
    with pytest.raises(duckdb.InvalidInputException):
        pipeline["conn"].execute("DELETE FROM artifacts")


# Verify comparisons stay within each name group and produce the expected scanner results.
def test_extraction_compares_adjacent_rows_within_each_name(notebook_cells, pipeline):
    source = pipeline["sample_artifacts"].copy(deep=True)
    run_cell(notebook_cells, "output_df = sample_artifacts", pipeline)
    output = pipeline["output_df"]
    log = pipeline["scan_log_df"]

    assert list(zip(log["base_id"], log["derived_id"])) == [
        (10, 11), (11, 12), (20, 21)
    ]
    assert log["status"].tolist() == ["scanned"] * 3
    pd.testing.assert_frame_equal(output[pipeline["SOURCE_COLUMNS"]], source)
    pd.testing.assert_frame_equal(pipeline["sample_artifacts"], source)
    assert output.loc[[0, 1, 3], "scanner_json"].isna().all()
    assert output.loc[[0, 1, 3], "rules_flagged"].isna().all()
    assert output.loc[[2, 4, 5], "rules_flagged"].tolist() == [1, 0, 0]
    assert str(output["rules_flagged"].dtype) == "Int64"

    payload = json.loads(output.loc[2, "scanner_json"])
    assert payload["rule_deltas"] == {
        "NET-001": {"base": 0, "derived": 2, "delta": 2}
    }
    assert payload["introduced"]["network_access"] is True
    assert payload["base"]["rule_match_count"] == 0
    assert payload["derived"]["rule_match_count"] == 2
    assert json.loads(output.loc[5, "scanner_json"])["rule_deltas"] == {}


# Check that null, empty, and whitespace-only required fields report the correct validation reason.
@pytest.mark.parametrize("field", ["name", "file_sha", "content"])
@pytest.mark.parametrize("missing_value", [None, pd.NA, "", " \t\n"])
def test_validation_reports_missing_required_fields(pipeline, field, missing_value):
    row = {"name": "alpha", "file_sha": "sha-a1", "content": SAFE_CONTENT}
    row[field] = missing_value
    assert pipeline["artifact_validation_reason"](row) == f"missing {field}"


# Verify that an empty artifact reports every missing required field together.
def test_validation_reports_all_missing_fields(pipeline):
    assert pipeline["artifact_validation_reason"]({}) == (
        "missing name; missing file_sha; missing content"
    )


# Verify an invalid artifact skips both neighboring comparisons while valid groups still scan.
@pytest.mark.parametrize("field", ["file_sha", "content"])
def test_invalid_artifact_skips_both_adjacent_pairs(notebook_cells, pipeline, field):
    pipeline["sample_artifacts"].at[2, field] = None
    run_cell(notebook_cells, "output_df = sample_artifacts", pipeline)
    log = pipeline["scan_log_df"]
    assert log["status"].tolist() == ["skipped", "skipped", "scanned"]
    assert log["reason"].tolist() == [
        f"base: valid; derived: missing {field}",
        f"base: missing {field}; derived: valid",
        "",
    ]
    assert log.loc[[0, 1], "rules_flagged"].isna().all()
    assert pipeline["output_df"].loc[[2, 5], "scanner_json"].isna().all()
    assert pipeline["output_df"].loc[[2, 5], "rules_flagged"].isna().all()


# Check that only rules with increased match counts are flagged, counting each rule once.
@pytest.mark.parametrize(
    "base, derived, expected_count, expected_deltas",
    [
        (SAFE_CONTENT, URL_CONTENT, 1, {"NET-001": {"base": 0, "derived": 2, "delta": 2}}),
        (URL_CONTENT, URL_CONTENT, 0, {}),
        (URL_CONTENT, SAFE_CONTENT, 0, {"NET-001": {"base": 2, "derived": 0, "delta": -2}}),
    ],
    ids=["increased-matches-count-as-one-rule", "unchanged", "removed-matches"],
)
def test_scan_pair_counts_only_positive_rule_deltas(
    pipeline, base, derived, expected_count, expected_deltas
):
    count, payload = pipeline["scan_pair"](base, derived)
    assert count == expected_count
    assert payload["rule_deltas"] == expected_deltas


# Save and reload extraction results to verify source values, nullable counts, and scanner JSON survive.
def test_parquet_round_trip_preserves_source_and_scanner_results(
    notebook_cells, pipeline, tmp_path
):
    pipeline["OUTPUT_DIR"] = tmp_path / "results"
    pipeline["OUTPUT_PARQUET"] = pipeline["OUTPUT_DIR"] / "scanner_results.parquet"
    run_cell(notebook_cells, "output_df = sample_artifacts", pipeline)
    run_cell(notebook_cells, "OUTPUT_DIR.mkdir", pipeline)
    run_cell(notebook_cells, "analysis_df = duckdb.read_parquet", pipeline)

    assert pipeline["OUTPUT_PARQUET"].is_file()
    reloaded = pipeline["analysis_df"]
    expected = pipeline["output_df"]
    pd.testing.assert_frame_equal(
        reloaded.drop(columns="scanner_json"), expected.drop(columns="scanner_json")
    )
    # DuckDB/Pandas may infer a string dtype when reloading the object column.
    pd.testing.assert_series_equal(
        reloaded["scanner_json"].astype("string"),
        expected["scanner_json"].astype("string"),
    )
