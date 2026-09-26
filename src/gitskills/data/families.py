"""DuckDB access for candidate-family analysis."""

from __future__ import annotations

from pathlib import Path

from gitskills.analysis.family_models import Artifact


_FAMILY_SQL = """
SELECT
    g.id AS group_id,
    g.artifact_id,
    g.repo_id,
    g.name,
    g.normalized_description,
    g.sibling_file_count,
    g.sibling_content_sha,
    a.file_sha,
    a.content,
    a.first_commit_at,
    r.created_at AS repo_created_at
FROM artifact_groupings AS g
JOIN artifacts AS a ON a.id = g.artifact_id
LEFT JOIN repos AS r ON r.id = g.repo_id
WHERE g.name = ?
ORDER BY
    g.id,
    g.artifact_id
"""


class DuckDBFamilyRepository:
    """Load candidate-family artifacts from the project DuckDB database."""

    def __init__(self, database: Path | str) -> None:
        self._database = Path(database)

    @property
    def database(self) -> Path:
        return self._database

    def load(self, name: str) -> tuple[Artifact, ...]:
        """Load every artifact for one exact candidate-family name."""

        try:
            import duckdb
        except ImportError as exc:  # pragma: no cover - environment failure
            raise RuntimeError(
                "duckdb is required to load candidate families"
            ) from exc

        connection = duckdb.connect(str(self._database), read_only=True)
        try:
            rows = connection.execute(_FAMILY_SQL, [name]).fetchall()
        finally:
            connection.close()

        return tuple(self._row_to_artifact(row) for row in rows)

    @staticmethod
    def _row_to_artifact(row: tuple[object, ...]) -> Artifact:
        (
            group_id,
            artifact_id,
            repo_id,
            name,
            normalized_description,
            sibling_file_count,
            sibling_content_sha,
            file_sha,
            content,
            first_commit_at,
            repo_created_at,
        ) = row

        if file_sha is None:
            raise ValueError(f"Artifact {artifact_id} has no file_sha")
        if content is None:
            raise ValueError(f"Artifact {artifact_id} has no content")

        return Artifact(
            artifact_id=int(artifact_id),
            group_id=int(group_id),
            repo_id=int(repo_id) if repo_id is not None else None,
            name=str(name),
            normalized_description=str(normalized_description),
            file_sha=str(file_sha),
            content=str(content),
            first_commit_at=(
                str(first_commit_at) if first_commit_at is not None else None
            ),
            repo_created_at=(
                str(repo_created_at) if repo_created_at is not None else None
            ),
            sibling_file_count=(
                int(sibling_file_count)
                if sibling_file_count is not None
                else None
            ),
            sibling_content_sha=(
                str(sibling_content_sha)
                if sibling_content_sha is not None
                else None
            ),
        )
