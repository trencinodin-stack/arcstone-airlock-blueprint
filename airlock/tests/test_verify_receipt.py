import hashlib
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
VERIFY_SCRIPT = REPO_ROOT / "airlock/scripts/verify-receipt.sh"


def sha256_file(rel_path: str) -> str:
    return hashlib.sha256((REPO_ROOT / rel_path).read_bytes()).hexdigest()


def build_valid_receipt(commit_sha: str) -> dict:
    return {
        "schema_version": 1,
        "status": "REFINEMENT-PROOF-CHAIN-CLOSED",
        "anchor": "A-77-DELTA-SHIELD-LOCKED",
        "release": {
            "repository": "trencinodin-stack/arcstone-airlock-blueprint",
            "tag": "v0.1.0",
            "commit_sha": commit_sha,
            "source_tree_id": "a" * 40,
            "source_archive_sha256": "b" * 64,
            "crate_path": "crates/example-no-std-gate",
            "upstream_doi_refs": [
                "10.5281/zenodo.22665852",
                "10.5281/zenodo.24041851",
                "10.5281/zenodo.24093739",
            ],
        },
        "toolchain": {
            "oci_image_digest": "ghcr.io/trencinodin-stack/arcstone-airlock-verifier@sha256:" + ("c" * 64),
            "rustc_nightly": "nightly-2024-11-01",
            "charon_commit": "1234567890abcdef",
            "aeneas_commit": "fedcba0987654321",
            "coq_version": "8.18.0",
        },
        "evidence": {
            "pins_lock_sha256": sha256_file("PINS.lock"),
            "cargo_lock_sha256": sha256_file("Cargo.lock"),
            "check_pins_sh_sha256": sha256_file("airlock/scripts/check-pins.sh"),
            "check_shape_sh_sha256": sha256_file("airlock/scripts/check-shape.sh"),
            "entrypoint_sh_sha256": sha256_file("airlock/scripts/entrypoint.sh"),
            "run_airlock_sh_sha256": sha256_file("airlock/scripts/run-airlock.sh"),
            "mint_receipt_py_sha256": sha256_file("airlock/scripts/mint-receipt.py"),
            "verify_receipt_sh_sha256": sha256_file("airlock/scripts/verify-receipt.sh"),
            "receipt_schema_json_sha256": sha256_file("airlock/schemas/receipt.schema.json"),
            "primitives_v_sha256": "d" * 64,
            "generated_interface_v_sha256": sha256_file("airlock/coq/GeneratedInterface.v"),
            "spec_v_sha256": sha256_file("airlock/coq/Spec.v"),
            "refinement_v_sha256": sha256_file("airlock/coq/Refinement.v"),
            "generated_shape_golden_sha256": sha256_file("airlock/golden/generated-shape.txt"),
            "statement_golden_sha256": sha256_file("airlock/golden/statement.txt"),
            "assumptions_allow_sha256": sha256_file("airlock/coq/ASSUMPTIONS.allow"),
            "llbc_sha256": "e" * 64,
            "generated_coq_manifest_sha256": "f" * 64,
        },
        "proof": {
            "theorems_verified": ["Airlock.Refinement.decide_refines_spec"],
            "coqchk_passed": True,
            "admitted_axioms": 0,
            "unexpected_assumptions": 0,
            "canary_mutant_rejected": True,
        },
    }


class TestVerifyReceiptNegative(unittest.TestCase):
    def setUp(self):
        self.commit_sha = "1" * 40
        self.tmpdir = tempfile.TemporaryDirectory()
        self.receipt_path = pathlib.Path(self.tmpdir.name) / "REFINEMENT-AUDIT.json"

    def tearDown(self):
        self.tmpdir.cleanup()

    def run_verifier(self, env_override=None):
        env = os.environ.copy()
        env["VERIFY_ATTESTATION"] = "0"
        env["EXPECTED_REPO"] = "trencinodin-stack/arcstone-airlock-blueprint"
        env["EXPECTED_TAG"] = "v0.1.0"
        if env_override:
            env.update(env_override)
        return subprocess.run(
            [str(VERIFY_SCRIPT), str(self.receipt_path), self.commit_sha],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
        )

    def test_valid_receipt_passes(self):
        self.receipt_path.write_text(json.dumps(build_valid_receipt(self.commit_sha)), encoding="utf-8")
        res = self.run_verifier()
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_rejects_wrong_commit_sha(self):
        self.receipt_path.write_text(json.dumps(build_valid_receipt("2" * 40)), encoding="utf-8")
        res = self.run_verifier()
        self.assertNotEqual(res.returncode, 0)

    def test_rejects_nonzero_admitted_axioms(self):
        r = build_valid_receipt(self.commit_sha)
        r["proof"]["admitted_axioms"] = 1
        self.receipt_path.write_text(json.dumps(r), encoding="utf-8")
        res = self.run_verifier()
        self.assertNotEqual(res.returncode, 0)

    def test_rejects_unrejected_canary(self):
        r = build_valid_receipt(self.commit_sha)
        r["proof"]["canary_mutant_rejected"] = False
        self.receipt_path.write_text(json.dumps(r), encoding="utf-8")
        res = self.run_verifier()
        self.assertNotEqual(res.returncode, 0)

    def test_rejects_tampered_spec_digest(self):
        r = build_valid_receipt(self.commit_sha)
        r["evidence"]["spec_v_sha256"] = "0" * 64
        self.receipt_path.write_text(json.dumps(r), encoding="utf-8")
        res = self.run_verifier()
        self.assertNotEqual(res.returncode, 0)

    def test_rejects_duplicate_json_keys(self):
        raw = '{"schema_version":1,"schema_version":2}'
        self.receipt_path.write_text(raw, encoding="utf-8")
        res = self.run_verifier()
        self.assertNotEqual(res.returncode, 0)

    def test_rejects_baseline_spec_mismatch(self):
        self.receipt_path.write_text(json.dumps(build_valid_receipt(self.commit_sha)), encoding="utf-8")
        res = self.run_verifier({"EXPECTED_SPEC_V_SHA256": "9" * 64})
        self.assertNotEqual(res.returncode, 0)


if __name__ == "__main__":
    unittest.main()
