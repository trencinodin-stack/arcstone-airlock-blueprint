(* Generated-code refinement proof: proves Aeneas-synthesized `decide`
   is total (never returns Fail/Div) and refines `Spec.spec_allow`. *)
From Coq Require Import Bool.Bool ZArith.ZArith.
From Airlock Require Import GeneratedInterface Spec.
Open Scope Z_scope.

Theorem decide_refines_spec :
  forall (m : gen_mode) (budget cost : gen_u32),
    gen_decide m budget cost =
    Ok (if spec_allow m (u32_to_Z budget) (u32_to_Z cost)
        then Verdict_Allow
        else Verdict_Deny).
Proof.
  intros m budget cost.
  unfold gen_decide, decide, spec_allow, u32_to_Z.
  destruct m; cbn; try reflexivity.
  (* Qualified against pinned Aeneas Primitives.v scalar comparison lemma *)
  destruct (Z.leb (cost.(val)) (budget.(val))) eqn:Hcmp;
    rewrite <- ?u32_leb_spec, ?Hcmp; reflexivity.
Qed.
