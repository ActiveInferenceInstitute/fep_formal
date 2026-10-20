module
public import FepSketches.compositions.core

@[expose] public section


example : HasDerivAt fep_fep018.FEP018.fep018_fisherCoordinate
    (fep_fep038.FEP038.fep038_coordinateJacobian 0) 0 := by
  exact FEPComposed.fep018_coordinate_derivative_is_fep038 (by norm_num) (by norm_num)
