#!/usr/bin/env bash
# Capped-parallelism build wrapper for the Lean/Mathlib FepSketches build.
# Prevents memory saturation: caps `lake build` at half the available cores,
# always warms the cache first, and runs at nice 10.
# Usage: ./lean/build.sh [lake build args...]  # callable from any directory
set -u
# Fail the wrapper when the left side of a pipe fails: without pipefail the
# `| tee` pipelines below report tee's status, so a failed build exited 0.
# Deliberately no `set -e`: the cache-get failure is tolerated downstream with
# a from-source fallback, and the build status is captured explicitly instead.
set -o pipefail
CORES=$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 8)
BUILD_JOBS=$(( CORES / 2 ))
[ "$BUILD_JOBS" -lt 1 ] && BUILD_JOBS=1

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOGFILE="$SCRIPT_DIR/.lake/build.log"
mkdir -p "$(dirname "$LOGFILE")"

echo "=== build.sh $(date) ===" | tee -a "$LOGFILE"
echo "  cores=$CORES  build_jobs=$BUILD_JOBS  cwd=$PWD" | tee -a "$LOGFILE"
# Resolve to the package dir before invoking lake: lake needs lakefile.lean in
# its cwd, so a repo-root invocation would otherwise fail with
# "no configuration file".
cd "$SCRIPT_DIR"

# Warm build cache (deterministic — pinned mathlib commit v4.33.1)
echo "  lake exe cache get..." | tee -a "$LOGFILE"
nice -n 10 lake exe cache get 2>&1 | tee -a "$LOGFILE"

# Build at reduced priority. NOTE: Lake 5.0 (Lean v4.33.1) removed the `-j`
# flag — parallelism is automatic. `BUILD_JOBS` is kept for the log line and
# future Lake versions that restore an explicit knob.
echo "  lake build (auto-parallelism, target_jobs=$BUILD_JOBS) $*" | tee -a "$LOGFILE"
nice -n 10 lake build "$@" 2>&1 | tee -a "$LOGFILE"
EXIT=${PIPESTATUS[0]}

echo "  exit=$EXIT $(date)" | tee -a "$LOGFILE"
exit $EXIT
