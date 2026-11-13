(* Transparent adapter bound to the pinned Aeneas Coq 8.18.0 tuple.
   Validated before compilation by airlock/scripts/check-shape.sh.
   Uses Require Export + Export ExampleNoStdGate so constructors resolve automatically in Spec.v and Refinement.v. *)
From Coq Require Export ZArith.ZArith.
From Primitives Require Export Primitives.
From Primitives Require Export ExampleNoStdGate.
Export ExampleNoStdGate.

Definition gen_mode    := Mode_t.
Definition gen_verdict := Verdict_t.
Definition gen_u32     := u32.
Definition u32_to_Z (x : gen_u32) : Z := x.(val).
Definition gen_decide  := decide.
