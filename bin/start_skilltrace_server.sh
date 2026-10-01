#!/usr/bin/env bash
set -eu

ROOT_DIR="$(git rev-parse --show-toplevel)"

echo "Starting SkillTrace Server..."

cd "$ROOT_DIR"

#python -m uvicorn apps.skilltrace:app --host 127.0.0.1 --port 8000 "$@"
python -m apps.skilltrace --db /c/data/duckdb/agent_skills_release.db --host 127.0.0.1 --port 8000 "$@"
