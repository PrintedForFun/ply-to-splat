#!/usr/bin/env bash
set -euo pipefail

read_optional_value() {
  local prompt="$1"
  local default_value="$2"
  local value

  read -r -p "$prompt [$default_value]: " value || true
  if [ -z "${value}" ]; then
    printf '%s' "$default_value"
  else
    printf '%s' "$value"
  fi
}

usage() {
  cat <<'EOF'
Usage:
  ./prepare-and-splat.sh
  ./prepare-and-splat.sh <input.ply> <output.ply> [subsample] [splat-size]
  ./prepare-and-splat.sh --input input.ply --output output.ply --subsample 0.0075 --splat-size -5
EOF
}

INPUT=""
OUTPUT=""
SUBSAMPLE="0.0075"
SPLAT_SIZE="-5"
POSITIONAL=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    -i|--input)
      INPUT="$2"
      shift 2
      ;;
    -o|--output)
      OUTPUT="$2"
      shift 2
      ;;
    -s|--subsample)
      SUBSAMPLE="$2"
      shift 2
      ;;
    --splat-size|--scale|-z)
      SPLAT_SIZE="$2"
      shift 2
      ;;
    --)
      shift
      POSITIONAL+=("$@")
      break
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

if [ "${#POSITIONAL[@]}" -gt 0 ]; then
  INPUT="${POSITIONAL[0]}"
fi
if [ "${#POSITIONAL[@]}" -gt 1 ]; then
  OUTPUT="${POSITIONAL[1]}"
fi
if [ "${#POSITIONAL[@]}" -gt 2 ]; then
  SUBSAMPLE="${POSITIONAL[2]}"
fi
if [ "${#POSITIONAL[@]}" -gt 3 ]; then
  SPLAT_SIZE="${POSITIONAL[3]}"
fi

if [ -z "$INPUT" ]; then
  INPUT="$(read_optional_value "Input PLY file" "./input.ply")"
fi
if [ -z "$OUTPUT" ]; then
  OUTPUT="$(read_optional_value "Output splat PLY file" "./output.ply")"
fi
if [ -z "$SUBSAMPLE" ] || ! python3 - <<'PY' "$SUBSAMPLE"
import sys
try:
    value = float(sys.argv[1])
    assert value > 0
except Exception:
    raise SystemExit(1)
PY
then
  SUBSAMPLE="$(read_optional_value "Subsampling value (e.g. 0.0075)" "0.0075")"
fi
if [ -z "$SPLAT_SIZE" ] || ! python3 - <<'PY' "$SPLAT_SIZE"
import sys
try:
    float(sys.argv[1])
except Exception:
    raise SystemExit(1)
PY
then
  SPLAT_SIZE="$(read_optional_value "Splat size / scale value (e.g. -5)" "-5")"
fi

if ! python3 - <<'PY' "$SUBSAMPLE"
import sys
value = float(sys.argv[1])
if value <= 0:
    raise SystemExit(1)
PY
then
  echo "Subsample must be greater than 0." >&2
  exit 1
fi

TMP="tmp-mesh.ply"

python3 src/cloud-compare-prepare.py --ss "$SUBSAMPLE" --rotate 90,0,0 "$INPUT" "$TMP"
python3 src/ply-to-splat.py --scale "$SPLAT_SIZE" "$TMP" "$OUTPUT"
rm -f "$TMP"
