#!/usr/bin/env bash
set -eu

# ============================================================
# Configuration
# ============================================================

SQLITE_DB="/c/data/sqlite/agent_skills_release.db"
DB_DIR="/c/data/duckdb"
DB_FILE="${DB_DIR}/agent_skills_release.db"
SQL_RELATIVE_PATH="sql/create_gitskills_duckdb.sql"


# ============================================================
# Prerequisites
# ============================================================

if ! command -v git >/dev/null 2>&1; then
    echo "Error: git is not available on PATH." >&2
    exit 1
fi

if ! command -v duckdb >/dev/null 2>&1; then
    echo "Error: duckdb is not available on PATH." >&2
    exit 1
fi

if ! PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    echo "Error: current directory is not inside a Git repository." >&2
    exit 1
fi

SQL_FILE="${PROJECT_ROOT}/${SQL_RELATIVE_PATH}"


# ============================================================
# Validation
# ============================================================

if [ ! -f "${SQL_FILE}" ]; then
    echo "Error: SQL script not found: ${SQL_FILE}" >&2
    exit 1
fi

if [ ! -f "${SQLITE_DB}" ]; then
    echo "Error: SQLite source database not found: ${SQLITE_DB}" >&2
    exit 1
fi

mkdir -p "${DB_DIR}"

if [ -e "${DB_FILE}" ]; then
    echo "Error: DuckDB database already exists: ${DB_FILE}" >&2
    echo "Remove it first if you want to rebuild the database." >&2
    exit 1
fi


# ============================================================
# Create DuckDB database
# ============================================================

export GITSKILLS_SQLITE_DB="${SQLITE_DB}"

cleanup_on_error() {
    status=$?

    if [ "${status}" -ne 0 ]; then
        echo "Error: DuckDB database creation failed." >&2

        if [ -e "${DB_FILE}" ]; then
            echo "Removing incomplete database: ${DB_FILE}" >&2
            rm -f "${DB_FILE}"
        fi
    fi

    exit "${status}"
}

trap cleanup_on_error EXIT

echo "Creating DuckDB database..."
echo "  SQLite:   ${SQLITE_DB}"
echo "  SQL file: ${SQL_FILE}"
echo "  DuckDB:   ${DB_FILE}"

duckdb "${DB_FILE}" < "${SQL_FILE}"

trap - EXIT

echo "DuckDB database created successfully."
