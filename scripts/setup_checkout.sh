#!/usr/bin/env bash
# Compose existing checkout workflows; pin/cache policy stays in fep-formal setup.
set -euo pipefail

usage() {
  echo "Usage: bash scripts/setup_checkout.sh [--catalogue-only]"
  echo "Default: locked Python dependencies, two guarded Lean setups, catalogue and figures."
}

catalogue_only=false
case "${1:-}" in
  --catalogue-only) catalogue_only=true ;;
  --help|-h) usage; exit 0 ;;
  "") ;;
  *) usage >&2; exit 2 ;;
esac
if [[ $# -gt 1 ]]; then
  usage >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

for tool in uv git; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "error: install $tool before running this kit" >&2
    exit 1
  fi
done
if [[ "$catalogue_only" == false ]] && ! command -v rsvg-convert >/dev/null 2>&1; then
  echo "error: install librsvg (rsvg-convert) for the native kit's figure gates" >&2
  exit 1
fi

run() {
  printf '+ '
  printf '%q ' "$@"
  printf '\n'
  "$@"
}

PYTHON_VERSION="$(cat .python-version)"
run uv sync --locked --extra dev --python "$PYTHON_VERSION"
run uv run --locked python -c 'import pathlib, sys; expected = pathlib.Path(".python-version").read_text().strip(); actual = f"{sys.version_info.major}.{sys.version_info.minor}"; print(f"validator Python: {actual} (pin: {expected})"); sys.exit(0 if actual == expected else 1)'
run uv lock --check
run uv pip check

if [[ "$catalogue_only" == false ]]; then
  run uv run --locked fep-formal setup
  # Deliberate second pass proves re-entry; both calls retain t-0058's guards.
  run bash scripts/_maint_bootstrap_lean_toolchain.sh
fi

run uv run --locked fep-formal catalogue
run uv run --locked fep-formal atlas --check
run uv run --locked fep-formal dashboard --check
if [[ "$catalogue_only" == false ]]; then
  run uv run --locked python scripts/build_manuscript_figures.py
  run uv run --locked python scripts/build_manuscript_figures.py --check
fi
echo "Checkout setup complete; run the tier's acceptance gates in docs/testing.md."
