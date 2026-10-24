"""Parse candidate-family lists shared by family command-line tools."""

from __future__ import annotations

from pathlib import Path


def read_family_names(path: Path, limit: int | None = None) -> list[str]:
    """Read ordered, unique family names, ignoring comments and blank lines."""
    names = [
        line.strip()
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if limit is not None:
        names = names[:limit]
    if not names or len(set(names)) != len(names):
        raise ValueError("Family input must contain unique, nonempty names")
    return names
