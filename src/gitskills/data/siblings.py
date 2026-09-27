"""DuckDB access for sibling files used by family security review."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from gitskills.analysis.family_risk_models import SiblingFile


class DuckDBSiblingRepository:
    """Load sibling-file rows for selected artifacts."""

    def __init__(self, database: Path | str) -> None:
        self._database = Path(database)

    @property
    def database(self) -> Path:
        return self._database

    def load(self, artifact_ids: Iterable[int]) -> tuple[SiblingFile, ...]:
        """Load sibling files for the requested artifact IDs."""

        ids = tuple(sorted(set(int(artifact_id) for artifact_id in artifact_ids)))
        if not ids:
            return ()

        try:
            import duckdb
        except ImportError as exc:  # pragma: no cover - environment failure
            raise RuntimeError(f"duckdb import failed: {exc}") from exc

        if not self._database.exists():
            raise RuntimeError(f"Database not found: {self._database}")

        placeholders = ", ".join("?" for _ in ids)
        query = f"""
            SELECT id AS sibling_id,
                   artifact_id,
                   entry_name,
                   entry_sha,
                   content,
                   skipped_reason
            FROM artifact_siblings
            WHERE artifact_id IN ({placeholders})
              AND entry_type = 'file'
            ORDER BY artifact_id, id
        """

        try:
            connection = duckdb.connect(str(self._database), read_only=True)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to connect to database {self._database}: {exc}"
            ) from exc

        try:
            rows = connection.execute(query, list(ids)).fetchall()
        finally:
            connection.close()

        return tuple(self._row_to_sibling(row) for row in rows)

    @staticmethod
    def _row_to_sibling(row: tuple[object, ...]) -> SiblingFile:
        sibling_id, artifact_id, entry_name, entry_sha, content, skipped_reason = row

        return SiblingFile(
            sibling_id=int(sibling_id),
            artifact_id=int(artifact_id),
            entry_name=str(entry_name),
            entry_sha=str(entry_sha) if entry_sha is not None else None,
            content=str(content) if content is not None else None,
            skipped_reason=(
                str(skipped_reason) if skipped_reason is not None else None
            ),
        )
