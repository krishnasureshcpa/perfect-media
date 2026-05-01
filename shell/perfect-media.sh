#!/usr/bin/env bash
set -euo pipefail

TOOL_DIR="/Users/sgkrishna/MasterBase/projects/external-integrations/perfect-media"
exec python3 "$TOOL_DIR/src/perfect_media.py" "$@"
