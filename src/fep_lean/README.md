# `fep_lean` — FEP_Formal Python package

The installable namespace for FEP_Formal's catalogue, reusable methods and
verification pipeline. The namespace and `fep-lean` console name remain stable
independently of the project-facing name.

The [source guide](../README.md) describes package responsibilities. Each
subpackage's `__init__.py` is the public export owner; the root
[`__init__.py`](__init__.py) resolves selected high-level exports lazily.

```python
from fep_lean.catalogue import FEPTopicCatalogue
from fep_lean.methods import build_mathematical_positioning, inspect_topic
from fep_lean.verification import LeanVerifier
```

## Interpreter and resource contracts

The packaging floor lives in [pyproject.toml](../../pyproject.toml). Development
and evidence validation use the interpreter declared by
[.python-version](../../.python-version); the strict mypy target is declared in
the same project configuration. The accepted validator profile is CPython 3.14,
and minimum-version compatibility has its own installed-wheel CI lanes.
See [testing](../../docs/testing.md) for their scope and
[ISA.md](../../ISA.md#current-assessment) for accepted source checkpoints.

Portable catalogue and mathematical-methods APIs read installed resources.
Checkout-bound operator workflows validate their required assets rather than
treating a `site-packages` ancestor as a project root. The package intentionally
installs no obsolete top-level compatibility modules.

Q7's current `ast.dump` scaffold contract refuses unsupported interpreters
before parsing. That guard limits Q7 evidence validation, not ordinary package
installation or catalogue use. The corresponding open work remains in
[TODO.md](../../TODO.md); a Python-version change needs a reviewed source and
custody migration rather than a documentation-only pin change.
