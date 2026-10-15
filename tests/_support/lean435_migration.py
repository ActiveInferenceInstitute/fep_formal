"""Compare frozen H3 carrier bytes across the enumerated Lean 4.35 migration."""

from __future__ import annotations

import re

_CARRIER_IMPORT_ADDITIONS = {
    "src/fep_lean/formal/fin4_gaussian_semigroup.lean": (
        "Mathlib.Probability.Distributions.Gaussian.Fernique",
    ),
    "src/fep_lean/formal/gaussian_precision_conditioning.lean": (
        "Mathlib.Probability.Distributions.Gaussian.HasGaussianLaw.Basic",
    ),
    "src/fep_lean/formal/scalar_gaussian_semigroup.lean": (),
    "src/fep_lean/formal/compositions/smooth_reference_kernel.lean": (),
    "src/fep_lean/formal/compositions/gaussian_filter.lean": (
        "Mathlib.Probability.Kernel.Composition.WithDensity",
    ),
    "src/fep_lean/formal/compositions/gaussian_control.lean": (),
}

_CARRIER_EXPORTED_SUPPORT = {
    "src/fep_lean/formal/scalar_gaussian_semigroup.lean": (
        "noncomputable def rateDenominator",
        "theorem stationaryVariance_pos",
    ),
    "src/fep_lean/formal/compositions/gaussian_control.lean": (
        "noncomputable instance actionKernelFamily_isMarkovKernel",
        "noncomputable def boolDynamics",
    ),
}


def historical_carrier_bytes(relative: str, live: bytes) -> bytes:
    """Reverse only known carrier migration edits, never update frozen evidence.

    Callers must compare the returned bytes with the immutable historical
    digest. Any other statement, proof, carrier, or import change survives
    this reversal and therefore invalidates that comparison.
    """
    additions = _CARRIER_IMPORT_ADDITIONS[relative]
    migrated = live.decode("utf-8")
    assert migrated.startswith("module\n"), relative
    assert migrated.count("\n@[expose] public section\n") == 1, relative
    historical = migrated.removeprefix("module\n").replace(
        "\n@[expose] public section\n", "", 1
    )
    for dependency in additions:
        extra_import = f"public import {dependency}\n"
        assert historical.count(extra_import) == 1, relative
        historical = historical.replace(extra_import, "", 1)
    historical = re.sub(r"(?m)^public import ", "import ", historical)
    for support in _CARRIER_EXPORTED_SUPPORT.get(relative, ()):
        # Declarations may continue on the next line; retain that exact suffix.
        pattern = rf"(?m)^{re.escape(support)}(?=\s)"
        assert len(re.findall(pattern, historical)) == 1, relative
        historical = re.sub(pattern, f"private {support}", historical, count=1)
    return historical.encode("utf-8")
