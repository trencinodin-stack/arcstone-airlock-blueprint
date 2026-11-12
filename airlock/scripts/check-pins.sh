#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

if [ ! -f PINS.lock ]; then
  echo "ERROR: PINS.lock missing" >&2
  exit 1
fi

# Parse key=value lines strictly
get_pin() {
  local key="$1"
  local val
  val="$(grep -E "^${key}=" PINS.lock | head -n1 | cut -d= -f2- || true)"
  if [ -z "$val" ]; then
    echo "ERROR: Missing key ${key} in PINS.lock" >&2
    exit 1
  fi
  printf '%s' "$val"
}

CRATE_PATH="$(get_pin UPSTREAM_CRATE_PATH)"
EXPECTED_TREE="$(get_pin UPSTREAM_CRATE_TREE_ID)"
EXPECTED_ARCHIVE_SHA="$(get_pin UPSTREAM_CRATE_ARCHIVE_SHA256)"

if [ ! -d "$CRATE_PATH" ]; then
  echo "ERROR: Crate path $CRATE_PATH does not exist" >&2
  exit 1
fi

# Reject symlinks inside upstream crate
if find "$CRATE_PATH" -type l | grep -q .; then
  echo "ERROR: Symlinks forbidden inside $CRATE_PATH" >&2
  exit 1
fi

ACTUAL_TREE="$(git rev-parse "HEAD:${CRATE_PATH}")"
ACTUAL_ARCHIVE_SHA="$(git archive --format=tar --mtime=1970-01-01T00:00:00Z "$ACTUAL_TREE" | sha256sum | awk '{print $1}')"

if [[ "$EXPECTED_TREE" == QUALIFY_* ]]; then
  echo "NOTICE: PINS.lock contains qualification placeholders."
  echo "  Current HEAD:${CRATE_PATH} tree ID = ${ACTUAL_TREE}"
  echo "  Current pax-free archive SHA256    = ${ACTUAL_ARCHIVE_SHA}"
  if [ "${ALLOW_UNQUALIFIED_PINS:-0}" != "1" ]; then
    echo "ERROR: Set qualified tree ID and archive SHA256 in PINS.lock (or pass ALLOW_UNQUALIFIED_PINS=1 during initial qualification)." >&2
    exit 1
  fi
else
  if [ "$ACTUAL_TREE" != "$EXPECTED_TREE" ]; then
    echo "ERROR: Tree hash drift! Expected $EXPECTED_TREE, got $ACTUAL_TREE" >&2
    exit 1
  fi
  if [ "$ACTUAL_ARCHIVE_SHA" != "$EXPECTED_ARCHIVE_SHA" ]; then
    echo "ERROR: Archive SHA256 drift! Expected $EXPECTED_ARCHIVE_SHA, got $ACTUAL_ARCHIVE_SHA" >&2
    exit 1
  fi
fi

echo "OK: Upstream crate pin verified ($ACTUAL_TREE / $ACTUAL_ARCHIVE_SHA)"
