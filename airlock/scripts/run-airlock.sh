#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

get_pin() {
  grep -E "^${1}=" PINS.lock | head -n1 | cut -d= -f2-
}

OCI_IMAGE_DIGEST="$(get_pin OCI_IMAGE_DIGEST)"
PINNED_RUST_NIGHTLY="$(get_pin RUST_NIGHTLY)"
CRATE_PATH="$(get_pin UPSTREAM_CRATE_PATH)"

RELEASE_COMMIT="$(git rev-parse --verify HEAD^{commit})"
SOURCE_TREE_ID="$(git rev-parse "HEAD:${CRATE_PATH}")"
SOURCE_ARCHIVE_SHA256="$(git archive --format=tar --mtime=1970-01-01T00:00:00Z "$SOURCE_TREE_ID" | sha256sum | awk '{print $1}')"

STAGED_INPUT_DIR="$(mktemp -d)"
OUT_DIR="${REPO_ROOT}/out"
mkdir -p "$OUT_DIR"
chmod 1777 "$OUT_DIR"

cleanup() {
  chmod -R u+w "$STAGED_INPUT_DIR" 2>/dev/null || true
  rm -rf "$STAGED_INPUT_DIR"
}
trap cleanup EXIT

# Stage clean read-only inputs from HEAD
mkdir -p "$STAGED_INPUT_DIR/crates"
git archive --format=tar "$SOURCE_TREE_ID" | tar -x -C "$STAGED_INPUT_DIR/crates"
mv "$STAGED_INPUT_DIR/crates" "$STAGED_INPUT_DIR/example-no-std-gate-tmp"
mkdir -p "$STAGED_INPUT_DIR/crates/example-no-std-gate"
cp -r "$STAGED_INPUT_DIR/example-no-std-gate-tmp/." "$STAGED_INPUT_DIR/crates/example-no-std-gate/"
rm -rf "$STAGED_INPUT_DIR/example-no-std-gate-tmp"

cp Cargo.toml Cargo.lock PINS.lock "$STAGED_INPUT_DIR/"
cp -r airlock "$STAGED_INPUT_DIR/"
chmod +x "$STAGED_INPUT_DIR"/airlock/scripts/*.sh
chmod -R a-w "$STAGED_INPUT_DIR"

docker run --rm \
  --network none \
  --cap-drop ALL \
  --security-opt no-new-privileges=true \
  --read-only \
  --user 65532:65532 \
  --pids-limit 256 \
  --memory 4g \
  --cpus 2 \
  --tmpfs /work:rw,exec,nosuid,nodev,size=2g,uid=65532,gid=65532 \
  --tmpfs /tmp:rw,nosuid,nodev,size=256m,uid=65532,gid=65532 \
  --env HOME=/work/home \
  --env CARGO_HOME=/opt/cargo \
  --env RUSTUP_HOME=/opt/rustup \
  --env RUSTUP_TOOLCHAIN="${PINNED_RUST_NIGHTLY}" \
  --env CARGO_TARGET_DIR=/work/target \
  --env CARGO_NET_OFFLINE=true \
  --env CARGO_INCREMENTAL=0 \
  --env RELEASE_REPO="${RELEASE_REPO:-trencinodin-stack/arcstone-airlock-blueprint}" \
  --env RELEASE_TAG="${RELEASE_TAG:-v0.1.0}" \
  --env RELEASE_COMMIT="${RELEASE_COMMIT}" \
  --env SOURCE_TREE_ID="${SOURCE_TREE_ID}" \
  --env SOURCE_ARCHIVE_SHA256="${SOURCE_ARCHIVE_SHA256}" \
  --env OCI_IMAGE_DIGEST="${OCI_IMAGE_DIGEST}" \
  --env LC_ALL=C.UTF-8 \
  --env TZ=UTC \
  --env SOURCE_DATE_EPOCH=0 \
  --mount "type=bind,src=$STAGED_INPUT_DIR,dst=/src,readonly" \
  --mount "type=bind,src=$OUT_DIR,dst=/out" \
  "$OCI_IMAGE_DIGEST" \
  /bin/bash /src/airlock/scripts/entrypoint.sh

echo "OK: Canonical receipt minted at ${OUT_DIR}/REFINEMENT-AUDIT.json"
