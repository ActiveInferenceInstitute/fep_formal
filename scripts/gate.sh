#!/usr/bin/env bash
# The repository's one local gate entry point.
#
# Every arm below executes the exact command CI executes for that purpose; the
# required-check owner is the "Required checks" block in AGENTS.md and
# tests/test_check_inventory.py keeps this file, CI and that block in step.
# Run `bash scripts/gate.sh <arm>`; the default arm is `fast`.
#
# Arms:
#   fast    the composition-inventory test and the gate-inventory contract
#   full    remainder, chrome and floor (the CI acceptance components)
#   remainder  parallel non-serial suite with coverage and its warning log
#   chrome  isolated live Chrome probes with appended coverage
#   floor   measured package line floors over the combined coverage
#   lint    ruff check and ruff format --check
#   types   strict mypy over the package, scripts, docs and two CI helpers
#   catalogue  generated projections and committed publication evidence
#   docs    catalogue plus link, hygiene and cross-reference audits
#   gnn     frozen-custody GNN conformance checks
#   static  deps, composition inventory, catalogue, docs prose, lint, types
#   all     fast, lint, types, docs and gnn (not full)
#
# CI calls the same arms instead of repeating their commands:
#   static job        -> bash scripts/gate.sh static
#   python job        -> bash scripts/gate.sh catalogue
#   documentation job -> bash scripts/gate.sh docs
#   gnn job           -> bash scripts/gate.sh gnn
#
# Wall times measured on the estate host are recorded in docs/gates.md.
# Failing commands are all attempted; the arm exits non-zero if any failed.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Credential-free selection unless the caller explicitly opts in.
export FEP_FORMAL_LIVE_TESTS="${FEP_FORMAL_LIVE_TESTS-0}"

failures=0
run() {
    printf '\n==> %s\n' "$*"
    "$@" || {
        status=$?
        printf 'FAILED (%s): %s\n' "$status" "$*" >&2
        failures=$((failures + 1))
    }
}

# Like run, but retains the CI warning/log artifact. PIPESTATUS keeps the
# command's status even though the pipeline's last writer is tee.
run_log() {
    log="$1"
    shift
    printf '\n==> %s (log %s)\n' "$*" "$log"
    "$@" 2>&1 | tee "$log"
    status=${PIPESTATUS[0]}
    if [ "$status" -ne 0 ]; then
        printf 'FAILED (%s): %s\n' "$status" "$*" >&2
        failures=$((failures + 1))
    fi
}

# The repository's existing fast selection: the composition inventory CI runs
# in its static job, plus the inventory contract that guards this entry point.
# The whole non-serial suite is `full`; it is not a fast default.
arm_fast() {
    run uv run pytest tests/test_composition_source_inventory.py -q -n 0 --no-cov
    run uv run pytest tests/test_check_inventory.py -q -n 0 --no-cov
}

# The three CI acceptance components, each retaining its CI step log. CI calls
# these same arms from its python job, so the command exists once.
arm_remainder() {
    mkdir -p output
    export FEP_FORMAL_COVERAGE_FLOOR_EVIDENCE=1
    run_log output/python-warning-inventory.log uv run pytest tests/ -q -n auto --dist loadgroup \
        --cov=src --cov-report=xml --cov-fail-under=89 -m "not serial_lean" \
        --deselect=tests/test_browser_capture.py::test_live_chrome_blocks_and_records_a_delayed_outbound_request \
        --deselect=tests/test_browser_capture.py::test_live_chrome_replay_terminates_every_profile_writer \
        --junitxml=output/python-acceptance.xml -W always --color=no
    unset FEP_FORMAL_COVERAGE_FLOOR_EVIDENCE
}

arm_chrome() {
    mkdir -p output
    run_log output/live-chrome-warning-inventory.log uv run pytest tests/test_browser_capture.py::test_live_chrome_blocks_and_records_a_delayed_outbound_request \
        tests/test_browser_capture.py::test_live_chrome_replay_terminates_every_profile_writer \
        -q -n 0 --cov=src --cov-append --cov-report=xml --cov-fail-under=89 \
        --junitxml=output/live-chrome-acceptance.xml -W always --color=no
}

arm_floor() {
    run_log output/coverage-floor-summary.json uv run python docs/check_coverage_floors.py --coverage coverage.xml
}

# The full acceptance: the same three sub-arms CI runs, in the same order. The
# membership validator stays in CI, where the step outcomes it consumes exist.
arm_full() {
    arm_remainder
    arm_chrome
    arm_floor
}

arm_lint() {
    run uv run ruff check .
    run uv run ruff format --check src tests scripts docs specs/openai-math-methods specs/cascadia-experiments specs/gnn-runner-execution specs/publication-browser-acceptance specs/identity-cutover
}

arm_types() {
    run uv run mypy src scripts docs specs/publication-browser-acceptance/wait_render_dependencies.py specs/publication-browser-acceptance/native_supplement.py
    run uv run python -m mypy --no-incremental src/fep_lean/__init__.py
}

# Generated projections and the committed publication evidence. The python CI
# job needs exactly this arm; the documentation lane adds the prose audits.
arm_catalogue() {
    run uv run fep-formal catalogue
    run uv run python scripts/_maint_build_topics_catalogue.py --check
    run uv run python scripts/_maint_build_fep_all_lean.py --check
    run uv run python scripts/_maint_build_formal_modules.py --check
    run uv run python scripts/theorem_maturity_audit.py --check
    run uv run python scripts/build_formalism_coverage.py --check
    run uv run python scripts/_maint_build_lean_landscape.py --check
    run uv run python scripts/build_formalism_atlas.py --check
    run uv run python scripts/build_formal_kernel_dashboard.py --check
    run uv run python specs/openai-math-methods/generate_package_methods.py --check
    run uv run python specs/identity-cutover/generate_legacy_stubs.py --check
    run uv run fep-formal --project-root . methods check --output-root docs/mathematical-positioning
    run uv run python scripts/build_render_fonts.py --check
    run uv run python scripts/check_render_log.py --verify-receipt
    run uv run python docs/theorem_ref_audit.py
    run uv run python docs/citation_audit.py
}

arm_docs() {
    arm_catalogue
    # `render_manuscript.py --check` needs the claim-ready native receipt and
    # stays in the native lane; a prose-only pull request must not depend on it.
    run uv run python docs/check_links.py --strict --include-root
    run uv run python docs/md_hygiene.py --strict --include-root
    run uv run python docs/xref_audit.py
    run git diff --check
}

arm_gnn() {
    mkdir -p output
    run uv run python specs/gnn-bridge-q5-artifact-proof/generate_probe.py --check
    run uv run python specs/cascadia-geo-act-proof/generate_probe.py --check
    run uv run python specs/geo-infer-notation-bridge/check_geo_notation_bridge.py --check
    run uv run python -B specs/gnn-runner-execution/validate_retained.py
    run uv run python -B specs/gnn-runner-execution/test_validate_retained.py
    run uv run pytest specs/gnn-semantic-witness-v1/test_composition.py -q -n 0 --no-cov --junitxml=output/gnn-composition-acceptance.xml
}

arm_static() {
    run uv lock --check
    run uv pip check
    run uv run pytest tests/test_composition_source_inventory.py -q -n 0 --no-cov
    run uv run fep-formal catalogue
    run uv run python docs/check_links.py --strict --include-root
    run uv run python docs/md_hygiene.py --strict --include-root
    run uv run python docs/xref_audit.py
    arm_types
    arm_lint
    run git diff --check
}

arm_all() {
    arm_fast
    arm_lint
    arm_types
    arm_docs
    arm_gnn
}

arm="${1:-fast}"
case "$arm" in
    fast | full | remainder | chrome | floor | lint | types | catalogue | docs | gnn | static | all) "arm_$arm" ;;
    -h | --help | help)
        sed -n '2,32p' "$0"
        exit 0
        ;;
    *)
        printf 'unknown arm: %s\n' "$arm" >&2
        printf 'arms: fast full remainder chrome floor lint types catalogue docs gnn static all\n' >&2
        exit 2
        ;;
esac

if [ "$failures" -ne 0 ]; then
    printf '\n%d gate command(s) failed\n' "$failures" >&2
    exit 1
fi
printf '\nall gate commands passed\n'
