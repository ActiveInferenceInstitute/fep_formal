#!/usr/bin/env bash
# =============================================================================
# scripts/00b_install_opengauss_cli.sh
# One-time math-inc/OpenGauss CLI setup for fep_formal.
#
# Clones the OpenGauss repository to ~/.gauss_src and runs the installer
# in headless/plain mode.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Color output ──────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✔${NC}  $*"; }
warn() { echo -e "${YELLOW}⚠${NC}  $*"; }
fail() { echo -e "${RED}✘${NC}  $*" >&2; exit 1; }
info() { echo -e "   $*"; }

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║  fep_formal — OpenGauss CLI Setup                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

GAUSS_SRC_DIR="${HOME}/.gauss_src"

if [[ ! -d "$GAUSS_SRC_DIR" ]]; then
    info "Cloning math-inc/OpenGauss into $GAUSS_SRC_DIR..."
    git clone https://github.com/math-inc/OpenGauss.git "$GAUSS_SRC_DIR"
else
    info "Directory $GAUSS_SRC_DIR exists, pulling latest..."
    cd "$GAUSS_SRC_DIR"
    git pull origin main
fi

cd "$GAUSS_SRC_DIR"

info "Installing OpenGauss headlessly (--plain)..."
./scripts/install.sh --plain

# The installer typically places the binary natively so it's globally available
ok "OpenGauss CLI successfully installed."
echo ""
echo "We recommend adding FEP_FORMAL_REQUIRE_GAUSS=1 to your FEP Lean environment."
echo ""
