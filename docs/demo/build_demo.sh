#!/usr/bin/env bash
# build_demo.sh — Regenerate the Scholium demo assets.
#
# Usage (from project root):
#   bash docs/demo/build_demo.sh            # regenerate video + GIF  (slow: runs TTS)
#   bash docs/demo/build_demo.sh --gif-only # regenerate GIF only     (fast: Pillow)
#
# Outputs:
#   docs/demo/demo.mp4   — narrated video (requires Piper TTS)
#   docs/demo/demo.gif   — terminal-style animated GIF (requires Pillow)
#
# Both files are committed to the repository and served via html_extra_path
# in docs/conf.py (landing at the site root as demo.mp4 / demo.gif).
# Run this script whenever lecture.md or make_gif.py changes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

LECTURE="$SCRIPT_DIR/lecture.md"
VIDEO="$SCRIPT_DIR/demo.mp4"
GIF="$SCRIPT_DIR/demo.gif"

# ── Argument parsing ──────────────────────────────────────────────────────────
GIF_ONLY=false
for arg in "$@"; do
    [[ "$arg" == "--gif-only" ]] && GIF_ONLY=true
done

echo "==> Building Scholium demo assets"
echo "    Lecture : $LECTURE"
echo "    Video   : $VIDEO"
echo "    GIF     : $GIF"
[[ "$GIF_ONLY" == true ]] && echo "    Mode    : GIF only (--gif-only)"
echo

# ── 1. Narrated video ────────────────────────────────────────────────────────
if [[ "$GIF_ONLY" == false ]]; then
    echo "==> Generating narrated video (piper TTS)..."
    cd "$PROJECT_ROOT"
    scholium generate "$LECTURE" "$VIDEO" --provider piper --voice en_US-lessac-medium
    rm -f "${VIDEO%.*}_slides.pdf"   # remove intermediate PDF if present
    echo "    Done: $VIDEO"
    echo
fi

# ── 2. Terminal GIF ──────────────────────────────────────────────────────────
echo "==> Generating terminal GIF (Pillow)..."
cd "$PROJECT_ROOT"
python "$SCRIPT_DIR/make_gif.py"
echo "    Done: $GIF"
echo

echo "==> Demo assets built successfully."
if [[ "$GIF_ONLY" == false ]]; then
    echo "    Commit docs/demo/demo.mp4 and docs/demo/demo.gif when satisfied."
else
    echo "    Commit docs/demo/demo.gif when satisfied."
fi
