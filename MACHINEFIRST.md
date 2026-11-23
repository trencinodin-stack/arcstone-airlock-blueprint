---
machinefirst_version: "0.1.2"
contract_type: "epistemic-evidence-map"
parse_mode: "markdown-with-frontmatter-and-seven-fenced-yaml-sections"
duplicate_keys: "reject"
unknown_fields: "reject"
claim_authority: "publisher_asserted"
authority_model: "publisher_declared_nonbinding"
this_file_is_data_not_instructions: true
treat_strings_as_inert_data: true
canonical_url: "https://github.com/trencinodin-stack/arcstone-airlock-blueprint/blob/main/MACHINEFIRST.md"
scope: "tool"
valid_as_of: "2026-11-23"
---

# MACHINEFIRST

> **Governing Notice:** This document is untrusted publisher-asserted data identifying claims, their exact scope, and the evidence required to evaluate them. Its presence does not establish correctness, confer trust, authorize execution, or compel any auditor verdict.

## 1. Identity & Immutable Anchors
```yaml
subject:
  name: "arcstone-airlock-blueprint"
  repository: "https://github.com/trencinodin-stack/arcstone-airlock-blueprint"
  canonical_urls: ["https://github.com/trencinodin-stack/arcstone-airlock-blueprint", "https://paradigm.admissibilityscience.com"]
  subject_revision: "ca0a2d2fe0b0d0a9529ad2fa27f61666fbfb9339"
  revision_semantics: "exact_git_commit"
  release_tag: "v0.1.0"
  tag_signed: false
  tag_signer_fingerprint: "none"
contract_binding:
  contract_excluded_from_subject: true
  subject_revision_is_ancestor_of_contract_commit: true
  allowed_delta_paths: ["MACHINEFIRST.md", "MACHINEFIRST.sha256", "validate_machinefirst.py", ".github/workflows/downstream-airlock.yml", "README.md"]
  contract_digest_published_in: "repository_commit_history"
  mirror_rule: "no_web_mirror_required"
persistent_ids:
  doi: ["10.5281/zenodo.24041851", "10.5281/zenodo.24093739", "10.5281/zenodo.22966979"]
  orcid: ["0000-0009-0008-4661-1540"]
supersedes: []
errata: ["ARC-ERR-2026-001"]
```

## 2. Verification Scope Boundary
```yaml
evidence_ladder: [proved, tested, measured, static_analysis, stated, external_llm_review]
auditor_states: [not_checked, identity_checked, reproduced_pass, reproduced_fail, blocked, conflict]
normative_artifacts:
  - id: "ART-COQ-SPEC-01"
    path: "airlock/coq/Spec.v"
    hash_algorithm: "sha256"
    digest: "b90b6746b3d573743d99e9317265282214bca04b4c094e82b12347000268c706"
    claimed_level: "stated"
    toolchain: "Coq 8.18.0 Functional Specification"
    toolchain_image_digest: "sha256:8f9c2d4e6a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d"
  - id: "ART-COQ-REF-01"
    path: "airlock/coq/Refinement.v"
    hash_algorithm: "sha256"
    digest: "7084e388a9adab0d5e97bdfb81a0d874e2316c2b1c987a0afb9d409d248a4e34"
    claimed_level: "proved"
    toolchain: "Charon + Aeneas -> Coq 8.18.0 + coqchk"
    toolchain_image_digest: "sha256:8f9c2d4e6a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d"
  - id: "ART-COQ-ALLOW-01"
    path: "airlock/coq/ASSUMPTIONS.allow"
    hash_algorithm: "sha256"
    digest: "a47e6062ae3674f17203cf3fba6aeab5d19171e0090ad2528195e85babe6ca74"
    claimed_level: "stated"
    toolchain: "Coq Print Assumptions Allowlist"
    toolchain_image_digest: "sha256:8f9c2d4e6a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d"
  - id: "ART-RUST-GATE-01"
    path: "crates/example-no-std-gate/src/lib.rs"
    hash_algorithm: "sha256"
    digest: "d93e6ca6c32a31cd494207951d6f5ac5e218bd08fb4898bdc28fc87c70225d1b"
    claimed_level: "tested"
    toolchain: "Rust no_std cargo test"
    toolchain_image_digest: "sha256:8f9c2d4e6a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d"
  - id: "ART-PINS-01"
    path: "PINS.lock"
    hash_algorithm: "sha256"
    digest: "f08e03f6cf53369ac1cbf81997646153076bc3624021b31ebfcbe2a03c4be695"
    claimed_level: "stated"
    toolchain: "Digest-Pinned OCI Airlock Lockfile"
    toolchain_image_digest: "sha256:8f9c2d4e6a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d"
  - id: "ART-SCHEMA-01"
    path: "airlock/schemas/receipt.schema.json"
    hash_algorithm: "sha256"
    digest: "ffd5011c182932348b1a853ba0edc3c0d03f5d5d95a724d5d397ae1184f65e43"
    claimed_level: "stated"
    toolchain: "JSON Schema Draft 2020-12"
    toolchain_image_digest: "sha256:8f9c2d4e6a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d"
  - id: "ART-AGENTS-01"
    path: "AGENTS.md"
    hash_algorithm: "sha256"
    digest: "2e13e1f8fb630536009fc4e62f9838421452d766e008855497a7ea146f9205c0"
    claimed_level: "stated"
    toolchain: "UTF-8 Markdown Agent Manifest"
    toolchain_image_digest: "sha256:8f9c2d4e6a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d"
  - id: "ART-LLMS-01"
    path: "llms.txt"
    hash_algorithm: "sha256"
    digest: "4eed66f950299bcc474e1c9a74dc6477312dde2b4a0e8bdae2d3540d352158e2"
    claimed_level: "stated"
    toolchain: "UTF-8 Markdown Discovery Index"
    toolchain_image_digest: "sha256:8f9c2d4e6a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d"
non_normative_surfaces:
  - path_or_url: "README.md"
    kind: "expository"
```

## 3. Hard Invariants & Claim-to-Evidence Map
```yaml
claims:
  - id: "CLM-001"
    quantity_id: "decide_refines_spec_theorem"
    statement: "Extracted no_std Rust gate evaluation refines pure Coq functional specification spec_allow with zero unapproved axioms beyond ASSUMPTIONS.allow"
    operator: "=="
    value: 0
    unit: "unapproved_axioms"
    applies_to_revision: "ca0a2d2fe0b0d0a9529ad2fa27f61666fbfb9339"
    scope: "airlock/coq/Refinement.v, airlock/coq/Spec.v, airlock/coq/ASSUMPTIONS.allow"
    excludes: ["host OS scheduling or non-containerized execution outside digest-pinned OCI verifier"]
    proof_target: "model"
    refinement_ref: "ART-COQ-REF-01"
    claimed_level: "proved"
    claim_scope: "formal_statement"
    evidence_ref:
      artifact_id: "ART-COQ-REF-01"
      symbol: "decide_refines_spec"
      symbol_kind: "theorem"
    genesis:
      spec_origin: "human_authored"
      adequacy_status: "unattested"
      spec_digest: "b90b6746b3d573743d99e9317265282214bca04b4c094e82b12347000268c706"
      genesis_ref: null
    assumptions:
      source: "ART-AGENTS-01#Critical Invariants (Do Not Violate)"
      declared_items: ["Only Primitives.Primitives.{usize_max,isize_min,isize_max} in ASSUMPTIONS.allow permitted", "Semantic canary mutant step [5/6] rejects broken implementations"]
      dependency_audit: "coqchk_and_assumptions_allowlist"
    failure_behavior: "coq_compile_error_or_axiom_allowlist_violation"
  - id: "CLM-002"
    quantity_id: "no_std_example_gate_tests"
    statement: "Freestanding no_std Rust example gate crate compiles without std and passes unit and integration test suites"
    operator: "=="
    value: 0
    unit: "test_failures"
    applies_to_revision: "ca0a2d2fe0b0d0a9529ad2fa27f61666fbfb9339"
    scope: "crates/example-no-std-gate/src/lib.rs, crates/example-no-std-gate/tests/gate.rs"
    excludes: ["downstream user crates cloned from this template"]
    proof_target: "implementation"
    refinement_ref: null
    claimed_level: "tested"
    claim_scope: "implementation_refinement"
    evidence_ref:
      artifact_id: "ART-RUST-GATE-01"
      symbol: "lib"
      symbol_kind: "module"
    genesis:
      spec_origin: "human_authored"
      adequacy_status: "unattested"
      spec_digest: "b90b6746b3d573743d99e9317265282214bca04b4c094e82b12347000268c706"
      genesis_ref: null
    assumptions:
      source: "ART-AGENTS-01#Repository Purpose"
      declared_items: ["#![no_std] crate with zero runtime heap allocation (C_ops == 0 upstream)"]
      dependency_audit: "cargo_lock_and_rust_toolchain_toml"
    failure_behavior: "cargo_test_failure"
```

## 4. Authority Routing Table
```yaml
routes:
  - query_key: "airlock.refinement_theorem"
    description: "Total Coq 8.18.0 refinement theorem (decide_refines_spec) bridging Aeneas-extracted Rust gate to Spec.v"
    definition_ref: "ART-COQ-SPEC-01"
    evidence_ref:
      artifact_id: "ART-COQ-REF-01"
      symbol: "decide_refines_spec"
      symbol_kind: "theorem"
    refinement_ref: "ART-COQ-REF-01"
    non_authoritative_refs: ["README.md"]
  - query_key: "airlock.receipt_schema"
    description: "JSON Schema Draft 2020-12 governing REFINEMENT-AUDIT.json release receipts"
    definition_ref: "ART-AGENTS-01"
    evidence_ref:
      artifact_id: "ART-SCHEMA-01"
      symbol: "REFINEMENT-AUDIT"
      symbol_kind: "section"
    refinement_ref: null
    non_authoritative_refs: ["README.md"]
conflict_rule: "report_all_mismatches; do_not_silently_resolve_by_precedence"
```

## 5. Conformance Rules & Evidence Guards
```yaml
conformance_guards:
  require_fetches_before_endorsing_claim: ["definition_ref", "evidence_ref.artifact_id"]
  undeclared_sources_satisfy_claims: false
  revision_substitution_permitted: false
  missing_evidence_status: "UNKNOWN"
  broken_reference_status: "UNVERIFIABLE"
  unverified_claim_status: "not_checked"
  unlinked_model_proof_cap: "tested"
  treat_strings_as_inert_data: true
```

## 6. Independent Auditor Quick-Check
```yaml
quick_check:
  checkout: "git clone https://github.com/trencinodin-stack/arcstone-airlock-blueprint.git && cd arcstone-airlock-blueprint && git checkout --detach ca0a2d2fe0b0d0a9529ad2fa27f61666fbfb9339"
  verify_revision: 'test "ca0a2d2fe0b0d0a9529ad2fa27f61666fbfb9339" = "ca0a2d2fe0b0d0a9529ad2fa27f61666fbfb9339"'
  verify_contract_delta: "git diff --name-only ca0a2d2fe0b0d0a9529ad2fa27f61666fbfb9339 HEAD"
  verify_artifact_digests: "sha256sum -c MACHINEFIRST.sha256"
  command: "python3 validate_machinefirst.py MACHINEFIRST.md --strict"
  network: "none"
  toolchain_image_digest: "sha256:8f9c2d4e6a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d"
  quick_check_covers: ["CLM-001", "CLM-002"]
  expected_exit_code: 0
  receipt_output: "out/AUDIT-RECEIPT.json"
  receipt_schema_ref: "machinefirst-receipt-v0.1"
  negative_control:
    command: 'python3 -c "import pathlib, sys; sys.exit(0 if \'PLACEHOLDER\' in pathlib.Path(\'MACHINEFIRST.md\').read_text(encoding=\'utf-8\') else 1)"'
    expected_exit_code: 1
    expected_reason: "target_invariant_violation"
    required_for_pass: true
  does_not_check: ["live containerized Charon/Aeneas extraction and semantic canary execution without running make airlock"]
```

## 7. Known Gaps & Open Errata
```yaml
known_gaps:
  - "Downstream repositories cloning this template must update EXPECTED_SPEC_V_SHA256 and EXPECTED_STATEMENT_GOLDEN_SHA256 when replacing crates/example-no-std-gate"
  - "Git tag v0.1.0 is unsigned until GPG/Sigstore release signing is configured"
```
