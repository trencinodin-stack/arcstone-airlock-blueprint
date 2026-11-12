# Security & Release Authorization Policy

## Trust Separation Model
- **`prove` Job (`contents: read` only):** Executes inside a `--network none --cap-drop ALL --read-only --user 65532:65532` container. Holds zero OIDC signing tokens and zero release-write credentials.
- **`attest` Job (`id-token: write`, `attestations: write`):** Treats downloaded proof outputs strictly as passive data. Never executes scripts from workflow artifacts. Validates strict JSON parsing (rejecting duplicate keys), JSON Schema compliance, and independent SHA-256 hashes against the checked-out commit before signing via commit-SHA-pinned `actions/attest`.
- **`release-gate` Job (`production` Environment):** Verifies GitHub Artifact Attestations via `gh attestation verify` with `--repo`, `--signer-workflow`, `--source-ref`, `--source-digest`, and `--deny-self-hosted-runners`, compares `spec_v_sha256` and `statement_golden_sha256` against protected Environment variables (`EXPECTED_SPEC_V_SHA256`, `EXPECTED_STATEMENT_GOLDEN_SHA256`), re-verifies the remote peeled tag commit SHA, and publishes an Immutable Release.

## Required Repository Controls
1. Enable **Immutable Releases** in GitHub repository settings.
2. Enforce a tag ruleset blocking creation, force-push updates, or deletion of `v*` tags by unauthorized actors.
3. Require `CODEOWNERS` review on `/airlock/`, `/.github/`, `/PINS.lock`, `/Cargo.toml`, and `/Cargo.lock`.
4. Configure required reviewers and branch/tag restrictions on the `production` GitHub Environment.
