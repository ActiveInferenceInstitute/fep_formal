"""Lean bodies for finite-to-native Markov-blanket transfer."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-135": """import FepSketches.native_blanket

namespace FEP135

open FEP MeasureTheory

variable {State : Type*} [Fintype State]
  [MeasurableSpace State] [DiscreteMeasurableSpace State]

/-- The weighted-Dirac embedding preserves every finite singleton mass. -/
theorem fep135_embeddedLaw_apply_singleton
    (law : FiniteLaw State) (state : State) :
    FEP.NativeBlanket.embeddedLaw law {state} = ENNReal.ofReal (law state) :=
  FEP.NativeBlanket.embeddedLaw_apply_singleton law state

/-- The embedded finite law is normalized as a native measure. -/
theorem fep135_embeddedLaw_normalized (law : FiniteLaw State) :
    FEP.NativeBlanket.embeddedLaw law Set.univ = 1 :=
  FEP.NativeBlanket.embeddedLaw_apply_univ law

end FEP135
""",
    "fep-136": """import FepSketches.native_blanket

namespace FEP136

open FEP MeasureTheory
open scoped BigOperators MeasureTheory

variable {State : Type*} [Fintype State]
  [MeasurableSpace State] [DiscreteMeasurableSpace State]

/-- Equality of native embeddings reflects equality of finite laws. -/
theorem fep136_embeddedLaw_injective :
    Function.Injective
      (FEP.NativeBlanket.embeddedLaw : FiniteLaw State → Measure State) :=
  FEP.NativeBlanket.embeddedLaw_injective

/-- Native expectation is exactly the authored finite weighted sum. -/
theorem fep136_embeddedLaw_expectation
    (law : FiniteLaw State) (observable : State → ℝ) :
    ∫ state, observable state ∂FEP.NativeBlanket.embeddedLaw law =
      ∑ state, law state * observable state :=
  FEP.NativeBlanket.embeddedLaw_integral_eq_sum law observable

end FEP136
""",
    "fep-137": """import FepSketches.native_blanket

namespace FEP137

open FEP MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory ProbabilityTheory

variable {Input Output : Type*} [Fintype Input] [Fintype Output]
  [MeasurableSpace Input] [MeasurableSpace Output]
  [DiscreteMeasurableSpace Input] [DiscreteMeasurableSpace Output]

/-- Finite prediction agrees with native measure-kernel composition. -/
theorem fep137_embeddedPredictive_eq_comp
    (prior : FiniteLaw Input) (kernel : FiniteKernel Input Output) :
    FEP.NativeBlanket.embeddedLaw (kernel.predictive prior) =
      FEP.NativeBlanket.embeddedKernel kernel ∘ₘ
        FEP.NativeBlanket.embeddedLaw prior :=
  FEP.NativeBlanket.embeddedPredictive_eq_comp prior kernel

end FEP137
""",
    "fep-138": """import FepSketches.native_blanket

namespace FEP138

open FEP FEP.MarkovBlanket MeasureTheory

variable {Internal Sensory Active External : Type*}
  [Fintype Internal] [Fintype Sensory] [Fintype Active] [Fintype External]
  [MeasurableSpace Internal] [MeasurableSpace Sensory]
  [MeasurableSpace Active] [MeasurableSpace External]
  [DiscreteMeasurableSpace Internal] [DiscreteMeasurableSpace Sensory]
  [DiscreteMeasurableSpace Active] [DiscreteMeasurableSpace External]

/-- Every singleton coordinate rectangle has the exact native blanket
factorization inherited from the finite joint. -/
theorem fep138_staticJoint_rectangle_factorization
    (model : StaticModel Internal Sensory Active External)
    (blanket : Blanket Sensory Active) (internal : Internal)
    (external : External) :
    FEP.NativeBlanket.embeddedLaw (staticJoint model)
        (FEP.NativeBlanket.blanketCoordinate ⁻¹' {blanket} ∩
          FEP.NativeBlanket.internalCoordinate ⁻¹' {internal} ∩
          FEP.NativeBlanket.externalCoordinate ⁻¹' {external}) =
      ENNReal.ofReal (model.blanketLaw blanket) *
        ENNReal.ofReal (model.internalGiven blanket internal) *
          ENNReal.ofReal (model.externalGiven blanket external) :=
  FEP.NativeBlanket.staticJoint_rectangle_factorization
    model blanket internal external

end FEP138
""",
    "fep-139": """import FepSketches.native_blanket

namespace FEP139

open FEP FEP.MarkovBlanket MeasureTheory ProbabilityTheory

variable {Internal Sensory Active External : Type*}
  [Fintype Internal] [Fintype Sensory] [Fintype Active] [Fintype External]
  [Nonempty Internal] [Nonempty External]
  [MeasurableSpace Internal] [MeasurableSpace Sensory]
  [MeasurableSpace Active] [MeasurableSpace External]
  [DiscreteMeasurableSpace Internal] [DiscreteMeasurableSpace Sensory]
  [DiscreteMeasurableSpace Active] [DiscreteMeasurableSpace External]

/-- The embedded static finite joint satisfies Mathlib's native conditional
independence predicate at the actual internal, external, and blanket maps. -/
theorem fep139_staticJoint_condIndepFun
    (model : StaticModel Internal Sensory Active External) :
    CondIndepFun
      (MeasurableSpace.comap FEP.NativeBlanket.blanketCoordinate inferInstance)
      FEP.NativeBlanket.blanketCoordinate_measurable.comap_le
      FEP.NativeBlanket.internalCoordinate
      FEP.NativeBlanket.externalCoordinate
      (FEP.NativeBlanket.embeddedLaw (staticJoint model)) :=
  FEP.NativeBlanket.staticJoint_condIndepFun model

/-- A concrete two-regime Boolean witness makes the native stop/go theorem
nonvacuous at the topic boundary. -/
theorem fep139_correlatedBlanket_nonvacuous :
    letI : MeasurableSpace Bool := ⊤
    CondIndepFun
        (MeasurableSpace.comap FEP.NativeBlanket.blanketCoordinate inferInstance)
        FEP.NativeBlanket.blanketCoordinate_measurable.comap_le
        FEP.NativeBlanket.internalCoordinate
        FEP.NativeBlanket.externalCoordinate
        (FEP.NativeBlanket.embeddedLaw
          (staticJoint FEP.NativeBlanket.correlatedBlanketModel)) ∧
      staticJoint FEP.NativeBlanket.correlatedBlanketModel
          (((false, false), false), false) = 1 / 2 ∧
      staticJoint FEP.NativeBlanket.correlatedBlanketModel
          (((true, true), true), true) = 1 / 2 ∧
      staticJoint FEP.NativeBlanket.correlatedBlanketModel
          (((false, true), false), false) ≠ 1 / 2 :=
  FEP.NativeBlanket.correlatedBlanket_nonvacuous

end FEP139
""",
    "fep-140": """import FepSketches.native_blanket

namespace FEP140

open FEP FEP.MarkovBlanket MeasureTheory ProbabilityTheory

variable {Internal Sensory Active External : Type*}
  [Fintype Internal] [Fintype Sensory] [Fintype Active] [Fintype External]
  [Nonempty Internal] [Nonempty External]
  [MeasurableSpace Internal] [MeasurableSpace Sensory]
  [MeasurableSpace Active] [MeasurableSpace External]
  [DiscreteMeasurableSpace Internal] [DiscreteMeasurableSpace Sensory]
  [DiscreteMeasurableSpace Active] [DiscreteMeasurableSpace External]

/-- Mathlib's composition law preserves the native blanket statement under
measurable coarsenings of both endpoint coordinates. -/
theorem fep140_condIndepFun_measurableImages
    {InternalImage ExternalImage : Type*}
    [MeasurableSpace InternalImage] [MeasurableSpace ExternalImage]
    (model : StaticModel Internal Sensory Active External)
    (internalImage : Internal → InternalImage)
    (externalImage : External → ExternalImage)
    (internalMeasurable : Measurable internalImage)
    (externalMeasurable : Measurable externalImage) :
    CondIndepFun
      (MeasurableSpace.comap FEP.NativeBlanket.blanketCoordinate inferInstance)
      FEP.NativeBlanket.blanketCoordinate_measurable.comap_le
      (internalImage ∘ FEP.NativeBlanket.internalCoordinate)
      (externalImage ∘ FEP.NativeBlanket.externalCoordinate)
      (FEP.NativeBlanket.embeddedLaw (staticJoint model)) :=
  (FEP.NativeBlanket.staticJoint_condIndepFun model).comp
    internalMeasurable externalMeasurable

end FEP140
""",
    "fep-141": """import FepSketches.native_blanket

namespace FEP141

open FEP FEP.MarkovBlanket MeasureTheory ProbabilityTheory

variable {Internal Sensory Active External : Type*}
  [Fintype Internal] [Fintype Sensory] [Fintype Active] [Fintype External]
  [Nonempty Internal] [Nonempty External]
  [MeasurableSpace Internal] [MeasurableSpace Sensory]
  [MeasurableSpace Active] [MeasurableSpace External]
  [DiscreteMeasurableSpace Internal] [DiscreteMeasurableSpace Sensory]
  [DiscreteMeasurableSpace Active] [DiscreteMeasurableSpace External]

/-- A factorized transition row induces a predicted native blanket law. -/
theorem fep141_prediction_preserves_nativeBlanket
    (dynamics : Dynamics Internal Sensory Active External)
    (current : DynamicState Internal Sensory Active External) :
    CondIndepFun
      (MeasurableSpace.comap FEP.NativeBlanket.blanketCoordinate inferInstance)
      FEP.NativeBlanket.blanketCoordinate_measurable.comap_le
      FEP.NativeBlanket.internalCoordinate
      FEP.NativeBlanket.externalCoordinate
      (FEP.NativeBlanket.embeddedLaw
        (staticJoint (nextStaticModel dynamics current))) :=
  FEP.NativeBlanket.prediction_preserves_nativeBlanket dynamics current

end FEP141
""",
}
