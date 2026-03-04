#!/usr/bin/env bash
# Build and upload skill to PyPI (skip CMDOP marketplace).
#
# Usage:
#   ./publish-pypi.sh [skill-dir] [--test-pypi] [--no-bump]
#
# Examples:
#   ./publish-pypi.sh test-scaffold-demo
#   ./publish-pypi.sh test-scaffold-demo --test-pypi
#   cd test-scaffold-demo && ../publish-pypi.sh . --no-bump

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="${1:-.}"
shift || true

# Resolve relative to script dir if not absolute
if [[ "$SKILL_DIR" != /* ]]; then
  SKILL_DIR="$SCRIPT_DIR/$SKILL_DIR"
fi

exec /opt/homebrew/bin/cmdop-skill release "$SKILL_DIR" --no-publish "$@"
