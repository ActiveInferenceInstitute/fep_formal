import Mathlib

/-- Root module for the FepSketches library. The lakefile declares
`lean_lib «FepSketches»` with `globs := #[.andSubmodules 'FepSketches]`, so every
topic file under `FepSketches/` is a default `lake build` target; ephemeral
verifier probes are typechecked via `lake env lean`. -/
theorem fepSketchesRoot : True := True.intro
