#!/usr/bin/env bash
set -euo pipefail

GEN_FILE="${1:?Usage: check-shape.sh <generated-coq-file.v> <golden-shape.txt>}"
GOLDEN_FILE="${2:?Usage: check-shape.sh <generated-coq-file.v> <golden-shape.txt>}"

if [ ! -f "$GEN_FILE" ]; then
  echo "ERROR: Generated Coq file not found: $GEN_FILE" >&2
  exit 1
fi

if [ ! -f "$GOLDEN_FILE" ]; then
  echo "ERROR: Golden shape file not found: $GOLDEN_FILE" >&2
  exit 1
fi

while IFS= read -r pattern || [ -n "$pattern" ]; do
  [ -z "$pattern" ] && continue
  if ! grep -Fq "$pattern" "$GEN_FILE"; then
    echo "SHAPE MISMATCH: Expected pattern '$pattern' not found in $GEN_FILE" >&2
    exit 1
  fi
done < "$GOLDEN_FILE"

echo "OK: Generated Coq module matches golden shape signatures."
