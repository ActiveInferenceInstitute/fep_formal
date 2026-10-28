"""Deprecated compatibility imports for :mod:`fep_formal`.

Every legacy descendant resolves to the canonical module object. Never execute
canonical source under a second name: that duplicates classes and receipt types.
"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.util
import sys
import warnings
from types import CodeType, ModuleType


class _AliasLoader(importlib.abc.Loader):
    def __init__(self, canonical: str) -> None:
        self.canonical = canonical

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> ModuleType | None:
        return None

    def exec_module(self, module: ModuleType) -> None:
        sys.modules[module.__name__] = importlib.import_module(self.canonical)

    def get_code(self, fullname: str) -> CodeType | None:
        spec = importlib.util.find_spec(self.canonical)
        if spec is None or not isinstance(spec.loader, importlib.abc.InspectLoader):
            raise ImportError(f"No executable canonical module for {fullname}")
        return spec.loader.get_code(self.canonical)


class _AliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(
        self,
        fullname: str,
        path: object = None,
        target: ModuleType | None = None,
    ) -> importlib.machinery.ModuleSpec | None:
        if not fullname.startswith("fep_lean."):
            return None
        canonical = "fep_formal" + fullname[len("fep_lean") :]
        spec = importlib.util.find_spec(canonical)
        if spec is None:
            return None
        return importlib.util.spec_from_loader(
            fullname,
            _AliasLoader(canonical),
            origin=spec.origin,
            is_package=spec.submodule_search_locations is not None,
        )


warnings.warn(
    "fep_lean is deprecated; import fep_formal instead. "
    "Compatibility is retained throughout the 2.x release line.",
    FutureWarning,
    stacklevel=2,
)
if not any(isinstance(finder, _AliasFinder) for finder in sys.meta_path):
    sys.meta_path.insert(0, _AliasFinder())
sys.modules[__name__] = importlib.import_module("fep_formal")
