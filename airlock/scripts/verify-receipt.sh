#!/usr/bin/env bash
set -euo pipefail

RECEIPT_PATH="${1:-out/REFINEMENT-AUDIT.json}"
EXPECTED_COMMIT="${2:-$(git rev-parse --verify HEAD^{commit})}"
EXPECTED_REPO="${EXPECTED_REPO:-${GITHUB_REPOSITORY:-trencinodin-stack/arcstone-airlock-blueprint}}"
EXPECTED_TAG="${EXPECTED_TAG:-${GITHUB_REF_NAME:-v0.1.0}}"
VERIFY_ATTESTATION="${VERIFY_ATTESTATION:-0}"

if [ ! -f "$RECEIPT_PATH" ]; then
  echo "ERROR: Receipt not found at $RECEIPT_PATH" >&2
  exit 1
fi

# Strict Python validation: rejects duplicate JSON keys, checks exact types, recomputes repo hashes
python3 - "$RECEIPT_PATH" "$EXPECTED_COMMIT" "$EXPECTED_REPO" "$EXPECTED_TAG" <<'PY'
import hashlib
import json
import pathlib
import sys

receipt_path = pathlib.Path(sys.argv[1])
expected_commit = sys.argv[2]
expected_repo = sys.argv[3]
expected_tag = sys.argv[4]


def no_duplicate_object_pairs_hook(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise ValueError(f"Duplicate JSON key rejected: {k}")
        obj[k] = v
    return obj


raw = receipt_path.read_text(encoding="utf-8")
data = json.loads(raw, object_pairs_hook=no_duplicate_object_pairs_hook)

assert data.get("schema_version") == 1, "Invalid schema_version"
assert data.get("status") == "REFINEMENT-PROOF-CHAIN-CLOSED", "Invalid status"
assert data.get("anchor") == "A-77-DELTA-SHIELD-LOCKED", "Invalid anchor"

rel = data["release"]
assert rel["repository"] == expected_repo, f"Repo mismatch: {rel['repository']} != {expected_repo}"
assert rel["tag"] == expected_tag, f"Tag mismatch: {rel['tag']} != {expected_tag}"
assert rel["commit_sha"] == expected_commit, f"Commit mismatch: {rel['commit_sha']} != {expected_commit}"

proof = data["proof"]
assert proof["coqchk_passed"] is True, "coqchk_passed must be true"
assert proof["admitted_axioms"] == 0, "admitted_axioms must be 0"
assert proof["unexpected_assumptions"] == 0, "unexpected_assumptions must be 0"
assert proof["canary_mutant_rejected"] is True, "canary_mutant_rejected must be true"
assert proof["theorems_verified"] == ["Airlock.Refinement.decide_refines_spec"], "Unexpected theorems_verified"


def sha256_file(p: str) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


ev = data["evidence"]
repo_file_map = {
    "pins_lock_sha256": "PINS.lock",
    "cargo_lock_sha256": "Cargo.lock",
    "check_pins_sh_sha256": "airlock/scripts/check-pins.sh",
    "check_shape_sh_sha256": "airlock/scripts/check-shape.sh",
    "entrypoint_sh_sha256": "airlock/scripts/entrypoint.sh",
    "run_airlock_sh_sha256": "airlock/scripts/run-airlock.sh",
    "mint_receipt_py_sha256": "airlock/scripts/mint-receipt.py",
    "verify_receipt_sh_sha256": "airlock/scripts/verify-receipt.sh",
    "receipt_schema_json_sha256": "airlock/schemas/receipt.schema.json",
    "generated_interface_v_sha256": "airlock/coq/GeneratedInterface.v",
    "spec_v_sha256": "airlock/coq/Spec.v",
    "refinement_v_sha256": "airlock/coq/Refinement.v",
    "generated_shape_golden_sha256": "airlock/golden/generated-shape.txt",
    "statement_golden_sha256": "airlock/golden/statement.txt",
    "assumptions_allow_sha256": "airlock/coq/ASSUMPTIONS.allow",
}

for key, rel_path in repo_file_map.items():
    actual = sha256_file(rel_path)
    assert ev.get(key) == actual, f"Evidence digest mismatch for {rel_path}: {ev.get(key)} != {actual}"

# Optional protected Environment baseline checks
import os
exp_spec = os.environ.get("EXPECTED_SPEC_V_SHA256", "").strip()
if exp_spec:
    assert ev["spec_v_sha256"] == exp_spec, "spec_v_sha256 does not match EXPECTED_SPEC_V_SHA256 baseline"

exp_stmt = os.environ.get("EXPECTED_STATEMENT_GOLDEN_SHA256", "").strip()
if exp_stmt:
    assert ev["statement_golden_sha256"] == exp_stmt, "statement_golden_sha256 does not match EXPECTED_STATEMENT_GOLDEN_SHA256 baseline"

print("OK: Receipt schema, proof flags, and repository evidence digests verified.")
PY

if [ "$VERIFY_ATTESTATION" = "1" ]; then
  gh attestation verify "$RECEIPT_PATH" \
    --repo "$EXPECTED_REPO" \
    --signer-workflow "${EXPECTED_REPO}/.github/workflows/downstream-airlock.yml" \
    --source-ref "refs/tags/${EXPECTED_TAG}" \
    --source-digest "$EXPECTED_COMMIT" \
    --deny-self-hosted-runners
  echo "OK: GitHub Artifact Attestation verified."
fi
