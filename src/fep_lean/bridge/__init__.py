"""GNN bridge operations; model interchange remains GNN documents.

Checks are read-only. Emission and custody pin changes are explicit operations.
No bridge result establishes native Lean or full-provider verification.

Operations surface (contract v0.5):
``status``, ``pin_sources``, ``check_sources``, ``emit``,
``certificate_receipt``, ``emit_certificate``, ``validate_certificate``,
``verify_document``; custody primitives ``fingerprint``,
``binding_digest``, ``validate_binding``; and the custody constants
``PIN``, ``EMITTERS``, ``DOCUMENTS``, ``CONTRACT``, ``MIRROR``,
``SYNTAX_PIN``, ``SYNTAX_FILES``.
"""

from fep_lean.bridge.custody import binding_digest, fingerprint, validate_binding
from fep_lean.bridge.operations import (
    CONTRACT,
    DOCUMENTS,
    EMITTERS,
    MIRROR,
    PIN,
    SYNTAX_FILES,
    SYNTAX_PIN,
    certificate_receipt,
    check_sources,
    emit,
    emit_certificate,
    pin_sources,
    status,
    validate_certificate,
    verify_document,
)

__all__ = [
    "CONTRACT",
    "DOCUMENTS",
    "EMITTERS",
    "MIRROR",
    "PIN",
    "SYNTAX_FILES",
    "SYNTAX_PIN",
    "binding_digest",
    "certificate_receipt",
    "check_sources",
    "emit",
    "emit_certificate",
    "fingerprint",
    "pin_sources",
    "status",
    "validate_binding",
    "validate_certificate",
    "verify_document",
]
