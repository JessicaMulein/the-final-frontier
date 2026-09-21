#!/usr/bin/env bash
# Package a GitHub release for The Final Frontier.
#
# Why this exists: the repo deliberately does not commit derived output. The
# manuscript, the narration pipeline, the patch assets and the voice reference
# are tracked; the ebook editions and the ~5 GB of audio are reproducible from
# them and are published as release assets instead (see .gitignore and LICENSE).
# This script assembles exactly those assets into a staging directory and prints
# the `gh release create` command. It does NOT publish: uploading is the one
# irreversible, bandwidth-committing step, so a human runs that line.
#
# Free-distribution note: GitHub release-asset downloads on a public repo do not
# bill the owner for bandwidth, unlike Git LFS. Nothing here uses LFS, by design.
# WAVs are intentionally excluded — they are lossless masters, regenerable from a
# manifest + the committed voice reference + seed, and no listener needs them.
# The consumption formats (M4B, MP3, EPUB, PDF) are what ship.
#
# Usage:
#   .tools/package_release.sh v1.0.0
#
# Requires: pandoc + xelatex (ebook), ffprobe (audio checks), zip, sha256sum
# (or shasum), and the rendered audiobook present under audiobook/.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

TAG="${1:-}"
if [[ -z "$TAG" ]]; then
  echo "usage: $0 <release-tag>   e.g. $0 v1.0.0" >&2
  exit 2
fi

VOICE_TAG="fish-clean92"
AUDIO_DIR="audiobook"
MP3_DIR="$AUDIO_DIR/mp3"
DIST_DIR="book/dist"
BUILD_DIR=".build"
M4B="$AUDIO_DIR/the-final-frontier-${VOICE_TAG}.m4b"
M4B_SIDECAR="$AUDIO_DIR/the-final-frontier-${VOICE_TAG}.json"
STAGE="release/$TAG"

PY="audiobook-studio/tools/narration/.venv/bin/python"
[[ -x "$PY" ]] || PY="python3"

sha() { if command -v sha256sum >/dev/null; then sha256sum "$@"; else shasum -a 256 "$@"; fi; }

echo "==> Staging release $TAG into $STAGE"
rm -rf "$STAGE"
mkdir -p "$STAGE"

# --- 1. Ebook editions (built fresh so they match current prose) -------------
echo "==> Building ebook editions (epub, pdf, markdown)"
"$PY" .tools/build_book.py all
cp "$DIST_DIR/the-final-frontier.epub" "$STAGE/"
cp "$DIST_DIR/the-final-frontier.pdf" "$STAGE/"
# The compiled single-file markdown is the readable plain-text edition.
if [[ -f "$BUILD_DIR/the-final-frontier.md" ]]; then
  cp "$BUILD_DIR/the-final-frontier.md" "$STAGE/the-final-frontier.md"
elif [[ -f "$DIST_DIR/the-final-frontier.md" ]]; then
  cp "$DIST_DIR/the-final-frontier.md" "$STAGE/the-final-frontier.md"
fi

# --- 2. Audiobook M4B + sidecar ----------------------------------------------
echo "==> Checking audiobook M4B"
[[ -f "$M4B" ]] || { echo "ERROR: missing $M4B — build it with build_m4b.py first" >&2; exit 1; }
# Release asset names drop the internal voice-tag suffix: a reader downloads
# "the-final-frontier.m4b", not the pipeline's provenance filename.
cp "$M4B" "$STAGE/the-final-frontier.m4b"
[[ -f "$M4B_SIDECAR" ]] && cp "$M4B_SIDECAR" "$STAGE/the-final-frontier.m4b.json"

# --- 3. Verify the full chapter set before packaging audio -------------------
echo "==> Verifying 128 chapters present (WAV + MP3)"
missing=0
for c in $(seq 1 128); do
  cc=$(printf "%03d" "$c")
  ls "$AUDIO_DIR"/*chapter-"$cc"-"$VOICE_TAG".wav >/dev/null 2>&1 || { echo "  missing WAV ch$cc" >&2; missing=1; }
  ls "$MP3_DIR"/*chapter-"$cc"-"$VOICE_TAG".mp3 >/dev/null 2>&1 || { echo "  missing MP3 ch$cc" >&2; missing=1; }
done
[[ "$missing" -eq 0 ]] || { echo "ERROR: chapter set incomplete; not packaging" >&2; exit 1; }

# --- 4. MP3 bundle (the streamable/portable audiobook) -----------------------
echo "==> Zipping MP3s"
( cd "$MP3_DIR" && zip -q -r -X "$REPO_ROOT/$STAGE/the-final-frontier-mp3.zip" ./*.mp3 )

# --- 5. Manifest bundle (verifiability without re-rendering 13 h of audio) ---
echo "==> Zipping per-chapter manifests"
( cd "$AUDIO_DIR" && zip -q -X "$REPO_ROOT/$STAGE/the-final-frontier-manifests.zip" ./*-"$VOICE_TAG".manifest.json )

# --- 6. Checksums + a short manifest of what shipped -------------------------
echo "==> Writing SHA256SUMS"
( cd "$STAGE" && sha ./* > SHA256SUMS 2>/dev/null || true )

echo ""
echo "==> Staged assets in $STAGE:"
ls -lh "$STAGE" | sed 's/^/    /'

cat <<EOF

==> Ready. Nothing has been published. To publish (irreversible), run:

  gh release create $TAG \\
    --repo JessicaMulein/the-final-frontier \\
    --title "The Final Frontier — $TAG" \\
    --notes-file release/RELEASE_NOTES-$TAG.md \\
    --latest \\
    "$STAGE"/the-final-frontier.epub \\
    "$STAGE"/the-final-frontier.pdf \\
    "$STAGE"/the-final-frontier.md \\
    "$STAGE"/the-final-frontier.m4b \\
    "$STAGE"/the-final-frontier.m4b.json \\
    "$STAGE"/the-final-frontier-mp3.zip \\
    "$STAGE"/the-final-frontier-manifests.zip \\
    "$STAGE"/SHA256SUMS

Note: write the notes at release/RELEASE_NOTES-$TAG.md — NOT inside $STAGE,
which this script wipes and rebuilds on every run.
EOF
