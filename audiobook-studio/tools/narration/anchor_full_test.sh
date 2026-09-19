#!/bin/bash
# Full-length anchor test on the worst measured run in the book.
#
# Chapters 10 -> 11 -> 12 have p20 F0 chapter means of 179.11, 188.05, 175.73 Hz in
# the current production renders: up 0.84 then down 1.17 semitones, which is the step
# the listener described as the voice going deeper, then higher, then back.
#
# Each chapter is a separate process, so each gets a fresh model load and a fresh
# Conversation. That is the condition under test: identical deterministic starting
# state per chapter, rather than continuity carried across chapters.
set -euo pipefail

cd "$(dirname "$0")"

export PYTHONPATH=/Users/jessica/Documents/frontier-book/audiobook-studio/tools/vendor/mlx-audio
PY=./.venv/bin/python
CHAPTERS=../../../"The Final Frontier Novel"/chapters
OUT=out/anchor-full
SEED=70

mkdir -p "$OUT"

render() {
  local number="$1" source="$2"
  local sequence=$((4 + number))
  local target
  target=$(printf "%s/%03d-chapter-%03d-fish-clean92.wav" "$OUT" "$sequence" "$number")
  if [ -f "$target" ]; then
    echo "chapter $number already rendered, skipping"
    return 0
  fi
  echo "=============================================================="
  echo "chapter $number -> $target"
  echo "=============================================================="
  "$PY" render_chapter_fish.py "$source" \
    --output "$target" \
    --anchor \
    --keep-anchor-audio \
    --seed "$SEED"
}

render 10 "$CHAPTERS/discovery-part/discovery-part-010-no-form-for-this.md"
render 11 "$CHAPTERS/discovery-part/discovery-part-011-the-mind-as-a-field.md"
render 12 "$CHAPTERS/discovery-part/discovery-part-012-one-call-end-to-end.md"

echo
echo "all three chapters rendered; measuring register"
"$PY" chapter_trajectory.py --book "$OUT" --out "$OUT/trajectory.json"
