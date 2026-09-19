#!/bin/bash
# Wait for any in-flight book render, then continue with the next range.
#
# Exists because editing pipeline code while a render is running broke chapters
# 7-14: book_fish.py spawns a fresh render_chapter_fish.py per chapter, so a
# half-applied refactor was picked up mid-run and eight chapters failed with
# NameError. Chaining keeps the machine busy without anyone touching source
# between ranges.
#
# Usage: ./chain_book.sh <first> <last> [logfile]

set -u

FIRST="${1:?first chapter}"
LAST="${2:?last chapter}"
LOG="${3:-out/book-${FIRST}-${LAST}.log}"

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE" || exit 1

export PYTHONPATH=/Users/jessica/Documents/frontier-book/audiobook-studio/tools/vendor/mlx-audio

echo "waiting for any running book_fish to finish..."
while pgrep -f "book_fish.py" >/dev/null; do
    sleep 30
done
echo "clear; starting chapters ${FIRST}-${LAST} at $(date)"

# The range starts at 1 deliberately: the resume check skips chapters that already
# have audio AND a passing manifest, so a chapter that failed earlier is retried
# rather than silently left out.
exec .venv/bin/python -u book_fish.py \
    --first 1 --last "${LAST}" \
    --out-dir out/book \
    >> "${LOG}" 2>&1
