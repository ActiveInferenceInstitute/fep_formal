import Lake
open Lake DSL

/-- FEP Lean Sketches — compiled FEP/Active Inference formalisms backed by Mathlib4.

    Add `require mathlib` so that `lake env lean <file>` resolves every
    `import Mathlib.*` module used in the sealed live catalogue.

    Run setup once in a non-sandboxed terminal:
        cd lean && lake exe cache get && lake build
    Then the LeanVerifier can call `lake env lean <sketch.lean>` for each topic.
-/
package «FepSketches»

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "v4.34.0"

@[default_target]
lean_lib «FepSketches» where
  globs := #[.andSubmodules `FepSketches]

lean_lib ACChoice where
  globs := #[.andSubmodules `ACChoice]
