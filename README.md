# arcstone-airlock-blueprint

**Turnkey Decoupled Refinement Airlock Template for Bare-Metal `#![no_std]` Rust Systems**

- **Master Epistemic Anchor:** `A-77-DELTA-SHIELD-LOCKED`
- **Reference Upstream Proof Witness:** [`trencinodin-stack/arcstone-refinement-harness`](https://github.com/trencinodin-stack/arcstone-refinement-harness) (`v0.1.0`)
- **Governance Alignment:** Canonical Downstream Verification Template across Paths A, B, C, and D (`ARC-FAQ-2026-PHASE7-01` Q16), preserving the read-only upstream flagplant policy (`Q15`).

---

## Core Architectural Invariants

1. **Zero Upstream Verification Intrusion (`C_ops = 0`):** The target `#![no_std]` Rust crate (`crates/example-no-std-gate`) contains zero verification macros, zero ghost variables, zero proof dependencies, and zero source modifications.
2. **Downstream Generated-Code Refinement (`Rust_Impl ⊑ Coq_Spec`):** Charon LLBC extraction (`--lib` only), Aeneas functional synthesis, and Coq 8.18.0 proofs run downstream against a read-only snapshot, proving equivalence directly against the Aeneas-synthesized Coq module.
3. **Zero Axiom Creep (`admitted_axioms: 0`):** Verification runs inside an offline, non-root, capability-dropped container (`--network none --cap-drop ALL --read-only --user 65532:65532`) and emits `REFINEMENT-AUDIT.json` validated by recursive `coqchk -o`, standalone `Audit.v` (`Print Assumptions`) against an explicitly empty allowlist (`ASSUMPTIONS.allow`), golden theorem statement pinning, and an in-sandbox semantic canary mutant.
4. **Upstream-Only DOI Topology:** Permanent archival DOIs remain strictly on upstream specifications (`10.5281/zenodo.22665852`, `10.5281/zenodo.24041851`, `10.5281/zenodo.24093739`). This template never mints a downstream DOI.

---

## 30-Minute Quickstart (Using Prebuilt Digest-Pinned OCI Image)

### Prerequisites
- Rust stable toolchain (`1.82.0` + `thumbv7em-none-eabihf` target)
- Docker / OCI runtime (`docker` with `--network none` support)
- Python 3.11+, `git`, `sha256sum`

### Step 1: Run the Fast Upstream Inner Loop (< 15s)
```bash
make quick
make lint
```
This runs `cargo fmt --check`, `cargo clippy -- -D warnings`, `cargo test --locked`, cross-compilation to `thumbv7em-none-eabihf`, and verifies zero proof-tooling leakage into `crates/`.

### Step 2: Run the Negative Receipt Verifier Unit Tests
```bash
python3 -m unittest discover -s airlock/tests -p 'test_*.py' -v
```

### Step 3: Run the Hermetic Downstream Airlock (`--network none`)
```bash
# Pull the digest-pinned verifier image recorded in PINS.lock (when published)
# docker pull "$(grep '^OCI_IMAGE_DIGEST=' PINS.lock | cut -d= -f2)"

make airlock
```
This executes the full offline pipeline inside `/work` `tmpfs`:
1. Stages a read-only snapshot of the crate from its Git tree object.
2. Runs Charon (`--preset=aeneas --locked -- --lib`) and Aeneas (`-backend coq`).
3. Verifies generated Coq module signatures against `airlock/golden/generated-shape.txt`.
4. Compiles `Primitives.v`, generated Coq modules, `GeneratedInterface.v`, `Spec.v`, and `Refinement.v`.
5. Executes the semantic canary mutant in `/work/canary` (flipping `cost <= budget` to `cost >= budget`) and confirms Coq fails specifically on `Refinement.v`.
6. Runs `coqchk -o` and standalone `Audit.v` (`Print Assumptions`) and writes `out/REFINEMENT-AUDIT.json`.

---

## Pre-Tag Toolchain Qualification Checklist (`v0.1.0`)

Before pushing a production `v0.1.0` tag:
1. Build and push the verifier OCI image via `.github/workflows/toolchain-image.yml` and record its `@sha256:...` digest in `PINS.lock`.
2. Run a one-time qualification pass against the pinned Aeneas commit to freeze exact generated constructor/lemma spellings in `airlock/coq/GeneratedInterface.v`, `airlock/coq/Refinement.v`, `airlock/golden/generated-shape.txt`, and `airlock/golden/statement.txt`.
3. Configure GitHub repository settings: **Immutable Releases**, protected `v*` tag rulesets, `CODEOWNERS` required reviews, and protected `production` Environment variables (`EXPECTED_SPEC_V_SHA256`, `EXPECTED_STATEMENT_GOLDEN_SHA256`).
