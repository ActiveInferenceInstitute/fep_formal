#!/usr/bin/env bash
# Both setup entry points share pin validation, acquisition, and deadline handling.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv is unavailable; install uv, then run uv sync --locked --extra dev" >&2
  exit 1
fi
exec uv run --locked --project "$PROJECT_ROOT" fep-formal --project-root "$PROJECT_ROOT" setup
