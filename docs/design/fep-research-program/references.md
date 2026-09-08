# Primary sources and pinned-library seams

This source map supports the research questions and feasibility gates. A cited
paper motivates an exact translation or countermodel; citation does not imply
that the repository accepts all of its claims. Mathlib links describe upstream
interfaces, while the local pinned source and compile probes decide what the
project can use.

## Current project boundary

- [FEP background](../../guides/fep-background.md) — current scientific scope and
  formalization boundary.
- [Formal-kernel methods](../../guides/formal-kernel-methods.md) — current carriers,
  module ownership, and evidence distinctions.
- [Topic reference](../../topics-reference.md) — canonical metadata, maturity,
  novelty, relation, body, and manifest owners.
- [Formalism coverage](../../formalism-coverage.md) — generated current
  theorem/capability projection; not a future-work owner.
- [v1.1.0 expansion record](../../../specs/done/formalism-catalogue-155/README.md)
  — why the released cut stops at finite risk, policy trees, native blankets,
  scalar exponential families, and a two-state CTMC.
- [Manuscript limitations](../../manuscript/05e_broader_impact_limitations.md)
  and [conclusion](../../manuscript/06_conclusion.md) — source of the open
  posterior, policy, blanket, geometry, continuous-time, and empirical seams.

## Free Energy Principle, blankets, and critical boundary

- Biehl, Pollock, and Kanai,
  [“A Technical Critique of Some Parts of the Free Energy Principle”](https://doi.org/10.3390/e23030293).
  H1 uses the non-equivalence of blanket notions and the counterexample to an
  unrestricted free-energy lemma as theorem requirements.
- Aguilera, Millidge, Tschantz, and Buckley,
  [“How Particular Is the Physics of the Free Energy Principle?”](https://doi.org/10.1016/j.plrev.2021.11.001).
  H1/H3 use its analysis of restrictive dynamical conditions and the
  flow-of-averages boundary as falsification targets.
- Da Costa, Friston, Heins, and Pavliotis,
  [“Bayesian Mechanics for Stationary Processes”](https://doi.org/10.1098/rspa.2021.0518).
  H2/H3 translate its stationary Gaussian, blanket, synchronization, inference,
  and control claims into separately gated propositions.
- Heins and Da Costa,
  [“Sparse Coupling and Markov Blankets”](https://arxiv.org/abs/2205.10190).
  H1 uses its sufficient/insufficient coupling distinctions when choosing
  positive and negative Gaussian models.

## Discrete active inference, policy, and decision

- Da Costa et al.,
  [“Active Inference on Discrete State-Spaces: A Synthesis”](https://doi.org/10.1016/j.jmp.2020.102447).
  H1 maps its discrete generative, inference, and policy objects to the shared
  finite carrier.
- Da Costa et al.,
  [“Reward Maximisation through Discrete Active Inference”](https://arxiv.org/abs/2009.08111).
  H1.4 treats the stated reward/Bellman equivalence conditions and finite-
  horizon distinction as theorem boundaries.
- Friston et al.,
  [“Sophisticated Inference”](https://arxiv.org/abs/2006.04120).
  H1.4 motivates observation-contingent recursive planning rather than an
  open-loop substitute.
- Millidge, Tschantz, and Buckley,
  [“Whence the Expected Free Energy?”](https://doi.org/10.1162/neco_a_01354).
  H1.4 uses competing EFE derivations to require named conventions and
  counterexamples.
- Blackwell,
  [“Equivalent Comparisons of Experiments”](https://doi.org/10.1214/aoms/1177729032).
  H1.2 interprets native Bayes-risk data processing as observation garbling,
  without extending that result automatically to total EFE.

## Bayesian learning and information geometry

- Ghosal and van der Vaart,
  [*Fundamentals of Nonparametric Bayesian Inference*](https://doi.org/10.1017/9781139029834).
  H1/H2 use its distinctions among posterior consistency, contraction, rates,
  and identifiability; the program does not claim a general nonparametric
  theorem.
- Amari and Nagaoka,
  [*Methods of Information Geometry*](https://doi.org/10.1090/mmono/191).
  H2.1--H2.2 specialize the Fisher metric, dual affine connections,
  exponential/mixture coordinates, and canonical divergence first to one
  Gaussian location family. Global dual coordinates remain gated rather than
  inferred from local invertibility.

## Stochastic thermodynamics

- Seifert,
  [“Stochastic Thermodynamics: Principles and Perspectives”](https://arxiv.org/abs/0710.1187).
  H1.7 and H3.5 separate master-equation/path-law identities from physical
  constitutive interpretation.
- Jarzynski,
  [“Nonequilibrium Equality for Free Energy Differences”](https://doi.org/10.1103/PhysRevLett.78.2690).
  Any later work relation must derive the exponential identity from a protocol
  law rather than assume the target normalization.
- Crooks,
  [“Entropy Production Fluctuation Theorem and the Nonequilibrium Work Relation”](https://doi.org/10.1103/PhysRevE.60.2721).
  H2/H3 finite-grid path ratios must state forward/reverse support and physical
  interpretation assumptions.

## Official Mathlib interfaces to probe at the active pin

- [KL data processing](https://leanprover-community.github.io/mathlib4_docs/Mathlib/InformationTheory/KullbackLeibler/DataProcessing.html)
  — map, trim, and Markov-kernel inequalities including
  `InformationTheory.klDiv_comp_right_le`.
- [Bayes estimators](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Probability/Decision/BayesEstimator.html)
  and [decision risk](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Probability/Decision/Risk/Basic.html)
  — native Bayes risk, argmin estimators, minimax comparison, and garbling.
- [Beta distribution](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Probability/Distributions/Beta.html)
  — normalized beta measure for the optional conjugacy spike.
- [Probability measures](https://leanprover-community.github.io/mathlib4_docs/Mathlib/MeasureTheory/Measure/ProbabilityMeasure.html)
  and [Lévy convergence](https://leanprover-community.github.io/mathlib4_docs/Mathlib/MeasureTheory/Measure/LevyConvergence.html)
  — weak-convergence topology and characteristic-function route.
- [Matrix exponential](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/Normed/Algebra/MatrixExponential.html)
  — H1.7's generator-construction spike.
- [Riemannian manifolds](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/Riemannian/Basic.html),
  [Riemannian vector bundles](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/VectorBundle/Riemannian.html),
  and [covariant derivatives](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/VectorBundle/CovariantDerivative/Basic.html)
  — H2.2's coordinate-to-bundled stop/go ladder.
- [Brownian motion](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Probability/BrownianMotion/Basic.html)
  — finite-dimensional Brownian laws and the weak Markov property; not a
  substitute for stochastic integration.
- [Ionescu--Tulcea trajectories](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Probability/Kernel/IonescuTulcea/Traj.html)
  — candidate path/trajectory carrier.

The public documentation site may describe a newer release candidate than the
project supports. Every implementation spec must check the local pin and
resolved revision rather than treating the public site's current build as the
project toolchain.
