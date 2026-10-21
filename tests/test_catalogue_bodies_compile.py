"""Full-catalogue native compile gate (opt-in).

Set ``FEP_LEAN_CATALOGUE_COMPILE_TEST=1`` to run the sealed roster's
``lake env lean`` checks.
Default pytest sessions skip this test so developer machines without a Mathlib
cache stay fast. CI or maintainers enable the gate after
``scripts/_maint_build_topics_catalogue.py`` alignment and a warm Lake workspace.

The default path uses ``check_mathlib_built()`` before batching. Explicit CI
receipt mode executes the production strict operation and independent validator
inside this same test; missing Mathlib then fails rather than skips.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.verification.lean_verifier import LeanVerifier
from tests._support.native_catalogue_gate import (
    CI_NATIVE_RECEIPT_ENV,
    produce_native_catalogue_receipt,
)

PROJ = Path(__file__).resolve().parent.parent
LEAN_DIR = PROJ / "lean"

pytestmark = pytest.mark.serial_lean


@pytest.mark.skipif(
    os.environ.get("FEP_LEAN_CATALOGUE_COMPILE_TEST") != "1"
    and CI_NATIVE_RECEIPT_ENV not in os.environ,
    reason="Set FEP_LEAN_CATALOGUE_COMPILE_TEST=1 for the full sealed Lake sweep.",
)
def test_all_catalogue_bodies_compile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FEP_LEAN_VERIFY_TIMEOUT", "300")
    if CI_NATIVE_RECEIPT_ENV in os.environ:
        produce_native_catalogue_receipt(PROJ, os.environ[CI_NATIVE_RECEIPT_ENV])
        return
    verifier = LeanVerifier(lean_dir=LEAN_DIR, project_root=PROJ)
    ok, msg = verifier.check_mathlib_built()
    if not ok:
        pytest.skip(msg)

    catalogue = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    items = [(t.id, t.lean_sketch) for t in catalogue.topics]
    assert len(items) == len(catalogue.roster.topic_ids)

    results = verifier.verify_batch(items)
    assert len(results) == len(items)
    failures = [
        (r.topic_id, r.status, r.failure_kind, r.errors[:3])
        for r in results
        if not r.compiles or r.has_sorry
    ]
    assert not failures, f"Catalogue compile failures: {failures}"
