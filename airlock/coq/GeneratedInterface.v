(* Transparent adapter bound to the pinned Aeneas Coq 8.18.0 tuple.
   Validated before compilation by airlock/scripts/check-shape.sh.
   Uses Require Export so constructors resolve automatically in Spec.v and Refinement.v. *)
From Coq Require Export ZArith.ZArith.
From Gen Require Export Primitives.
From Gen Require Export ExampleNoStdGate.

Definition gen_mode    := mode_t.
Definition gen_verdict := verdict_t.
Definition gen_u32     := u32.
Definition u32_to_Z (x : gen_u32) : Z := x.(val).
Definition gen_decide  := decide.
