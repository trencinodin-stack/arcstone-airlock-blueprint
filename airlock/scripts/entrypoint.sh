#!/usr/bin/env bash
set -euo pipefail

echo "=== [1/6] Staging immutable inputs into writable /work scratch space ==="
mkdir -p /work/home /work/src/crates /work/gen /work/coq /work/audit /work/canary

cp /src/Cargo.toml /work/src/Cargo.toml
cp /src/Cargo.lock /work/src/Cargo.lock
cp -r /src/crates/example-no-std-gate /work/src/crates/example-no-std-gate
cp /src/airlock/coq/_CoqProject /work/coq/_CoqProject
cp /src/airlock/coq/GeneratedInterface.v /work/coq/GeneratedInterface.v
cp /src/airlock/coq/Spec.v /work/coq/Spec.v
cp /src/airlock/coq/Refinement.v /work/coq/Refinement.v

# Copy Aeneas Coq support primitives into /work/gen
cp -r /opt/aeneas/backends/coq/* /work/gen/
chmod -R u+w /work/src /work/coq /work/gen

echo "=== [2/6] Running Charon LLBC extraction (--lib only) & Aeneas Coq synthesis ==="
cd /work/src/crates/example-no-std-gate
charon cargo --preset=aeneas --locked -- --lib
LLBC_FILE="$(find /work/src -maxdepth 4 -name '*.llbc' | head -n1)"
if [ -z "$LLBC_FILE" ]; then
  echo "ERROR: Charon produced no .llbc file" >&2
  exit 1
fi
cp "$LLBC_FILE" /work/gen/example_no_std_gate.llbc

cd /work/gen
aeneas -backend coq /work/gen/example_no_std_gate.llbc -dest /work/gen

GEN_V="$(find /work/gen -maxdepth 1 -name '*.v' ! -name 'Primitives.v' | sort | head -n1)"
if [ -z "$GEN_V" ]; then
  echo "ERROR: Aeneas produced no generated .v module" >&2
  exit 1
fi

echo "=== [3/6] Verifying generated Coq interface shape ==="
/bin/bash /src/airlock/scripts/check-shape.sh "$GEN_V" /src/airlock/golden/generated-shape.txt

echo "=== [4/6] Compiling Primitives, Generated Module, Spec & Refinement Proof ==="
cd /work/coq
# Compile all .v files in /work/gen first in topological order
for f in $(find /work/gen -maxdepth 1 -name '*.v' | sort); do
  coqc -q -Q /work/gen Gen "$f"
done
coqc -q -Q /work/gen Gen -Q /work/coq Airlock /work/coq/GeneratedInterface.v
coqc -q -Q /work/gen Gen -Q /work/coq Airlock /work/coq/Spec.v
coqc -q -Q /work/gen Gen -Q /work/coq Airlock /work/coq/Refinement.v

echo "=== [5/6] Running isolated semantic canary mutant in /work/canary ==="
mkdir -p /work/canary/src/crates /work/canary/gen /work/canary/coq
cp /src/Cargo.toml /work/canary/src/Cargo.toml
cp /src/Cargo.lock /work/canary/src/Cargo.lock
cp -r /src/crates/example-no-std-gate /work/canary/src/crates/example-no-std-gate
cp -r /opt/aeneas/backends/coq/* /work/canary/gen/
cp /src/airlock/coq/GeneratedInterface.v /work/canary/coq/GeneratedInterface.v
cp /src/airlock/coq/Spec.v /work/canary/coq/Spec.v
cp /src/airlock/coq/Refinement.v /work/canary/coq/Refinement.v
chmod -R u+w /work/canary

# Inject semantic mutation: flip `cost <= budget` to `cost >= budget`
python3 - <<'PY'
p = "/work/canary/src/crates/example-no-std-gate/src/lib.rs"
txt = open(p, "r", encoding="utf-8").read()
assert "cost <= budget" in txt, "Canary target pattern missing"
open(p, "w", encoding="utf-8").write(txt.replace("cost <= budget", "cost >= budget", 1))
PY

cd /work/canary/src/crates/example-no-std-gate
CARGO_TARGET_DIR=/work/canary/target charon cargo --preset=aeneas --locked -- --lib
CANARY_LLBC="$(find /work/canary/src -maxdepth 4 -name '*.llbc' | head -n1)"
[ -n "$CANARY_LLBC" ] || { echo "ERROR: Canary extraction failed unexpectedly" >&2; exit 1; }
cd /work/canary/gen
aeneas -backend coq "$CANARY_LLBC" -dest /work/canary/gen

# Prerequisites (Primitives, Generated module, Interface, Spec) MUST compile cleanly on mutant
for f in $(find /work/canary/gen -maxdepth 1 -name '*.v' | sort); do
  coqc -q -Q /work/canary/gen Gen "$f"
done
coqc -q -Q /work/canary/gen Gen -Q /work/canary/coq Airlock /work/canary/coq/GeneratedInterface.v
coqc -q -Q /work/canary/gen Gen -Q /work/canary/coq Airlock /work/canary/coq/Spec.v

# Refinement.v MUST fail specifically on the refinement proof obligation
set +e
CANARY_OUT="$(coqc -q -Q /work/canary/gen Gen -Q /work/canary/coq Airlock /work/canary/coq/Refinement.v 2>&1)"
CANARY_RC=$?
set -e
if [ "$CANARY_RC" -eq 0 ]; then
  echo "SECURITY ERROR: Semantic canary mutant unexpectedly passed Refinement.v!" >&2
  exit 1
fi
echo "OK: Semantic canary mutant rejected as expected (exit $CANARY_RC)."

echo "=== [6/6] Running Kernel Assumption Closure & Minting Canonical Receipt ==="
python3 /src/airlock/scripts/mint-receipt.py \
  --src-root /src \
  --work-gen /work/gen \
  --work-coq /work/coq \
  --work-audit /work/audit \
  --out-receipt /out/REFINEMENT-AUDIT.json
