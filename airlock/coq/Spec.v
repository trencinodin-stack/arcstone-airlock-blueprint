(* Independent human-authored admission policy over mathematical Z.
   Protected by CODEOWNERS and EXPECTED_SPEC_V_SHA256 release baseline. *)
From Coq Require Import Bool.Bool ZArith.ZArith.
From Airlock Require Import GeneratedInterface.
Open Scope Z_scope.

Definition spec_allow (m : gen_mode) (budget cost : Z) : bool :=
  match m with
  | Mode_Armed => Z.leb cost budget
  | Mode_Safe | Mode_Fault => false
  end.
