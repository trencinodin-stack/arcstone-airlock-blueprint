# AGENTS.md — Operational Rules for AI & Automated Contributors

## Repository Purpose
`arcstone-airlock-blueprint` provides a hermetic, reproducible formal refinement pipeline verifying the `#![no_std]` Rust crate `crates/example-no-std-gate` against a Coq 8.18.0 functional specification (`airlock/coq/Spec.v`) using Charon and Aeneas, anchored under `A-77-DELTA-SHIELD-LOCKED`.

## Critical Invariants (Do Not Violate)
1. **Zero Unapproved Axioms**: Never introduce `Admitted`, `admit`, `Axiom`, `Parameter`, `Hypothesis`, `Conjecture`, `Variable`, `Declare ML`, `native_compute`, or guard/positivity/universe overrides in `airlock/coq/*.v`. Only the three pinned `Primitives.Primitives.{usize_max,isize_min,isize_max}` constants in `airlock/coq/ASSUMPTIONS.allow` are permitted.
2. **Protected Specification & Theorem Baselines**: `airlock/coq/Spec.v` and `airlock/golden/statement.txt` are pinned via SHA-256 baseline variables (`EXPECTED_SPEC_V_SHA256`, `EXPECTED_STATEMENT_GOLDEN_SHA256`) in the GitHub `production` environment. Do not alter their semantics or formatting without updating the baseline digests after explicit review.
3. **Hermetic Toolchain Pins**: Do not modify `PINS.lock`, `rust-toolchain.toml`, or `Cargo.lock` unless upgrading the pinned verifier container digest (`ghcr.io/trencinodin-stack/arcstone-airlock-blueprint-verifier`).
4. **Canary Sensitivity**: Any change to `crates/example-no-std-gate` or `airlock/coq/Refinement.v` must preserve sensitivity to the semantic canary test (Step `[5/6]`), which mutates the gate logic and asserts proof rejection.
5. **Pinned GitHub Actions**: All workflow actions in `.github/workflows/downstream-airlock.yml` must remain pinned to full 40-character commit SHAs.

## Standard Commands
- Verify upstream crate pins: `make check-pins`
- Run full hermetic proof, canary, and receipt minting: `make airlock`
- Verify a minted canonical receipt: `./airlock/scripts/verify-receipt.sh out/REFINEMENT-AUDIT.json`

## Key File Map
- `crates/example-no-std-gate/` — Target `#![no_std]` Rust gate crate under verification.
- `airlock/coq/Spec.v` — Pure Coq specification (`spec_allow`).
- `airlock/coq/GeneratedInterface.v` — Glue interface bridging Aeneas-generated Coq types to `Spec.v`.
- `airlock/coq/Refinement.v` — Total refinement theorem (`decide_refines_spec`).
- `airlock/coq/ASSUMPTIONS.allow` — Allowlist of permitted Aeneas `Primitives.v` width constants.
- `airlock/golden/` — Golden interface shape (`generated-shape.txt`) and theorem signature (`statement.txt`).
- `airlock/scripts/` — Airlock execution (`run-airlock.sh`), pin/shape checks, receipt minting (`mint-receipt.py`), and verification (`verify-receipt.sh`).
- `airlock/schemas/receipt.schema.json` — JSON Schema (`Draft 2020-12`) for `REFINEMENT-AUDIT.json`.
