#!/usr/bin/env bash
set -eu

REPO="umdnp/csc580-project8"
PROJECT_OWNER="umdnp"
PROJECT_NUMBER="4"

ROOT_DIR="$(git rev-parse --show-toplevel)"

python "$ROOT_DIR/scripts/export_backlog.py" \
  --repo "$REPO" \
  --project-owner "$PROJECT_OWNER" \
  --project-number "$PROJECT_NUMBER" \
  "$@"
