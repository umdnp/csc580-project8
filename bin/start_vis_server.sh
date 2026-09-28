#!/usr/bin/env bash
set -eu

ROOT_DIR="$(git rev-parse --show-toplevel)"

echo "Starting Visualization Server..."

cd "$ROOT_DIR"

python -m uvicorn visualization.app:app --db /c/data/duckdb/agent_skills_release.db --host 127.0.0.1 --port 8000 "$@"
