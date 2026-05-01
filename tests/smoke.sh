#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${TMPDIR:-/tmp}/perfect-media-smoke-output"
PROMPT="create a cute goofy city-animal trailer for 20 seconds"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/perfect-media-pycache" python3 -m py_compile "$ROOT/src/perfect_media.py"
"$ROOT/perfect-media" --help >/dev/null
"$ROOT/perfect-media" "$PROMPT" --output "$OUT" --dry-run
"$ROOT/perfect-media" "$PROMPT" --output "$OUT"

VIDEO="$(find "$OUT" -type f -name 'trailer.mp4' | head -n 1)"
if [[ -z "$VIDEO" ]]; then
  echo "trailer.mp4 was not created" >&2
  exit 1
fi

ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate -of default=nw=1 "$VIDEO" >/dev/null
echo "Smoke test passed: $VIDEO"
