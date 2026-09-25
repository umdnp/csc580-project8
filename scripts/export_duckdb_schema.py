#!/usr/bin/env python3
"""Export DuckDB schema DDL and small CSV samples."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote as urlquote

try:
    import duckdb
except ImportError:
    print(
        "ERROR: The 'duckdb' Python package is required.\n"
        "Install it with:\n\n"
        "    python -m pip install duckdb\n",
        file=sys.stderr,
    )
    raise SystemExit(2)


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sql_ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def qualified_name(*parts: str) -> str:
    return ".".join(sql_ident(part) for part in parts)


def safe_filename_part(value: str) -> str:
    return urlquote(value, safe="._-")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export DuckDB schema DDL and small CSV samples.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  %(prog)s source.duckdb output/
  %(prog)s source.duckdb output/ --sample-rows 10
  %(prog)s source.duckdb output/ --sample-mode random
  %(prog)s source.duckdb output/ --sample-rows 0
  %(prog)s source.duckdb output/ --overwrite
""",
    )
    parser.add_argument(
        "source",
        type=Path,
        help="source DuckDB database",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="directory for the DDL and sample files",
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=20,
        metavar="N",
        help="rows to export per table; use 0 to skip samples (default: 20)",
    )
    parser.add_argument(
        "--sample-mode",
        choices=("first", "random"),
        default="first",
        help=(
            "use LIMIT ('first') or reservoir sampling ('random'); "
            "random sampling may scan the table (default: first)"
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace files from a previous export",
    )
    return parser.parse_args()


def export_ddl(conn, source: Path, ddl_file: Path, duckdb_version: str) -> int:
    with tempfile.TemporaryDirectory(prefix="duckdb_schema_") as temp_dir:
        conn.execute("ATTACH ':memory:' AS temp_schema")
        try:
            conn.execute("COPY FROM DATABASE src TO temp_schema (SCHEMA)")
            conn.execute("USE temp_schema")
            conn.execute(f"EXPORT DATABASE {sql_string(temp_dir)}")

            schema_sql = (Path(temp_dir) / "schema.sql").read_text(encoding="utf-8")
        finally:
            conn.execute("USE src")
            conn.execute("DETACH temp_schema")

    ddl_parts = [
        "-- DuckDB schema DDL\n",
        f"-- Source: {source.name}\n",
        f"-- DuckDB: {duckdb_version}\n\n",
        schema_sql.rstrip(),
        "\n",
    ]

    index_rows = conn.execute(
        """
        SELECT sql
        FROM duckdb_indexes()
        WHERE database_name = 'src'
          AND sql IS NOT NULL
        ORDER BY schema_name, table_name, index_name
        """
    ).fetchall()

    if index_rows:
        ddl_parts.append("\n-- Secondary indexes\n\n")
        for (index_sql,) in index_rows:
            ddl_parts.append(index_sql.rstrip().rstrip(";") + ";\n")

    ddl_file.write_text("".join(ddl_parts), encoding="utf-8")

    macro_count = conn.execute(
        """
        SELECT count(*)
        FROM duckdb_functions()
        WHERE database_name = 'src'
          AND NOT internal
          AND function_type IN ('macro', 'table_macro')
        """
    ).fetchone()[0]

    return macro_count


def export_samples(
    conn,
    tables: list[tuple[str, str]],
    samples_dir: Path,
    sample_rows: int,
    sample_mode: str,
) -> int:
    samples_dir.mkdir(parents=True, exist_ok=True)
    errors = 0

    for number, (schema_name, table_name) in enumerate(tables, start=1):
        filename = (
            f"{safe_filename_part(schema_name)}__"
            f"{safe_filename_part(table_name)}.csv"
        )
        sample_file = samples_dir / filename
        table_ref = qualified_name("src", schema_name, table_name)

        if sample_mode == "random":
            query = (
                f"SELECT * FROM {table_ref} "
                f"USING SAMPLE reservoir({sample_rows} ROWS)"
            )
        else:
            query = f"SELECT * FROM {table_ref} LIMIT {sample_rows}"

        copy_sql = (
            f"COPY ({query}) "
            f"TO {sql_string(str(sample_file))} "
            "(FORMAT CSV, HEADER TRUE)"
        )

        try:
            conn.execute(copy_sql)
            print(
                f"  [{number:>3}/{len(tables)}] "
                f"{schema_name}.{table_name}"
            )
        except Exception as exc:
            errors += 1
            sample_file.unlink(missing_ok=True)
            print(
                f"  [{number:>3}/{len(tables)}] "
                f"{schema_name}.{table_name} - ERROR: {exc}",
                file=sys.stderr,
            )

    return errors


def main() -> int:
    args = parse_args()

    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()

    ddl_file = output / f"{source.stem}.ddl"
    samples_dir = output / "samples"

    if args.sample_rows < 0:
        print("ERROR: --sample-rows must be >= 0.", file=sys.stderr)
        return 2

    if not source.exists():
        print(f"ERROR: Source database not found: {source}", file=sys.stderr)
        return 2

    if not source.is_file():
        print(f"ERROR: Source path is not a file: {source}", file=sys.stderr)
        return 2

    output.mkdir(parents=True, exist_ok=True)

    existing = [ddl_file] if ddl_file.exists() else []
    if args.sample_rows > 0 and samples_dir.exists():
        existing.append(samples_dir)

    if existing and not args.overwrite:
        paths = "\n".join(f"  {path}" for path in existing)
        print(
            "ERROR: Output already exists. Re-run with --overwrite to replace it:",
            file=sys.stderr,
        )
        print(paths, file=sys.stderr)
        return 2

    if args.overwrite:
        if ddl_file.exists():
            ddl_file.unlink()
        if args.sample_rows > 0 and samples_dir.exists():
            shutil.rmtree(samples_dir)

    conn = duckdb.connect(database=":memory:")

    try:
        conn.execute(f"ATTACH {sql_string(str(source))} AS src (READ_ONLY)")

        duckdb_version = conn.execute("SELECT version()").fetchone()[0]

        tables = conn.execute(
            """
            SELECT schema_name, table_name
            FROM duckdb_tables()
            WHERE database_name = 'src'
              AND NOT internal
              AND NOT temporary
            ORDER BY schema_name, table_name
            """
        ).fetchall()

        print(f"DuckDB version: {duckdb_version}")
        print(f"Source:         {source}")
        print(f"Output:         {output}")
        print()

        print("[1/2] Exporting DDL...")
        macro_count = export_ddl(conn, source, ddl_file, duckdb_version)
        print(f"  Created: {ddl_file}")

        if macro_count:
            print(
                f"  WARNING: {macro_count} custom macro(s) were not included in the DDL.",
                file=sys.stderr,
            )

        print()

        if args.sample_rows == 0:
            print("[2/2] Sample export disabled (--sample-rows 0).")
            sample_errors = 0
        else:
            mode = "random " if args.sample_mode == "random" else ""
            print(
                f"[2/2] Exporting up to {args.sample_rows} "
                f"{mode}rows per table..."
            )

            sample_errors = export_samples(
                conn,
                tables,
                samples_dir,
                args.sample_rows,
                args.sample_mode,
            )

    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1

    finally:
        conn.close()

    print()
    print("Done.")
    print(f"  DDL     : {ddl_file}")

    if args.sample_rows > 0:
        print(f"  Samples : {samples_dir}")

    if sample_errors:
        print(
            f"\nWARNING: {sample_errors} table sample(s) "
            "could not be exported.",
            file=sys.stderr,
        )
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
