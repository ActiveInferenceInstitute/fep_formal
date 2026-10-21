# Finite weighted-Dirac KL extraction

Issue [#110](https://github.com/ActiveInferenceInstitute/fep_formal/issues/110).

The maintained generic helpers live beside `finiteKL` in
`src/fep_lean/formal/finite_information.lean`, under `FEP.FiniteInformation`.
They construct arbitrary finite measures from nonnegative weights. Normalization
is explicit; relative support permits shared zeros. The existing DecisionRisk
public theorem names and types delegate to these helpers through the existing
finite-law embedding. No second normalized probability carrier is introduced.

`ConsumerControls.lean` checks positive unequal normalized laws, sparse shared
zeros, singular native infinity and failed support, unequal-mass correction,
failed normalization, rejection of an uncorrected score, definitional equality
with the existing carrier, and four legacy public consumers.

`FiniteWeightKL.lean` is the separately compiled local upstream draft. It imports
only Mathlib and uses no FEP namespace. General finite masses retain the native
KL mass correction. The serial Lean suite compiles both files and checks their
16 and 10 unique axiom reports against the standard three-axiom allowlist.
These checks establish the exact typed formulas and controls, without promoting
catalogue maturity, scientific relations, or full runtime acceptance.

The draft was prepared after bounded source inspection at Mathlib commit
`6d442b50c0ae2cde369cd21de31907e228545df8`; the inspected KL Basic source
matched the compiled dependency pin
`56a005855ea17e0b0958f73ec801ae140b0a1679`.
[Inspected upstream source](https://github.com/leanprover-community/mathlib4/blob/6d442b50c0ae2cde369cd21de31907e228545df8/Mathlib/InformationTheory/KullbackLeibler/Basic.lean).
This bounded inspection does not prove theorem absence or novelty, and current
master was not compiled. Naming, representation and location remain topics for
upstream maintainer discussion. This is a local draft, not a submitted or
accepted Mathlib PR.

Run the project serial test lane from the root required-check contract. The
existing-carrier and standalone files compile separately to avoid conflating
project namespace compatibility with Mathlib-only portability.
