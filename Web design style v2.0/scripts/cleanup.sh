#!/usr/bin/env bash
# WebPPT Maker · Output Cleanup Script
# Removes transient generated outputs (NOT assets, NOT tests, NOT scripts).
#
# Usage:
#   ./scripts/cleanup.sh           # dry-run (lists targets)
#   ./scripts/cleanup.sh --execute # actually delete
#   ./scripts/cleanup.sh --keep    # keep most recent 1 (default: delete all)
#
# Targets:
#   - output_*/          # Generated PPT HTML outputs
#   - tests/_test_output_*/  # Test scratch dirs
#   - tests/__pycache__/     # Python cache

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SKILL_DIR"

DRY_RUN=1
KEEP_RECENT=0

for arg in "$@"; do
  case "$arg" in
    --execute) DRY_RUN=0 ;;
    --keep)    KEEP_RECENT=1 ;;
    --help|-h)
      echo "Usage: $0 [--execute] [--keep]"
      echo "  --execute  Actually delete (default: dry-run)"
      echo "  --keep     Keep the most recent output_* directory"
      exit 0
      ;;
  esac
done

# Collect targets
TARGETS=()

# 1) output_* dirs (skip if --keep, keep most recent)
if ls -d output_* 2>/dev/null >/dev/null; then
  if [ "$KEEP_RECENT" -eq 1 ]; then
    MOST_RECENT=$(ls -1td output_* 2>/dev/null | head -1)
    for d in output_*; do
      [ "$d" != "$MOST_RECENT" ] && TARGETS+=("$d")
    done
    echo "[--keep] preserving most recent: $MOST_RECENT"
  else
    for d in output_*; do
      TARGETS+=("$d")
    done
  fi
fi

# 2) tests/_test_output_*/
for d in tests/_test_output*/; do
  TARGETS+=("$d")
done

# 3) tests/__pycache__/
[ -d "tests/__pycache__" ] && TARGETS+=("tests/__pycache__")

# 4) Pytest caches
for d in tests/__pycache__/; do
  TARGETS+=("$d")
done

if [ ${#TARGETS[@]} -eq 0 ]; then
  echo "✓ Nothing to clean."
  exit 0
fi

# Report
echo "─────────────────────────────────────"
echo "Targets (${#TARGETS[@]}):"
TOTAL_SIZE=0
for t in "${TARGETS[@]}"; do
  if [ -e "$t" ]; then
    SIZE=$(du -sh "$t" 2>/dev/null | cut -f1)
    echo "  $t ($SIZE)"
    SIZE_KB=$(du -sk "$t" 2>/dev/null | cut -f1)
    TOTAL_SIZE=$((TOTAL_SIZE + SIZE_KB))
  fi
done
echo "─────────────────────────────────────"
echo "Total: ~$((TOTAL_SIZE / 1024)) MB"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "[DRY-RUN] Pass --execute to actually delete."
  exit 0
fi

# Execute
for t in "${TARGETS[@]}"; do
  if [ -e "$t" ]; then
    rm -rf "$t"
    echo "  ✗ removed $t"
  fi
done
echo "✓ Cleanup complete."