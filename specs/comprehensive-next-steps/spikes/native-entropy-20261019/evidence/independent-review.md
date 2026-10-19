# Issue111 / L06 independent component review

Decision: COMPONENT ACCEPTANCE SUPPORTED. No concrete theorem/consumer gap found against Issue111's stated acceptance: a measure-level Donsker–Varadhan inequality proved without FEP types. This is a component source/feasibility conclusion, not terminal horizon approval or upstream submission.

Base/source epoch: 2b0654713fc128940d109ddfd89c08696e9876f1. The inspected source is byte-identical to that Git blob. The hosted log embeds the canonical marked proof block verbatim and imports only Mathlib.KullbackLeibler.Basic, Mathlib.Probability.Moments.Basic and Mathlib.Tactic (fully qualified paths in the retained consumer).

## Lean lens

variational_duality.lean:1659 onward isolates three general declarations: nativeKL_tilted_gap, nativeEntropy_le_klDiv and nativeCgf_le_klDiv. Their types use only a measurable space, real functions, probability measures, native integration/tilting and InformationTheory.klDiv. No FEP carrier or assumed duality is introduced. The gap is derived from Mathlib's integrable_llr_tilted_right and integral_llr_tilted_right, after explicitly establishing finite KL hypotheses for both reference measures. The bound splits infinite versus finite native KL and applies the exact gap only in the finite branch. CGF specializes f=tX via the native mgf/cgf definitions and integral_const_mul, with no sign restriction on t.

The retained uploaded consumer reports lake env lean returncode0, empty stderr and exactly three axiom reports, each [propext, Classical.choice, Quot.sound]. The consumer includes the exact marked block, so this is direct Mathlib-only elaboration evidence, not compilation relying on an imported FEP theorem. No warning/error or sorry axiom is reported. This review inspected that record and its source hashes; it did not rerun Lean or independently download the job.

## Domain lens

The orientation is correct: E_mu[f] - log E_nu[exp f] is bounded by D(mu||nu). Both laws are probabilities; f is integrable under the candidate and exp f under the reference. The latter is essential, not boilerplate: Mathlib's Bochner integral is totalized, and absent integrability its exponential normalizer could collapse to zero. For an integrable positive exponential under a probability law, the normalizer is positive and finite. No additional full-support or finite-cardinality assumption is hidden in the generic theorem.

The finite gap states D(mu||nu tilted f) = D(mu||nu) - E_mu[f] + log Z in toReal, only with explicit mu<<nu and integrable likelihood ratio. Mathlib defines klDiv as infinity otherwise; the general inequality retains this extended value. No infinite KL is converted to a finite real bound. This is an entropy/DV inequality, not the unrestricted supremum representation, and Issue111's explicit acceptance asks for the inequality.

## Skeptical lens and controls

The actual consumer uses a fair Boolean reference and a nonconstant potential log3 at true and0 at false. It derives normalizer2 and tilted masses3/4 and1/4, proves the tilt differs from the reference, and attains D(tilt||reference)=3/4 log3-log2. This is non-vacuous attainment with the correct argument orientation.

A separate same-law example has negative real objective but zero KL: ENNReal.ofReal clips the objective to0, yielding equality although the candidate is not the tilt. It also proves failure of the corresponding real equality. Thus clipped equality is correctly not advertised as an optimizer iff. A singular dirac-true/dirac-false pair gives native KL=infinity, validates the extended inequality with positive log3 objective and disproves the improper toReal bound. Exploding/nonintegrable normalizers are explicitly excluded by hexp; there is no claim to cover them or a need to infer their admissibility from finite examples. The generic proof and imported API hypotheses, rather than these finite consumers alone, establish the measure-level scope.

## Scope and remaining publication work

The live Issue111 body explicitly asks for the measure-level DV inequality without FEP types, while leaving upstream submission to a separate maintainer decision. L06's target similarly separates score/Fisher candidates. The implemented inequality, exact real gap, CGF specialization, attained and boundary consumers, raw axioms, and this independent Lean/domain/skeptical component assessment satisfy that bounded technical scope. Upstream novelty is a small reusable consequence of existing Mathlib APIs, not an independent new mathematical discovery; no upstream submission or maintainer consent is inferred.

research-contract.md's quorum at lines139-149 expressly applies to terminal horizon theorems. This component review does not supply three human approvals, waive any terminal quorum, or promote full FEP, Fisher/score, scientific, empirical, path/horizon or optimization claims. Work-packages still lists L06 in_progress and CHANGELOG near#111 still says warning-free hosted elaboration remains required. That prospective statement is now superseded by the supplied retained hosted evidence and should be reconciled in a separate exact reviewed acceptance/status patch before closure. No current source defect blocks that bounded update.

## Exact SHA256 bindings

- source: b7acb60b2832abb27c7ff233e90fcbd76150408f1cbba2608919591bee0bc6c9
- L06_MATHLIB_ONLY_block: c40870732bf724346cb50da7b00fdc2575c2d55239218dd0d07899039cbaa1f2
- consumer: df3fffdc6eeefd85364a2a54a6afed7140420d9132289f95993fbf99cbcc6de4
- hosted_log: 495c95ec04d53ba4462fac118f86e2a9ebd21104d4a705790f58ff232aa3eb48

Read-only assessment: source/contracts/tests and local pinned Mathlib API definitions read; actual Issue111 body read via gh. No subject code, Lean compilation, tests, models/providers/services, source edits or repository state changes. Only these requested review artifacts were saved outside the repository.
