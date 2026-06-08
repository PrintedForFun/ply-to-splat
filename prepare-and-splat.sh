#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <input.ply> <output.ply>" >&2
  exit 1
fi

INPUT="$1"
OUTPUT="$2"
TMP="tmp-mesh.ply"

python3 src/cloud-compare-prepare.py --rotate 90,0,0 "$INPUT" "$TMP"
python3 src/ply-to-splat.py "$TMP" "$OUTPUT"
rm -f "$TMP"
