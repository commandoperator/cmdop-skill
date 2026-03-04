#!/usr/bin/env bash
# Publish skill to local Django dev server (localhost:8000)
#
# Usage:
#   ./publish-local.sh [skill-dir]
#
# Examples:
#   ./publish-local.sh test-scaffold-demo
#   cd test-scaffold-demo && ../publish-local.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="${1:-.}"

# Resolve relative to script dir if not absolute
if [[ "$SKILL_DIR" != /* ]]; then
  SKILL_DIR="$SCRIPT_DIR/$SKILL_DIR"
fi

export CMDOP_API_KEY="cmdop_rJUCKJFTdyH1e8ZY3ZJbg_hIw69WFkrS2f8vgRJ4lhk"

exec /opt/homebrew/bin/cmdop-skill publish --path "$SKILL_DIR" --mode local --json
