#!/usr/bin/env bash
# install.sh: Build and install originctl from the Rust workspace.
# Usage: ./scripts/install.sh [--release]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$WORKSPACE_ROOT"

BUILD_MODE="--release"
if [[ "${1:-}" == "--debug" ]]; then
    BUILD_MODE=""
fi

echo "Building originctl..."
cargo build $BUILD_MODE --package originctl

if [[ -n "$BUILD_MODE" ]]; then
    BIN_PATH="$WORKSPACE_ROOT/target/release/originctl"
else
    BIN_PATH="$WORKSPACE_ROOT/target/debug/originctl"
fi

if [[ -f "$BIN_PATH" ]]; then
    echo "Built successfully: $BIN_PATH"
    echo ""
    echo "To install system-wide (optional):"
    echo "  cp $BIN_PATH /usr/local/bin/originctl"
    echo ""
    echo "To verify:"
    echo "  $BIN_PATH --help"
else
    echo "ERROR: Build succeeded but binary not found at $BIN_PATH"
    exit 1
fi
