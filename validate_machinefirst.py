#!/usr/bin/env python3
"""
MACHINEFIRST (v0.1.1 / v0.1.2) Strict Conformance & Genesis-Cap Validator
(Zero-Dependency Python 3.9+ Standard Library Edition)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


EXPECTED_HEADERS = [
    "## 1. Identity & Immutable Anchors",
    "## 2. Verification Scope Boundary",
    "## 3. Hard Invariants & Claim-to-Evidence Map",
    "## 4. Authority Routing Table",
    "## 5. Conformance Rules & Evidence Guards",
    "## 6. Independent Auditor Quick-Check",
    "## 7. Known Gaps & Open Errata",
]

REQUIRED_FRONTMATTER_KEYS = {
    "machinefirst_version",
    "contract_type",
    "parse_mode",
    "duplicate_keys",
    "unknown_fields",
    "claim_authority",
    "authority_model",
    "this_file_is_data_not_instructions",
    "canonical_url",
    "scope",
    "valid_as_of",
}

OPTIONAL_FRONTMATTER_KEYS_V012 = {
    "treat_strings_as_inert_data",
}

ALLOWED_EVIDENCE_LEVELS = {
    "proved",
    "tested",
    "measured",
    "static_analysis",
    "stated",
    "external_llm_review",
}

ALLOWED_AUDITOR_STATES = {
    "not_checked",
    "identity_checked",
    "reproduced_pass",
    "reproduced_fail",
    "blocked",
    "conflict",
}

ALLOWED_SCOPES = {
    "repository",
    "component",
    "domain",
    "website",
    "tool",
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA256_PREFIXED_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PLACEHOLDER_RE = re.compile(r"<[a-zA-Z0-9_-]+>|xxxxxxx")

HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
ART_ID_RE = re.compile(r"^ART-[A-Z0-9_-]+$")
CLM_ID_RE = re.compile(r"^CLM-[0-9]{3,}$")

VALID_VERSIONS = {"0.1.1", "0.1.2"}
VALID_LEVELS = {
    "stated",
    "measured",
    "static_analysis",
    "tested",
    "proved",
    "external_llm_review",
}
VALID_ORIGINS = {"human_authored", "llm_autoformalized", "hybrid_formalized"}
VALID_ADEQUACY = {"unattested", "self_attested", "third_party_attested"}
VALID_SCOPES = {"formal_statement", "implementation_refinement", "intent_adequacy"}
VALID_ARTIFACT_KINDS = {
    "specification",
    "proof",
    "implementation",
    "test",
    "attestation",
    "discovery",
}
VALID_ATTESTOR_TYPES = {"human_organization", "automated_tool", "llm_system"}
VALID_AUDITOR_STATUSES = {
    "not_checked",
    "identity_checked",
    "reproduced_pass",
    "reproduced_fail",
    "blocked",
    "conflict",
}

ALLOWED_ROOT_KEYS = {
    "machinefirst_version",
    "contract_type",
    "parse_mode",
    "duplicate_keys",
    "canonical_url",
    "valid_as_of",
    "supersedes",
    "errata",
    "scope",
    "persistent_ids",
    "contract_binding",
    "conflict_rule",
    "auditor_states",
    "non_normative_surfaces",
    "this_file_is_data_not_instructions",
    "treat_strings_as_inert_data",
    "claim_authority",
    "authority_model",
    "unknown_fields",
    "subject",
    "conformance_guards",
    "evidence_ladder",
    "routes",
    "quick_check",
    "known_gaps",
    "normative_artifacts",
    "claims",
    "non_normative_formal_backing",
}

ALLOWED_ARTIFACT_KEYS = {
    "id",
    "path",
    "kind",
    "claimed_level",
    "toolchain",
    "toolchain_image_digest",
    "hash_algorithm",
    "digest",
    "attestor",
    "attestor_type",
    "attested_spec_digest",
}

ALLOWED_CLAIM_KEYS = {
    "id",
    "statement",
    "claimed_level",
    "claim_scope",
    "quantity_id",
    "operator",
    "value",
    "unit",
    "applies_to_revision",
    "scope",
    "proof_target",
    "assumptions",
    "failure_behavior",
    "definition_ref",
    "evidence_ref",
    "refinement_ref",
    "excludes",
    "genesis",
}

ALLOWED_GENESIS_KEYS = {"spec_origin", "adequacy_status", "spec_digest", "genesis_ref"}

ALLOWED_BACKING_KEYS = {
    "repository",
    "revision",
    "release",
    "coq_version",
    "normative_for_conformance",
    "auditor_status",
    "artifacts",
}

ALLOWED_BACKING_ART_KEYS = {"path", "sha256", "theorems"}


def is_hex64(value: Any) -> bool:
    return isinstance(value, str) and HEX64_RE.fullmatch(value) is not None


def is_hex40(value: Any) -> bool:
    return isinstance(value, str) and HEX40_RE.fullmatch(value) is not None


def extract_publisher_ids(manifest: Dict[str, Any]) -> Set[str]:
    pubs: Set[str] = {"publisher", "self"}
    subject = manifest.get("subject")
    if isinstance(subject, dict):
        name = subject.get("name")
        if isinstance(name, str) and name.strip():
            pubs.add(name.strip().lower())
        aliases = subject.get("publisher_aliases")
        if isinstance(aliases, list):
            for alias in aliases:
                if isinstance(alias, str) and alias.strip():
                    pubs.add(alias.strip().lower())
    return pubs


def build_artifact_registry(manifest: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    errors: List[str] = []
    registry: Dict[str, Dict[str, Any]] = {}
    artifacts = manifest.get("normative_artifacts")
    if not isinstance(artifacts, list):
        return registry, ["INVALID_ARTIFACTS_TYPE: 'normative_artifacts' must be a list"]

    for idx, item in enumerate(artifacts):
        if not isinstance(item, dict):
            errors.append(f"INVALID_ARTIFACT_ITEM: normative_artifacts[{idx}] must be an object")
            continue
        unknown = set(item.keys()) - ALLOWED_ARTIFACT_KEYS
        if unknown:
            errors.append(f"UNKNOWN_ARTIFACT_KEYS: normative_artifacts[{idx}] has {sorted(unknown)}")
        art_id = item.get("id")
        if not isinstance(art_id, str) or ART_ID_RE.fullmatch(art_id) is None:
            errors.append(f"INVALID_ARTIFACT_ID: normative_artifacts[{idx}] has invalid id '{art_id}'")
            continue
        if art_id in registry:
            errors.append(f"DUPLICATE_ARTIFACT_ID: '{art_id}' declared multiple times")
            continue
        path = item.get("path")
        if not isinstance(path, str) or not path.strip():
            errors.append(f"[{art_id}] INVALID_ARTIFACT_PATH: 'path' must be a non-empty string")
        if "kind" in item:
            kind = item.get("kind")
            if not isinstance(kind, str) or kind not in VALID_ARTIFACT_KINDS:
                errors.append(f"[{art_id}] INVALID_ARTIFACT_KIND: '{kind}'")
        if "claimed_level" in item:
            art_level = item.get("claimed_level")
            if not isinstance(art_level, str) or art_level not in VALID_LEVELS:
                errors.append(f"[{art_id}] INVALID_ARTIFACT_CLAIMED_LEVEL: '{art_level}'")
        for opt_nullable_str in ("toolchain", "toolchain_image_digest"):
            if opt_nullable_str in item and item[opt_nullable_str] is not None:
                if not isinstance(item[opt_nullable_str], str):
                    errors.append(
                        f"[{art_id}] INVALID_ARTIFACT_{opt_nullable_str.upper()}: must be string or null"
                    )
        if "attestor" in item:
            att = item.get("attestor")
            if not isinstance(att, str) or not att.strip():
                errors.append(f"[{art_id}] INVALID_ATTESTOR: 'attestor' must be a non-empty string")
        if "attestor_type" in item:
            att_type = item.get("attestor_type")
            if not isinstance(att_type, str) or att_type not in VALID_ATTESTOR_TYPES:
                errors.append(f"[{art_id}] INVALID_ATTESTOR_TYPE: '{att_type}'")
        if "attested_spec_digest" in item and not is_hex64(item.get("attested_spec_digest")):
            errors.append(f"[{art_id}] INVALID_ATTESTED_SPEC_DIGEST: expected 64-char lowercase hex sha256")
        if item.get("hash_algorithm") != "sha256":
            errors.append(f"[{art_id}] INVALID_HASH_ALGORITHM: expected 'sha256'")
        if not is_hex64(item.get("digest")):
            errors.append(f"[{art_id}] INVALID_ARTIFACT_DIGEST: expected 64-char lowercase hex sha256")
        registry[art_id] = item
    return registry, errors


def check_attestation(
    cid: str,
    adequacy: str,
    ref: Any,
    spec_digest: Any,
    registry: Dict[str, Dict[str, Any]],
    publisher_ids: Set[str],
) -> List[str]:
    if not isinstance(ref, str) or not ref:
        return [f"[{cid}] DANGLING_ATTESTATION: adequacy_status='{adequacy}' requires 'genesis_ref'"]
    if ref not in registry:
        return [f"[{cid}] UNRESOLVED_GENESIS_REF: '{ref}' not found in normative_artifacts[]"]

    art = registry[ref]
    errs: List[str] = []
    if not is_hex64(art.get("digest")):
        errs.append(f"[{cid}] UNPINNED_GENESIS_ARTIFACT: '{ref}' lacks valid 64-hex digest")
    if art.get("kind") != "attestation":
        errs.append(f"[{cid}] WRONG_ARTIFACT_KIND: '{ref}' must have kind='attestation', got '{art.get('kind')}'")

    att = art.get("attestor")
    if not isinstance(att, str) or not att.strip():
        errs.append(f"[{cid}] MISSING_ATTESTOR: '{ref}' must declare a non-empty 'attestor'")
    elif adequacy == "third_party_attested" and att.strip().lower() in publisher_ids:
        errs.append(
            f"[{cid}] ATTESTOR_NOT_INDEPENDENT: '{ref}' attestor '{att}' matches publisher identity"
        )

    if adequacy == "third_party_attested" and art.get("attestor_type") == "llm_system":
        errs.append(f"[{cid}] LLM_ATTESTOR_DISALLOWED: '{ref}' has attestor_type='llm_system'")

    attested_digest = art.get("attested_spec_digest")
    if not is_hex64(attested_digest):
        errs.append(f"[{cid}] MISSING_ATTESTED_SPEC_DIGEST: '{ref}' lacks valid attested_spec_digest")
    elif is_hex64(spec_digest) and attested_digest != spec_digest:
        errs.append(
            f"[{cid}] STALE_GENESIS_BINDING: artifact '{ref}' attests spec '{attested_digest}', "
            f"which does not match claim spec_digest '{spec_digest}'"
        )
    return errs


def validate_genesis_cap(
    claim: Dict[str, Any],
    artifacts_by_id: Dict[str, Dict[str, Any]],
    strict: bool = False,
    manifest_version: str = "0.1.2",
    publisher_ids: Optional[Set[str]] = None,
) -> List[str]:
    errors: List[str] = []
    if not isinstance(claim, dict):
        return ["INVALID_CLAIM_TYPE: claim must be an object"]

    pub_ids = publisher_ids if publisher_ids is not None else {"publisher", "self"}
    cid = claim.get("id") if isinstance(claim.get("id"), str) else "<unknown>"
    if not isinstance(claim.get("id"), str) or CLM_ID_RE.fullmatch(claim["id"]) is None:
        errors.append(f"[{cid}] INVALID_CLAIM_ID: expected pattern ^CLM-[0-9]{{3,}}$")

    stmt = claim.get("statement")
    if not isinstance(stmt, str) or not stmt.strip():
        errors.append(f"[{cid}] INVALID_CLAIM_STATEMENT: 'statement' must be a non-empty string")

    unknown_claim = set(claim.keys()) - ALLOWED_CLAIM_KEYS
    if unknown_claim:
        errors.append(f"[{cid}] UNKNOWN_CLAIM_KEYS: {sorted(unknown_claim)}")

    has_resolved_evidence = False
    if "evidence_ref" in claim and claim["evidence_ref"] is not None:
        ev = claim["evidence_ref"]
        if not isinstance(ev, dict):
            errors.append(f"[{cid}] INVALID_EVIDENCE_REF_TYPE: must be an object or null")
        else:
            ev_unknown = set(ev.keys()) - {"artifact_id", "symbol", "symbol_kind"}
            if ev_unknown:
                errors.append(f"[{cid}] UNKNOWN_EVIDENCE_REF_KEYS: {sorted(ev_unknown)}")
            ev_art = ev.get("artifact_id")
            if not isinstance(ev_art, str) or ART_ID_RE.fullmatch(ev_art) is None:
                errors.append(f"[{cid}] INVALID_EVIDENCE_REF_ARTIFACT_ID: '{ev_art}'")
            elif ev_art not in artifacts_by_id:
                errors.append(f"[{cid}] UNRESOLVED_EVIDENCE_REF: '{ev_art}' not found in normative_artifacts[]")
            else:
                has_resolved_evidence = True
            for opt_str in ("symbol", "symbol_kind"):
                if opt_str in ev and ev[opt_str] is not None and not isinstance(ev[opt_str], str):
                    errors.append(f"[{cid}] INVALID_EVIDENCE_REF_{opt_str.upper()}: must be string or null")

    if "assumptions" in claim:
        if not isinstance(claim["assumptions"], (dict, list)):
            errors.append(f"[{cid}] INVALID_ASSUMPTIONS_TYPE: must be an object or array")

    if "excludes" in claim:
        excl = claim["excludes"]
        if not isinstance(excl, list) or not all(isinstance(x, str) for x in excl):
            errors.append(f"[{cid}] INVALID_EXCLUDES: must be a list of strings")

    for opt_claim_str in (
        "quantity_id",
        "operator",
        "unit",
        "applies_to_revision",
        "scope",
        "proof_target",
        "failure_behavior",
        "definition_ref",
        "refinement_ref",
    ):
        if opt_claim_str in claim and claim[opt_claim_str] is not None:
            if not isinstance(claim[opt_claim_str], str):
                errors.append(
                    f"[{cid}] INVALID_CLAIM_{opt_claim_str.upper()}: must be string or null"
                )

    level = claim.get("claimed_level")
    if not isinstance(level, str) or level not in VALID_LEVELS:
        errors.append(f"[{cid}] INVALID_CLAIMED_LEVEL: '{level}'")
        return errors

    require_v012_fields = strict or (manifest_version == "0.1.2")

    if require_v012_fields and level == "proved" and not has_resolved_evidence:
        errors.append(
            f"[{cid}] UNLINKED_PROOF_CAP: 'proved' claims in v0.1.2 / --strict require a resolved 'evidence_ref'"
        )

    if "claim_scope" not in claim:
        if require_v012_fields:
            errors.append(f"[{cid}] MISSING_CLAIM_SCOPE: 'claim_scope' required in v0.1.2 / --strict")
            return errors
        scope = "formal_statement"
    else:
        scope = claim.get("claim_scope")
        if not isinstance(scope, str) or scope not in VALID_SCOPES:
            errors.append(f"[{cid}] INVALID_CLAIM_SCOPE: '{scope}'")
            return errors

    if "genesis" not in claim or claim.get("genesis") is None:
        if require_v012_fields:
            errors.append(f"[{cid}] MISSING_GENESIS_BLOCK: 'genesis' required in v0.1.2 / --strict")
        elif scope == "intent_adequacy" and level == "proved":
            errors.append(f"[{cid}] GENESIS_CAP_VIOLATION: intent_adequacy cannot claim 'proved' without genesis")
        return errors

    genesis = claim.get("genesis")
    if not isinstance(genesis, dict):
        errors.append(f"[{cid}] INVALID_GENESIS_TYPE: 'genesis' must be an object")
        return errors

    unknown_genesis = set(genesis.keys()) - ALLOWED_GENESIS_KEYS
    if unknown_genesis:
        errors.append(f"[{cid}] UNKNOWN_GENESIS_KEYS: {sorted(unknown_genesis)}")

    origin = genesis.get("spec_origin")
    adequacy = genesis.get("adequacy_status")
    spec_digest = genesis.get("spec_digest")
    genesis_ref = genesis.get("genesis_ref")

    if not isinstance(origin, str) or origin not in VALID_ORIGINS:
        errors.append(f"[{cid}] INVALID_SPEC_ORIGIN: '{origin}'")
    if not isinstance(adequacy, str) or adequacy not in VALID_ADEQUACY:
        errors.append(f"[{cid}] INVALID_ADEQUACY_STATUS: '{adequacy}'")
    if not is_hex64(spec_digest):
        errors.append(f"[{cid}] INVALID_SPEC_DIGEST: expected 64-char lowercase hex sha256")
    if genesis_ref is not None and (not isinstance(genesis_ref, str) or ART_ID_RE.fullmatch(genesis_ref) is None):
        errors.append(f"[{cid}] INVALID_GENESIS_REF_FORMAT: '{genesis_ref}'")
        return errors

    if isinstance(adequacy, str) and adequacy in {"self_attested", "third_party_attested"}:
        errors.extend(check_attestation(cid, adequacy, genesis_ref, spec_digest, artifacts_by_id, pub_ids))
    elif genesis_ref is not None:
        if genesis_ref not in artifacts_by_id:
            errors.append(f"[{cid}] UNRESOLVED_GENESIS_REF: '{genesis_ref}' not found in normative_artifacts[]")

    if level == "proved" and scope == "intent_adequacy":
        if adequacy != "third_party_attested":
            errors.append(
                f"[{cid}] GENESIS_CAP_VIOLATION: intent_adequacy with adequacy_status='{adequacy}' "
                f"is not permitted to use 'proved' under this policy (requires 'third_party_attested')"
            )

    return errors


def validate_non_normative_backing(manifest: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if "non_normative_formal_backing" not in manifest:
        return errors

    backing = manifest["non_normative_formal_backing"]
    if not isinstance(backing, dict):
        return ["INVALID_BACKING_TYPE: 'non_normative_formal_backing' must be an object"]

    unknown = set(backing.keys()) - ALLOWED_BACKING_KEYS
    if unknown:
        errors.append(f"UNKNOWN_BACKING_KEYS: {sorted(unknown)}")

    if backing.get("normative_for_conformance") is not False:
        errors.append("BACKING_MUST_BE_NON_NORMATIVE: normative_for_conformance must be false")

    if not is_hex40(backing.get("revision")):
        errors.append("INVALID_BACKING_REVISION: expected 40-char lowercase hex git SHA")

    if "auditor_status" in backing:
        status = backing.get("auditor_status")
        if not isinstance(status, str) or status not in VALID_AUDITOR_STATUSES:
            errors.append(f"INVALID_BACKING_AUDITOR_STATUS: '{status}'")

    for req_str in ("repository", "release", "coq_version"):
        val = backing.get(req_str)
        if not isinstance(val, str) or not val.strip():
            errors.append(f"INVALID_BACKING_{req_str.upper()}: must be a non-empty string")

    artifacts = backing.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) == 0:
        errors.append("INVALID_BACKING_ARTIFACTS: 'artifacts' must be a non-empty list")
        return errors

    for idx, art in enumerate(artifacts):
        if not isinstance(art, dict):
            errors.append(f"INVALID_BACKING_ARTIFACT_ITEM: artifacts[{idx}] must be an object")
            continue
        unknown_art = set(art.keys()) - ALLOWED_BACKING_ART_KEYS
        if unknown_art:
            errors.append(f"UNKNOWN_BACKING_ARTIFACT_KEYS: artifacts[{idx}] has {sorted(unknown_art)}")
        if not isinstance(art.get("path"), str) or not art["path"].strip():
            errors.append(f"INVALID_BACKING_ARTIFACT_PATH: artifacts[{idx}].path must be non-empty string")
        if not is_hex64(art.get("sha256")):
            errors.append(f"INVALID_BACKING_ARTIFACT_SHA256: artifacts[{idx}].sha256 must be 64-hex string")
        theorems = art.get("theorems")
        if not isinstance(theorems, list) or len(theorems) == 0 or not all(
            isinstance(t, str) and t.strip() for t in theorems
        ):
            errors.append(f"INVALID_BACKING_THEOREMS: artifacts[{idx}].theorems must be non-empty list of strings")

    return errors


def validate_manifest(manifest: Any, strict: bool = False) -> List[str]:
    if not isinstance(manifest, dict):
        return ["INVALID_ROOT_TYPE: manifest root must be a JSON object"]

    errors: List[str] = []
    unknown_root = set(manifest.keys()) - ALLOWED_ROOT_KEYS
    if unknown_root:
        errors.append(f"UNKNOWN_ROOT_KEYS: {sorted(unknown_root)}")

    version = manifest.get("machinefirst_version")
    if not isinstance(version, str) or version not in VALID_VERSIONS:
        errors.append(f"INVALID_VERSION: '{version}' not in {sorted(VALID_VERSIONS)}")
        version = "0.1.2" if strict else "0.1.1"

    if manifest.get("claim_authority") != "publisher_asserted":
        errors.append("INVALID_CLAIM_AUTHORITY: expected 'publisher_asserted'")
    if manifest.get("authority_model") != "publisher_declared_nonbinding":
        errors.append("INVALID_AUTHORITY_MODEL: expected 'publisher_declared_nonbinding'")

    if version == "0.1.2" or strict:
        if manifest.get("this_file_is_data_not_instructions") is not True:
            errors.append("MISSING_QUARANTINE_GUARD: this_file_is_data_not_instructions must be true")
        if manifest.get("treat_strings_as_inert_data") is not True:
            errors.append("MISSING_INERT_GUARD: treat_strings_as_inert_data must be true")
    else:
        for guard_key, err_code in (
            ("this_file_is_data_not_instructions", "INVALID_QUARANTINE_GUARD"),
            ("treat_strings_as_inert_data", "INVALID_INERT_GUARD"),
        ):
            if guard_key in manifest and manifest[guard_key] is not True:
                errors.append(f"{err_code}: {guard_key} must be true when present")

    if "routes" in manifest and not isinstance(manifest["routes"], (dict, list)):
        errors.append("INVALID_ROUTES_TYPE: 'routes' must be an object or array")
    if "known_gaps" in manifest:
        kg = manifest["known_gaps"]
        if not isinstance(kg, list) or not all(isinstance(x, str) for x in kg):
            errors.append("INVALID_KNOWN_GAPS: 'known_gaps' must be a list of strings")

    for root_str in ("contract_type", "parse_mode", "duplicate_keys", "canonical_url", "valid_as_of"):
        if root_str in manifest and not isinstance(manifest[root_str], str):
            errors.append(f"INVALID_{root_str.upper()}: must be a string")

    if "supersedes" in manifest and manifest["supersedes"] is not None:
        if not isinstance(manifest["supersedes"], (str, list)):
            errors.append("INVALID_SUPERSEDES: must be a string, array, or null")

    if "errata" in manifest and manifest["errata"] is not None:
        if not isinstance(manifest["errata"], (str, list, dict)):
            errors.append("INVALID_ERRATA: must be a string, array, object, or null")

    if "scope" in manifest and not isinstance(manifest["scope"], (str, dict)):
        errors.append("INVALID_SCOPE: must be a string or object")

    if "conflict_rule" in manifest and not isinstance(manifest["conflict_rule"], (str, dict)):
        errors.append("INVALID_CONFLICT_RULE: must be a string or object")

    for root_obj in ("persistent_ids", "contract_binding", "quick_check"):
        if root_obj in manifest and not isinstance(manifest[root_obj], dict):
            errors.append(f"INVALID_{root_obj.upper()}: must be an object")

    for root_arr_or_obj in ("auditor_states", "non_normative_surfaces"):
        if root_arr_or_obj in manifest and not isinstance(manifest[root_arr_or_obj], (list, dict)):
            errors.append(f"INVALID_{root_arr_or_obj.upper()}: must be an array or object")

    if "unknown_fields" in manifest:
        uf = manifest["unknown_fields"]
        if not isinstance(uf, str) or uf not in {"reject", "ignore"}:
            errors.append(f"INVALID_UNKNOWN_FIELDS: '{uf}' must be 'reject' or 'ignore'")

    if "subject" in manifest:
        subj = manifest["subject"]
        if not isinstance(subj, dict):
            errors.append("INVALID_SUBJECT: must be an object")
        else:
            if "name" in subj and (not isinstance(subj["name"], str) or not subj["name"].strip()):
                errors.append("INVALID_SUBJECT_NAME: 'name' must be a non-empty string")
            if "publisher_aliases" in subj:
                aliases = subj["publisher_aliases"]
                if not isinstance(aliases, list) or not all(
                    isinstance(a, str) and a.strip() for a in aliases
                ):
                    errors.append("INVALID_SUBJECT_PUBLISHER_ALIASES: must be a list of non-empty strings")

    if "conformance_guards" in manifest:
        cg = manifest["conformance_guards"]
        if not isinstance(cg, dict):
            errors.append("INVALID_CONFORMANCE_GUARDS: must be an object")
        else:
            for guard_key in ("this_file_is_data_not_instructions", "treat_strings_as_inert_data"):
                if guard_key in cg and cg[guard_key] is not True:
                    errors.append(f"INVALID_CONFORMANCE_GUARD_{guard_key.upper()}: must be true")

    if "evidence_ladder" in manifest:
        ladder = manifest["evidence_ladder"]
        if not isinstance(ladder, list) or not all(
            isinstance(lvl, str) and lvl in VALID_LEVELS for lvl in ladder
        ):
            errors.append("INVALID_EVIDENCE_LADDER: must be a list of valid evidence levels")

    registry, reg_errors = build_artifact_registry(manifest)
    errors.extend(reg_errors)
    publisher_ids = extract_publisher_ids(manifest)

    claims = manifest.get("claims")
    if not isinstance(claims, list) or len(claims) == 0:
        errors.append("INVALID_CLAIMS: 'claims' must be a non-empty list")
    else:
        for claim in claims:
            errors.extend(
                validate_genesis_cap(
                    claim,
                    registry,
                    strict=strict,
                    manifest_version=version,
                    publisher_ids=publisher_ids,
                )
            )

    errors.extend(validate_non_normative_backing(manifest))
    return errors


def check_mirror_byte_parity(primary_path: pathlib.Path, mirror_path: pathlib.Path) -> List[str]:
    if not primary_path.is_file():
        return [f"MIRROR_PRIMARY_MISSING: '{primary_path}' does not exist"]
    if not mirror_path.is_file():
        return [f"MIRROR_TARGET_MISSING: '{mirror_path}' does not exist"]
    h1 = hashlib.sha256(primary_path.read_bytes()).hexdigest()
    h2 = hashlib.sha256(mirror_path.read_bytes()).hexdigest()
    if h1 != h2:
        return [f"MIRROR_DIGEST_MISMATCH: '{primary_path}' ({h1}) != '{mirror_path}' ({h2})"]
    return []


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    escape = False
    out = []
    for ch in line:
        if escape:
            out.append(ch)
            escape = False
            continue
        if ch == "\\" and in_double:
            out.append(ch)
            escape = True
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            out.append(ch)
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            out.append(ch)
            continue
        if ch == "#" and not in_single and not in_double:
            break
        out.append(ch)
    return "".join(out).rstrip()


def _split_top_level_commas(text: str) -> List[str]:
    parts: List[str] = []
    buf: List[str] = []
    depth = 0
    in_single = False
    in_double = False
    escape = False
    for ch in text:
        if escape:
            buf.append(ch)
            escape = False
            continue
        if ch == "\\" and in_double:
            buf.append(ch)
            escape = True
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            buf.append(ch)
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            buf.append(ch)
            continue
        if not in_single and not in_double:
            if ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
            elif ch == "," and depth == 0:
                parts.append("".join(buf).strip())
                buf = []
                continue
        buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _parse_scalar(token: str, context: str) -> Any:
    token = token.strip()
    if token.startswith("&") or token.startswith("*"):
        raise ValueError(f"[{context}] YAML anchors or aliases (&/*) are prohibited: {token!r}")
    if token.startswith("!"):
        raise ValueError(f"[{context}] Custom YAML tags (!) are prohibited: {token!r}")
    if token == "":
        return ""
    if token in ("null", "Null", "NULL", "~"):
        return None
    if token in ("true", "True", "TRUE"):
        return True
    if token in ("false", "False", "FALSE"):
        return False
    if token.startswith('"') and token.endswith('"') and len(token) >= 2:
        try:
            return json.loads(token)
        except json.JSONDecodeError as exc:
            raise ValueError(f"[{context}] Invalid double-quoted string {token!r}: {exc}") from exc
    if token.startswith("'") and token.endswith("'") and len(token) >= 2:
        return token[1:-1].replace("''", "'")
    if token.startswith("[") and token.endswith("]"):
        inner = token[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(item, context) for item in _split_top_level_commas(inner)]
    if token.startswith("{") and token.endswith("}"):
        inner = token[1:-1].strip()
        if not inner:
            return {}
        mapping: Dict[str, Any] = {}
        for item in _split_top_level_commas(inner):
            if ":" not in item:
                raise ValueError(f"[{context}] Invalid inline mapping entry: {item!r}")
            k_raw, v_raw = item.split(":", 1)
            k = str(_parse_scalar(k_raw.strip(), context))
            if k in mapping:
                raise ValueError(f"[{context}] Found duplicate key: {k!r}")
            mapping[k] = _parse_scalar(v_raw.strip(), context)
        return mapping
    if re.match(r"^-?[0-9]+$", token):
        return int(token)
    if re.match(r"^-?[0-9]+\.[0-9]+$", token):
        return float(token)
    return token


def _split_kv(text: str, context: str) -> Tuple[str, str]:
    in_single = False
    in_double = False
    escape = False
    for idx, ch in enumerate(text):
        if escape:
            escape = False
            continue
        if ch == "\\" and in_double:
            escape = True
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            continue
        if ch == ":" and not in_single and not in_double:
            if idx + 1 == len(text) or text[idx + 1].isspace():
                key = str(_parse_scalar(text[:idx].strip(), context))
                val = text[idx + 1 :].strip()
                return key, val
    raise ValueError(f"[{context}] Expected 'key: value' mapping syntax, got: {text!r}")


def parse_strict_yaml(raw_yaml: str, context: str) -> Dict[str, Any]:
    cleaned: List[Tuple[int, str]] = []
    for raw_line in raw_yaml.splitlines():
        stripped = _strip_comment(raw_line)
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        if "\t" in stripped[:indent]:
            raise ValueError(f"[{context}] Tab indentation is prohibited in YAML.")
        cleaned.append((indent, stripped.strip()))

    if not cleaned:
        return {}

    def parse_block(idx: int, base_indent: int) -> Tuple[Any, int]:
        if idx >= len(cleaned):
            return {}, idx
        indent, text = cleaned[idx]
        if text.startswith("- ") or text == "-":
            items: List[Any] = []
            while idx < len(cleaned):
                cur_indent, cur_text = cleaned[idx]
                if cur_indent < base_indent:
                    break
                if cur_indent > base_indent:
                    raise ValueError(f"[{context}] Unexpected indentation at line: {cur_text!r}")
                if not (cur_text.startswith("- ") or cur_text == "-"):
                    break
                rest = cur_text[1:].strip()
                if not rest:
                    val, idx = parse_block(idx + 1, base_indent + 2)
                    items.append(val)
                elif ":" in rest and not (
                    rest.startswith('"')
                    or rest.startswith("'")
                    or rest.startswith("[")
                    or rest.startswith("{")
                ):
                    k, v_str = _split_kv(rest, context)
                    item_map: Dict[str, Any] = {}
                    if v_str == "":
                        val, idx = parse_block(idx + 1, base_indent + 2)
                        item_map[k] = val
                    else:
                        item_map[k] = _parse_scalar(v_str, context)
                        idx += 1
                    while idx < len(cleaned) and cleaned[idx][0] == base_indent + 2:
                        sub_text = cleaned[idx][1]
                        if sub_text.startswith("- "):
                            break
                        sk, sv_str = _split_kv(sub_text, context)
                        if sk in item_map:
                            raise ValueError(f"[{context}] Found duplicate key: {sk!r}")
                        if sv_str == "":
                            sval, idx = parse_block(idx + 1, base_indent + 4)
                            item_map[sk] = sval
                        else:
                            item_map[sk] = _parse_scalar(sv_str, context)
                            idx += 1
                    items.append(item_map)
                else:
                    items.append(_parse_scalar(rest, context))
                    idx += 1
            return items, idx
        else:
            mapping: Dict[str, Any] = {}
            while idx < len(cleaned):
                cur_indent, cur_text = cleaned[idx]
                if cur_indent < base_indent:
                    break
                if cur_indent > base_indent:
                    raise ValueError(f"[{context}] Unexpected indentation at line: {cur_text!r}")
                if cur_text.startswith("- "):
                    raise ValueError(f"[{context}] Unexpected sequence item in mapping at: {cur_text!r}")
                k, v_str = _split_kv(cur_text, context)
                if k == "<<":
                    raise ValueError(f"[{context}] YAML merge key '<<' is prohibited.")
                if k in mapping:
                    raise ValueError(f"[{context}] Found duplicate key: {k!r}")
                if v_str == "":
                    val, idx = parse_block(idx + 1, base_indent + 2)
                    mapping[k] = val
                else:
                    mapping[k] = _parse_scalar(v_str, context)
                    idx += 1
            return mapping, idx

    root, next_idx = parse_block(0, cleaned[0][0])
    if next_idx != len(cleaned) or not isinstance(root, dict):
        raise ValueError(f"[{context}] Top-level YAML structure must be a single mapping.")
    return root


def extract_sections(content: str) -> Tuple[Dict[str, Any], Dict[int, Dict[str, Any]]]:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("Document must begin on line 1 with YAML frontmatter delimiter '---'.")

    fm_end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            fm_end = idx
            break
    if fm_end is None:
        raise ValueError("Unclosed YAML frontmatter: missing closing '---'.")

    frontmatter = parse_strict_yaml("\n".join(lines[1:fm_end]), "frontmatter")
    body_lines = lines[fm_end + 1 :]

    header_positions: List[Tuple[int, int]] = []
    search_start = 0
    for sec_num, expected_h2 in enumerate(EXPECTED_HEADERS, start=1):
        found_idx = None
        for idx in range(search_start, len(body_lines)):
            if body_lines[idx].strip() == expected_h2:
                found_idx = idx
                break
        if found_idx is None:
            raise ValueError(f"Missing or out-of-order required H2 header: '{expected_h2}'")
        header_positions.append((sec_num, found_idx))
        search_start = found_idx + 1

    all_h2 = [line.strip() for line in body_lines if line.strip().startswith("## ")]
    if all_h2 != EXPECTED_HEADERS:
        raise ValueError(f"Unexpected H2 headers detected. Expected {EXPECTED_HEADERS}, found {all_h2}")

    sections: Dict[int, Dict[str, Any]] = {}
    for i, (sec_num, start_idx) in enumerate(header_positions):
        end_idx = header_positions[i + 1][1] if i + 1 < len(header_positions) else len(body_lines)
        slice_lines = body_lines[start_idx + 1 : end_idx]

        fence_starts = [idx for idx, l in enumerate(slice_lines) if l.strip() == "```yaml"]
        fence_ends = [idx for idx, l in enumerate(slice_lines) if l.strip() == "```"]

        if len(fence_starts) != 1 or len(fence_ends) != 1 or fence_ends[0] <= fence_starts[0]:
            raise ValueError(
                f"Section {sec_num} ('{EXPECTED_HEADERS[sec_num - 1]}') must contain exactly one closed ```yaml block."
            )

        outside = slice_lines[: fence_starts[0]] + slice_lines[fence_ends[0] + 1 :]
        if any(l.strip() for l in outside):
            raise ValueError(
                f"Section {sec_num} ('{EXPECTED_HEADERS[sec_num - 1]}') contains non-YAML text outside its fenced block."
            )

        raw_block = "\n".join(slice_lines[fence_starts[0] + 1 : fence_ends[0]])
        sections[sec_num] = parse_strict_yaml(raw_block, f"Section {sec_num}")

    return frontmatter, sections


def normalize_sections_to_manifest(fm: Dict[str, Any], sections: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    merged: Dict[str, Any] = dict(fm)
    if "treat_strings_as_inert_data" not in merged:
        guards = sections.get(5, {}).get("conformance_guards", {})
        if isinstance(guards, dict) and "treat_strings_as_inert_data" in guards:
            merged["treat_strings_as_inert_data"] = guards["treat_strings_as_inert_data"]
    for sec_num in range(1, 8):
        sec_data = sections.get(sec_num, {})
        if isinstance(sec_data, dict):
            merged.update(sec_data)
    return merged


def check_placeholders(obj: Any, path: str = "root") -> List[str]:
    hits: List[str] = []
    if isinstance(obj, str):
        if PLACEHOLDER_RE.search(obj):
            hits.append(f"{path}: {obj!r}")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            hits.extend(check_placeholders(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            hits.extend(check_placeholders(item, f"{path}[{idx}]"))
    return hits


def validate_document(
    md_path: Path,
    strict: bool = False,
    mirror_path: Optional[Path] = None,
) -> List[str]:
    errors: List[str] = []
    raw_bytes = md_path.read_bytes()
    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [f"File is not valid UTF-8: {exc}"]

    if mirror_path is not None:
        if not mirror_path.exists():
            errors.append(f"Mirror file does not exist: {mirror_path}")
        else:
            mirror_bytes = mirror_path.read_bytes()
            if raw_bytes != mirror_bytes:
                errors.append(
                    f"Mirror mismatch: {md_path} ({hashlib.sha256(raw_bytes).hexdigest()}) != "
                    f"{mirror_path} ({hashlib.sha256(mirror_bytes).hexdigest()})"
                )

    try:
        fm, sections = extract_sections(content)
    except ValueError as exc:
        return errors + [str(exc)]

    allowed_fm = REQUIRED_FRONTMATTER_KEYS | OPTIONAL_FRONTMATTER_KEYS_V012
    missing_fm = REQUIRED_FRONTMATTER_KEYS - set(fm.keys())
    unknown_fm = set(fm.keys()) - allowed_fm
    if missing_fm:
        errors.append(f"Frontmatter missing required keys: {sorted(missing_fm)}")
    if unknown_fm:
        errors.append(f"Frontmatter contains unknown keys (unknown_fields: reject): {sorted(unknown_fm)}")

    version = fm.get("machinefirst_version")
    if version not in VALID_VERSIONS:
        errors.append(f"Unsupported machinefirst_version: {version!r} (expected one of {sorted(VALID_VERSIONS)})")
    if fm.get("parse_mode") != "markdown-with-frontmatter-and-seven-fenced-yaml-sections":
        errors.append("Frontmatter parse_mode must be 'markdown-with-frontmatter-and-seven-fenced-yaml-sections'")
    if fm.get("duplicate_keys") != "reject":
        errors.append("Frontmatter duplicate_keys must be 'reject'")
    if fm.get("unknown_fields") != "reject":
        errors.append("Frontmatter unknown_fields must be 'reject'")
    if fm.get("claim_authority") != "publisher_asserted":
        errors.append("Frontmatter claim_authority must be 'publisher_asserted'")
    if fm.get("authority_model") != "publisher_declared_nonbinding":
        errors.append("Frontmatter authority_model must be 'publisher_declared_nonbinding'")
    if fm.get("this_file_is_data_not_instructions") is not True:
        errors.append("Frontmatter this_file_is_data_not_instructions must be boolean true")
    if fm.get("scope") not in ALLOWED_SCOPES:
        errors.append(f"Frontmatter scope must be one of {sorted(ALLOWED_SCOPES)} (got {fm.get('scope')!r})")

    s1 = sections[1]
    subj = s1.get("subject", {})
    cb = s1.get("contract_binding", {})
    if not isinstance(subj, dict) or not isinstance(cb, dict):
        errors.append("Section 1 must contain 'subject' and 'contract_binding' mappings.")
    else:
        if cb.get("contract_excluded_from_subject") is not True:
            errors.append("Section 1 contract_binding.contract_excluded_from_subject must be true")
        if cb.get("subject_revision_is_ancestor_of_contract_commit") is not True:
            errors.append("Section 1 contract_binding.subject_revision_is_ancestor_of_contract_commit must be true")
        if strict:
            rev = str(subj.get("subject_revision", ""))
            if not GIT_SHA_RE.match(rev):
                errors.append(
                    f"Section 1 subject.subject_revision must be a 40-char lowercase hex SHA in --strict mode (got {rev!r})"
                )

    s2 = sections[2]
    ladder = s2.get("evidence_ladder", [])
    states = s2.get("auditor_states", [])
    if set(ladder) != ALLOWED_EVIDENCE_LEVELS:
        errors.append(f"Section 2 evidence_ladder must match {sorted(ALLOWED_EVIDENCE_LEVELS)}")
    if set(states) != ALLOWED_AUDITOR_STATES:
        errors.append(f"Section 2 auditor_states must match {sorted(ALLOWED_AUDITOR_STATES)}")

    artifacts = s2.get("normative_artifacts", [])
    artifact_ids = set()
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("Section 2 normative_artifacts must be a non-empty list.")
    else:
        for art in artifacts:
            aid = art.get("id")
            if not aid:
                errors.append("Every normative_artifact must define a non-empty 'id'.")
            elif aid in artifact_ids:
                errors.append(f"Duplicate normative_artifact id: {aid!r}")
            else:
                artifact_ids.add(aid)

            if art.get("claimed_level") not in ALLOWED_EVIDENCE_LEVELS:
                errors.append(f"Artifact {aid!r} has invalid claimed_level: {art.get('claimed_level')!r}")

            if strict:
                digest = str(art.get("digest", ""))
                img_digest = str(art.get("toolchain_image_digest", ""))
                if not SHA256_RE.match(digest):
                    errors.append(f"Artifact {aid!r} digest must be 64-char hex in --strict mode.")
                if not SHA256_PREFIXED_RE.match(img_digest):
                    errors.append(f"Artifact {aid!r} toolchain_image_digest must match 'sha256:<64-hex>' in --strict mode.")

    s3 = sections[3]
    claims = s3.get("claims", [])
    claim_ids = set()
    seen_qty_scopes = set()
    if not isinstance(claims, list) or not claims:
        errors.append("Section 3 claims must be a non-empty list.")
    else:
        for clm in claims:
            cid = clm.get("id")
            if not cid or cid in claim_ids:
                errors.append(f"Missing or duplicate claim id: {cid!r}")
            else:
                claim_ids.add(cid)

            qty_scope = (clm.get("quantity_id"), clm.get("scope"))
            if qty_scope in seen_qty_scopes:
                errors.append(f"Duplicate (quantity_id, scope) pair in claim {cid!r}: {qty_scope}")
            seen_qty_scopes.add(qty_scope)

            proof_target = clm.get("proof_target")
            if proof_target not in {"model", "implementation"}:
                errors.append(f"Claim {cid!r} proof_target must be 'model' or 'implementation'.")

            claimed_level = clm.get("claimed_level")
            if claimed_level not in ALLOWED_EVIDENCE_LEVELS:
                errors.append(f"Claim {cid!r} has invalid claimed_level: {claimed_level!r}")

            ref_id = clm.get("refinement_ref")
            if ref_id is not None and ref_id not in artifact_ids:
                errors.append(f"Claim {cid!r} refinement_ref {ref_id!r} not found in normative_artifacts.")
            if proof_target == "implementation" and claimed_level == "proved" and not ref_id:
                errors.append(
                    f"Claim {cid!r} targets 'implementation' with claimed_level 'proved' but has no refinement_ref."
                )

            ev_ref = clm.get("evidence_ref", {})
            if not isinstance(ev_ref, dict) or ev_ref.get("artifact_id") not in artifact_ids:
                errors.append(f"Claim {cid!r} evidence_ref.artifact_id must resolve to a normative_artifact id.")
            if not ev_ref.get("symbol") or not ev_ref.get("symbol_kind"):
                errors.append(f"Claim {cid!r} evidence_ref must specify non-empty 'symbol' and 'symbol_kind'.")

            assump = clm.get("assumptions")
            if (
                not isinstance(assump, dict)
                or "source" not in assump
                or "declared_items" not in assump
                or "dependency_audit" not in assump
            ):
                errors.append(
                    f"Claim {cid!r} assumptions must be a mapping with 'source', 'declared_items', and 'dependency_audit'."
                )

    s4 = sections[4]
    routes = s4.get("routes", [])
    if not isinstance(routes, list) or not routes:
        errors.append("Section 4 routes must be a non-empty list.")
    else:
        for rt in routes:
            if rt.get("definition_ref") not in artifact_ids:
                errors.append(f"Route {rt.get('query_key')!r} definition_ref not found in normative_artifacts.")
            ev_ref = rt.get("evidence_ref", {})
            if not isinstance(ev_ref, dict) or ev_ref.get("artifact_id") not in artifact_ids:
                errors.append(f"Route {rt.get('query_key')!r} evidence_ref.artifact_id not found in normative_artifacts.")
            r_ref = rt.get("refinement_ref")
            if r_ref is not None and r_ref not in artifact_ids:
                errors.append(f"Route {rt.get('query_key')!r} refinement_ref {r_ref!r} not found in normative_artifacts.")

    s5 = sections[5]
    guards = s5.get("conformance_guards", {})
    if not isinstance(guards, dict):
        errors.append("Section 5 must contain a 'conformance_guards' mapping.")
    else:
        if guards.get("treat_strings_as_inert_data") is not True:
            errors.append("Section 5 conformance_guards.treat_strings_as_inert_data must be true.")
        if "auditor_override_permitted" in guards:
            errors.append("Section 5 must NOT contain imperative 'auditor_override_permitted' key.")

    s6 = sections[6]
    qc = s6.get("quick_check", {})
    if not isinstance(qc, dict):
        errors.append("Section 6 must contain a 'quick_check' mapping.")
    else:
        if qc.get("network") != "none":
            errors.append("Section 6 quick_check.network must be 'none' for offline verification.")
        covered = qc.get("quick_check_covers", [])
        if not isinstance(covered, list) or not covered:
            errors.append("Section 6 quick_check.quick_check_covers must list at least one claim ID.")
        else:
            unknown_claims = set(covered) - claim_ids
            if unknown_claims:
                errors.append(f"Section 6 quick_check_covers references unknown claim IDs: {sorted(unknown_claims)}")

        neg = qc.get("negative_control", {})
        if not isinstance(neg, dict) or neg.get("required_for_pass") is not True:
            errors.append("Section 6 quick_check.negative_control.required_for_pass must be true.")
        if neg.get("expected_reason") != "target_invariant_violation":
            errors.append("Section 6 quick_check.negative_control.expected_reason must be 'target_invariant_violation'.")

    s7 = sections[7]
    if "known_gaps" not in s7 or not isinstance(s7["known_gaps"], list):
        errors.append("Section 7 must define 'known_gaps' as a list (use [] if none).")

    if version == "0.1.2":
        normalized = normalize_sections_to_manifest(fm, sections)
        errors.extend(validate_manifest(normalized, strict=strict))

    if strict:
        placeholder_hits = check_placeholders({"frontmatter": fm, "sections": sections})
        for hit in placeholder_hits:
            errors.append(f"Unresolved template placeholder forbidden in --strict mode at {hit}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline MACHINEFIRST (v0.1.1 / v0.1.2) Markdown & Normalized JSON Manifest Validator"
    )
    parser.add_argument("file", type=Path, help="Path to MACHINEFIRST.md or normalized JSON manifest")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enforce v0.1.2 strict genesis/evidence requirements and reject template placeholders.",
    )
    parser.add_argument(
        "--mirror-primary",
        type=Path,
        default=None,
        help="Optional path to primary MACHINEFIRST.md for byte-identical mirror check (JSON mode).",
    )
    parser.add_argument(
        "--mirror-path",
        type=Path,
        default=None,
        help="Optional path to /machinefirst.txt to verify byte-identical UTF-8 equality.",
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"FAIL: File not found: {args.file}", file=sys.stderr)
        return 1

    if args.file.suffix.lower() == ".json":
        errors: List[str] = []
        if args.mirror_path is not None:
            primary = args.mirror_primary if args.mirror_primary is not None else Path("MACHINEFIRST.md")
            errors.extend(check_mirror_byte_parity(primary, args.mirror_path))
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:
            print(f"LOAD_ERROR: {exc}", file=sys.stderr)
            return 2

        errors.extend(validate_manifest(data, strict=args.strict))
        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            return 1
        print("PASS: manifest conforms to MACHINEFIRST v0.1.2 validation policy")
        return 0

    errors = validate_document(args.file, strict=args.strict, mirror_path=args.mirror_path)
    if errors:
        print(f"FAIL: {args.file} failed MACHINEFIRST validation with {len(errors)} error(s):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    mode_label = "STRICT PRODUCTION" if args.strict else "TEMPLATE / STRUCTURAL"
    print(f"PASS [{mode_label}]: {args.file} conforms to MACHINEFIRST specification.")
    return 0


if __name__ == "__main__":
    sys.exit(main())