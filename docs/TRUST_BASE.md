# Trusted Computing Base & Scope Boundaries

## 1. What `v0.1.0` Proves
`v0.1.0` establishes **functional refinement of the extracted Coq model** (`Rust_Impl ⊑ Coq_Spec` for `example_no_std_gate::decide`):
- For every valid `Mode` and `u32` pair `(budget, cost)`, `decide` terminates without panicking (`Ok (...)`) and returns `Verdict::Allow` if and only if `mode == Mode::Armed` and `cost <= budget`.

## 2. What `v0.1.0` Does Not Prove
- **Whole-System External-State Conservation (`D(a) = DENY => Delta_external = 0`):** `decide` is a pure admission predicate without an external effect executor. Modeling hardware/actuator state isolation belongs to `v0.3.0` (`example-mmio-shim`).
- **Compiler & Extractor Soundness:** `rustc` (pinned nightly MIR during extraction vs. pinned stable `1.82.0` for `thumbv7em-none-eabihf` target builds), Charon, Aeneas, Coq 8.18.0 (`coqc` / `coqchk`), and Aeneas's `Primitives.v` library form the documented Trusted Computing Base (TCB).
- **Operational Effort Scope:** `C_ops = 0` measures **zero upstream verification intrusion** into the production Rust crate. Maintaining downstream proofs, OCI images, and release baselines incurs bounded engineering effort inside `airlock/`.
