"""One strict-JSON loader for every receipt/custody engine.

All five former hand-rolled parsers rejected duplicate keys; most rejected
non-finite constants; only one wrapped ``RecursionError``. This module owns
one canonical semantics so the drift that produced SC-3 cannot regrow.
Error-message texts of the migrated sites are preserved verbatim: tests and
receipts pin them.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

__all__ = ["load_strict_json"]


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key}")
        result[key] = value
    return result


def load_strict_json(
    source: str | bytes,
    *,
    fail: Callable[[str, str], None] | None = None,
    parse_float: Callable[[str], object] | None = None,
) -> Any:
    """Parse strict JSON: duplicate keys and non-finite constants rejected.

    With ``fail`` supplied, every rejection is funneled through it with a
    ``(reason, detail)`` pair (``"json"`` / the message) so a caller's typed
    error contract is preserved; otherwise ``ValueError`` propagates.
    ``parse_float`` is forwarded for custody engines that decode numbers as
    ``Decimal``.
    """

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        try:
            return _unique_pairs(items)
        except ValueError as exc:
            if fail is not None:
                fail("json", str(exc))
            raise

    def constant(token: str) -> Any:
        if fail is not None:
            fail("json", f"nonstandard constant {token}")
        raise ValueError(f"nonfinite JSON number: {token}")

    try:
        return json.loads(
            source,
            object_pairs_hook=pairs,
            parse_constant=constant,
            parse_float=parse_float,
        )
    except json.JSONDecodeError as exc:
        if fail is not None:
            fail("json", str(exc))
        raise ValueError(f"invalid JSON: {exc}") from exc
    except RecursionError as exc:
        if fail is not None:
            fail("json", "JSON nesting exceeds the parser limit")
        raise ValueError("JSON nesting exceeds the parser limit") from exc
