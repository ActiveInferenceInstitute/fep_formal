"""Canonical Lean bodies for finite path-space stochastic thermodynamics."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-093": """import FepSketches.path_thermodynamics

namespace FEP093

open FEP FEP.PathThermodynamics Finset
open scoped BigOperators

variable {Path : Type*} [Fintype Path]

/-- The supported forward/reverse likelihood ratio reconstructs forward path
mass, while both finite path laws remain normalized. -/
theorem fep093_forward_reverse_pathLaw_ratio
    (protocol : FinitePathProtocol Path)
    (hReverse : ∀ path, 0 < protocol.reverseAligned path) (path : Path) :
    pathRatio protocol path * protocol.reverseAligned path =
      protocol.forward path :=
  pathRatio_mul_reverse protocol hReverse path

/-- Forward and reverse path-law normalization is structural. -/
theorem fep093_pathLaws_normalized
    (protocol : FinitePathProtocol Path) :
    (∑ path, protocol.forward path = 1) ∧
      ∑ path, protocol.reverseAligned path = 1 :=
  pathLaw_normalization protocol

/-- The recorded path reversal is involutive. -/
theorem fep093_pathReversal_involutive
    (protocol : FinitePathProtocol Path) (path : Path) :
    protocol.reversal (protocol.reversal path) = path :=
  reverse_reverse protocol path

end FEP093
""",
    "fep-094": """import FepSketches.path_thermodynamics

namespace FEP094

open FEP FEP.PathThermodynamics FEP.FiniteInformation Finset
open scoped BigOperators

variable {Path : Type*} [Fintype Path]

/-- Mean stochastic entropy production is exactly the finite path-space KL
divergence. -/
theorem fep094_entropyProduction_as_pathKL
    (protocol : FinitePathProtocol Path) :
    entropyProduction protocol =
      finiteKL protocol.forward protocol.reverseAligned :=
  rfl

/-- Full path support converts the KL definition to the expected log ratio. -/
theorem fep094_entropyProduction_expected_logRatio
    (protocol : FinitePathProtocol Path)
    (hForward : ∀ path, 0 < protocol.forward path)
    (hReverse : ∀ path, 0 < protocol.reverseAligned path) :
    entropyProduction protocol =
      ∑ path, protocol.forward path * pathwiseEntropyProduction protocol path :=
  entropyProduction_eq_expected_logRatio protocol hForward hReverse

/-- Finite path entropy production is nonnegative. -/
theorem fep094_entropyProduction_nonnegative
    (protocol : FinitePathProtocol Path) :
    0 ≤ entropyProduction protocol :=
  entropyProduction_nonneg protocol

end FEP094
""",
    "fep-095": """import FepSketches.path_thermodynamics

namespace FEP095

open FEP FEP.PathThermodynamics

variable {Path : Type*} [Fintype Path]

/-- The supported pointwise detailed fluctuation symmetry reconstructs the
forward path law from the reverse law and exponential entropy production. -/
theorem fep095_detailedFluctuation_symmetry
    (protocol : FinitePathProtocol Path)
    (hForward : ∀ path, 0 < protocol.forward path)
    (hReverse : ∀ path, 0 < protocol.reverseAligned path) (path : Path) :
    protocol.reverseAligned path *
        Real.exp (pathwiseEntropyProduction protocol path) =
      protocol.forward path :=
  detailedFluctuation_identity protocol hForward hReverse path

/-- When reversal exchanges the aligned laws, pathwise entropy production is
odd under the involution. -/
theorem fep095_entropyProduction_reversal_antisymmetry
    (protocol : FinitePathProtocol Path)
    (hForward : ∀ path, 0 < protocol.forward path)
    (hReverse : ∀ path, 0 < protocol.reverseAligned path)
    (hExchangeForward : ∀ path,
      protocol.forward (protocol.reversal path) = protocol.reverseAligned path)
    (hExchangeReverse : ∀ path,
      protocol.reverseAligned (protocol.reversal path) = protocol.forward path)
    (path : Path) :
    pathwiseEntropyProduction protocol (protocol.reversal path) =
      -pathwiseEntropyProduction protocol path :=
  pathwiseEntropyProduction_reverse protocol hForward hReverse
    hExchangeForward hExchangeReverse path

end FEP095
""",
    "fep-096": """import FepSketches.path_thermodynamics

namespace FEP096

open FEP FEP.PathThermodynamics Finset
open scoped BigOperators

variable {Path : Type*} [Fintype Path]

/-- Supported normalized finite path laws obey the integral fluctuation
identity. -/
theorem fep096_integralFluctuation_theorem
    (protocol : FinitePathProtocol Path)
    (hForward : ∀ path, 0 < protocol.forward path)
    (hReverse : ∀ path, 0 < protocol.reverseAligned path) :
    ∑ path, protocol.forward path *
        Real.exp (-pathwiseEntropyProduction protocol path) = 1 :=
  integralFluctuation_eq_one protocol hForward hReverse

end FEP096
""",
    "fep-097": """import FepSketches.path_thermodynamics

namespace FEP097

open FEP FEP.PathThermodynamics

variable {Path : Type*} [Fintype Path]

/-- A positive inverse temperature and explicit exponential-work
normalization imply the finite Jarzynski equality. -/
theorem fep097_finiteJarzynski_equality
    (law : FiniteLaw Path) (beta deltaFreeEnergy : ℝ)
    (work : Path → ℝ)
    (hNormalization :
      HasJarzynskiNormalization law beta deltaFreeEnergy work) :
    exponentialWorkAverage law beta work =
      Real.exp (-beta * deltaFreeEnergy) :=
  finiteJarzynski_eq law beta deltaFreeEnergy work hNormalization

end FEP097
""",
    "fep-098": """import FepSketches.path_thermodynamics

namespace FEP098

open FEP FEP.FiniteMarkovDynamics FEP.PathThermodynamics

variable {State : Type*} [Fintype State]

/-- Finite detailed balance cancels every oriented local probability current. -/
theorem fep098_localDetailedBalance_currentCancellation
    (law : FiniteLaw State) (kernel : FiniteKernel State State)
    (hReversible : IsReversible law kernel) (source target : State) :
    probabilityCurrent law kernel source target = 0 :=
  localDetailedBalance_current_zero law kernel hReversible source target

/-- A zero reverse rate is kept as an explicit totalized-log boundary rather
than reported as an extended-real affinity. -/
theorem fep098_zeroReverseRate_boundary
    (law : FiniteLaw State) (kernel : FiniteKernel State State)
    (source target : State) (hZero : kernel target source = 0) :
    localAffinity law kernel source target = 0 :=
  localAffinity_zero_reverseRate_boundary law kernel source target hZero

end FEP098
""",
    "fep-099": """import FepSketches.path_thermodynamics

namespace FEP099

open FEP FEP.FiniteInformation FEP.FiniteMarkovDynamics
  FEP.PathThermodynamics

variable {State : Type*} [Fintype State]

/-- One full-support reversible Markov step dissipates KL to its stationary
law; detailed balance supplies stationarity and finite channel data processing
supplies the inequality. -/
theorem fep099_reversibleChain_oneStep_KL_dissipation
    [Nonempty State]
    (actual stationary : FiniteLaw State)
    (kernel : FiniteKernel State State)
    (hActual : ∀ state, 0 < actual state)
    (hStationary : ∀ state, 0 < stationary state)
    (hKernel : ∀ source target, 0 < kernel source target)
    (hReversible : IsReversible stationary kernel) :
    finiteKL (kernel.predictive actual) stationary ≤
      finiteKL actual stationary :=
  reversibleKL_oneStep_dissipation actual stationary kernel hActual
    hStationary hKernel hReversible

/-- The identity transition is the exact reversible equality boundary. -/
theorem fep099_reversibleEquality_boundary [DecidableEq State]
    (actual stationary : FiniteLaw State) :
    finiteKL
        ((FiniteKernel.identity : FiniteKernel State State).predictive actual)
        stationary = finiteKL actual stationary :=
  identityKernel_KL_equality actual stationary

/-- A concrete unequal full-support Boolean forward/reverse pair has strictly
positive path entropy production. -/
theorem fep099_irreversiblePositiveProduction_witness :
    0 < entropyProduction irreversibleBoolProtocol :=
  irreversibleBool_entropyProduction_pos

end FEP099
""",
}
